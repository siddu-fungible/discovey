from web.fun_test.analytics_models_helper import MetricChartHelper
from web.fun_test.metrics_models import MetricChartStatus
from datetime import datetime
from django.apps import apps
from fun_global import get_localized_time
import pytz

if __name__ == "__main__":
    trim_date = datetime(year=2018, month=6, day=01, minute=0, hour=0, second=0)
    trim_date = get_localized_time(trim_date)
    # tz = pytz.timezone("UTC")
    # trim_date = tz.localize(trim_date, is_dst=None)
    models = apps.all_models['fun_test']
    container_model = MetricChartStatus.objects.all()
    for container in container_model:
        if hasattr(container, 'date_time'):
            if container.date_time < trim_date:
                container.delete()
                # print container
    for model_name, model in models.iteritems():
        model_entries = model.objects.all()
        print model_name
        for model_entry in model_entries:
            if hasattr(model_entry, 'input_date_time'):
                if model_entry.input_date_time < trim_date:
                    model_entry.delete()
        #             print model_entry
        # print 'hello'
