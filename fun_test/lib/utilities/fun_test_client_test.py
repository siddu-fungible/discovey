from lib.utilities.fun_test_client import FunTestClient
base_url = "http://0.0.0.0:5000"
base_url = "http://server17:5000"

fun_test_client = FunTestClient(base_url=base_url)

suite_name = "test.json"
DEFAULT_BUILD_URL = "http://dochub.fungible.local/doc/jenkins/funsdk/latest/"

for i in range(10):

    job_id = fun_test_client.submit_job(suite_path=suite_name,
                                        build_url=DEFAULT_BUILD_URL,
                                        tags=["tag1"],
                                        email_list="john.abraham@fungible.com",
                                        environment=None,
                                        submitter_email="john.abraham@fungible.com",
                                        test_bed_type="simulation")