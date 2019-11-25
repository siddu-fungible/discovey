from lib.system.fun_test import *
from start_traffic import *


class ParsingFunos(FrsTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        super(ParsingFunos, self).setup()

    def run(self):
        self.initial_stats()
        self.start_collecting_stats(heading="Before starting traffic")
        self.stop_collection_of_stats_for_count(count=1)
        self.run_the_traffic()
        self.start_collecting_stats(heading="During traffic")
        fun_test.sleep("For the apps to stop", seconds=600)
        # timer = FunTimer(max_time=1200)
        # apps_are_done = False
        # while not timer.is_expired():
        #     apps_are_done = self.are_apps_done(timer)
        #     if apps_are_done :
        #         break
        #     fun_test.sleep("before checking the apps status", seconds=30)
        self.stop_collection_of_stats()

    # def create_files_based_on_the_stats(self):
    #     pass



if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(ParsingFunos())
    myscript.run()