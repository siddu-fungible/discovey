
# Setup needed for the regression server in production mode

## Initial setup
All configuration steps below need to be performed with "qa-admin" as the user

### Account settings

~~~~
# sudo adduser qa-admin sudo
# echo $PRODUCTION_MODE
1
# cat ~/.bash_profile
if [ -f $HOME/.bashrc ]; then
        source $HOME/.bashrc
fi

# export LC_ALL=en_US.UTF-8
# export LANG=en_US.UTF-8
qa-admin@qa-ubuntu-01:~$ cat ~/.bashrc
# export PRODUCTION_MODE=1
# export PYTHONPATH=/project/users/QA/regression/Integration/fun_test
~~~~

### Install Python modules
```
# cd /project/users/QA/regression/Integration/fun_test
# pip install -r requirements.txt --user
```

### Install Postgres database
Refer: https://github.com/fungible-inc/Integration/blob/master/fun_test/web/documentation/postgres_notes.md


### iptables
~~~~
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$  sudo iptables -i enp3s0f0 -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 5000
~~~~

## SSH settings
~~~~
qa-admin@qa-ubuntu-01:~$ grep Client /etc/ssh/sshd_config 
ClientAliveInterval 1200
ClientAliveCountMax 3
~~~~

## Starting the web-server
~~~~
# cd /project/users/QA/regression/Integration/fun_test
# export PYTHONPATH=`pwd`
# export PRODUCTION_MODE=1
# python web/manage.py migrate --database=default
# cd web/angular/qadashboard/
# npm install
# ng build --prod  --output-hashing none
# cd ../../../
# nohup python web/start_production_server.py &> server.out  &
~~~~

## Starting the scheduler
- Ensure the web-server was started successfully
- Ensure that 'ps -ef | grep scheduler_main' does not show any entry
~~~~
# cd /project/users/QA/regression/Integration/fun_test
# export PYTHONPATH=`pwd`
# export PRODUCTION_MODE=1
# scheduler/restart_scheduler.sh
~~~~
