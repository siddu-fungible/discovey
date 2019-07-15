
# this script requires a passwordless login provisioning

#for passwordless login perform below -
#ssh-copy-id root@FPGAHOST
#enter FPGAHOST password, see the message of authkey added.
#try command ssh root@FPGAHOST date ... should print the date command

#usage example - bash wait_until_alive_and_reboot.sh <FPGA-HOST>
#bash wait_until_alive_and_reboot.sh 10.1.104.109

FPGAHOST=$1

WAITFOR=500
WAITFORSSH=15

REBOOTCMD="ssh root@$FPGAHOST reboot"

attempt=1
while true;
do
    echo ""
	echo "Attempt=$attempt ..." && date && attempt=$((attempt+1))
	echo "waiting for ($WAITFOR) seconds for host($FPGAHOST) to be online ..."
	timeout $WAITFOR bash -c "until ping -c1 $FPGAHOST >/dev/null 2>&1; do :; done"
	if [ $? -eq 0 ]; then
		echo "host($FPGAHOST) is pinging again ..." && sleep $WAITFORSSH && date && echo "rebooting $FPGAHOST ..." && $REBOOTCMD
		sleep 5
	else
		echo "Alert timeout !! host($FPGAHOST) seem to be down ... user intervention required ..." && break
	fi
done
