from web.fun_test.maintenance_old import *

if __name__ == "__main__":
    charts = MetricChart.objects.all()
    for chart in charts:
        if chart.internal_chart_name.endswith('_S1'):
            chart.platform = "S1"
            chart.save()
            print "chart name is: {}".format(chart.chart_name)
            