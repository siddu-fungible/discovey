from lib.system.fun_test import *
from scripts.helpers.palladium_app_parser_script import RetrieveLogLinesCase, PalladiumAppParserScript

ZIP_SANITY_TAG = "zip_sanity"
# TOTAL_NUMBER_OF_TEST_CASES = 10
TOTAL_NUMBER_OF_TEST_CASES = 2


class GeneratedTc(FunTestCase):
    id = 1

    def describe(self):
        self.set_test_details(id=self.id,
                              summary="GeneratedTc",
                              steps="""
        1. Retrieve the log lines from the shared variable
                              """)
        self.summary += "_" + str(self.id)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        lines = fun_test.shared_variables["lines"]
        # Validate these log lines if needed


if __name__ == "__main__":
    script = PalladiumAppParserScript(tag=ZIP_SANITY_TAG)
    script.add_test_case(RetrieveLogLinesCase(tag=ZIP_SANITY_TAG))
    for i in xrange(2, TOTAL_NUMBER_OF_TEST_CASES + 2):
        generated_test_case = GeneratedTc()
        generated_test_case.id = i
        script.add_test_case(generated_test_case)
    script.run()
