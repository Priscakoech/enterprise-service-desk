# Custom migration: add reference_id, populate existing tickets, then enforce unique

from django.db import migrations, models
from django.utils import timezone


def populate_reference_ids(apps, schema_editor):
    """Generate reference_id for all existing tickets that don't have one."""
    ServiceTicket = apps.get_model('servicedesk', 'ServiceTicket')
    Department = apps.get_model('teams', 'Department')

    # Build dept id -> abbreviation map
    dept_map = {}
    for dept in Department.objects.all():
        if not dept.abbreviation:
            words = dept.name.split()
            if len(words) == 1:
                abbrev = dept.name[:3].upper()
            else:
                abbrev = ''.join(w[0] for w in words).upper()
        else:
            abbrev = dept.abbreviation
        dept_map[dept.id] = abbrev

    for ticket in ServiceTicket.objects.select_related('category', 'category__department').all():
        if ticket.reference_id:
            continue
        dept_abbrev = 'GEN'
        if ticket.category and ticket.category.department_id:
            dept_abbrev = dept_map.get(ticket.category.department_id, 'GEN')
        num_padded = str(ticket.pk).zfill(3)
        date_str = ticket.created_at.strftime('%d%m%y') if ticket.created_at else timezone.now().strftime('%d%m%y')
        ticket.reference_id = f'{dept_abbrev}TKTREQ{num_padded}{date_str}'
        ticket.save(update_fields=['reference_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('servicedesk', '0004_slapolicy_category_slapolicy_is_default'),
        ('teams', '0003_department_abbreviation'),
    ]

    operations = [
        # Step 1: Add field without unique constraint
        migrations.AddField(
            model_name='serviceticket',
            name='reference_id',
            field=models.CharField(blank=True, default='', help_text='Auto-generated e.g. HRTKTREQ001150326', max_length=30),
        ),
        # Step 2: Populate existing rows
        migrations.RunPython(populate_reference_ids, migrations.RunPython.noop),
        # Step 3: Now enforce unique
        migrations.AlterField(
            model_name='serviceticket',
            name='reference_id',
            field=models.CharField(blank=True, help_text='Auto-generated e.g. HRTKTREQ001150326', max_length=30, unique=True),
        ),
    ]
