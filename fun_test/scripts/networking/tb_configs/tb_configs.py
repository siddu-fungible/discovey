import yaml


class TBConfigs:
    def __init__(self, tb_config_file):
        with open(tb_config_file) as f:
            self.configs = yaml.load(f)

    def get_nu_host_name(self):
        return self.configs['nu_host']['hostname']

    def get_nu_host_username(self):
        return self.configs['nu_host']['username']

    def get_nu_host_password(self):
        return self.configs['nu_host']['password']
