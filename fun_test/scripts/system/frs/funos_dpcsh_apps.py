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
        self.collect_the_stats(count=3, heading="Before starting traffic")
        self.run_the_traffic()
        timer = FunTimer(max_time=1200)
        apps_are_done = False
        while not timer.is_expired():
            if not apps_are_done:
                apps_are_done = self.are_apps_done(timer)
            self.collect_the_stats(count=1, heading="During traffic")
        self.stop_traffic()
        self.collect_the_stats(count=3, heading="After traffic")

    def create_files_based_on_the_stats(self):
        pass

    def cleanup(self):
        pass


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(ParsingFunos())
    myscript.run()