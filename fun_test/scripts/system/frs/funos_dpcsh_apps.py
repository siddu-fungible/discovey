from start_traffic import *


class ParsingFunos(FrsTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        super(ParsingFunos, self).setup()
        # Any additional setup add it here.

    def run(self):
        self.initial_stats()
        self.start_collecting_stats(heading="Before starting traffic")
        self.stop_collection_of_stats_for_count(count=1)
        self.run_the_traffic()
        self.start_collecting_stats(heading="During traffic")
        # fun_test.sleep("For the apps to stop", seconds=self.duration + 20)
        timer = FunTimer(max_time=self.duration + 20)
        while not timer.is_expired():
            if not fun_test.shared_variables["stat_collection_threads_status"]:
                fun_test.test_assert(False, "Stats collection has failed: Mainly because of DPCSH failure")
            else:
                fun_test.sleep("Check if the stats are being collected", seconds=60)
        self.stop_traffic()
        self.stop_collection_of_stats()


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(ParsingFunos())
    myscript.run()