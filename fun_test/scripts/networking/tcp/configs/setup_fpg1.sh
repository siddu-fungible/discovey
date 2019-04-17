sudo ip addr add 20.1.1.1/24 dev fpg1
sudo ip link set fpg1 address fe:dc:ba:44:55:77
sudo ip link set fpg1 up
sudo ifconfig fpg1 up
sudo route add -net 29.1.1.0/24 gw 20.1.1.2
sudo arp -s 20.1.1.2 00:de:ad:be:ef:00
