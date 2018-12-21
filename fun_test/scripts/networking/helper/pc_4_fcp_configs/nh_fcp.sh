ifconfig enp6s0f0 hw ether fe:dc:ba:44:55:77 
ifconfig enp6s0f1 hw ether fe:dc:ba:44:55:99 
#ifconfig enp4s0f0 hw ether 00:de:ad:be:ef:61

ifconfig enp6s0f1 75.0.0.4/24 up
ifconfig enp6s0f0 3.3.2.1/24 up
ifconfig enp6s0f1 mtu 9000
ifconfig enp6s0f0 mtu 9000
#ifconfig enp4s0f0 52.1.1.1/24 up
#ifconfig enp4s0f0 mtu 1200

ip route add 180.0.0.0/8 nexthop via 75.0.0.50 nexthop via 3.3.2.50
ip route add 18.0.0.0/8 nexthop via 75.0.0.50
#ip route add 51.1.1.0/24 nexthop via 52.1.1.50

arp -s 75.0.0.50 00:de:ad:be:ef:00
arp -s 3.3.2.50 00:de:ad:be:ef:00
#arp -s 52.1.1.50 00:de:ad:be:ef:00

echo 1 > /proc/sys/net/ipv4/ip_forward
echo 0 > /proc/sys/net/ipv4/conf/all/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/default/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/enp6s0f1/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/enp6s0f0/rp_filter
