ifconfig enp6s0f1 hw ether fe:dc:ba:44:55:99 

ifconfig enp6s0f1 75.0.0.4/24 up
ifconfig enp6s0f1 mtu 9000

#ip route add 180.0.0.0/8 nexthop via 75.0.0.50 
ip route add 190.0.0.0/8 nexthop via 75.0.0.50

arp -s 75.0.0.50 00:de:ad:be:ef:00
echo 1 > /proc/sys/net/ipv4/ip_forward
echo 0 > /proc/sys/net/ipv4/conf/all/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/default/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/enp6s0f1/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/enp6s0f0/rp_filter
