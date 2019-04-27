sudo ip addr add 21.1.1.1/24 dev p5p2
sudo ip link set p5p2 address fe:dc:ba:44:66:31
sudo ip link set p5p2 up
sudo ifconfig p5p2 up
sudo route add -net 29.1.1.0/24 gw 21.1.1.2
sudo arp -s 21.1.1.2 00:de:ad:be:ef:00
