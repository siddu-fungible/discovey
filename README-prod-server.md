
# Setup needed for the main regression server

## Initial setup
### Account settings
sudo adduser qa-admin sudo

### Install python modules
cd /project/users/QA/regression/Integration/fun_test  
pip install -r requirements.txt —user  
mkdir /project/users/QA/regression/database  
nohup python web/start_production_server.py & 

### Postgres settings
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ grep "data_dir"   /etc/postgresql/9.5/main/postgresql.conf  
#data_directory = '/var/lib/postgresql/9.5/main'		# use data in another directory   
data_directory = '/project/users/QA/regression/database/postgresql’ 
