"""
SLA Engine for Enterprise Service Desk.

Provides business-hours-aware SLA calculation, policy matching, lifecycle
management, and audit logging.  Every datetime operation uses
``django.utils.timezone.now()`` and handles timezone-aware values throughout.
"""

import json
import logging
from datetime import datetime, time, timedelta

import pytz
from django.utils import timezone

from .models import (
    BusinessSchedule,
    SLAAuditLog,
    SLAPolicy,
    SLATarget,
    TicketSLAInstance,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Metrics that begin counting the moment a ticket is created.
CREATION_METRICS = frozenset({
    "first_reply_time",
    "requester_wait_time",
    "agent_work_time",
    "total_resolution_time",
})

# Metrics that begin counting only after a later event.
DEFERRED_METRICS = frozenset({
    "next_reply_time",
    "pausable_update_time",
})

# Every metric the engine knows about.
ALL_METRICS = CREATION_METRICS | DEFERRED_METRICS

# =========================================================================
# 1.  Business Hours Engine
# =========================================================================


def get_default_schedule_hours():
    """Return the default Mon-Fri 08:00-17:00 schedule as a list of dicts.

    Format::

        [{"day": 0, "start": "08:00", "end": "17:00"}, ...]

    ``day`` follows Python's weekday convention: 0 = Monday ... 4 = Friday.
    """
    return [
        {"day": day, "start": "08:00", "end": "17:00"}
        for day in range(5)  # Monday through Friday
    ]


def _parse_schedule(schedule):
    """Return ``(hours_list, holidays_set, tz)`` from a BusinessSchedule or
    ``None``.

    *hours_list* is a list of dicts as described in
    ``get_default_schedule_hours``.  *holidays_set* is a ``set`` of
    ``datetime.date`` objects.  *tz* is a ``pytz`` timezone.
    """
    if schedule is None:
        return get_default_schedule_hours(), set(), pytz.UTC

    hours = schedule.hours if schedule.hours else get_default_schedule_hours()
    tz = pytz.timezone(schedule.timezone) if schedule.timezone else pytz.UTC

    holidays = set()
    if schedule.holidays:
        for h in schedule.holidays:
            if isinstance(h, str):
                try:
                    holidays.add(datetime.strptime(h, "%Y-%m-%d").date())
                except ValueError:
                    logger.warning("Ignoring unparseable holiday string: %s", h)
            elif hasattr(h, "date"):
                # Already a date/datetime-like object.
                holidays.add(h if not callable(getattr(h, "date", None)) else h.date())

    return hours, holidays, tz


def _get_day_window(dt_local, hours_list):
    """Return ``(start_time, end_time)`` for *dt_local*'s weekday, or
    ``None`` if the day has no business hours defined.

    *hours_list* is as produced by ``get_default_schedule_hours``.
    """
    weekday = dt_local.weekday()  # 0 = Monday
    for entry in hours_list:
        if entry["day"] == weekday:
            start = time.fromisoformat(entry["start"])
            end = time.fromisoformat(entry["end"])
            return start, end
    return None


def is_holiday(dt, holidays):
    """Return ``True`` if *dt*'s date is present in *holidays*.

    *holidays* can be a set/list of ``datetime.date`` objects or ISO-format
    date strings.
    """
    check_date = dt.date() if hasattr(dt, "date") and callable(dt.date) else dt
    for h in holidays:
        if isinstance(h, str):
            try:
                if datetime.strptime(h, "%Y-%m-%d").date() == check_date:
                    return True
            except ValueError:
                continue
        elif hasattr(h, "date") and callable(h.date):
            if h.date() == check_date:
                return True
        else:
            if h == check_date:
                return True
    return False


def is_business_time(dt, schedule=None):
    """Return ``True`` if *dt* falls within business hours.

    If *schedule* is ``None`` the default Mon-Fri 08:00-17:00 UTC schedule
    is used.  Otherwise *schedule* must be a :class:`BusinessSchedule`
    instance.
    """
    hours, holidays, tz = _parse_schedule(schedule)
    dt_local = dt.astimezone(tz)

    if is_holiday(dt_local, holidays):
        return False

    window = _get_day_window(dt_local, hours)
    if window is None:
        return False

    start, end = window
    local_time = dt_local.time()
    return start <= local_time < end


def get_next_business_time(dt, schedule=None):
    """Return the earliest business-time moment >= *dt*.

    If *dt* is already within business hours it is returned unchanged.
    """
    hours, holidays, tz = _parse_schedule(schedule)
    dt_local = dt.astimezone(tz)

    # Safety limit to avoid infinite loops on misconfigured schedules.
    max_days = 365
    for _ in range(max_days):
        if not is_holiday(dt_local, holidays):
            window = _get_day_window(dt_local, hours)
            if window is not None:
                start, end = window
                local_time = dt_local.time()

                if local_time < start:
                    # Before business hours today -- snap to opening.
                    dt_local = dt_local.replace(
                        hour=start.hour,
                        minute=start.minute,
                        second=0,
                        microsecond=0,
                    )
                    return dt_local.astimezone(dt.tzinfo or pytz.UTC)

                if start <= local_time < end:
                    # Already in business hours.
                    return dt

        # Advance to start-of-day tomorrow and retry.
        dt_local = (dt_local + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    logger.error(
        "get_next_business_time: could not find business time within %d days "
        "of %s -- returning original datetime.",
        max_days,
        dt,
    )
    return dt


def calculate_business_minutes(start_dt, end_dt, schedule=None):
    """Calculate the number of elapsed **business minutes** between
    *start_dt* and *end_dt*.

    Non-business time (nights, weekends, holidays) is excluded.  If
    *end_dt* <= *start_dt*, returns ``0``.
    """
    if end_dt <= start_dt:
        return 0

    hours, holidays, tz = _parse_schedule(schedule)

    cursor = start_dt.astimezone(tz)
    end_local = end_dt.astimezone(tz)
    total_minutes = 0

    # Safety limit.
    max_iterations = 366 * 24 * 60  # roughly one year of minutes
    iterations = 0

    while cursor < end_local and iterations < max_iterations:
        iterations += 1

        if is_holiday(cursor, holidays):
            cursor = (cursor + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            continue

        window = _get_day_window(cursor, hours)
        if window is None:
            # No business hours today -- skip to next day.
            cursor = (cursor + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            continue

        day_start = cursor.replace(
            hour=window[0].hour,
            minute=window[0].minute,
            second=0,
            microsecond=0,
        )
        day_end = cursor.replace(
            hour=window[1].hour,
            minute=window[1].minute,
            second=0,
            microsecond=0,
        )

        if cursor < day_start:
            cursor = day_start

        if cursor >= day_end:
            # Past business hours today -- jump to next day.
            cursor = (cursor + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            continue

        # Determine how much of the current business window to count.
        effective_end = min(end_local, day_end)
        delta = effective_end - cursor
        total_minutes += delta.total_seconds() / 60.0

        # Move cursor past this window.
        cursor = day_end

    return int(round(total_minutes))


def add_business_minutes(start_dt, minutes, schedule=None):
    """Add *minutes* business minutes to *start_dt* and return the
    resulting deadline datetime.

    Non-business time is skipped.
    """
    if minutes <= 0:
        return start_dt

    hours, holidays, tz = _parse_schedule(schedule)

    cursor = get_next_business_time(start_dt, schedule).astimezone(tz)
    remaining = float(minutes)

    # Safety limit.
    max_days = 366
    days_iterated = 0

    while remaining > 0 and days_iterated < max_days:
        days_iterated += 1

        if is_holiday(cursor, holidays):
            cursor = (cursor + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0,
            )
            # After advancing day, snap to next business open.
            cursor = get_next_business_time(cursor.astimezone(start_dt.tzinfo or pytz.UTC), schedule).astimezone(tz)
            continue

        window = _get_day_window(cursor, hours)
        if window is None:
            cursor = (cursor + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0,
            )
            cursor = get_next_business_time(cursor.astimezone(start_dt.tzinfo or pytz.UTC), schedule).astimezone(tz)
            continue

        day_start = cursor.replace(
            hour=window[0].hour, minute=window[0].minute,
            second=0, microsecond=0,
        )
        day_end = cursor.replace(
            hour=window[1].hour, minute=window[1].minute,
            second=0, microsecond=0,
        )

        if cursor < day_start:
            cursor = day_start

        if cursor >= day_end:
            cursor = (cursor + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0,
            )
            cursor = get_next_business_time(cursor.astimezone(start_dt.tzinfo or pytz.UTC), schedule).astimezone(tz)
            continue

        available = (day_end - cursor).total_seconds() / 60.0

        if remaining <= available:
            cursor = cursor + timedelta(minutes=remaining)
            remaining = 0
        else:
            remaining -= available
            cursor = (cursor + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0,
            )
            cursor = get_next_business_time(cursor.astimezone(start_dt.tzinfo or pytz.UTC), schedule).astimezone(tz)

    return cursor.astimezone(start_dt.tzinfo or pytz.UTC)


# =========================================================================
# 2.  Policy Matching Engine
# =========================================================================

# Maps condition keys to callables that extract the comparable value from a
# ticket.  Each callable returns a **string** (or ``None`` when the value
# cannot be resolved).
_CONDITION_EXTRACTORS = {
    "priority": lambda t: getattr(t, "priority", None),
    "status": lambda t: getattr(t, "status", None),
    "team": lambda t: str(t.team_id) if getattr(t, "team_id", None) else None,
    "department": lambda t: (
        str(t.team.department_id)
        if getattr(t, "team", None) is not None
        and getattr(t.team, "department_id", None) is not None
        else None
    ),
}


def evaluate_conditions(ticket, conditions):
    """Check if *ticket* matches every entry in *conditions*.

    *conditions* is a ``dict`` mapping condition keys to lists of acceptable
    values.  All conditions must match (AND logic).  If a key has no known
    extractor it is silently skipped (forward-compatibility).

    Returns ``True`` if **all** resolvable conditions match.
    """
    if not conditions:
        return True

    for key, acceptable_values in conditions.items():
        extractor = _CONDITION_EXTRACTORS.get(key)
        if extractor is None:
            # Unknown condition key -- skip for forward-compatibility.
            continue

        ticket_value = extractor(ticket)
        if ticket_value is None:
            # Cannot resolve the field on this ticket -- condition fails.
            return False

        # Normalise both sides to strings for reliable comparison.
        acceptable_strings = {str(v) for v in acceptable_values}
        if str(ticket_value) not in acceptable_strings:
            return False

    return True


def match_policy(ticket):
    """Return the best matching active :class:`SLAPolicy` for *ticket*.

    Priority order:
    1. Policy with ``team`` matching ticket's team (first by position)
    2. Policy with ``department`` matching ticket's department (first by position)
    3. Conditions-based matching (position-ordered, first match wins)
    4. Default policy (``is_default=True``)
    5. None
    """
    # 1. Team-specific policy
    if ticket.team_id:
        team_policy = (
            SLAPolicy.objects.filter(
                is_active=True, team_id=ticket.team_id
            )
            .order_by("position")
            .first()
        )
        if team_policy:
            return team_policy

    # 2. Department-specific policy
    department_id = None
    if ticket.team_id and hasattr(ticket, 'team') and ticket.team is not None:
        department_id = getattr(ticket.team, 'department_id', None)
    if department_id:
        dept_policy = (
            SLAPolicy.objects.filter(
                is_active=True, department_id=department_id, team__isnull=True,
            )
            .order_by("position")
            .first()
        )
        if dept_policy:
            return dept_policy

    # 3. Conditions-based matching (skip team-bound, dept-bound, and default policies)
    policies = SLAPolicy.objects.filter(
        is_active=True, team__isnull=True, department__isnull=True, is_default=False
    ).order_by("position")

    for policy in policies:
        conditions = policy.conditions or {}
        if evaluate_conditions(ticket, conditions):
            return policy

    # 4. Default fallback
    default_policy = (
        SLAPolicy.objects.filter(is_active=True, is_default=True)
        .order_by("position")
        .first()
    )
    return default_policy


# =========================================================================
# 3.  SLA Lifecycle Manager
# =========================================================================

def create_sla_instances(ticket, policy):
    """For a matched *policy*, create :class:`TicketSLAInstance` records for
    each applicable SLA target at the ticket's current priority.

    Only **creation-time** metrics are instantiated here
    (``first_reply_time``, ``requester_wait_time``, ``agent_work_time``,
    ``total_resolution_time``).  Deferred metrics (``next_reply_time``,
    ``pausable_update_time``) are started by later lifecycle events.

    Returns a list of the newly-created instances.
    """
    now = timezone.now()
    targets = SLATarget.objects.filter(
        policy=policy,
        priority=ticket.priority,
    )

    instances = []
    for target in targets:
        if target.metric not in CREATION_METRICS:
            continue

        started_at = ticket.created_at if hasattr(ticket, "created_at") else now
        due_at = add_business_minutes(started_at, target.target_minutes, policy.schedule)

        instance = TicketSLAInstance.objects.create(
            ticket=ticket,
            policy=policy,
            metric=target.metric,
            target_minutes=target.target_minutes,
            started_at=started_at,
            due_at=due_at,
            state="active",
        )
        instances.append(instance)

        log_sla_event(
            ticket=ticket,
            sla_instance=instance,
            event_type="instance_created",
            old_state="",
            new_state="active",
            details={
                "metric": target.metric,
                "target_minutes": target.target_minutes,
                "due_at": due_at.isoformat(),
            },
        )

    return instances


# --- Ticket lifecycle hooks -----------------------------------------------

def on_ticket_created(ticket):
    """Called when a new ticket is created.

    1. Match the best SLA policy.
    2. Create SLA instances for creation-time metrics.
    3. Log the event.

    Returns the matched :class:`SLAPolicy` or ``None``.
    """
    policy = match_policy(ticket)
    if policy is None:
        logger.info("No SLA policy matched for ticket #%s.", ticket.pk)
        log_sla_event(
            ticket=ticket,
            sla_instance=None,
            event_type="no_policy_matched",
            details={"priority": ticket.priority},
        )
        return None

    logger.info(
        "SLA policy '%s' matched for ticket #%s.",
        policy.name,
        ticket.pk,
    )

    log_sla_event(
        ticket=ticket,
        sla_instance=None,
        event_type="policy_matched",
        details={"policy_id": policy.pk, "policy_name": policy.name},
    )

    create_sla_instances(ticket, policy)
    return policy


def on_status_changed(ticket, old_status, new_status):
    """Handle status transitions for SLA metrics.

    Pause / resume / fulfil rules:

    * **To ``pending``** -- pause ``requester_wait_time``,
      ``agent_work_time``, ``pausable_update_time``.
    * **To ``on_hold``** -- pause ``agent_work_time``.
      ``requester_wait_time`` and ``pausable_update_time`` stay active.
    * **From ``pending`` to ``open``/``new``** -- resume all three paused
      metrics.
    * **From ``on_hold`` to ``open``/``new``** -- resume
      ``agent_work_time``.
    * **To ``solved``** -- fulfil all active metrics:
      ``requester_wait_time``, ``agent_work_time``,
      ``total_resolution_time``, ``pausable_update_time``.
    * **From ``solved`` to ``open`` (reopen)** -- reactivate
      ``total_resolution_time``, ``requester_wait_time``,
      ``agent_work_time``.
    """
    now = timezone.now()
    active_instances = TicketSLAInstance.objects.filter(
        ticket=ticket,
        state__in=["active", "paused"],
    )

    schedule = _get_ticket_schedule(ticket)

    # --- To pending ---
    if new_status == "pending":
        for inst in active_instances:
            if inst.metric in ("requester_wait_time", "agent_work_time", "pausable_update_time"):
                if inst.state == "active":
                    pause_instance(inst, now=now)

    # --- To on_hold ---
    elif new_status == "on_hold":
        for inst in active_instances:
            if inst.metric == "agent_work_time" and inst.state == "active":
                pause_instance(inst, now=now)

    # --- From pending -> open/new (resume) ---
    elif old_status == "pending" and new_status in ("open", "new"):
        for inst in active_instances:
            if inst.metric in ("requester_wait_time", "agent_work_time", "pausable_update_time"):
                if inst.state == "paused":
                    resume_instance(inst, schedule=schedule, now=now)

    # --- From on_hold -> open/new (resume) ---
    elif old_status == "on_hold" and new_status in ("open", "new"):
        for inst in active_instances:
            if inst.metric == "agent_work_time" and inst.state == "paused":
                resume_instance(inst, schedule=schedule, now=now)

    # --- To solved ---
    if new_status == "solved":
        fulfillable = ("requester_wait_time", "agent_work_time",
                       "total_resolution_time", "pausable_update_time")
        for inst in TicketSLAInstance.objects.filter(
            ticket=ticket,
            state__in=["active", "paused"],
            metric__in=fulfillable,
        ):
            if inst.state == "paused":
                resume_instance(inst, schedule=schedule, now=now)
            fulfill_instance(inst, now=now)

    # --- Reopen (solved -> open) ---
    if old_status == "solved" and new_status in ("open", "new"):
        reactivatable = ("total_resolution_time", "requester_wait_time", "agent_work_time")
        for inst in TicketSLAInstance.objects.filter(
            ticket=ticket,
            state="fulfilled",
            metric__in=reactivatable,
        ):
            _reactivate_instance(inst, schedule=schedule, now=now)

    log_sla_event(
        ticket=ticket,
        sla_instance=None,
        event_type="status_changed",
        old_state=old_status,
        new_state=new_status,
    )


def on_public_agent_reply(ticket, response):
    """Called when an agent posts a public reply.

    1. Fulfil ``first_reply_time`` if active.
    2. Fulfil ``next_reply_time`` if active.
    3. Start ``pausable_update_time`` if not yet started (first agent
       reply triggers it).
    4. Reset ``pausable_update_time`` timer (agent has provided an update).
    """
    now = timezone.now()
    schedule = _get_ticket_schedule(ticket)

    # 1. Fulfil first_reply_time
    first_reply = TicketSLAInstance.objects.filter(
        ticket=ticket,
        metric="first_reply_time",
        state="active",
    ).first()
    if first_reply is not None:
        fulfill_instance(first_reply, now=now)

    # 2. Fulfil next_reply_time
    next_reply = TicketSLAInstance.objects.filter(
        ticket=ticket,
        metric="next_reply_time",
        state__in=["active", "paused"],
    ).first()
    if next_reply is not None:
        if next_reply.state == "paused":
            resume_instance(next_reply, schedule=schedule, now=now)
        fulfill_instance(next_reply, now=now)

    # 3 & 4. Handle pausable_update_time
    pausable = TicketSLAInstance.objects.filter(
        ticket=ticket,
        metric="pausable_update_time",
    ).first()

    if pausable is None:
        # First agent reply -- create the instance now.
        policy = _get_ticket_policy(ticket)
        if policy is not None:
            target = SLATarget.objects.filter(
                policy=policy,
                metric="pausable_update_time",
                priority=ticket.priority,
            ).first()
            if target is not None:
                due_at = add_business_minutes(now, target.target_minutes, schedule)
                pausable = TicketSLAInstance.objects.create(
                    ticket=ticket,
                    policy=policy,
                    metric="pausable_update_time",
                    target_minutes=target.target_minutes,
                    started_at=now,
                    due_at=due_at,
                    state="active",
                )
                log_sla_event(
                    ticket=ticket,
                    sla_instance=pausable,
                    event_type="instance_created",
                    new_state="active",
                    details={"trigger": "agent_reply"},
                )
    else:
        # Reset the timer -- agent provided an update.
        if pausable.state in ("active", "paused"):
            _reset_instance_timer(pausable, schedule=schedule, now=now)

    log_sla_event(
        ticket=ticket,
        sla_instance=None,
        event_type="agent_reply",
        details={"response_id": response.pk if response else None},
    )


def on_requester_reply(ticket, response):
    """Called when the requester posts a public reply.

    Creates or activates a ``next_reply_time`` SLA instance so the clock
    starts ticking for the next agent response.
    """
    now = timezone.now()
    schedule = _get_ticket_schedule(ticket)

    # If there is already an active next_reply_time, leave it alone.
    existing = TicketSLAInstance.objects.filter(
        ticket=ticket,
        metric="next_reply_time",
        state__in=["active", "paused"],
    ).first()

    if existing is not None:
        # Already tracking -- nothing to do.
        log_sla_event(
            ticket=ticket,
            sla_instance=existing,
            event_type="requester_reply",
            details={"action": "next_reply_time_already_active"},
        )
        return

    policy = _get_ticket_policy(ticket)
    if policy is None:
        return

    target = SLATarget.objects.filter(
        policy=policy,
        metric="next_reply_time",
        priority=ticket.priority,
    ).first()
    if target is None:
        return

    due_at = add_business_minutes(now, target.target_minutes, schedule)
    instance = TicketSLAInstance.objects.create(
        ticket=ticket,
        policy=policy,
        metric="next_reply_time",
        target_minutes=target.target_minutes,
        started_at=now,
        due_at=due_at,
        state="active",
    )

    log_sla_event(
        ticket=ticket,
        sla_instance=instance,
        event_type="instance_created",
        new_state="active",
        details={"trigger": "requester_reply"},
    )


def on_priority_changed(ticket, old_priority, new_priority):
    """Recalculate due dates for all active SLA instances when the ticket's
    priority changes.

    For each active instance the engine looks up the target for the *new*
    priority, computes how many business minutes have already elapsed, and
    derives a fresh ``due_at``.
    """
    now = timezone.now()
    schedule = _get_ticket_schedule(ticket)
    policy = _get_ticket_policy(ticket)

    if policy is None:
        return

    active_instances = TicketSLAInstance.objects.filter(
        ticket=ticket,
        state__in=["active", "paused"],
    )

    for instance in active_instances:
        new_target = SLATarget.objects.filter(
            policy=policy,
            metric=instance.metric,
            priority=new_priority,
        ).first()

        if new_target is None:
            # No target defined for the new priority -- leave as-is.
            continue

        old_target_minutes = instance.target_minutes

        # Calculate elapsed business minutes so far.
        if instance.state == "active":
            elapsed = calculate_business_minutes(
                instance.started_at, now, schedule,
            )
            # Subtract accumulated pause time already recorded.
            elapsed = max(0, elapsed - instance.accumulated_pause_minutes)
        else:
            # Paused -- use whatever was recorded at pause time.
            elapsed = instance.active_business_minutes

        remaining = max(0, new_target.target_minutes - elapsed)

        # Compute new due_at from now (or from resume point).
        base_time = now if instance.state == "active" else now
        new_due = add_business_minutes(base_time, remaining, schedule)

        old_due = instance.due_at
        instance.target_minutes = new_target.target_minutes
        instance.due_at = new_due
        instance.save(update_fields=["target_minutes", "due_at"])

        log_sla_event(
            ticket=ticket,
            sla_instance=instance,
            event_type="priority_changed",
            details={
                "old_priority": old_priority,
                "new_priority": new_priority,
                "old_target_minutes": old_target_minutes,
                "new_target_minutes": new_target.target_minutes,
                "old_due_at": old_due.isoformat() if old_due else None,
                "new_due_at": new_due.isoformat(),
                "elapsed_minutes": elapsed,
            },
        )


# --- Instance state transitions --------------------------------------------

def pause_instance(instance, now=None):
    """Pause an active SLA instance.

    Records ``paused_at`` and snapshots the business minutes elapsed so
    far into ``active_business_minutes``.
    """
    if instance.state != "active":
        logger.warning(
            "Cannot pause instance %s -- current state is '%s'.",
            instance.pk,
            instance.state,
        )
        return

    now = now or timezone.now()
    schedule = _get_instance_schedule(instance)

    elapsed = calculate_business_minutes(instance.started_at, now, schedule)
    elapsed = max(0, elapsed - instance.accumulated_pause_minutes)

    old_state = instance.state
    instance.state = "paused"
    instance.paused_at = now
    instance.active_business_minutes = elapsed
    instance.save(update_fields=["state", "paused_at", "active_business_minutes"])

    log_sla_event(
        ticket=instance.ticket,
        sla_instance=instance,
        event_type="instance_paused",
        old_state=old_state,
        new_state="paused",
        details={"active_business_minutes": elapsed},
    )


def resume_instance(instance, schedule=None, now=None):
    """Resume a paused SLA instance.

    Adds the pause duration (in business minutes) to
    ``accumulated_pause_minutes`` and recalculates ``due_at``.
    """
    if instance.state != "paused":
        logger.warning(
            "Cannot resume instance %s -- current state is '%s'.",
            instance.pk,
            instance.state,
        )
        return

    now = now or timezone.now()
    if schedule is None:
        schedule = _get_instance_schedule(instance)

    # Calculate business minutes spent paused.
    if instance.paused_at:
        pause_business_minutes = calculate_business_minutes(
            instance.paused_at, now, schedule,
        )
    else:
        pause_business_minutes = 0

    accumulated = instance.accumulated_pause_minutes + pause_business_minutes
    remaining = max(0, instance.target_minutes - instance.active_business_minutes)
    new_due = add_business_minutes(now, remaining, schedule)

    old_state = instance.state
    instance.state = "active"
    instance.paused_at = None
    instance.accumulated_pause_minutes = accumulated
    instance.due_at = new_due
    instance.save(update_fields=[
        "state", "paused_at", "accumulated_pause_minutes", "due_at",
    ])

    log_sla_event(
        ticket=instance.ticket,
        sla_instance=instance,
        event_type="instance_resumed",
        old_state=old_state,
        new_state="active",
        details={
            "pause_business_minutes": pause_business_minutes,
            "accumulated_pause_minutes": accumulated,
            "new_due_at": new_due.isoformat(),
        },
    )


def fulfill_instance(instance, now=None):
    """Mark an SLA instance as fulfilled, recording ``achieved_at``."""
    if instance.state not in ("active", "paused"):
        logger.warning(
            "Cannot fulfil instance %s -- current state is '%s'.",
            instance.pk,
            instance.state,
        )
        return

    now = now or timezone.now()
    old_state = instance.state

    # Determine whether the SLA was met.
    was_on_time = instance.due_at is not None and now <= instance.due_at

    instance.state = "fulfilled"
    instance.achieved_at = now
    instance.save(update_fields=["state", "achieved_at"])

    log_sla_event(
        ticket=instance.ticket,
        sla_instance=instance,
        event_type="instance_fulfilled",
        old_state=old_state,
        new_state="fulfilled",
        details={
            "achieved_at": now.isoformat(),
            "on_time": was_on_time,
            "due_at": instance.due_at.isoformat() if instance.due_at else None,
        },
    )


def breach_instance(instance, now=None):
    """Mark an SLA instance as breached."""
    if instance.state not in ("active", "paused"):
        logger.warning(
            "Cannot breach instance %s -- current state is '%s'.",
            instance.pk,
            instance.state,
        )
        return

    now = now or timezone.now()
    old_state = instance.state

    instance.state = "breached"
    instance.breached_at = now
    instance.save(update_fields=["state", "breached_at"])

    log_sla_event(
        ticket=instance.ticket,
        sla_instance=instance,
        event_type="instance_breached",
        old_state=old_state,
        new_state="breached",
        details={
            "breached_at": now.isoformat(),
            "due_at": instance.due_at.isoformat() if instance.due_at else None,
        },
    )


def recalculate_sla(ticket):
    """Full re-evaluation when policy-relevant ticket attributes change.

    If the newly matched policy differs from the one on existing instances,
    all active/paused instances are deactivated and fresh ones are created
    under the new policy.  If the same policy still matches, the existing
    instances are left untouched (priority changes are handled separately
    by ``on_priority_changed``).
    """
    now = timezone.now()
    new_policy = match_policy(ticket)

    existing_instances = TicketSLAInstance.objects.filter(
        ticket=ticket,
        state__in=["active", "paused"],
    )

    current_policy_id = None
    if existing_instances.exists():
        first_inst = existing_instances.first()
        current_policy_id = first_inst.policy_id if first_inst else None

    new_policy_id = new_policy.pk if new_policy else None

    if current_policy_id == new_policy_id:
        # Same policy -- nothing to do at the policy level.
        return

    # Deactivate old instances.
    for inst in existing_instances:
        old_state = inst.state
        inst.state = "fulfilled"
        inst.achieved_at = now
        inst.save(update_fields=["state", "achieved_at"])
        log_sla_event(
            ticket=ticket,
            sla_instance=inst,
            event_type="instance_superseded",
            old_state=old_state,
            new_state="fulfilled",
            details={"reason": "policy_changed", "new_policy_id": new_policy_id},
        )

    # Create new instances under the new policy.
    if new_policy is not None:
        create_sla_instances(ticket, new_policy)

    log_sla_event(
        ticket=ticket,
        sla_instance=None,
        event_type="sla_recalculated",
        details={
            "old_policy_id": current_policy_id,
            "new_policy_id": new_policy_id,
        },
    )


# =========================================================================
# 4.  Audit Logging
# =========================================================================

def log_sla_event(ticket, sla_instance, event_type, old_state="", new_state="", details=None):
    """Create an :class:`SLAAuditLog` entry.

    All parameters are persisted as-is.  *details* defaults to an empty
    dict.
    """
    try:
        SLAAuditLog.objects.create(
            ticket=ticket,
            sla_instance=sla_instance,
            event_type=event_type,
            old_state=old_state or "",
            new_state=new_state or "",
            details=details or {},
        )
    except Exception:
        logger.exception(
            "Failed to write SLA audit log for ticket #%s, event '%s'.",
            ticket.pk if ticket else "?",
            event_type,
        )


# =========================================================================
# Internal helpers
# =========================================================================

def _get_ticket_policy(ticket):
    """Return the SLA policy currently associated with *ticket*'s active
    instances, falling back to ``match_policy`` if none exist.
    """
    active = TicketSLAInstance.objects.filter(
        ticket=ticket,
        state__in=["active", "paused"],
    ).select_related("policy").first()

    if active is not None and active.policy is not None:
        return active.policy

    return match_policy(ticket)


def _get_ticket_schedule(ticket):
    """Return the :class:`BusinessSchedule` for *ticket* (via its current
    policy), or ``None`` for the default schedule.
    """
    policy = _get_ticket_policy(ticket)
    if policy is not None:
        return policy.schedule
    return None


def _get_instance_schedule(instance):
    """Return the :class:`BusinessSchedule` associated with an SLA
    instance's policy, or ``None``.
    """
    if instance.policy is not None:
        return instance.policy.schedule
    return None


def _reactivate_instance(instance, schedule=None, now=None):
    """Reactivate a fulfilled instance (e.g. on ticket reopen).

    The timer continues from where it left off: the remaining business
    minutes are used to compute a new ``due_at``.
    """
    now = now or timezone.now()
    if schedule is None:
        schedule = _get_instance_schedule(instance)

    # Compute how many business minutes were consumed before fulfilment.
    if instance.achieved_at and instance.started_at:
        elapsed = calculate_business_minutes(
            instance.started_at, instance.achieved_at, schedule,
        )
        elapsed = max(0, elapsed - instance.accumulated_pause_minutes)
    else:
        elapsed = instance.active_business_minutes

    remaining = max(0, instance.target_minutes - elapsed)
    new_due = add_business_minutes(now, remaining, schedule)

    old_state = instance.state
    instance.state = "active"
    instance.achieved_at = None
    instance.due_at = new_due
    instance.active_business_minutes = elapsed
    instance.save(update_fields=[
        "state", "achieved_at", "due_at", "active_business_minutes",
    ])

    log_sla_event(
        ticket=instance.ticket,
        sla_instance=instance,
        event_type="instance_reactivated",
        old_state=old_state,
        new_state="active",
        details={
            "elapsed_minutes": elapsed,
            "remaining_minutes": remaining,
            "new_due_at": new_due.isoformat(),
        },
    )


def _reset_instance_timer(instance, schedule=None, now=None):
    """Reset the countdown on a recurring metric (e.g.
    ``pausable_update_time``) back to its full target.

    The ``started_at`` is updated to *now* and ``due_at`` is recalculated
    from scratch.
    """
    now = now or timezone.now()
    if schedule is None:
        schedule = _get_instance_schedule(instance)

    new_due = add_business_minutes(now, instance.target_minutes, schedule)

    instance.started_at = now
    instance.due_at = new_due
    instance.accumulated_pause_minutes = 0
    instance.active_business_minutes = 0
    if instance.state == "paused":
        instance.state = "active"
        instance.paused_at = None
    instance.save(update_fields=[
        "started_at", "due_at", "accumulated_pause_minutes",
        "active_business_minutes", "state", "paused_at",
    ])

    log_sla_event(
        ticket=instance.ticket,
        sla_instance=instance,
        event_type="instance_timer_reset",
        new_state=instance.state,
        details={
            "new_started_at": now.isoformat(),
            "new_due_at": new_due.isoformat(),
            "target_minutes": instance.target_minutes,
        },
    )
