kill `cat /tmp/fun_test_scheduler.pid`
kill -9 `cat /tmp/fun_test_scheduler.pid`
rm -rf /tmp/fun_test_scheduler.pid
nohup python scheduler/scheduler_main.py &> scheduler.out &
