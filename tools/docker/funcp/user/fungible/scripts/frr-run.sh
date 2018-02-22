#!/bin/bash

sudo /etc/init.d/ssh restart
sudo /opt/fungible/sbin/frr/frr start

echo "Container UP. Idling now"
while [ 1 ]
    do
        sleep 1
    done
