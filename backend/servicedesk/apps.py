from django.apps import AppConfig


class ServicedeskConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'servicedesk'

    def ready(self):
        import servicedesk.signals  # noqa: F401

        # Auto-sync org_config.py on server startup
        import threading
        def _sync():
            try:
                from org_config_sync import sync_org_config
                depts, teams = sync_org_config(force=True)
                if depts or teams:
                    import logging
                    logging.getLogger(__name__).info(
                        f'org_config sync: created {depts} dept(s), {teams} team(s)'
                    )
            except Exception:
                pass
            # Bulk-sync user.team FK → Team.members M2M (single query instead of per-user loop)
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO teams_team_members (team_id, customuser_id)
                        SELECT u.team_id, u.id
                        FROM accounts_customuser u
                        WHERE u.team_id IS NOT NULL
                          AND NOT EXISTS (
                            SELECT 1 FROM teams_team_members m
                            WHERE m.team_id = u.team_id AND m.customuser_id = u.id
                          )
                    """)
            except Exception:
                pass
        # Run in a thread to avoid blocking startup and migration checks
        threading.Timer(2, _sync).start()
