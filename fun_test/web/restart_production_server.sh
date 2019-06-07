kill `cat /tmp/fun_test_web_server.pid`
kill -9 `cat /tmp/fun_test_web_server.pid`
rm -rf /tmp/fun_test_web_server.pid
nohup python web/start_production_server.py $1 &> server.out &
sleep 3
ps -ef | grep start_production_server
