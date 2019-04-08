from lib.system.fun_test import *
import verifications


def link_failures(tb, src_node_name, dst_node_names):
    """Link failure test.

    :param
        tb: testbed.TestBed() obj
        src_node_name: str, e.g. '1-1'
        dst_node_names: str, e.g. '1-3,0-2,0-3', or 'all spine links', 'all inter-node links'
    :return:
    """
    node = tb.get_node_from_name(src_node_name)
    if dst_node_names == 'all spine links':
        dst_nodes = node.get_peer_spines()
    elif dst_node_names == 'all inter-node links':
        dst_nodes = node.get_peer_leaves()
    else:
        dst_nodes = dst_node_names.split(',')

    # Shutdown
    msg = 'Shutdown link(s) - between Node %s and Spine(s)/Node(s) %s' % (src_node_name, ','.join(dst_nodes))
    fun_test.test_assert(tb.shutdown_links(src_node_name, dst_nodes), msg)
    _, bgp_hold = node.get_bgp_timers()
    fun_test.sleep("Wait for BGP/ISIS/RIB/FIB to converge after link down", seconds=bgp_hold + 2)
    verifications.baseline_verifications(tb)

    # No shutdown
    msg = 'No ' + msg
    fun_test.test_assert(
        tb.no_shutdown_links(src_node_name, dst_nodes), msg)
    fun_test.sleep("Wait for BGP/ISIS/RIB/FIB to converge after link up", seconds=bgp_hold + 2)
    verifications.baseline_verifications(tb)
