from start_traffic import *

class StatsCollection(FunTestScript):
    def describe(self):
        self.set_test_details(steps="")

    def setup(self):
        pass

    def cleanup(self):
        pass


class ParsingFunos(FrsTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        super(ParsingFunos, self).setup()
        # Any additional setup add it here.

    def run(self):
        self.start_collecting_stats(heading="During traffic")
        fun_test.sleep("For the apps to stop", seconds=self.duration + 20)
        self.stop_collection_of_stats()


if __name__ == "__main__":
    myscript = StatsCollection()
    myscript.add_test_case(ParsingFunos())
    myscript.run()