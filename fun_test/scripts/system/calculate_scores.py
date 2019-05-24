from scripts.system.palladium_performance_master import *

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
        chart_names = [F1, S1, "All metrics"]
        prepare_status_db(chart_names=chart_names)
        TimeKeeper.set_time(name=LAST_ANALYTICS_DB_STATUS_UPDATE, time=get_current_time())

    def cleanup(self):
        pass


if __name__ == "__main__":
    myscript = MyScript()

    myscript.add_test_case(PrepareDbTc())

    myscript.run()