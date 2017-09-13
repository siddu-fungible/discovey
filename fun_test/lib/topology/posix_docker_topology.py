from lib.system.fun_test import fun_test
from asset.asset_manager import AssetManager
from lib.orchestration.simulation_orchestrator import SimulationOrchestrator
from netaddr import IPNetwork
inter_f1_cidr = IPNetwork('192.169.1.0/22')

spine_cidr = IPNetwork('192.168.0.0/16')
spine_subnet = spine_cidr.subnet(30)

class Rack:
    def __init__(self, index):
        self.leaves = []
        self.index = index
        self.leaf_to_leaf_links = []
        self.leaf_to_spine_links = []

    def __repr__(self):
        return str(self.index)

class Link:
    def __init__(self, subnet, index1, index2):
        self.subnet = subnet
        self.set_ips()
        self.index1 = index1
        self.index2 = index2

    def get_ip(self, index):
        pass

    def set_ips(self):
        subnet_iter = self.subnet.next()
        ip_addr_iter = subnet_iter.iter_hosts()
        self.ip_1 = str(ip_addr_iter.next()) + '/' + str(subnet_iter.prefixlen)
        self.ip_2 = str(ip_addr_iter.next()) + '/' + str(subnet_iter.prefixlen)

    def __repr__(self):
        return str(self.index1) + "-->" + str(self.index2) + " " + str(self.ip_1) + ":" + str(self.ip_2)

class Leaf:
    def __init__(self, index):
        self.link_leaves = []
        self.link_spines = []
        self.index = index

    def __repr__(self):
        return str(self.index)

    def add_link_to_leaf(self, num_leaves, subnet):
        for leaf_index in range(0, num_leaves):
            self.link_leaves.append(Link(subnet=subnet))

    def add_link_to_spine(self, num_spines, subnet):
        for spine_index in range(0, num_spines):
            self.link_spines.append(Link(subnet=subnet))

class Spine:
    def __init__(self, index):
        self.index = index


class PosixDockerTopology:

    @fun_test.log_parameters
    def __init__(self, num_racks, num_spines, num_leaves):
        self.num_racks = num_racks
        self.num_spines = num_spines
        self.num_leaves = num_leaves
        self.orchestrators = []
        self.duts = []
        self.instances = []

    @fun_test.log_parameters
    def deploy(self):
        result = None
        try:
            asset_manager = AssetManager()
            simulation_orchestrator_obj = SimulationOrchestrator.get(asset_manager.get_asset(name="ubuntu1"))
            self.orchestrators.append(simulation_orchestrator_obj)

            # Create bitmap
            # Create router configs
            # launch instance


            # Create ns / connect ns

            # Connect namespaces

            for rack_index in range(0, self.num_racks):
                fun_test.log_section("Deploying rack {}".format(rack_index))
                for spine_index in range(0, self.num_spines):
                    fun_test.log_section("Deploying spine {}".format(spine_index))
                    simulation_orchestrator_obj.launch_docker_instance(type="quagga-router")





            fun_test.test_assert(True, "Instances deployed")
            result = self
        except Exception as ex:
            fun_test.critical(str(ex))
        return result


    @fun_test.log_parameters
    def get_vms(self):
        return self.instances


    @fun_test.log_parameters
    def get_duts(self):
        return self.duts


    @fun_test.log_parameters
    def get_orchestrators(self):
        return self.orchestrators



    def get_bitmap(self):

        # Create spines
        spines = []
        num_spines_per_leaf = self.num_spines / self.num_leaves
        for spine_index in range(0, num_spines_per_leaf):
            spines.append(Spine(index=spine_index))


        # Create racks
        rack = []

        for rack_index in range(0, self.num_racks):

            one_rack = Rack(index=rack_index)






            # Leaf bitmap
            for leaf_index in range(0, self.num_leaves):
                one_leaf = Leaf(index=leaf_index)
                one_rack.leaves.append(one_leaf)

                # Spine bitmap




            # Create Links
            leaf_links = []
            for leaf_index in range(0, self.num_leaves, 2):
                subnet = inter_f1_cidr.subnet(30)

                link_obj = Link(subnet=subnet, index1=rack.get_leaf(), index2=leaf_index + 1)
                leaf1.add_link(link_obj)
                leaf2.add_link(link_obj)

            spine_links = []
            for leaf_index in range(0, self.num_leaves):
                for spine_index in range(0, num_spines_per_leaf):
                    spine_links.append(Link(subnet=spine_subnet, index1=leaf_index, index2=0))

            one_rack.leaf_to_leaf_links = leaf_links
            one_rack.leaf_to_spine_links = spine_links
            rack.append(one_rack)

        i = 0

if __name__ == "__main__":
    docker_topology = PosixDockerTopology(num_racks=2,
                                          num_spines=32,
                                          num_leaves=8)
    docker_topology.get_bitmap()