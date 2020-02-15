Before running any script do the following at least once
~~~
cd /project/users/QA/regression/Integration/fun_test
export PYTHONPATH=`pwd`
pip install -r requirements.txt --user
~~~

To run a simple script
~~~
python scripts/examples/sanity.py
~~~

To run a simple test on FS (bringup FS1600) say scripts/examples/test_fs.py, use the following run parameters in Pycharm
~~~
python scripts/examples/test_fs.py --environment={\"test_bed_type\":\"fs-118\",\"tftp_image_path\":\"s_57410_funos-f1.stripped.signed.gz\”}

where s_57410_funos-f1.stripped.signed.gz is an image stored in the TFTP server (qa-ubuntu-02:/tftpboot)
~~~


To install a bundle image
~~~
python scripts/examples/test_fs_bundle.py --environment={\"test_bed_type\":\"fs-118\",\"bundle_image_parameters\":{\"release_train\":\"master\",\"build_number\":\"latest\"}}

~~~
