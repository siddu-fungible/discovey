from django.apps import AppConfig
from django.contrib import admin
from lib.utilities.jira_manager import JiraManager
from lib.utilities.mongo_db_manager import MongoDbManager
from lib.utilities.git_manager import GitManager
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Lock
#from scheduler.scheduler import scheduler
#from web.fun_test.django_scheduler.django_scheduler import SchedulerMainWorker


class ListAdminMixin(object):
    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields if field.name != "id"]
        super(ListAdminMixin, self).__init__(model, admin_site)


class FunTestConfig(AppConfig):

    name = "web.fun_test"
    scheduler_thread = None

    def __init__(self, *args, **kwargs):
        super(FunTestConfig, self).__init__(*args, **kwargs)
        self.metric_models = {}

        self.mongo_db_manager = None


    def start_scheduler(self):
        """ Not used yet """
        self.scheduler_thread = SchedulerMainWorker()
        print "Starting Scheduler"
        self.scheduler_thread.start()


    def scheduler_pre_flight(self):
        from web.fun_test.models import SchedulerInfo
        try:
            if SchedulerInfo.objects.count() == 0:
                SchedulerInfo().save()
        except:
            pass

    def ready(self):
        self.set_metric_models()

        ''' Auto-register models for admin '''
        models = self.get_models()
        for model in models:
            admin_class = type('AdminClass', (ListAdminMixin, admin.ModelAdmin), {})
            try:
                admin.site.register(model, admin_class)
            except admin.sites.AlreadyRegistered:
                pass

        # self.start_scheduler()
        self.scheduler_pre_flight()


    def get_mongo_db_manager(self):
        if not self.mongo_db_manager:
            self.mongo_db_manager = MongoDbManager()
        return self.mongo_db_manager

    def get_jira_manager(self):
        if not hasattr(self, "jira_manager"):
            self.jira_manager = JiraManager()
        return self.jira_manager

    def get_site_lock(self):
        if not hasattr(self, "lock"):
            self.lock = Lock()
        return self.lock

    def get_git_manager(self):
        if not hasattr(self, "git_manager"):
            self.git_manager = GitManager()
        return self.git_manager

    def get_background_scheduler(self):
        if not hasattr(self, "background_scheduler"):
            self.background_scheduler = BackgroundScheduler()
            self.background_scheduler.start()
        return self.background_scheduler

    def set_metric_models(self):
        for model in self.get_models():
            self.metric_models[model.__name__] = model

    def get_metric_models(self):
        return self.metric_models