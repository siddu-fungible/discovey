from web.fun_test.django_interactive import *
import json
from web.fun_test.metrics_models import MetricsRunTime
from fun_global import get_epoch_time_from_datetime
import iso8601
run_time_objects = MetricsRunTime.objects.all()
from web.fun_test.metrics_models import BltVolumePerformance, InspurZipCompressionRatiosPerformance
from web.fun_test.analytics_models_helper import get_data_collection_time


for run_time_object in run_time_objects:
    for key, value in run_time_object.value.iteritems():
        print value
        # time_string = value["data_collection_time"]
        # print key, time_string

        iso_date_time = iso8601.parse_date(time_string)
        print get_epoch_time_from_datetime(iso_date_time)
        run_time_object.value[key] = get_epoch_time_from_datetime(iso_date_time)
        run_time_object.save()

'''
blt = InspurZipCompressionRatiosPerformance(input_date_time=get_data_collection_time())
blt.save()

'''