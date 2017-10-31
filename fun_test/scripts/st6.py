import tarfile, requests, urllib

def extract(tar_url, extract_path='/Users/johnabraham/ws/tgz/out/f1'):
    print tar_url
    file_tmp, http_message = urllib.urlretrieve(tar_url, "/tmp/1.tgz")

    tgz_file = tarfile.open(name=file_tmp, mode="r:gz")
    members = tgz_file.getmembers()
    f = filter(lambda x: x.path == 'build/funos-f1', members)
    tgz_file.extract(member=f[0], path=extract_path)

if __name__ == "__main__":
    extract(tar_url='http://dochub.fungible.local/doc/jenkins/funos/940/funos.tgz')
