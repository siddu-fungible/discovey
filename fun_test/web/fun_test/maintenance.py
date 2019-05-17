from web.fun_test.maintenance_old import *
from lib.system.fun_test import *

if __name__ == "__main__":
    charts = MetricChart.objects.all()
    for chart in charts:
        if chart.internal_chart_name.endswith('_S1'):
            chart.platform = "S1"
            chart.last_build_status = fun_test.PASSED
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["output"]["min"] = 0
                data_set["output"]["max"] = -1
                data_set["output"]["expected"] = -1
                data_set["output"]["reference"] = -1
                data_set["output"]["unit"] = chart.visualization_unit
            chart.data_sets = json.dumps(data_sets)
            chart.save()
            print "chart name is: {}".format(chart.chart_name)
            print "peer chart ids: {}".format(json.loads(chart.peer_ids))
