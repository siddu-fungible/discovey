#!/usr/bin/env bash

# Move this file to /home/fun/ and run

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
#log_interval=300
########################

#if [[ -d "/home/fun/workspace/opt/fungible" ]]
#then
#    MY_SCRIPT_VARIABLE="/home/fun/workspace"
#    echo "/opt/fungible dir found at $MY_SCRIPT_VARIABLE"
#    cp -r $MY_SCRIPT_VARIABLE/opt/fungible/ /opt/
#elif [[ -d "/opt/fungible" ]]
if [[ -d "/opt/fungible" ]]
then
    MY_SCRIPT_VARIABLE="/"
    echo "/opt/fungible dir found at $MY_SCRIPT_VARIABLE"
else
    echo "/opt/fungible directory not found. Please check"
    exit 1
fi

function setup_dpc {
    cmd=`ps -aef | grep dpc | grep -v grep -c`
    if [ $cmd -eq 0 ]
    then
        echo "Dpcsh over proxy not started. Starting it"
        cd $MY_SCRIPT_VARIABLE/opt/fungible/FunSDK/bin/Linux/dpcsh/; ./dpcsh --pcie_nvme_sock=/dev/nvme0 --nvme_cmd_timeout=600000 --tcp_proxy=40220 &> /tmp/f1_0_dpc.txt &
        cd $MY_SCRIPT_VARIABLE/opt/fungible/FunSDK/bin/Linux/dpcsh/; ./dpcsh --pcie_nvme_sock=/dev/nvme1 --nvme_cmd_timeout=600000 --tcp_proxy=40221 &> /tmp/f1_1_dpc.txt &
        process1=`ps -aef | grep dpc | grep -v grep -c`
        if [ $process1 -ne 2 ]
        then
            echo "Dpcsh processes not started"
        fi
    elif [ $cmd -eq 2 ]
    then
        echo "Dpcsh process already running"
    fi
}

function stats() {
    s=$1
    echo "Capturing stats $s test"
    for f1 in 0 1
    do
        f1_file="/home/fun/f1_$f1-dpc_stats.txt"

        if [ $s == "before" ]
        then
            rm -f $f1_file
        fi

        $MY_SCRIPT_VARIABLE/opt/fungible/FunSDK/bin/Linux/dpcsh/dpcsh --pcie_nvme_sock=/dev/nvme$f1 --nocli peek stats/psw/nu/global >> $f1_file
        for fpg in 0 4 8 12 16 20
        do
            $MY_SCRIPT_VARIABLE/opt/fungible/FunSDK/bin/Linux/dpcsh/dpcsh --pcie_nvme_sock=/dev/nvme$f1 --nocli peek stats/fpg/nu/port[$fpg] >> $f1_file
        done
    done
}

function generic_setup {
    for pkg in libaio-dev fio
        do
            apt-get -yq install $pkg
            dpkg -s $pkg | grep -x 'Status: install ok installed'
            if [ $? -ne 0 ]
            then
                echo "Package $pkg not installed. Please check"
                exit 1
            fi
            echo "Installed package $pkg"
        done
}

function check_nvme_cli {
	sudo nvme create-ns --help 2>&1 | grep "block-size"
	if [ $? -ne 0 ]
	then
		echo "Nvme-cli not found. Installing it"
		apt-get -yq install nvme-cli
		dpkg -s $pkg | grep -x 'Status: install ok installed'
        if [ $? -ne 0 ]
        then
            echo "Package nvme-cli not installed. Please check"
            exit 1
        fi
        echo "Installed package nvme-cli"
	fi
}

function network_setup {
    network_setup_successful=1
    echo "########## Setup docker containers for snake ############"
    snake_file_path="$MY_SCRIPT_VARIABLE/opt/fungible/cclinux/snake_test.sh"
    if [ -f "$snake_file_path" ]
    then
        echo "$snake_file_path found"
        sh $snake_file_path
    else
        echo  "$snake_file_path does not exists"
        network_setup_successful=0
        return "$network_setup_successful"
    fi

    echo "Check  docker containers are created"
    if [ `docker ps | wc -l` -ne 5 ]
    then
        docker ps
        echo "Docker containers are not up. Please check"
        network_setup_successful=0
        return "$network_setup_successful"
    fi

    echo "#### Setup interfaces  ####"
    for f1 in 0 1
    do
        device_name="04:00.1"
        if [ $f1 == 1 ]
        then
            device_name="05:00.1"
        fi
        nu_test_file="/home/fun/f1-$f1-nutest.txt"
        docker exec -i "F1-$f1-fpg0" bash -c "cd $MY_SCRIPT_VARIABLE/opt/fungible/FunControlPlane/bin/; FUNQ_MODE=yes FUNQ_DEVICE_NAME=$device_name ./nu_test ../scripts/snake_nutest.json" > $nu_test_file 2>&1
        #  Need validations
        for fpg_int in 0 4 8 12 16 20
        do
            f="f$f1"
            fpg="fpg$fpg_int"
            interface="$f$fpg"
            sudo ifconfig $interface up
            create_status=$?
            if [ ${create_status} -ne 0 ]
            then
                echo "$interface not created. Please check"
                network_setup_successful=0
                return "$network_setup_successful"
            fi
        done
    done

    # echo "Add arp and routes to interfaces inside docker"
    # for f1 in 0 1
    # do
    #     for fpg_int in 0 20
    #     do
    #         docker_name="F1-$f1-fpg$fpg_int"
    #        intf_ip_mask="9.2.2.1/24"
    #         arp="00:de:ad:be:ef:00"
    #         route_ip_mask="9.1.2.0/24"
    #         gw="9.2.2.10"
    #         if [ $fpg_int -ne 0 ]
    #         then
    #             intf_ip_mask="9.1.2.1/24"
    #             arp="00:de:ad:be:ef:00"
    #             route_ip_mask="9.2.2.0/24"
    #             gw="9.1.2.10"
    #         fi
    #         f="f$f1"
    #         fpg="fpg$fpg_int"
    #         interface="$f$fpg"
    #         docker exec $docker_name ifconfig $interface $intf_ip_mask up
    #         docker exec $docker_name ifconfig $interface hw ether $arp
    #         docker exec $docker_name ip route add $route_ip_mask via $gw
    #         docker exec $docker_name arp -s $gw $arp
    #         docker exec $docker_name ifconfig $interface
    #         create_status=$?
    #         if [ ${create_status} -ne 0 ]
    #         then
    #             echo "Error: Route addition failed for $interface"
    #             network_setup_successful=0
    #             return "$network_setup_successful"
    #         fi
    #     done
    # done
    return "$network_setup_successful"
}

function storage_setup() {
    f1_id=$1
    storage_setup_successful=1

    echo "#####Loading nvme driver#####"
    sudo modprobe nvme

    block_size=4096
    nsze=$((${vol_size} / ${block_size}))
    ncap=${nsze}
    device="/dev/nvme"${f1_id}

    for j in `eval echo {1..$num_ssds_per_f1}`
    do
        cmd="sudo nvme create-ns --nsze=${nsze} --ncap=${ncap} ${device}"
        echo "$cmd"
        create_op=`sudo nvme create-ns --nsze=${nsze} --ncap=${ncap} ${device}`
        create_status=$?
        if [ ${create_status} -ne 0 ]
        then
            echo "Error: Create nvme namespace failed for $device and volume $j; Check funos logs"
            storage_setup_successful=0
        else
            ns_id=`echo ${create_op} | awk -F ':' '{print $3}'`

            #sudo nvme attach-ns -n ${ns_id} -c ${controller_id} ${device}
            sudo nvme attach-ns -n ${ns_id} ${device}
            attach_status=$?
            if [ ${attach_status} -ne 0 ]
            then
                echo "Error: Attach nvme namespace ${ns_id} failed; Check funos logs"
                storage_setup_successful=0
            fi
        fi
    done
    return "$storage_setup_successful"

}

function run {
	echo "#####Running fio#####"
	numjobs=2
	iodepth=4
	size="100%"
	bs="4k"
	rw="readwrite"
	outfile1="test_snake0.out"
	outfile2="test_snake1.out"

	log_interval=$((runtime / 10))
    if [ $log_interval == 0 ]
    then
        log_interval=1
    fi

	start_time=`date +%s`
	for dev in `ls /dev/nvme*n*`
	do
		outfile="test_fio_$(basename $dev).out"
		cmd="sudo fio --name=test-test --ioengine=libaio --direct=1 --filename=${dev} --numjobs=${numjobs} --iodepth=${iodepth} --rw=${rw} --bs=${bs} --size=${size} --group_reporting --time_based --runtime=${runtime} --status-interval=${log_interval}"
   		echo ${cmd}
   		fio_pid=`${cmd} 1>${outfile} 2>&1 & echo $!`
	done

	echo "#####Running snake on F1_0#####"
	cmd="docker exec F1-0-fpg0 ping 9.1.2.1 -w${runtime} -i 0.05"
	echo ${cmd}
	snake1_pid=`${cmd} 1>${outfile1} 2>&1 & echo $!`

	echo "#####Running snake on F1_1#####"
	cmd="docker exec F1-1-fpg0 ping 9.1.2.1 -w${runtime} -i 0.05"
	echo ${cmd}
	snake2_pid=`${cmd} 1>${outfile2} 2>&1 & echo $!`

   	trap stop_tests INT TERM HUP

	echo "#####Running test test for ${runtime} seconds...#####"
	sleep $(( ${runtime} + 2))
}

function verify_storage_result() {
    f1_id=$1
    storage_test=1
    no_files_found=1
    for outfile in `ls test_fio_nvme$f1_id*.out`
    do
        if [ -f $outfile ]
        then
            no_files_found=0
        fi
        grep -iE 'error|fail' ${outfile}
        if [ $? -eq 0 ]
        then
            echo "Error in ${outfile}"
            storage_test=0
        fi
    done
    if [ $no_files_found == 1 ]
    then
        echo "fio output files not found for F1-$f1_id"
        storage_test=0
    fi
    return "$storage_test"
}

function verify_network_result() {
    f1_id=$1
    network_test=0
    outfile="test_snake$f1_id.out"
    if [ -f $outfile ]
    then
        tx_count=`grep -iE 'packet loss' ${outfile} | cut -d' ' -f1`
        rx_count=`grep -iE 'packet loss' ${outfile} | cut -d' ' -f4`
        echo "Packets transmitted for F1-$f1_id: $tx_count"
        echo "Packets received for F1-$f1_id: $rx_count"
        if [ $tx_count -eq $rx_count ] && [ $tx_count -ge 0 ]
        then
            network_test=1
        fi
    else
        echo "File $outfile not found"
    fi
    return "$network_test"
}

function verify_results {
    for f1 in 0 1
    do
        verify_storage_result $f1
        if [ "$storage_test" == 0 ]
        then
            echo "F1-$f1: Storage Test Failed"
        else
            echo "F1-$f1: Storage Test Passed"
        fi
        verify_network_result $f1
        if [ "$network_test" == 0 ]
        then
            echo "F1-$f1: Network Test Failed"
        else
            echo "F1-$f1: Network Test Passed"
        fi
    done
}

function verify_results1 {
    my_array=()
    for f1 in 0 1
    do
        verify_storage_result $f1
        my_array+=( "$storage_test" )
        verify_network_result $f1
        my_array+=( "$network_test" )
    done

    for i in "${!my_array[@]}"
    do
        if [ ${my_array[$i]} -ne 1 ]
        then
            result="FAIL"
        else
            result="PASS"
        fi
        if [ "$i" == 0 ]
        then
            echo "F1-0: Storage test $result"
        elif [ "$i" == 1 ]
        then
            echo "F1-0: Network test $result"
        elif [ "$i" == 2 ]
        then
            echo "F1-1: Storage test $result"
        elif [ "$i" == 3 ]
        then
            echo "F1-1: Network test $result"
        fi
    done
}

function usage {
	echo "Usage: $0 [runtime in secs]"
	exit 1
}

function cleanup {
    echo "kill all docker conttainers"
    cmd=`docker kill $(docker ps -q)`
    echo "Remove all test files"
    rm -rf test* f1*
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
}

#### MAIN ####
#if [ -z "$1" ]; then runtime=30; else runtime=$1; fi

#echo "######### Start Dpcsh ##########"
#setup_dpc

#echo "########Installing libaio and fio########"
#generic_setup

#echo "#####Check nvme-cli installed########"
#check_nvme_cli

echo "Setup docker containers for network test"
network_setup
if [ "$network_setup_successful" == 1 ]
then
    echo "Network setup successful"
else
    echo "Network setup failed"
fi

#for f1 in 1 0
#do
#    storage_setup $f1
#    if [ "$storage_setup_successful" == 0 ]
#    then
#        echo "Storage setup failed for F1-$f1"
#    else
#        echo "Storage setup successful for F1-$f1"
#    fi
#done
#sleep 60
#echo "Capture stats before test"
#stats before

#echo "Running storage and network test"
#run

#echo "Capture stats after test"
#stats after

#echo "Verifying output results"
#verify_results1

#echo "Call cleanup"
#cleanup
