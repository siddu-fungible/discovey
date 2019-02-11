ifconfig fpg1 hw ether fe:dc:ba:44:55:77 
ifconfig fpg2 hw ether fe:dc:ba:44:55:99 

ifconfig fpg1 3.3.2.1/24 up 
ifconfig fpg1 mtu 9000
ifconfig fpg2 3.3.3.1/24 up 
ifconfig fpg2 mtu 9000


arp -s 3.3.2.50 00:de:ad:be:ef:00
arp -s 3.3.3.50 00:de:ad:be:ef:00

#ip route add 180.0.0.0/16 proto static scope global nexthop via 3.3.2.50 nexthop via 3.3.3.50
ip route add 190.0.0.0/16 proto static scope global nexthop via 3.3.2.50 nexthop via 3.3.3.50 

echo 1 > /proc/sys/net/ipv4/ip_forward
echo 1 > /proc/sys/net/ipv4/fib_multipath_hash_policy
echo 0 > /proc/sys/net/ipv4/conf/all/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/default/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/fpg0/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/fpg1/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/fpg2/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/fpg3/rp_filter

