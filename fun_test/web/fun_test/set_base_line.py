from datetime import datetime
import web.fun_test.django_interactive
from web.fun_test.metrics_models import MetricChart, MetricChartStatus

class SetBaseLine():
    def set_base_line(self, metric_id, base_line_date, y1_axis_title=None):
        mc = MetricChart.objects.get(metric_id=metric_id)
        print mc.base_line_date
        mc.base_line_date = base_line_date
        if y1_axis_title:
            mc.y1_axis_title = y1_axis_title
        print mc.base_line_date
        mc.save()

if __name__ == "__main__":
    metric_id = 212
    base_line_date = datetime(year=2019, month=1, day=5, minute=0, hour=0, second=0)
    sbl = SetBaseLine()
    sbl.set_base_line(metric_id, base_line_date)
    print "completed"
