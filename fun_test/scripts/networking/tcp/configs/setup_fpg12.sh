sudo ip link set enp216s0 down
sudo ip link set enp216s0 name fpg12
sudo ip addr flush fpg12
sudo ip addr add 23.1.1.10/24 dev fpg12
sudo ip link set fpg12 address fe:dc:ba:44:55:33
sudo ip link set fpg12 up
sudo ifconfig fpg12 up
sudo route add -net 29.1.1.0/24 gw 23.1.1.2
sudo route add -host 20.1.1.1 gw 23.1.1.2
sudo arp -s 23.1.1.2 00:de:ad:be:ef:00
sudo python /local-home/localadmin/mks/mlx_load.py
#sudo /usr/sbin/set_irq_affinity_bynode.sh 1 fpg12