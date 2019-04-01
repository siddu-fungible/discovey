# import django
import os

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
# django.setup()
from fun_settings import COMMON_WEB_LOGGER_NAME
from django.db import models
from fun_global import RESULTS
from fun_global import is_lite_mode, get_current_time
from web.fun_test.jira_models import *
from web.fun_test.demo1_models import *
from rest_framework import serializers
from datetime import datetime, timedelta
from scheduler.scheduler_global import SchedulerStates, SuiteType, SchedulerJobPriority, JobStatusType
import json
from rest_framework.serializers import ModelSerializer


logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)

RESULT_CHOICES = [(k, v)for k, v in RESULTS.items()]

TAG_LENGTH = 50

class TimeKeeper(models.Model):
    time = models.DateTimeField(default=datetime.now)
    name = models.TextField(default="", unique=True)

    @staticmethod
    def set_time(name, time):
        try:
            time_keeper_obj = TimeKeeper.objects.get(name=name)
        except ObjectDoesNotExist:
            time_keeper_obj = TimeKeeper(name=name, time=time)
        time_keeper_obj.time = time
        time_keeper_obj.save()

    @staticmethod
    def get(name):
        result = None
        try:
            time_keeper_obj = TimeKeeper.objects.get(name=name)
            result = time_keeper_obj.time
        except ObjectDoesNotExist as ex:
            logging.exception(str(ex))
        return result


class CatalogTestCase(models.Model):
    jira_id = models.IntegerField()

    def __str__(self):
        return str(self.jira_id)

class TestBed(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{} {}".format(self.name, self.description)


class CatalogSuite(models.Model):
    category = models.CharField(max_length=20,
                                choices=[(k, v) for k, v in CATALOG_CATEGORIES.items()],
                                default=CATALOG_CATEGORIES["ON_DEMAND"])
    jqls = models.TextField(default="[]")
    name = models.TextField(default="UNKNOWN", unique=True)
    test_cases = models.ManyToManyField(CatalogTestCase, blank=True)


    def __str__(self):
        s = "{} {}".format(self.category, self.name)
        return s

class SuiteContainerExecution(models.Model):
    suite_path = models.CharField(max_length=200, default="")
    execution_id = models.IntegerField(unique=True)
    tags = models.TextField(default="[]")
    version = models.TextField(default=-1)
    suite_item_execution_ids = models.TextField(default="[]")

    def __str__(self):
        s = "E: {} Tags: {} I: {}".format(self.execution_id, str(self.tags), str(self.suite_item_execution_ids))
        return s


class SuiteExecution(models.Model):
    """
    Suite selection
    """
    suite_path = models.CharField(max_length=100)
    suite_type = models.TextField(default=SuiteType.STATIC)
    dynamic_suite_spec = models.TextField(default="{}", null=True)

    """
    Job inputs related
    """
    test_bed_type = models.TextField(default="")
    environment = models.TextField(default="{}", null=True)  # extra environment dictionary (only networking uses this)
    inputs = models.TextField(default="{}", null=True)  # inputs dictionary
    build_url = models.TextField(default="")
    version = models.CharField(max_length=50, null=True)
    requested_priority_category = models.TextField(default=SchedulerJobPriority.NORMAL)
    tags = models.TextField(default="[]")

    """
    Scheduling
    """
    scheduling_type = models.TextField(default="")
    submitted_time = models.DateTimeField(null=True)
    scheduled_time = models.DateTimeField(null=True)
    queued_time = models.DateTimeField(null=True)
    completed_time = models.DateTimeField()
    requested_days = models.TextField(default="[]")  # Days of the week as an array with Monday being 0
    requested_hour = models.IntegerField(null=True)  # Hour of the day
    requested_minute = models.IntegerField(null=True)  # minute in the hour
    timezone_string = models.TextField(default="PST")  # timezone string PST or IST
    repeat_in_minutes = models.IntegerField(null=True)  # Repeat the job in some minutes

    """
    Job result related
    """
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default="UNKNOWN")
    emails = models.TextField(default="[]", null=True)  # email addresses to send reports to
    email_on_failure_only = models.BooleanField(default=False)

    """
    Execution
    """
    state = models.TextField(default=JobStatusType.SUBMITTED)
    suite_container_execution_id = models.IntegerField(default=-1)
    is_scheduled_job = models.BooleanField(default=False)
    finalized = models.BooleanField(default=False)
    banner = models.TextField(default="")
    execution_id = models.IntegerField(unique=True, db_index=True)
    test_case_execution_ids = models.CharField(max_length=10000, default="[]")
    # catalog_reference = models.TextField(null=True, blank=True, default=None)
    build_done = models.BooleanField(default=False)

    def __str__(self):
        s = "Suite: {} {} state: {}".format(self.execution_id, self.suite_path, self.state)
        return s

    class Meta:
        indexes = [
            models.Index(fields=['execution_id'])
        ]

    def set_state(self, state):
        self.state = state
        self.save()


class SuiteExecutionSerializer(serializers.Serializer):
    version = serializers.CharField(max_length=50)
    execution_id = serializers.IntegerField()

    class Meta:
        model = SuiteExecution
        fields = ('version', 'execution_id')


class LastSuiteExecution(models.Model):
    last_suite_execution_id = models.IntegerField(unique=True, default=10)


class LastTestCaseExecution(models.Model):
    last_test_case_execution_id = models.IntegerField(unique=True, default=10)

class TestCaseExecution(models.Model):
    script_path = models.CharField(max_length=128)
    execution_id = models.IntegerField(unique=True, db_index=True)
    test_case_id = models.IntegerField()
    suite_execution_id = models.IntegerField(db_index=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default="NOTRUN")
    started_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    overridden_result = models.BooleanField(default=False)
    bugs = models.TextField(default="[]")
    comments = models.TextField(default="")
    log_prefix = models.TextField(default="")
    tags = models.TextField(default="[]")
    inputs = models.TextField(default="{}")
    re_run_history = models.TextField(default="[]")
    re_run_state = models.TextField(default="")

    class Meta:
        indexes = [
            models.Index(fields=['execution_id']),
            models.Index(fields=['suite_execution_id'])
        ]

    def __str__(self):
        s = "E: {} S: {} T: {} R: {} P: {} Re: {} Reh: {}".format(self.execution_id,
                                                   self.suite_execution_id,
                                                   self.test_case_id,
                                                   self.result,
                                                   self.script_path,
                                                          self.re_run_state,
                                                          self.re_run_history)
        return s

    def add_re_run_entry(self, entry):
        current_history = json.loads(self.re_run_history)
        current_history.append(entry)
        self.re_run_history = json.dumps(current_history)

class TestCaseExecutionSerializer(ModelSerializer):
    started_time = serializers.DateTimeField()
    end_time = models.DateTimeField()
    class Meta:
        model = TestCaseExecution
        fields = "__all__"

class Tag(models.Model):
    tag = models.CharField(max_length=TAG_LENGTH)

    def __str__(self):
        return self.tag

class Engineer(models.Model):
    email = models.CharField(max_length=100)
    short_name = models.CharField(max_length=20)

    def __str__(self):
        return "{} {}".format(self.short_name, self.email)



class CatalogSuiteExecution(models.Model):
    suite_execution_id = models.IntegerField(unique=True)
    owner_email = models.EmailField()
    instance_name = models.CharField(max_length=50, unique=True)
    catalog_name = models.TextField(default="UNKNOWN")
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default="UNKNOWN")
    active = models.BooleanField(default=False)

    def __str__(self):
        return "{} {} {} {}".format(self.suite_execution_id, self.owner_email, self.instance_name, self.result)

class CatalogTestCaseExecution(models.Model):
    execution_id = models.IntegerField(unique=True)
    catalog_suite_execution_id = models.IntegerField(default=0)
    jira_id = models.IntegerField()
    engineer = models.ForeignKey(Engineer)
    test_bed = models.CharField(max_length=100, default="simulation")

    # result

    def __str__(self):
        return "{} {} {} {}".format(self.execution_id, self.jira_id, self.engineer, self.test_bed)

class Module(models.Model):
    name = models.TextField(unique=True)
    verbose_name = models.TextField(default="Verbose Name")

class JenkinsJobIdMap(models.Model):
    jenkins_job_id = models.IntegerField()
    fun_sdk_branch = models.TextField(default="")
    git_commit = models.TextField(default="")
    software_date = models.IntegerField(default=0)
    hardware_version = models.TextField(default="")
    completion_date = models.TextField(default="")
    build_properties = models.TextField(default="")

    def __str__(self):
        return "{} {} {} {}".format(self.completion_date, self.jenkins_job_id, self.fun_sdk_branch, self.hardware_version)

class JenkinsJobIdMapSerializer(ModelSerializer):
    class Meta:
        model = JenkinsJobIdMap
        fields = "__all__"

class JiraCache(models.Model):
    jira_id = models.IntegerField()
    module = models.CharField(max_length=100, default="networking")

class RegresssionScripts(models.Model):
    """
    This is probably a temporary model. We can store the path to several scripts that can be considered as regression
    scripts
    """
    script_path = models.TextField(unique=True)
    modules = models.TextField(default='["storage"]')  # Refers to class Module
    components = models.TextField(default=json.dumps(['component1']))
    tags = models.TextField(default=json.dumps(['tag1']))
    baseline_suite_execution_id = models.IntegerField(default=-1, null=True)

class RegresssionScriptsSerializer(serializers.Serializer):
    script_path = serializers.CharField(max_length=200)
    modules = serializers.SerializerMethodField()
    components = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    def get_modules(self, obj):
        return json.loads(obj.modules)

    def get_components(self, obj):
        return json.loads(obj.components)

    def get_tags(self, obj):
        return json.loads(obj.tags)

    class Meta:
        model = RegresssionScripts
        fields = ('script_path', 'modules', 'components', 'tags', 'id', 'baseline_suite_execution_id')

class ScriptInfo(models.Model):
    script_id = models.IntegerField()
    created_time = models.DateTimeField(default=datetime.now)
    status = models.TextField(default="ACTIVE")
    bug = models.TextField(default="")

class SchedulerInfo(models.Model):
    """
    A place to store scheduler state such as time started, time restarted, current state
    """
    state = models.CharField(max_length=30, default=SchedulerStates.SCHEDULER_STATE_UNKNOWN)
    last_start_time = models.DateTimeField(default=datetime.now)
    last_restart_request_time = models.DateTimeField(default=datetime.now)
    main_loop_heartbeat = models.IntegerField(default=0)

class SuiteReRunInfo(models.Model):
    """
    Suite execution id to re-run suite id mappings
    """
    original_suite_execution_id = models.IntegerField()
    re_run_suite_execution_id = models.IntegerField()






class JobQueue(models.Model):
    """
    Scheduler's job queue
    """
    priority = models.IntegerField()
    job_id = models.IntegerField(unique=True)
    test_bed_type = models.TextField(default="", null=True)
    message = models.TextField(default="", null=True)

if not is_lite_mode():
    from web.fun_test.metrics_models import *


if __name__ == "__main__":
    #import django
    #import os

    #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
    #django.setup()
    pass
