#!/bin/bash

# Global configuration #
########################
# Defaulting to 12 SSDs per F1
num_ssds_per_f1=12
# Id of nvme controller to attach the volumes to
# Currently its hard-coded to 2
#TODO: Check if its common across F1s
controller_id=2
# Number of nvme block devices will depend on this number
num_f1s=2
# Volume size in bytes; Default is 400GB
vol_size=$((400 * 1024 * 1024 * 1024))
# Log interval for fio; Default is 5 mins
# Note: Fio will dump full stats at these intervals;
# So if runtime is large then it will bloat the output file
log_interval=300
########################

function stats() {
    s=$1
    f1_0_file="/home/fun/f1_0_dpc_stats.txt"
    f1_1_file="/home/fun/f1_1_dpc_stats.txt"
    echo "Capturing stats $s test"
    /opt/fungible/FunSDK/bin/Linux/dpcsh/dpcsh --pcie_nvme_sock=/dev/nvme0 --nocli peek stats/psw/nu/global >> $f1_0_file
    /opt/fungible/FunSDK/bin/Linux/dpcsh/dpcsh --pcie_nvme_sock=/dev/nvme1 --nocli peek stats/psw/nu/global >> $f1_1_file
}

function usage {
	echo "Usage: $0 <setup/run/cleanup> [network|storage] [runtime in secs]"
	exit 1
}

function check_nvme_cli {
	sudo nvme create-ns --help 2>&1 | grep "block-size"
	if [ $? -ne 0 ]
	then
		tar -zxvf nvme-cli.tgz
		pushd nvme-cli
		make && sudo make install
		popd
	fi
}

function stop_tests {
	sudo pkill -9 fio
	sudo pkill -9 ping
	end_time=`date +%s`
	run_duration=$(($end_time - $start_time))
	echo "#####All tests stopped; Run duration: ${run_duration}#####"
}

function scrub_outfiles {
	echo "#####Checking outfiles for any errors...#####"

    if [ ${test} == "network" ] || [ ${test} == "all" ]
    then
        for outfile in `ls compliance_snake*.out`
        do
            grep -iE '[0-9]+ packets transmitted' ${outfile}
            if [ $? -ne 0 ]
            then
                echo "FAIL: No packets transmitted in ${outfile}. Make sure you run with sudo."
            fi

            grep -iE ' 0 received|100% packet loss' ${outfile}
            if [ $? -eq 0 ]
            then
                echo "FAIL: No packets received in ${outfile}. Check your snake connections."
            fi
        done
    fi

    if [ ${test} == "storage" ] || [ ${test} == "all" ]
    then
    	for outfile in `ls compliance_fio_*.out`
    	do
    		grep -iE 'error|fail' ${outfile}
    		if [ $? -eq 0 ]
    		then
    			echo "Error in ${outfile}"
    		fi
    	done
    fi
}

function setup {
    if [ ${test} == "storage" ] || [ ${test} == "all" ]
    then
        echo "#####Loading nvme driver#####"
        sudo modprobe nvme

            echo "#####Checking if fio is present#####"
            sudo apt list --installed | grep fio
            if [ $? -ne 0 ]
            then
            # Install libaio-dev since its needed for fio
            sudo apt install libaio-dev_0.3.110-5ubuntu0.1_amd64.deb
            # Install fio
            tar -zxvf fio.tgz
            pushd fio
            ./configure
            sudo make
            sudo make install
            popd
            fi

        echo "#####Checking if nvme create-ns cmd has --block-size option#####"
        check_nvme_cli

        memvol=`ls /dev/nvme*n*`
        if [ $? -ne 0 ]
        then
            echo "No existing volumes found which means memory volumes were not found/created"
        fi

        echo "#####Creating nvme namespaces; these will be created on all online SSDs in round-robin fashion#####"
        block_size=4096
        nsze=$((${vol_size} / ${block_size}))
        ncap=${nsze}

        f1_id=$(($num_f1s - 1))
        for i in `eval echo {0..$f1_id}`
        do
            device="/dev/nvme"${i}

            for j in `eval echo {1..$num_ssds_per_f1}`
            do
                create_op=`sudo nvme create-ns --nsze=${nsze} --ncap=${ncap} --block-size=${block_size} ${device} 2>&1`
                create_status=$?
                if [ ${create_status} -ne 0 ]
                then
                    echo "Error: Create nvme namespace failed; Check funos logs"
                    exit ${create_status}
                fi
                ns_id=`echo ${create_op} | awk -F ':' '{print $3}'`

                #sudo nvme attach-ns -n ${ns_id} -c ${controller_id} ${device}
                sudo nvme attach-ns -n ${ns_id} ${device}
                attach_status=$?
                if [ ${attach_status} -ne 0 ]
                then
                    echo "Error: Attach nvme namespace ${ns_id} failed; Check funos logs"
                    exit ${attach_status}
                fi
            done
        done
    fi

    if [ ${test} == "network" ] || [ ${test} == "all" ]
    then
        echo "########## Setup docker containers for snake ############"
        snake_file="/opt/fungible/cclinux/snake_test.sh"
        if [ -f "$snake_file" ]
        then
            echo "$snake_file found"
        else
            echo  "$snake_file does not exists"
            exit 1
        fi

        sh $snake_file

        echo "Check  docker containers are created"
        if [ `docker ps | wc -l` -ne 5 ]
        then
            docker ps
            echo "Docker containers are not up. Please check"
            exit 1
        fi

        echo "#### Setup interfaces  ####"
        for f1 in 0 1
        do
            device_name="04:00.1"
            if [ $f1 == 1 ]
            then
                device_name="06:00.1"
            fi
            docker exec -i "F1-$f1-fpg0" bash -c "cd /opt/fungible/FunControlPlane/bin/; FUNQ_MODE=yes"
            docker exec -i "F1-$f1-fpg0" bash -c "cd /opt/fungible/FunControlPlane/bin/; FUNQ_DEVICE_NAME=$device_name"
            docker exec -i "F1-$f1-fpg0" bash -c "cd /opt/fungible/FunControlPlane/bin/; ./nu_test ../scripts/snake_nutest.json"
            #  Need validations
            for fpg_int in 4 8 12 16
            do
                f="f$f1"
                fpg="fpg$fpg_int"
                interface="$f$fpg"
                sudo ifconfig $interface up
                create_status=$?
                if [ ${create_status} -ne 0 ]
                then
                    echo "$interface not created. Please check"
                    exit ${create_status}
                fi
            done
        done

        echo "Add arp and routes to interfaces inside docker"
        for f1 in 0 1
        do
            for fpg_int in 0 20
            do
                docker_name="F1-$f1-fpg$fpg_int"
                intf_ip_mask="9.2.2.1/24"
                arp="00:de:ad:be:ef:00"
                route_ip_mask="9.1.2.0/24"
                gw="9.2.2.10"
                if [ $fpg_int -ne 0 ]
                then
                    intf_ip_mask="9.1.2.1/24"
                    arp="00:de:ad:be:ef:00"
                    route_ip_mask="9.2.2.0/24"
                    gw="9.1.2.10"
                fi
                f="f$f1"
                fpg="fpg$fpg_int"
                interface="$f$fpg"
                docker exec $docker_name ifconfig $interface $intf_ip_mask up
                docker exec $docker_name ifconfig $interface hw ether $arp
                docker exec $docker_name ip route add $route_ip_mask via $gw
                docker exec $docker_name arp -s $gw $arp
                docker exec $docker_name ifconfig $interface
                create_status=$?
                if [ ${create_status} -ne 0 ]
                    then
                echo "Error: Route addition failed for $interface"
                exit ${create_status}
                        fi
            done
        done
    fi
}

function run {
    echo "Dump stats before run"
    stats before
    outfile1="compliance_snake1.out"
    outfile2="compliance_snake2.out"

    if [ ${test} == "storage" ] || [ ${test} == "all" ]
    then
        echo "#####Running fio#####"
        numjobs=2
        iodepth=4
        size="100%"
        bs="4k"
        rw="readwrite"


        start_time=`date +%s`
        for dev in `ls /dev/nvme*n*`
        do
            outfile="compliance_fio_$(basename $dev).out"
            cmd="sudo fio --name=compliance-test --ioengine=libaio --direct=1 --filename=${dev} --numjobs=${numjobs} --iodepth=${iodepth} --rw=${rw} --bs=${bs} --size=${size} --group_reporting --time_based --runtime=${runtime} --status-interval=${log_interval}"
            echo ${cmd}
            fio_pid=`${cmd} 1>${outfile} 2>&1 & echo $!`
        done
    fi

    if [ ${test} == "network" ] || [ ${test} == "all" ]
    then
        echo "#####Running snake on F1_0#####"
        cmd="docker exec F1-0-fpg0 ping 9.1.2.1 -w${runtime} -i 0.01"
        echo ${cmd}
        snake1_pid=`${cmd} 1>${outfile1} 2>&1 & echo $!`

        echo "#####Running snake on F1_1#####"
        cmd="docker exec F1-1-fpg0 ping 9.1.2.1 -w${runtime} -i 0.01"
        echo ${cmd}
        snake2_pid=`${cmd} 1>${outfile2} 2>&1 & echo $!`

        trap stop_tests INT TERM HUP
        #trap "kill -9 ${snake2_pid}" INT TERM HUP
        #trap "kill -9 ${fio_pid}" INT TERM HUP

        echo "#####Running compliance test for ${runtime} seconds...#####"
        sleep $(( ${runtime} ))
        #wait ${fio_pid}
        #wait ${snake1_pid}
        #wait ${snake2_pid}

        echo "#### Collecting stats after test run #####"
        stats after

        echo "#####All tests finished; Run duration: ${run_duration}#####"
        scrub_outfiles
    fi
}

function cleanup {
	echo "#####Detaching and deleting nvme namespaces#####"
	f1_id=$(($num_f1s - 1))
	for i in `eval echo {0..$f1_id}`
	do
		device="/dev/nvme"${i}
		for j in `eval echo {1..$num_ssds_per_f1}`
		do
			sudo nvme detach-ns -n ${j} -c ${controller_id} ${device}
			sudo nvme delete-ns -n ${j} ${device}
		done
	done

	echo "#####Unloading funeth driver#####"
	cmd="sudo rmmod funeth"
	echo ${cmd}
	${cmd}
}

#####Main#####
[ $# -lt 1 ] && usage

if [ $1 == "setup" ]
then
    if [ -z "$2" ]; then test="all"; else test=$2; fi
	setup
elif [ $1 == "run" ]
then
	if [ -z "$3" ]; then runtime=600; else runtime=$3; fi
	if [ -z "$2" ]; then test="all"; else test=$2; fi
	run
elif [ $1 == "cleanup" ]
then
    if [ -z "$2" ]; then test="all"; else test=$2; fi
	cleanup
else
	echo "Invalid argument"
fi
