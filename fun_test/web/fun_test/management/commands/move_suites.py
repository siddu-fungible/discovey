from web.fun_test.django_interactive import *
from web.fun_test.models import Suite
from fun_settings import SUITES_DIR
from glob import glob
import json

networking_key_words = ["funeth", "baba", "networking"]
storage_key_words = ["inspur", "apple", "review", "pcie", "nvme", "storage", "rdma", "multi", "lsv", "memvol", "ec", "blt"]
accelerator_key_words = ["regex", "rgx", "crypto"]
system_key_words = ["s1", "palladium", "sbp", "system"]

def get_category(suite_file):
    category = "general"
    if any(keyword in suite_file for keyword in networking_key_words):
        category = "networking"
    elif any(keyword in suite_file for keyword in storage_key_words):
        category = "storage"
    elif any(keyword in suite_file for keyword in accelerator_key_words):
        category = "accelerators"
    elif any(keyword in suite_file for keyword in system_key_words):
        category = "system"
    return category

Suite.objects.all().delete()
suite_files = glob(SUITES_DIR + "/*.json")
suite_files.sort()
for suite_file in suite_files:
    new_suite = Suite()
    new_suite.name = os.path.basename(suite_file)
    new_suite.categories = [get_category(suite_file)]


    if not suite_file.endswith("_container.json"):
        f = open(suite_file, "r")
        contents = f.read()
        f.close()
        spec = json.loads(contents)
        for spec_line in spec:
            info = spec_line.get("info", None)
            if info:
                tags = info.get("tags", None)
                if tags:
                    new_suite.tags = tags
                custom_test_bed_spec = info.get("custom_test_bed_spec", None)
                if custom_test_bed_spec:
                    new_suite.custom_test_bed_spec = custom_test_bed_spec

            path = spec_line.get("path", None)
            if path:
                new_script_entry = {}
                new_script_entry["script_path"] = path
                test_case_ids = spec_line.get("test_case_ids", None)
                if test_case_ids:
                    new_script_entry["test_case_ids"] = test_case_ids
                inputs = spec_line.get("inputs", None)
                if inputs:
                    new_script_entry["inputs"] = inputs
                new_suite.add_entry(new_script_entry)

        try:
            new_suite.save()
        except:
            pass