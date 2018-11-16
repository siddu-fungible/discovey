ifconfig fpg0 hw ether 00:1b:21:8f:04:38
ifconfig fpg1 hw ether fe:dc:ba:fc:b1:03 
ifconfig fpg2 hw ether fe:dc:ba:fc:b1:04
ifconfig fpg3 hw ether 00:1b:21:8f:04:3d
ifconfig fpg4 hw ether 00:1b:21:96:91:c0
#ifconfig hnu_fpg0 hw ether 00:de:ad:be:ef:51

ifconfig fpg0 3.3.1.1/24 up
ifconfig fpg0 mtu 9000
ifconfig fpg1 3.3.2.1/24 up 
ifconfig fpg1 mtu 9000
ifconfig fpg2 3.3.3.1/24 up 
ifconfig fpg2 mtu 9000
ifconfig fpg3 3.3.4.1/24 up 
ifconfig fpg3 mtu 9000
ifconfig fpg4 3.3.5.1/24 up
ifconfig fpg4 mtu 9000
#ifconfig hnu_fpg0 51.1.1.1/24 up

ip route add 180.0.0.0/8 nexthop via 3.3.1.50 nexthop via 3.3.2.50 nexthop via 3.3.3.50 nexthop via 3.3.4.50 nexthop via 3.3.5.50 
#ip route add 52.1.1.0/24 nexthop via 51.1.1.50

arp -s 3.3.1.50 00:de:ad:be:ef:00
arp -s 3.3.2.50 00:de:ad:be:ef:00
arp -s 3.3.3.50 00:de:ad:be:ef:00
arp -s 3.3.4.50 00:de:ad:be:ef:00
arp -s 3.3.5.50 00:de:ad:be:ef:00
#arp -s 51.1.1.50 00:de:ad:be:ef:00

echo 1 > /proc/sys/net/ipv4/ip_forward
echo 0 > /proc/sys/net/ipv4/conf/all/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/default/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/fpg0/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/fpg1/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/fpg2/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/fpg3/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/fpg4/rp_filter

