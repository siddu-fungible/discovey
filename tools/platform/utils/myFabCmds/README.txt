############ do the following to work with fabric ##############
# oneliner : fabric is easy tool to call ssh/deploy jobs
# syntax is # fab -f <taskfile.py> task1:arg1=value1,arg2=value2 task2:arg3=value3 ...
#######################################################################################

# pip install -r requirements.txt

# to get all the task defined
# fab -f flib.py -l

# to get help of a task called 'imageF'. This display all arguments provided to task
# fab -f flib.py -d imageF

# provide your imagename to this task  (here setup is important)
# example:
# fab -f flib.py setup:ABC imageF:"10.1.21.11:paragm/funos.gz',index=1


# some task might require to feed ',' or '='.
# note ',' '=' , are special characters and should be escaped with a '\'
# example:
# fab -f flib.py setup:ABC argsF:"sku\=SKU_FS1600_0 app\=hw_hsu_test syslog\=6"

