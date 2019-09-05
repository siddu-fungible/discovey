sudo ip addr flush p3p1
sudo ip addr add 20.1.1.1/24 dev p3p1
sudo ip link set p3p1 address fe:dc:ba:44:66:30
sudo ip link set p3p1 up
sudo ifconfig p3p1 up
sudo route add -net 29.1.1.0/24 gw 20.1.1.2
sudo arp -s 20.1.1.2 00:de:ad:be:ef:00
sudo python /home/localadmin/mks/mlx_load.py