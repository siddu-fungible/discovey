import os
import django
import json
import random
from web.web_global import PRIMARY_SETTINGS_FILE

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
from web.fun_test.metrics_models import Performance1, PerformanceIkv, PerformanceBlt, VolumePerformance
from web.fun_test.metrics_models import AllocSpeedPerformance
from web.fun_test.site_state import *
from web.fun_test.metrics_models import MetricChart


if __name__ == "__main__":
    pass