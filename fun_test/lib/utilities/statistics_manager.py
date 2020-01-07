from lib.system.fun_test import fun_test
from fun_global import Codes, TimeSeriesTypes
from threading import Thread
from bson import json_util



class StatisticsCategory(Codes):
    FS_SYSTEM = 10
    FS_STORAGE = 50
    FS_NETWORKING = 100


class StatisticsCollector:
    def __init__(self, collector, category, type, storage_file_handler=None, storage_db_handler=None, asset_id=None, **kwargs):
        self.collector = collector
        self.category = category
        self.type = type
        self.storage_file_handler = storage_file_handler
        self.storage_db_handler = storage_db_handler
        self.kwargs = kwargs
        self.storage_db = True
        self.asset_id = asset_id

    def get_type(self):
        return self.type

    def get_asset_id(self):
        return self.asset_id

class StatisticsStorageHandler:
    FILE_TYPE_HANDLER = 10
    DB_TYPE_HANDLER = 20

    def __init__(self, handler_type, formatter_function=None):
        self.handler_type = handler_type
        self.formatter_function = formatter_function

    def add_entry(self):
        pass


class CollectorWorker(Thread):
    def __init__(self,  collector_id, collector, interval_in_seconds=60):
        super(CollectorWorker, self).__init__()
        self.collector = collector
        self.collector_id = collector_id
        self.interval_in_seconds = interval_in_seconds
        self.stopped = False

    def run(self):
        fun_test.log("Starting collector: {}".format(self.collector_id))
        while not fun_test.closed and not self.stopped:
            collector_instance = self.collector.collector
            fun_test.debug("Running dispatch for {}".format(self.collector_id))
            result = collector_instance.statistics_dispatcher(self.collector.type, **self.collector.kwargs)
            if self.collector.storage_db:
                # result = self.collector.storage_db_handler(result)
                collection_name = fun_test.get_time_series_collection_name()
                data = json_util.loads(json_util.dumps(result["data"]))  #TODO

                mongo_db_manager = fun_test.get_mongo_db_manager()
                mongo_db_manager.insert_one(collection_name=collection_name,
                                            epoch_time=result["epoch_time"],
                                            type=TimeSeriesTypes.STATISTICS,
                                            te=fun_test.get_current_test_case_execution_id(),
                                            t=self.collector.get_type(),
                                            asset_id=self.collector.get_asset_id(),
                                            data=data)
            fun_test.sleep(seconds=self.interval_in_seconds, message="", no_log=True)


    def stop(self):
        self.stopped = True


class StatisticsManager(object):
    def __init__(self):
        self.collectors = {}
        self.next_collector_id = 1
        self.collector_threads = {}

    def _get_next_collector_id(self):
        result = self.next_collector_id
        self.next_collector_id += 1
        return result

    def register_collector(self, collector):
        collector_id = self._get_next_collector_id()
        self.collectors[collector_id] = collector
        return collector_id

    def start_all(self):
        for collector_id, collector in self.collectors.iteritems():
            t = CollectorWorker(collector_id=collector_id, collector=collector)
            t.start()
            self.collector_threads[collector_id] = t

    def start(self, collector_id):
        t = CollectorWorker(collector_id=collector_id, collector=self.collectors[collector_id])
        t.start()
        self.collector_threads[collector_id] = t

    def stop(self, collector_id):
        self.collector_threads[collector_id].stop()

if __name__ == "__main__":
    from lib.fun.fs import Fs
    from asset.asset_manager import AssetManager

    asset_manager = AssetManager()
    fs_spec = asset_manager.get_fs_spec("fs-118")

    fs_obj = Fs.get(fs_spec=fs_spec, already_deployed=True, disable_f1_index=1)
    #come_obj = fs_obj.get_come()
    #come_obj.command("date")
    #come_obj.command("ps -ef | grep nvme")
    # fs_obj.bam()
    # fs_obj.debug_vp_util()



    sm = StatisticsManager()
    sc = StatisticsCollector(collector=fs_obj, category=StatisticsCategory.FS_SYSTEM, type=Fs.StatisticsType.BAM)
    collector_id = sm.register_collector(collector=sc)
    sc = StatisticsCollector(collector=fs_obj, category=StatisticsCategory.FS_SYSTEM, type=Fs.StatisticsType.DEBUG_VP_UTIL)
    collector_id = sm.register_collector(collector=sc)

    sm.start_all()

    # fun_test.sleep(seconds=120, message="just wait")

