import os,re,sys,datetime,time

#example: python nvme_performance.py 4 read 1 8 30
argv_list = sys.argv
len_argv = len(argv_list)
if len_argv != 6:
    print "Enter in this format:"
    print "python nvme_performance.py number_of_namespace operation(read/write/readwrite) number_of_jobs iodepth sleep_time"
    sys.exit()

#take the given input as respective variable name
number_of_namespace = int(argv_list[1])
operation = argv_list[2]
number_of_jobs = int(argv_list[3])
iodepth = int(argv_list[4])
sleep_time = int(argv_list[5])

#output variable refers to output that is obtained when the command is executed
output = os.popen("lsmod | grep nvme").read()

#search's for nvme in the output and if driver not present than loads the driver and sleeps for 20s
match_nvme = re.search(r'nvme', output)
if not match_nvme:
    print "nvme driver not loaded, loading nvme driver..."
    os.system("modprobe nvme")
    print "Loaded nvme driver, sleeping for 20s\n"
    time.sleep(20)
else:
    print "nvme driver is already loaded\n"

try:
    output = os.popen("ls /dev/nvme0").read()
    print "/dev/nvme0 is present"
    print output
except:
    print "/dev/nvme0 is not present, try rebooting the system"
    sys.exit()

#fetching the numa_node number
output = os.popen("cat /sys/class/nvme/nvme0/device/numa_node").read()
numa_node = int(output)
print "NVMe numa_node is:", numa_node

output = os.popen("lscpu | grep node%s" % numa_node).read()
output = output.strip()
print "numa node and CPUs associated are:",output

list_of_cpu_number = []
while True:
    num = re.search(r'[\d]+', output)
    if num:
        number = num.group()
        output = re.sub(r'[\d]+', '$', output, 1)
        list_of_cpu_number.append(int(number))
    else:
        break
list_of_cpu_number.pop(0)
print "\nlist of cpus:",list_of_cpu_number

sum_value = 0
leng_num_list = len(list_of_cpu_number)
for i in range(0, leng_num_list, 2):
    sum_value = sum_value + list_of_cpu_number[i + 1] - list_of_cpu_number[i] + 1

number_of_cpus = sum_value
print "Number of cpus on NUMA node%s: %s\n"%(numa_node, number_of_cpus)

#checking whether the namespaces have been created or not
#if not created than creates the namespaces if created skips the creation part
output = os.popen("nvme list|grep nvme0n* | wc -l").read()
output = int(output)
if output == 0:
    print "Creating and attaching namespaces:\n"
    for i in range(number_of_cpus):
        os.system("sudo nvme create-ns -s 1024 -c 1024 -b 4096 /dev/nvme0")
        #os.system("sudo nvme create-ns -s 1024 -c 1024 /dev/nvme0")
        os.system("sudo nvme attach-ns -n %d /dev/nvme0"%(i+1))
    print "\nPerforming ns-rescan"
    os.system("sudo nvme ns-rescan /dev/nvme0")
    print "\nSleeping for 5sec"
    time.sleep(5)
else:
    print "Namespaces already exists, proceeding with fio test."

file_name = "/dev/nvme"
time_stamp = "n1-" + datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

print "\nTIME stamp:",time_stamp
print "\nStarting FIO\n"
leng = len(list_of_cpu_number)
count_temp = 0
for j in range(0,leng,2):
    for i in range(list_of_cpu_number[j], list_of_cpu_number[j + 1] + 1):
        cpu_mask = 2**i
        count_temp = count_temp + 1
        if count_temp > number_of_namespace:
            break
        print "cpu_mask=",cpu_mask
        j = i+1
        print "cpu mask used for FIO test:",cpu_mask
        os.system("fio --filename=/dev/nvme0n%s --rw=%s --bs=64k --size=4m --direct=1 --ioengine=libaio --numjobs=%s --iodepth=%s --group_reporting --name=%s%s --output=result%s%s --status-interval=30 --time_based --runtime=%s --group_reporting --prio=0 --cpumask=%s&"
                  % (count_temp, operation, number_of_jobs, iodepth, count_temp, time_stamp, count_temp ,time_stamp, sleep_time, cpu_mask))

print "\nSleeping for %ss for fio completion\n"%sleep_time
time.sleep(sleep_time)

#waits for fio completion
while True:
    output = os.popen("ps -ef | grep fio | grep iodepth | wc -l").read()
    output = int(output.strip())
    if output == 1:
        break
    else:
        time.sleep(5)
print "\nFIO completed successfully\n\n"

read_flag = False
write_flag = False
readwrite_flag = False
if operation == "read":
    read_flag = True
elif operation == 'write':
    write_flag = True
elif operation == 'readwrite':
    readwrite_flag = True

output = os.popen("ls result*%s" % time_stamp).read()
print "files :",output

if read_flag or write_flag :
    output = os.popen("cat result*%s | grep READ || cat result* | grep WRITE" % time_stamp).read()
elif readwrite_flag:
    output = os.popen("cat result*%s | grep READ" % time_stamp).read()
    output = output + os.popen("cat result*%s | grep WRITE" % time_stamp).read()

if not output:
    print "no read or write data was found"
    sys.exit()

lines = output.split('\n')
number_count = 0
sum_of_num = 0.0

for line in lines:
    print line
    match_speed_mbps = re.search(r'[\d.]+(?=MB/s)',line)
    match_speed_kbps = re.search(r'[\d.]+(?=kB/s)',line)
    if match_speed_kbps:
        speed = float(match_speed_kbps.group())/1024
        number_count+=1
        sum_of_num = sum_of_num + speed
    if match_speed_mbps:
        speed = float(match_speed_mbps.group())
        number_count+=1
        sum_of_num = sum_of_num + speed

avg = float(sum_of_num) / number_count
print "Average bandwidth in MB/s is:",avg,"Mbps"

bw = 0.0
if read_flag or write_flag:
    bw = avg*2*number_of_namespace*8
elif readwrite_flag:
    bw = avg*number_of_namespace*8

gbps = float(bw)/1024.0
print "Bandwidth in Gbps           :",gbps,"Gbps"
