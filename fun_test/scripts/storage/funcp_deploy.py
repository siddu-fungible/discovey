from lib.host.linux import Linux


class FunCpDockerContainer(Linux):
    CUSTOM_PROMPT_TERMINATOR = r'# '

    def __init__(self, f1_index, **kwargs):
        super(FunCpDockerContainer, self).__init__(**kwargs)
        self.f1_index = f1_index

    def _connect(self):
        super(FunCpDockerContainer, self)._connect()

        self.command("docker exec -it F1-{} bash".format(self.f1_index))
        self.clean()
        self.set_prompt_terminator(self.CUSTOM_PROMPT_TERMINATOR)
        self.command("export PS1='{}'".format(self.CUSTOM_PROMPT_TERMINATOR), wait_until_timeout=3,
                     wait_until=self.CUSTOM_PROMPT_TERMINATOR)
        return True
