from lib.system.fun_test import fun_test
from fun_global import Codes
from threading import Thread


class StatisticsCategory(Codes):
    FS_SYSTEM = 10
    FS_STORAGE = 50
    FS_NETWORKING = 100


class StatisticsCollector:
    def __init__(self, collector, category, type, **kwargs):
        self.collector = collector
        self.category = category
        self.type = type
        self.kwargs = kwargs


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
        self.terminated = False

    def run(self):
        fun_test.log("Starting collector: {}".format(self.collector_id))
        while not fun_test.closed and not self.terminated:
            collector_instance = self.collector.collector
            collector_instance.statistics_dispatcher(self.collector.type, **self.collector.kwargs)
            fun_test.sleep(seconds=self.interval_in_seconds, no_log=True)

    def terminate(self):
        self.terminated = True


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

    def start(self):
        for collector_id, collector in self.collectors.iteritems():
            t = CollectorWorker(collector_id=collector_id, collector=collector)
            t.start()
            self.collector_threads[collector_id] = t

    def run(self):
        pass



if __name__ == "__main__":
    from lib.fun.fs import Fs
    from asset.asset_manager import AssetManager

    asset_manager = AssetManager()
    fs_spec = asset_manager.get_fs_by_name("fs-102")

    fs_obj = Fs.get(fs_spec=fs_spec, already_deployed=True, disable_f1_index=1)
    come_obj = fs_obj.get_come()
    come_obj.command("date")
    come_obj.command("ps -ef | grep nvme")
    fs_obj.bam()

    sm = StatisticsManager()
    sc = StatisticsCollector(collector=fs_obj, category=StatisticsCategory.FS_SYSTEM, type=Fs.StatisticsType.BAM)
    collector_id = sm.register_collector(collector=sc)
    sm.start()
