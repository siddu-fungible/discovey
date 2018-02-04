site_state = None


class SiteState():
    def __init__(self):
        self.metric_models = {}

    def register_metric(self, model, name):
        self.metric_models[name] = model

    def get_metric_model_by_name(self, name):
        result = None
        if name in self.metric_models:
            result = self.metric_models[name]
        return result

if not site_state:
    site_state = SiteState()
