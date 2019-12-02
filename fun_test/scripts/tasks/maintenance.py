from lib.system.fun_test import *
from lib.templates.tasks.tasks_template import TaskTemplate
from web.fun_test.models_helper import get_suite_execution
import subprocess
import re
from scheduler.scheduler_global import JobStatusType
from datetime import timedelta
from fun_global import get_current_time


class MaintenanceScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")

    def cleanup(self):
        fun_test.log("Script-level cleanup")

class ManageSsh(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Manage SSH connections",
                              steps="""
                              """)

    def setup(self):
        fun_test.log("Testcase setup")
        fun_test.sleep("demo", seconds=1)

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        max_allowed_ssh = 1024
        t = TaskTemplate()
        t.call("sudo kill -9 $(ps -eo comm,pid,etimes,cmd | awk '/^ssh/ {if ($3 > 36000) { print $2 }}')")
        commands = ["ps -ef", "grep ssh", "wc -l"]
        t.piped_commands(commands=commands)
        # active_ssh = t.popen("ps", ["-ef", "\|",  "grep", "ssh", "\|", "wc", "-l"])
        return_code, output, err = t.piped_commands(commands=["ps -ef", "grep ssh"])
        fun_test.simple_assert(not return_code, "Return code valid")
        all_sshs = output.split("\n")
        for ssh in all_sshs:
            fun_test.log(ssh)
        fun_test.test_assert(len(all_sshs) <= max_allowed_ssh, "Num ssh < {}".format(max_allowed_ssh))


class WebBackup(FunTestCase):
    BACKUP_SCRIPT = "backup_db_raw.sh"
    def describe(self):
        self.set_test_details(id=2,
                              summary="Take web database backups",
                              steps="""
                              """)

    def setup(self):
        pass

    def run(self):

        t = TaskTemplate()
        t.call("./{}".format(self.BACKUP_SCRIPT), working_directory=WEB_DIR)
        current_time = get_current_time()
        top_of_the_day = current_time - timedelta(hours=current_time.hour, minutes=current_time.minute, seconds=current_time.second)
        files_from_today = t.list_files_by_time(directory=DATA_STORE_DIR + "/web_backup", from_time=top_of_the_day)
        backup_file_found = None
        fun_test.log("Files found: {}".format(files_from_today))

        for file in files_from_today:
            base_name = os.path.basename(file)
            if base_name.startswith("fun_test") and base_name.endswith(".tgz"):
                backup_file_found = file
                break
        fun_test.test_assert(backup_file_found, "Backup file found")
        file_size = t.get_file_size(file_name=backup_file_found)

        one_kb = 1024
        one_mb = 1024 * one_kb
        minimum_size = 20 * one_mb
        fun_test.test_assert(file_size > minimum_size, "Backup file size > {}".format(minimum_size))

        pass

    def cleanup(self):
        pass


class CleanupOldDirectories(FunTestCase):
    SPIRENT_DIR = ""
    def describe(self):
        self.set_test_details(id=3,
                              summary="Remove old directories",
                              steps="""
                              """)

    def setup(self):
        pass

    def run(self):
        t = TaskTemplate()
        working_directory = "{}/fun_test/management".format(WEB_DIR)
        t.call("python archiver.py", working_directory=working_directory)

    def cleanup(self):
        pass

class DetectLargeFiles(FunTestCase):
    MAX_FILE_SIZE = "400M"
    def describe(self):
        self.set_test_details(id=4, summary="Detect files larger than", steps=""" """)

    def setup(self):
        pass

    def run(self):
        t = TaskTemplate()
        working_directory = "{}".format(LOGS_DIR)
        return_code, output, err = t.piped_commands(commands=["find {} -type f -size +{}".format(LOGS_DIR, self.MAX_FILE_SIZE)])
        lines = output.split("\n")
        fun_test.test_assert(len(lines) < 3, "No of files > {}: {}".format(self.MAX_FILE_SIZE, len(lines)))

    def cleanup(self):
        pass


class CheckMongoCollectionCount(FunTestCase):
    MAX_COLLECTIONS = 5000

    def describe(self):
        self.set_test_details(id=5, summary="Ensure mongodb collection count is in control", steps=""" """)

    def setup(self):
        pass

    def run(self):
        m = fun_test.get_mongo_db_manager()
        collection_count = m.collections_count()
        fun_test.test_assert(collection_count < self.MAX_COLLECTIONS, "Mongodb collections < {}. Actual: {}".format(self.MAX_COLLECTIONS, collection_count))

    def cleanup(self):
        pass


class RemoveOldCollections(FunTestCase):
    MAX_DAYS_IN_PAST = 30

    def describe(self):
        self.set_test_details(id=6, summary="Remove collections older than {} days".format(self.MAX_DAYS_IN_PAST), steps=""" """)

    def setup(self):
        pass

    def run(self):
        mongo = fun_test.get_mongo_db_manager()
        collection_names = mongo.get_all_collection_names()
        for collection_name in collection_names:
            if collection_name.startswith("s_"):
                m = re.search("s_(\d+)", collection_name)
                if m:
                    suite_execution_id = m.group(1)
                    try:
                        s = get_suite_execution(suite_execution_id=suite_execution_id)
                        if s and s.state <= JobStatusType.COMPLETED:
                            completed_time = s.completed_time
                            time_in_the_past = get_current_time() - timedelta(days=self.MAX_DAYS_IN_PAST)
                            if completed_time < time_in_the_past and not s.preserve_logs:
                                fun_test.log("Dropping collection {} {} {}".format(collection_name, suite_execution_id, s.completed_time))
                                collection = mongo.get_collection(collection_name=collection_name)
                                if collection:
                                    collection.drop()
                    except Exception as ex:
                        pass
    def cleanup(self):
        pass


if __name__ == "__main__":
    myscript = MaintenanceScript()
    myscript.add_test_case(ManageSsh())
    myscript.add_test_case(WebBackup())
    myscript.add_test_case(CleanupOldDirectories())
    myscript.add_test_case(DetectLargeFiles())
    myscript.add_test_case(CheckMongoCollectionCount())
    myscript.add_test_case(RemoveOldCollections())
    myscript.run()
