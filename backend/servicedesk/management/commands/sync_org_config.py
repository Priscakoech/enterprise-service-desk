from django.core.management.base import BaseCommand
from org_config_sync import sync_org_config, get_config_path


class Command(BaseCommand):
    help = 'Sync departments and teams from org_config.py'

    def handle(self, *args, **options):
        config_file = get_config_path()
        if not config_file.exists():
            self.stderr.write(self.style.ERROR(
                'Could not find org_config.py. Make sure it exists in the backend/ directory.'
            ))
            return

        # Force-import to show detailed output
        import sys
        config_dir = str(config_file.parent)
        if config_dir not in sys.path:
            sys.path.insert(0, config_dir)
        if 'org_config' in sys.modules:
            del sys.modules['org_config']

        try:
            from org_config import DEPARTMENTS
        except ImportError:
            self.stderr.write(self.style.ERROR(
                'Could not import org_config.py.'
            ))
            return

        from teams.models import Department, Team

        created_depts = 0
        created_teams = 0

        for dept_name, teams in DEPARTMENTS.items():
            dept, dept_created = Department.objects.get_or_create(
                name=dept_name,
                defaults={'description': ''},
            )
            if dept_created:
                created_depts += 1
                self.stdout.write(self.style.SUCCESS(f'  + Department: {dept_name}'))
            else:
                self.stdout.write(f'  = Department: {dept_name} (exists)')

            for team_name in teams:
                _, team_created = Team.objects.get_or_create(
                    name=team_name,
                    department=dept,
                    defaults={'description': ''},
                )
                if team_created:
                    created_teams += 1
                    self.stdout.write(self.style.SUCCESS(f'      + Team: {team_name}'))
                else:
                    self.stdout.write(f'      = Team: {team_name} (exists)')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done. Created {created_depts} department(s) and {created_teams} team(s).'
        ))
