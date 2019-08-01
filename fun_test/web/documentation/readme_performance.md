## To apply changes on the regression server

~~~~
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ git pull
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test/web$ python manage.py makemigrations
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test/web$ python manage.py migrate --database=default
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test/web$ python manage.py initialize
~~~~