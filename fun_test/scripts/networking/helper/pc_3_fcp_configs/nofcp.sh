route del -net 180.0.4.0/24
route del -net 180.0.3.0/24
route del -net 180.20.0.0/15
route del -net 180.10.0.0/15
ip netns exec n1 ip link set hu_server1 netns 1
