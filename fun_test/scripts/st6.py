import tarfile, requests, urllib
import os

TMP_DIR = "/tmp"

def prepare_tmp_directory(suite_execution_id):
    result = None
    directory = TMP_DIR + "/s_" + str(suite_execution_id)
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        result = directory
    except Exception as ex:
        raise SchedulerException(str(ex))
    return result

def extract(suite_execution_id, tar_url, extract_path='out/f1'):
    tmp_directory = prepare_tmp_directory(suite_execution_id=suite_execution_id)
    file_tmp, http_message = urllib.urlretrieve(tar_url, tmp_directory + "/funos.tgz")
    tgz_file = tarfile.open(name=file_tmp, mode="r:gz")
    members = tgz_file.getmembers()
    f = filter(lambda x: x.path == 'build/funos-f1', members)
    tgz_file.extract(member=f[0], path=tmp_directory + "/" + extract_path)

if __name__ == "__main__":
    suite_execution_id = 100
    extract(suite_execution_id=suite_execution_id, tar_url='http://dochub.fungible.local/doc/jenkins/funos/940/funos.tgz')
