from web.fun_test.models import Engineer


class UsersRouter(object):
    def db_for_read(self, model, **hints):
        if model == Engineer:
            return 'users'
        return 'default'

    def db_for_write(self, model, **hints):
        if model == Engineer:
            return 'users'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
