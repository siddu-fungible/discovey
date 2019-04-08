import json
class Metric:
    def __init__(self, name, label=None, info=None, leaf=False, metric_model_name=None):
        if not metric_model_name:
            metric_model_name = "MetricContainer"
        self.name = name
        if not label:
            label = name
        self.label = label
        if not info:
            self.info = label
        self.leaf = leaf
        self.children = []
        self.metric_model_name = metric_model_name

    def add_child(self, metric):
        self.children.append(metric)

    def serialize(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

if __name__ == "__main__":
    total = Metric(name="Total")
    networking = Metric(name="Networking")
    storage = Metric(name="Storage")
    accelerators = Metric(name="Accelerators")
    funos = Metric(name="FunOS")
    terra_marks = Metric(name="TerraMarks")
    total.add_child(networking)
    total.add_child(storage)
    total.add_child(accelerators)
    total.add_child(funos)
    total.add_child(terra_marks)

    nucleus = Metric(name="Nucleus")
    allocation = Metric(name="Allocation")
    wus = Metric(name="WUs")

    funos.add_child(nucleus)
    funos.add_child(allocation)
    funos.add_child(wus)

    btmw = Metric(name="Best time for 1 malloc/free (WU)", leaf=True, metric_model_name="AllocSpeedPerformance")
    btmt = Metric(name="Best time for 1 malloc/free (Threaded)", leaf=True, metric_model_name="AllocSpeedPerformance")

    wulas = Metric(name="WU Latency: Alloc Stack", leaf=True, metric_model_name="WuLatencyAllocStack")
    wulu = Metric(name="WU Latency: Ungated", leaf=True, metric_model_name="WuLatencyUngated")

    wus.add_child(btmw)
    wus.add_child(btmt)
    wus.add_child(wulas)
    wus.add_child(wulu)
    s = total.serialize()
    print "[" + s + "]"