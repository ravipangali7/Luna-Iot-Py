# luna_iot_py/luna_iot_py/db_routers.py
class NoAuthMigrationsRouter:
    BLOCKED_APPS = {
        'auth',
        'contenttypes',
        'admin',
        'sessions',
        'messages',
    }

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.BLOCKED_APPS:
            return False
        return None  