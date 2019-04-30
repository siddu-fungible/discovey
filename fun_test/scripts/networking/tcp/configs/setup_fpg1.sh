sudo ip addr add 21.1.1.1/24 dev b2b
sudo ip link set b2b address fe:dc:ba:44:66:31
sudo ip link set b2b up
sudo ifconfig b2b up
sudo route add -net 29.1.1.0/24 gw 21.1.1.2
sudo arp -s 21.1.1.2 00:de:ad:be:ef:00
