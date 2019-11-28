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
        fun_test.sleep("For the apps to stop", seconds=self.duration + 20)
        self.stop_traffic()
        self.stop_collection_of_stats()


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(ParsingFunos())
    myscript.run()