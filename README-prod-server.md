
# Setup needed for the main regression server

## Initial setup
### Account settings

~~~~
sudo adduser qa-admin sudo
qa-admin@qa-ubuntu-01:~$ echo $PRODUCTION_MODE
1
qa-admin@qa-ubuntu-01:~$ cat ~/.bash_profile
if [ -f $HOME/.bashrc ]; then
        source $HOME/.bashrc
fi

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
qa-admin@qa-ubuntu-01:~$ cat ~/.bashrc 
export PRODUCTION_MODE=1
export PYTHONPATH=/project/users/QA/regression/Integration/fun_test
~~~~

### Install python modules
cd /project/users/QA/regression/Integration/fun_test  
pip install -r requirements.txt —user  
mkdir /project/users/QA/regression/database  
nohup python web/start_production_server.py & 

### Postgres settings
~~~~
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ grep "data_dir"   /etc/postgresql/9.5/main/postgresql.conf  
#data_directory = '/var/lib/postgresql/9.5/main'		# use data in another directory   
data_directory = '/project/users/QA/regression/database/postgresql’ 

qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ sudo systemctl stop postgresql
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ sudo systemctl start postgresql
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ sudo systemctl status postgresql
● postgresql.service - PostgreSQL RDBMS
   Loaded: loaded (/lib/systemd/system/postgresql.service; enabled; vendor preset: enabled)
   Active: active (exited) since Sat 2019-02-23 07:20:42 PST; 2s ago
  Process: 27461 ExecStart=/bin/true (code=exited, status=0/SUCCESS)
 Main PID: 27461 (code=exited, status=0/SUCCESS)

Feb 23 07:20:42 qa-ubuntu-01 systemd[1]: Starting PostgreSQL RDBMS...
Feb 23 07:20:42 qa-ubuntu-01 systemd[1]: Started PostgreSQL RDBMS.
~~~~

### iptables
~~~~
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$  sudo iptables -i enp3s0f0 -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 5000
~~~~


## Starting the web-server
~~~~
cd /project/users/QA/regression/Integration/fun_test
export PYTHONPATH=`pwd`
export PRODUCTION_MODE=1
python web/manage.py migrate --database=default
cd web/angular/qadashboard/
ng build --prod  --output-hashing none
python web/start_production_server.py &> server.out  &
~~~~

## Starting/Re-starting the scheduler
- Ensure the web-server was started successfully
~~~~
cd /project/users/QA/regression/Integration/fun_test
export PYTHONPATH=`pwd`
export PRODUCTION_MODE=1
~~~~
- Ensure that ps -ef | grep scheduler_main does not show any entry

## Debugging postgres
Check: /var/log/syslog, 
Run without daemon mode:
/usr/lib/postgresql/9.5/bin/postgres -d 3 -D /project/users/QA/regression/database/postgresql/9.5/main  -c config_file=/etc/postgresql/9.5/main/postgresql.conf 



