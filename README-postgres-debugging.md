John-Abrahams-MacBook-Pro:fun_test johnabraham$ psql postgres
psql (10.4)
Type "help" for help.

postgres=# SHOW HBA;
ERROR:  unrecognized configuration parameter "hba"
postgres=# SHOW hba_file;
              hba_file               
-------------------------------------
 /usr/local/var/postgres/pg_hba.conf
(1 row)
