# Custom migration: add abbreviation and populate for existing departments

from django.db import migrations, models


def populate_abbreviations(apps, schema_editor):
    Department = apps.get_model('teams', 'Department')
    for dept in Department.objects.all():
        if not dept.abbreviation:
            words = dept.name.split()
            if len(words) == 1:
                dept.abbreviation = dept.name[:3].upper()
            else:
                dept.abbreviation = ''.join(w[0] for w in words).upper()
            dept.save(update_fields=['abbreviation'])


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0002_team_members_department_team_department'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='abbreviation',
            field=models.CharField(blank=True, help_text='Short code e.g. IT, HR, FIN. Auto-generated if blank.', max_length=10),
        ),
        migrations.RunPython(populate_abbreviations, migrations.RunPython.noop),
    ]
