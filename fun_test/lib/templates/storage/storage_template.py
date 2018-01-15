from lib.system.fun_test import fun_test

# comment 1
# comment 2
# comment 3

class StorageTemplate:
    STORAGE_TYPE = "NORMAL"
    IKV_TYPE = "IKV"
    def __init__(self, topology):
        self.topology = topology

    @fun_test.safe
    def create_volume(self,
                      host_obj=None,
                      size=32768,
                      capacity=32768,
                      type=STORAGE_TYPE):
        volume_id = None
        if True: # TODO self.topology.mode == fun_test.MODE_SIMULATION:


            # host_obj.nvme_setup()

            fun_test.log("Output of lsblk prior to test")
            host_obj.command("lsblk")

            device = "/dev/nvme0"
            fun_test.test_assert(host_obj.nvme_create_namespace(size=size,
                                                            capacity=capacity,
                                                            device=device),
                                 "Create Namespace")
            fun_test.sleep("Create Namespace", 10)

        # if self.topology.mode == fun_test.MODE_REAL:
        #    if host_obj:
        #        pass # nvme style
        #    else:
        #        pass # open-stack style
        return volume_id

    @fun_test.safe
    def attach_volume(self, host_obj):
        if True: # TODO self.topology.mode == fun_test.MODE_SIMULATION:

            device = "/dev/nvme0"
            namespace_id = 1
            controllers = 1
            fun_test.test_assert(host_obj.nvme_attach_namespace(namespace_id=namespace_id,
                                                            controllers=controllers,
                                                            device=device),
                                 "Attach Namespace")

            fun_test.sleep("Attach Namespace", 10)
        return True

    @fun_test.safe
    def deploy(self):
        deploy_result = False

        if True: # TODO self.topology.mode == fun_test.MODE_SIMULATION:
            # Create volume

            fun_test.test_assert(self.create_volume(), "Create Volume")

            # Attach volume

            fun_test.test_assert(self.attach_volume(), "Attach Volume")

            deploy_result = True

        elif self.topology.mode == fun_test.MODE_REAL:
            if self.topology.platform == "OpenStack":
                pass

        return deploy_result

class StorageOsTemplate(StorageTemplate):
    def deploy(self):
        pass
