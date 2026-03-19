"""
Reusable sync logic for org_config.py ↔ database.
- Reads org_config.py → creates departments/teams in DB
- Writes DB state back → org_config.py when teams/departments change via UI
Tracks the file's last-modified time so it only re-syncs when the file changes.
"""
import sys
import os
from pathlib import Path

_last_mtime = 0.0
_write_lock = False  # Prevent feedback loop when we write the file ourselves


def get_config_path():
    return Path(__file__).resolve().parent / 'org_config.py'


def has_config_changed():
    """Return True if org_config.py has been modified since last sync."""
    global _last_mtime
    config_file = get_config_path()
    if not config_file.exists():
        return False
    current_mtime = os.path.getmtime(config_file)
    return current_mtime != _last_mtime


def sync_org_config(force=False):
    """
    Sync departments/teams from org_config.py into the database.
    Skips if the file hasn't changed since last sync (unless force=True).
    Returns (created_depts, created_teams) tuple.
    """
    global _last_mtime

    config_file = get_config_path()
    if not config_file.exists():
        return 0, 0

    current_mtime = os.path.getmtime(config_file)
    if not force and current_mtime == _last_mtime:
        return 0, 0

    # Import the config
    config_dir = str(config_file.parent)
    if config_dir not in sys.path:
        sys.path.insert(0, config_dir)

    # Force re-import in case file changed
    if 'org_config' in sys.modules:
        del sys.modules['org_config']

    try:
        from org_config import DEPARTMENTS
    except ImportError:
        return 0, 0

    from teams.models import Department, Team

    created_depts = 0
    created_teams = 0

    config_dept_names = set(DEPARTMENTS.keys())
    config_team_map = {}  # dept_name -> set of team names
    for dept_name, teams in DEPARTMENTS.items():
        config_team_map[dept_name] = set(teams)

    for dept_name, teams in DEPARTMENTS.items():
        dept, dept_created = Department.objects.get_or_create(
            name=dept_name,
            defaults={'description': ''},
        )
        if dept_created:
            created_depts += 1

        for team_name in teams:
            _, team_created = Team.objects.get_or_create(
                name=team_name,
                department=dept,
                defaults={'description': ''},
            )
            if team_created:
                created_teams += 1

        # Delete teams no longer in the config for this department
        Team.objects.filter(department=dept).exclude(
            name__in=config_team_map[dept_name]
        ).delete()

    # Delete departments no longer in the config
    Department.objects.exclude(name__in=config_dept_names).delete()

    _last_mtime = current_mtime
    return created_depts, created_teams


def write_config_from_db():
    """
    Write the current DB state of departments/teams back to org_config.py.
    Called when a team or department is created/updated/deleted via the UI.
    """
    global _last_mtime, _write_lock

    if _write_lock:
        return
    _write_lock = True

    try:
        from teams.models import Department, Team

        departments = Department.objects.all().order_by('name')
        data = {}
        for dept in departments:
            teams = list(
                Team.objects.filter(department=dept)
                .order_by('name')
                .values_list('name', flat=True)
            )
            data[dept.name] = teams

        config_file = get_config_path()
        lines = [
            '# Organization Configuration',
            '# --------------------------',
            '# Edit this file to define your organization\'s departments and teams.',
            '# Changes are auto-detected at runtime — no server restart needed.',
            '# You can also manually run: python manage.py sync_org_config',
            '# New departments/teams will be created automatically.',
            '# Existing ones (matched by name) will NOT be duplicated.',
            '',
            'DEPARTMENTS = {',
        ]

        dept_items = list(data.items())
        for i, (dept_name, teams) in enumerate(dept_items):
            lines.append(f'    "{dept_name}": [')
            for team in teams:
                lines.append(f'        "{team}",')
            lines.append('    ],')

        lines.append('}')
        lines.append('')

        config_file.write_text('\n'.join(lines), encoding='utf-8')
        _last_mtime = os.path.getmtime(config_file)
    finally:
        _write_lock = False
