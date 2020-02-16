# import django
import os

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
# django.setup()
from django.dispatch import receiver

from fun_settings import COMMON_WEB_LOGGER_NAME
from django.db import models
from fun_global import RESULTS
from fun_global import is_lite_mode, get_current_time, get_epoch_time_from_datetime
from web.fun_test.jira_models import *
#from web.fun_test.demo1_models import *
from rest_framework import serializers
from datetime import datetime, timedelta
from scheduler.scheduler_global import SchedulerStates, SuiteType, SchedulerJobPriority, JobStatusType
from django.contrib.postgres.fields import JSONField, ArrayField
import json
from asset.asset_global import AssetType, AssetHealthStates
from rest_framework.serializers import ModelSerializer
from django.utils import timezone
import logging
from django.contrib.auth.models import User as AuthUser
from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist



logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)

RESULT_CHOICES = [(k, v)for k, v in RESULTS.items()]

TAG_LENGTH = 50


class SiteConfig(models.Model):
    version = models.IntegerField(default=101)
    announcement = models.TextField(default="", null=True, blank=True)
    announcement_level = models.IntegerField(default=1)

    def bump_version(self):
        self.version += 1
        self.save()

    @staticmethod
    def get_version():
        result = 100
        try:
            result = SiteConfig.objects.all()[0].version
        except:
            pass
        return result

class FunModel(models.Model):
    def to_dict(self):
        result = {}
        fields = self._meta.get_fields()
        for field in fields:
            value = getattr(self, field.name)
            result[field.name] = value
            if type(value) == datetime:
                result[field.name + "_timestamp"] = get_epoch_time_from_datetime(value)
        return result

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


class SavedJobConfig(FunModel):
    config = JSONField(default=None, null=True)


class TestBed(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    manual_lock = models.BooleanField(default=False)
    manual_lock_expiry_time = models.DateTimeField(default=datetime.now)
    manual_lock_submitter = models.EmailField(null=True, blank=True)
    disabled = models.BooleanField(default=False)
    health_check_enabled = models.BooleanField(default=True)
    state_change_time = models.DateTimeField(default=timezone.now)
    health_status = models.IntegerField(default=AssetHealthStates.HEALTHY)
    health_check_message = models.TextField(default="")

    def __str__(self):
        return "{} {} {} {} {}".format(self.name,
                                       self.description,
                                       self.manual_lock,
                                       self.manual_lock_expiry_time,
                                       self.manual_lock_submitter)

    def set_health(self, status, force_update=False, message=""):
        if status != self.health_status or force_update:
            self.health_status = status
            self.state_change_time = get_current_time()
            self.health_check_message = message
            # if status == AssetHealthStates.UNHEALTHY:
            #     self.disabled = True
            self.save()
        if message != self.health_check_message:
            self.health_check_message = message
            self.save()


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
    suite_path = models.CharField(max_length=100, null=True)
    suite_id = models.IntegerField(null=True)  # replacement for suite_path
    script_path = models.TextField(default=None, null=True)
    suite_type = models.TextField(default=SuiteType.STATIC)
    dynamic_suite_spec = models.TextField(default="{}", null=True)

    """
    Job inputs related
    """
    test_bed_type = models.TextField(default="")
    environment = models.TextField(default="{}", null=True)  # extra environment dictionary (only networking uses this)
    inputs = models.TextField(default="{}", null=True)  # inputs dictionary
    build_url = models.TextField(default="", null=True)
    version = models.CharField(max_length=50, null=True)
    requested_priority_category = models.TextField(default=SchedulerJobPriority.NORMAL)
    tags = models.TextField(default="[]", null=True)
    description = models.TextField(default="", null=True)

    """
    Scheduling
    """
    scheduling_type = models.TextField(default="")
    submitted_time = models.DateTimeField(null=True)
    scheduled_time = models.DateTimeField(null=True)
    queued_time = models.DateTimeField(null=True)
    completed_time = models.DateTimeField()
    started_time = models.DateTimeField(null=True)
    requested_days = models.TextField(default="[]")  # Days of the week as an array with Monday being 0
    requested_hour = models.IntegerField(null=True)  # Hour of the day
    requested_minute = models.IntegerField(null=True)  # minute in the hour
    timezone_string = models.TextField(default="PST")  # timezone string PST or IST
    repeat_in_minutes = models.IntegerField(null=True)  # Repeat the job in some minutes
    submitter_email = models.EmailField(default="john.abraham@fungible.com")

    """
    Job result related
    """
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default="UNKNOWN")
    emails = models.TextField(default="[]", null=True)  # email addresses to send reports to
    email_on_failure_only = models.BooleanField(default=False)
    finalized = models.BooleanField(default=False)
    preserve_logs = models.NullBooleanField(default=False, null=True)  # Preserve logs do not archive

    """
    Execution
    """
    state = models.IntegerField(default=JobStatusType.UNKNOWN)
    suite_container_execution_id = models.IntegerField(default=-1)
    is_auto_scheduled_job = models.BooleanField(default=False)
    banner = models.TextField(default="")
    execution_id = models.IntegerField(unique=True, db_index=True)
    test_case_execution_ids = models.CharField(max_length=10000, default="[]")
    build_done = models.BooleanField(default=False)
    auto_scheduled_execution_id = models.IntegerField(default=-1)
    disable_schedule = models.BooleanField(default=False)
    assets_used = JSONField(default={}, null=True)
    run_time = JSONField(default={}, null=True)
    is_re_run = models.NullBooleanField(default=False)
    re_run_info = JSONField(default={}, null=True)
    rich_inputs = JSONField(default=None, null=True)
    max_run_time = models.IntegerField(default=7 * 24 * 3600, null=True)
    pause_on_failure = models.BooleanField(default=False)

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

    def set_properties(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
            self.save()

    def add_run_time_variable(self, name, value):
        run_time = self.run_time
        run_time[name] = value
        self.save()
        return run_time

    def get_run_time_variable(self, name):
        result = None
        if name in self.run_time:
            result = self.run_time[name]
        return result

    def to_dict(self):
        result = {}
        fields = self._meta.get_fields()
        for field in fields:
            result[field.name] = getattr(self, field.name)
        return result

    def get_tags(self):
        """

        :return: a list of tags or None
        """
        result = None
        try:
            if self.tags:
                result = json.loads(self.tags)
        except:
            pass
        return result

    def get_environment(self):
        result = None
        environment = self.environment
        if environment:
            try:
                result = json.loads(self.environment)
            except:
                pass
        return result


    def get_inputs(self):
        result = None
        if self.inputs:
            try:
                result = json.loads(self.inputs)
            except:
                pass
        return result

class SuiteExecutionSerializer(serializers.Serializer):
    version = serializers.CharField(max_length=50)
    execution_id = serializers.IntegerField()

    class Meta:
        model = SuiteExecution
        fields = ('version', 'execution_id')


class LastSuiteExecution(models.Model):
    last_suite_execution_id = models.IntegerField(unique=True, default=10)

    @staticmethod
    def get_next():
        all = LastSuiteExecution.objects.all()
        if all.count():
            first = LastSuiteExecution.objects.first()
            first.last_suite_execution_id += 1
            first.save()
        else:
            LastSuiteExecution(last_suite_execution_id=10).save()

        return LastSuiteExecution.objects.first().last_suite_execution_id
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

class LastGoodBuild(FunModel):
    release_train = models.TextField(default="master", null=True)
    build_number = models.TextField(default="", null=True)
    release_catalog_execution_id = models.IntegerField()
    updated_date = models.DateTimeField(default=datetime.now)

    @staticmethod
    def set(release_train, build_number, release_catalog_execution_id):
        # lg = LastGoodBuild.objects.get(release_train=release_train)
        object, created = LastGoodBuild.objects.get_or_create(release_train=release_train)
        object.build_number = build_number
        object.release_catalog_execution_id = release_catalog_execution_id
        object.updated_date = get_current_time()
        object.save()
        return object

    @staticmethod
    def get(release_train):
        result = None
        try:
            last_good_build = LastGoodBuild.objects.filter(release_train=release_train).order_by('-updated_date').first()
            if last_good_build:
                result = last_good_build
        except ObjectDoesNotExist:
            logger.error("Release train: {} last good build does not exist".format(release_train))
        return result

class ReleaseCatalogExecution(FunModel):
    release_catalog_id = models.IntegerField()
    created_date = models.DateTimeField(default=datetime.now)
    started_date = models.DateTimeField(default=datetime.now)
    completion_date = models.DateTimeField(null=True, default=None)
    owner = models.EmailField(null=True, blank=True)
    state = models.IntegerField(default=JobStatusType.UNKNOWN)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default="UNKNOWN")
    description = models.TextField(default="TBD")
    recurring = models.BooleanField(default=True)
    release_train = models.TextField(default="master", null=True)
    build_number = models.TextField(default="latest", null=True)
    master_execution_id = models.IntegerField(default=None, null=True)
    suite_executions = JSONField(default=None, null=True)
    ready_for_execution = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    error_message = models.TextField(default=None, null=True)
    update_last_good_build = models.BooleanField(default=False)

    def __str__(self):
        return "CID: {} ME: {}".format(self.id, self.master_execution_id)


class ReleaseCatalog(FunModel):
    name = models.TextField(default="TBD")
    description = models.TextField(default="TBD")
    created_date = models.DateTimeField(default=datetime.now)
    modified_date = models.DateTimeField(default=datetime.now)
    suites = JSONField(default=[])

class Module(models.Model):
    name = models.TextField(unique=True)
    verbose_name = models.TextField(default="Verbose name")


class SubModules(FunModel):   # Say Module: Networking, sub-module: PSW
    name = models.TextField(unique=True)
    verbose_name = models.TextField(default="Verbose name")


class MetricsDataRunTime(FunModel):
    date_time = models.DateTimeField(verbose_name="Date", default=datetime.now)
    build_properties = JSONField(default=None, null=True, blank=True)
    lsf_job_id = models.IntegerField(default=None, null=True, verbose_name="lsf job id")
    suite_execution_id = models.IntegerField(default=None, null=True, verbose_name="suite execution id")
    jenkins_build_number = models.IntegerField(default=None, null=True, verbose_name="Jenkins Build Number")
    version = models.TextField(default=None, verbose_name="Version", null=True)
    associated_suites = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        s = ""
        for key, value in self.__dict__.iteritems():
            s += "{}:{} ".format(key, value)
        return s


class JenkinsJobIdMap(models.Model):
    jenkins_job_id = models.IntegerField()
    fun_sdk_branch = models.TextField(default="")
    git_commit = models.TextField(default="")
    software_date = models.IntegerField(default=0)
    hardware_version = models.TextField(default="")
    build_properties = models.TextField(default="")
    lsf_job_id = models.TextField(default="")
    sdk_version = models.TextField(default="")
    build_date = models.DateTimeField(default=datetime.now)
    suite_execution_id = models.IntegerField(default=-1)
    associated_suites = ArrayField(models.IntegerField(default=-1), default=[])

    def __str__(self):
        return "{} {} {} {}".format(self.build_date, self.jenkins_job_id, self.fun_sdk_branch, self.hardware_version)

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

    @staticmethod
    def get(script_path):
        result = None
        if script_path:
            try:
                result = RegresssionScripts.objects.get(script_path=script_path)
            except ObjectDoesNotExist:
                pass
        return result


class TestCaseInfo(FunModel):
    """
    # Model to store test-case id to script path mappings and associated summaries
    """
    test_case_id = models.TextField()
    summary = models.TextField()
    script_path = models.TextField()  # Maps to RegressionScripts
    steps = models.TextField(default="")

    @staticmethod
    def add_update(test_case_id, summary, script_path, steps=None):
        if TestCaseInfo.objects.filter(test_case_id=test_case_id, script_path=script_path).exists():
            t = TestCaseInfo.objects.get(test_case_id=test_case_id, script_path=script_path)
            t.summary = summary
            if steps:
                t.steps = steps
            t.save()
        else:
            t = TestCaseInfo(test_case_id=test_case_id, script_path=script_path, summary=summary)
            if steps:
                t.steps = steps
            t.save()

    @staticmethod
    def get_summary(test_case_id, script_path):
        result = "Unknown"
        try:
            t = TestCaseInfo.objects.get(test_case_id=test_case_id, script_path=script_path)
            result = t.summary
        except Exception as ex:
            pass
        return result

    def __str__(self):
        return "{} {}".format(self.test_case_id, self.summary)


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


class SchedulerConfig(models.Model):
    asset_unlock_warning_time = models.IntegerField(default=30)
    debug = models.BooleanField(default=False)

    @staticmethod
    def get():
        if not SchedulerConfig.objects.exists():
            SchedulerConfig().save()
        return SchedulerConfig.objects.first()

    @staticmethod
    def get_asset_unlock_warning_time():
        config = SchedulerConfig.get()
        return config.asset_unlock_warning_time

    @staticmethod
    def get_debug():
        config = SchedulerConfig.get()
        return config.debug

class SchedulerInfo(models.Model):
    """
    A place to store scheduler state such as time started, time restarted, current state
    """
    state = models.CharField(max_length=30, default=SchedulerStates.SCHEDULER_STATE_UNKNOWN)
    last_start_time = models.DateTimeField(default=datetime.now)
    last_restart_request_time = models.DateTimeField(default=datetime.now)
    main_loop_heartbeat = models.IntegerField(default=0)

    def to_dict(self):
        result = {}
        fields = self._meta.get_fields()
        for field in fields:
            result[field.name] = getattr(self, field.name)
        return result

    @staticmethod
    def get():
        result = None
        if SchedulerInfo.objects.count():
            result = SchedulerInfo.objects.first()
        return result

class SchedulerDirective(models.Model):
    """
    Stores actions that need to be completed by the scheduler.
    Usually the web-interface would request such actions
    """
    date_time = models.DateTimeField(default=datetime.now)
    directive = models.IntegerField(default=-1)
    active = models.BooleanField(default=True)   # Usually set after Directive has been processed

    def disable(self):
        self.active = False
        self.save()

    def enable(self):
        self.active = True
        self.save()

    @staticmethod
    def get_recent():
        directives = SchedulerDirective.objects.all().order_by('date_time')
        recent = None
        if directives:
            recent = directives.last()
        return recent

    @staticmethod
    def remove_recent():
        last_directive = SchedulerDirective.get_recent()
        if last_directive:
            last_directive.delete()

    @staticmethod
    def remove(directive):
        objects = SchedulerDirective.objects.filter(directive=directive)
        if objects:
            objects.delete()

    @staticmethod
    def add(directive):
        SchedulerDirective.objects.update_or_create(directive=directive, defaults={'date_time': datetime.now()})




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
    pre_emption_allowed = models.NullBooleanField(default=True)  # Mainly used for suite-based test-beds.
    # if a suite-based item is on top of the queue, if pre_emption allowed is disabled, all suite-based items of
    # lower-priority in the queue will not be considered for de-queueing until the highest priority ones get de-queued
    suspend = models.NullBooleanField(default=False)  # if set, the queued item is not eligible for de-queue


    def is_suite_based(self):
        return self.test_bed_type == "suite-based"

class KilledJob(models.Model):
    job_id = models.IntegerField(unique=True)
    killed_time = models.DateTimeField(default=datetime.now)


class User(FunModel):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(max_length=60, unique=True)

    def __str__(self):
        return "{} {} {}".format(self.first_name, self.last_name, self.email)

class PerformanceUserWorkspaces(FunModel):
    email = models.EmailField(max_length=60)
    workspace_name = models.TextField(default="")
    description = models.TextField(default="")
    date_created = models.DateTimeField(default=datetime.now)
    date_modified = models.DateTimeField(default=datetime.now)
    subscribe_to_alerts = models.BooleanField(default=False)
    alert_emails = models.TextField(default="")

    def __str__(self):
        return (str(self.__dict__))


class InterestedMetrics(FunModel):
    workspace_id = models.IntegerField()
    email = models.EmailField(max_length=60)
    metric_id = models.IntegerField()
    subscribe = models.BooleanField(default=False)
    track = models.BooleanField(default=False)
    chart_name = models.TextField(default='')
    category = models.TextField(default='')
    lineage = models.TextField(default="")
    date_created = models.DateTimeField(default=datetime.now)
    date_modified = models.DateTimeField(default=datetime.now)
    comments = models.TextField(default="")

    def __str__(self):
        return (str(self.__dict__))


class Daemon(FunModel):
    name = models.TextField(unique=True)
    daemon_id = models.IntegerField()
    heart_beat_time = models.DateTimeField(default=datetime.now)
    logging_level = models.IntegerField(default=logging.DEBUG)
    exception_logs = JSONField(default=[])

    def beat(self):
        self.heart_beat_time = get_current_time()
        self.save()

    @staticmethod
    def next_id():
        return Daemon.objects.all().count() + 1

    @staticmethod
    def get(name):
        if Daemon.objects.filter(name=name).exists():
            result = Daemon.objects.get(name=name)
        else:
            d = Daemon(name=name, daemon_id=Daemon.next_id())
            d.save()
            result = d
        return result

    def clear_exception_logs(self):
        self.exception_logs = []
        self.save()

    def add_exception_log(self, log):
        self.exception_logs.append({"time": get_current_time(), "log": log})

class Asset(FunModel):
    name = models.TextField()
    type = models.TextField()
    job_ids = JSONField(default=[])
    manual_lock_user = models.TextField(default=None, null=True)
    test_beds = JSONField(default=[])
    manual_lock_expiry_time = models.DateTimeField(default=timezone.now)
    disabled = models.BooleanField(default=False)
    health_check_enabled = models.BooleanField(default=True)
    state_change_time = models.DateTimeField(default=timezone.now)
    health_status = models.IntegerField(default=AssetHealthStates.HEALTHY)
    health_check_message = models.TextField(default="")

    @staticmethod
    def add_update(name, type, job_ids=None):
        try:
            if not Asset.objects.filter(name=name, type=type).exists():
                a = Asset(name=name, type=type)
                if job_ids:
                    a.job_ids = job_ids
                a.save()
            else:
                a = Asset.objects.get(name=name, type=type)
                if job_ids:
                    a.job_ids = job_ids
                a.save()
        except Exception as ex:
            pass

    @staticmethod
    def get(name, type):
        result = None
        if Asset.objects.filter(name=name, type=type).exists():
            try:
                result = Asset.objects.get(name=name, type=type)
            except Exception as ex:
                pass
        return result

    @staticmethod
    def add_job_id(name, type, job_id):
        a = Asset.get(name=name, type=type)
        if a:
            job_ids = a.job_ids
            job_ids.append(job_id)
            a.job_ids = job_ids
            a.save()
        else:
            raise Exception("Asset: {} type: {} not found".format(name, type))

    def remove_job_id(self, job_id):
        job_ids = self.job_ids
        if job_id in job_ids:
            job_ids.remove(job_id)
        self.job_ids = job_ids
        self.save()

    @staticmethod
    def add_manual_lock_user(name, type, manual_lock_user):
        a = Asset.get(name=name, type=type)
        if a:
            a.manual_lock_user = manual_lock_user
            a.save()
        else:
            raise Exception("Asset: {} type: {} not found".format(name, type))

    def remove_manual_lock_user(self, manual_lock_user):
        if self.manual_lock_user == manual_lock_user:
            self.manual_lock_user = None
            self.save()

    def add_time(self, minutes):
        self.manual_lock_expiry_time += timedelta(minutes=minutes)
        self.save()

    def set_health(self, status, force_update=False, message=""):
        if status != self.health_status or force_update:
            self.health_status = status
            self.state_change_time = get_current_time()
            self.health_check_message = message
            # if status == AssetHealthStates.UNHEALTHY:
            #    self.disabled = True
            self.save()

    def remove_test_bed(self, test_bed_name):
        self.test_beds = [x for x in self.test_beds if x != test_bed_name]
        self.save()

class SuiteItems(models.Model):
    script_path = models.TextField()
    inputs = JSONField(default=None)
    test_case_ids = ArrayField(models.IntegerField(default=-1), default=None)


class Suite(models.Model):
    name = models.TextField(default="TBD")
    type = models.TextField(default="SUITE")   # Other types are TASK
    categories = JSONField(default=[], null=True)
    sub_categories = JSONField(default=[], null=True)
    short_description = models.TextField(default="", null=True)
    long_description = models.TextField(default="", null=True)
    tags = JSONField(default=[], null=True)
    custom_test_bed_spec = JSONField(default=None, null=True)
    entries = JSONField(default=None)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(default=timezone.now)
    owner_email = models.EmailField(max_length=60, default="john.abraham@fungible.com")

    def to_dict(self):
        result = {}
        fields = self._meta.get_fields()
        for field in fields:
            result[field.name] = getattr(self, field.name)
        return result

    def add_entry(self, entry):
        if self.entries is None:
            self.entries = []
        self.entries.append(entry)
        self.save()


class TaskStatus(models.Model):
    path = models.TextField(unique=True, default="")
    name = models.TextField(unique=True)
    last_counter = models.IntegerField(default=0)
    state = models.TextField(default="")   # Job status type
    """ 
    Tasks logs switch between index 0 and index 1.
    One of these is the previous log and the other is
    is the current log
    """
    date_time = models.DateTimeField(default=datetime.now)

    @staticmethod
    def set_state(path, name, state=JobStatusType.UNKNOWN):
        TaskStatus.objects.update_or_create(path=path, name=name, defaults={"state": state, "date_time": get_current_time()})

    @staticmethod
    def get(path, name, state=JobStatusType.UNKNOWN):
        obj, _ = TaskStatus.objects.update_or_create(path=path, name=name, defaults={"state": state, "date_time": get_current_time()})
        return obj

    @staticmethod
    def get_state(path, name):
        state = None
        try:
            t = TaskStatus.objects.get(path=path, name=name)
            state = t.state
        except ObjectDoesNotExist:
            logger.error("Task status: {} {} Object does not exist".format(path, name))
        return state


class TestbedNotificationEmails(FunModel):
    email = models.EmailField(max_length=30, unique=True)

class Profile(models.Model):
    user = models.OneToOneField(AuthUser, on_delete=models.CASCADE)

@receiver(post_save, sender=AuthUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    if instance and not created:
        if not Profile.objects.filter(user=instance).exists():
            Profile.objects.create(user=instance)

        if not User.objects.filter(email=instance.email.lower()).exists():
            User(email=instance.email.lower(), first_name=instance.first_name, last_name=instance.last_name).save()

@receiver(post_save, sender=AuthUser)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

if not is_lite_mode():
    from web.fun_test.metrics_models import *


if __name__ == "__main__":
    #import django
    #import os

    #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
    #django.setup()
    pass
