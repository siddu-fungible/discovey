#!/usr/bin/python
from flask import Flask
from flask import request
import os, urllib, tarfile

app = Flask(__name__)

FUNOS_POSIX_PATH_IN_TGZ = 'build/funos-posix'
TEST_ARTIFACTS_RELATIVE_DIR = "/static/test_artifacts"
TEST_ARTIFACTS_DIR = "." + TEST_ARTIFACTS_RELATIVE_DIR

@app.route('/')
def index():
    return "Hello, World!"

def get_test_artifacts_directory(suite_execution_id, relative=False):
    directory = TEST_ARTIFACTS_DIR
    if relative:
        directory = TEST_ARTIFACTS_RELATIVE_DIR
    directory += "/s_" + str(suite_execution_id)
    return directory

def prepare_test_artifacts_directory(suite_execution_id):
    result = None
    directory = get_test_artifacts_directory(suite_execution_id)
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        result = directory
    except:
        pass
    return result

def extract_funos_posix(tgz_url, suite_execution_id):
    tmp_directory = prepare_test_artifacts_directory(suite_execution_id)
    file_tmp, http_message = urllib.urlretrieve(tgz_url, tmp_directory + "/funos.tgz")
    tgz_file = tarfile.open(name=file_tmp, mode="r:gz")
    members = tgz_file.getmembers()
    f = filter(lambda x: x.path == FUNOS_POSIX_PATH_IN_TGZ, members)
    if not f:
        Exception("Unable to find {} in tgz".format(FUNOS_POSIX_PATH_IN_TGZ))
    extraction_path = tmp_directory
    tgz_file.extract(member=f[0], path=extraction_path)
    if not os.path.exists(extraction_path):
        raise Exception("Extraction to {} failed".format(extraction_path))
    #try:
    #    os.remove(file_tmp)
    #except:
    #    pass
    return extraction_path

@app.route('/extract', methods=['POST'])
def extract():
    print request.data
    request_json = request.get_json(force=True)
    tgz_url = request_json["tgz_url"]
    suite_execution_id = request_json["suite_execution_id"]
    extract_funos_posix(tgz_url=tgz_url, suite_execution_id=suite_execution_id)
    path_to_funos_posix = get_test_artifacts_directory(suite_execution_id, relative=True) + "/" + FUNOS_POSIX_PATH_IN_TGZ
    return_url = "http://10.1.20.67:5001" + path_to_funos_posix
    print return_url
    return return_url

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
