site_state = None


class SiteState():
    def __init__(self):
        self.metric_models = []

    def register_metric(self, model):
        self.metric_models.append(model)


if not site_state:
    site_state = SiteState()
