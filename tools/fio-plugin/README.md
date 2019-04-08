## Synopsis

IO engine for fio. Acts as NVMeoF client for F1.

## Build

1. Clone fio: https://github.com/axboe/fio.git
2. cd into 'fio' 
3. Clone integtration repo: git@github.com:fungible-inc/Integration.git
4. Apply patch to modify the  fio Makefile and register plugin:
	 'git apply Integration/tools/fio-plugin/patch'   
5. make install

## Options

fun specific fio options:

--ioengine=fun
-source_ip=ip address of client machine
--dest_ip=ip address of F1
--io_queues=number of NVM IO queues
--nrfiles=number of namespaces
--nqn=target subsystem nqn
--nvme_mode=FULL_TEST, CREATE_ONLY or IO_ONLY

Sample jobs are at: 'Integration/tools/fio-plugin/examples'

## Caveats

1. Supports only one job: "--numjobs=1" as RDS protocol is not thread safe.
2. Do not run "create_only" or "full_test" twice since F1 has issues. If you
   have to repeat the test, please restart F1. You can run IO_only test as
   many times as you want without restarting F1. For this, the sequence would
   be:
	1. Full test  OR create only
	2. IO_only
	3. IO_only
	4. IO_only
	5. ...
3. Doesn't run on Mac - native fio itself doesn't run; complains about shared memory.
