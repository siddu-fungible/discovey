from scripts.system.palladium_performance_master import *
from web.fun_test.metrics_models import LAST_ANALYTICS_DB_STATUS_UPDATE
from web.fun_test.analytics_models_helper import prepare_status_db
from web.fun_test.models import TimeKeeper
from web.fun_test.metrics_lib import MetricLib
from web.web_global import *

S1 = FunPlatform.S1
F1 = FunPlatform.F1

class PrepareDbTc(FunTestCase):
    def describe(self):
        self.set_test_details(id=100,
                              summary="Calculate scores for both F1 and S1",
                              steps="Steps 1")

    def setup(self):
        pass

    def run(self):
        # chart_names = [F1, S1]
        metric_ids = [F1_ROOT_ID, S1_ROOT_ID, OTHER_ROOT_ID]
        prepare_status_db(metric_ids=metric_ids)
        TimeKeeper.set_time(name=LAST_ANALYTICS_DB_STATUS_UPDATE, time=get_current_time())

    def cleanup(self):
        pass


class RemoveResolvedBugsTc(PalladiumPerformanceTc):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Remove resolved bugs",
                              steps="Steps 1")

    def run(self):
        ml = MetricLib()
        ml.remove_resolved_bugs()


if __name__ == "__main__":
    myscript = MyScript()

    myscript.add_test_case(RemoveResolvedBugsTc())
    myscript.add_test_case(PrepareDbTc())

    myscript.run()