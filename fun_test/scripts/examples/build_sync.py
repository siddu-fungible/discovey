from fun_settings import *
import os
import re
import requests


protocol = 'http://'
local_server_path = '{}localhost:5000/static/media/Linux/'.format(protocol)
media_path = MEDIA_DIR + '/' + 'Linux/'
dockhub_path = "{}/Linux/".format(DEFAULT_BUILD_URL)
build_info_file = 'build_info.txt'
build_info_url = "{}/build_info.txt".format(DEFAULT_BUILD_URL)
fun_cp_path = "{}{}/doc/jenkins/funcontrolplane/latest/functrlp.tgz".format(protocol,DOCHUB_FUNGIBLE_LOCAL)
fun_cp = "functrlp.tgz"
modules_path = "{}{}/doc/jenkins/fungible-host-drivers/latest/x86_64/modules.tgz".format(protocol,DOCHUB_FUNGIBLE_LOCAL)
modules = "modules.tgz"


def download_file(web_addr, local_addr):
    try:
        r = requests.get(url=web_addr, stream=True, timeout=3)
        file_size = r.headers['Content-length']
        count = 0
        print "Downloading File {0} size:{2} bytes at {1}".format(web_addr, local_addr, file_size)
        with open(local_addr, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    count += 1
                    if not count % 200:
                        print "#",
        print "\nDownload complete"
    except Exception as e:
        print "Download Failed!! For file {}".format(local_addr)
        os.remove(local_addr)
        raise e.message


def connect_jenkins():
    result = False
    try:
        resp = requests.get(url=build_info_url, timeout=3)
        result = True if resp.status_code == 200 else False
    except Exception, e:
        print e.message
    return result


def get_build_id(build_url):
    build_id = '0'
    try:
        r = requests.get(build_url, timeout=3)
        if r.status_code == 200 and not re.search(r'Not Found', r.content, re.M & re.I):
            build_id = r.content.strip()
    except Exception as e:
        print e.message
    return build_id


def compare_build():
    diff = 0
    try:
        local_build_id = get_build_id(local_server_path + build_info_file)
        print "Current Build Id: ", local_build_id
        jenkin_build_id = get_build_id(build_info_url)
        diff = int(jenkin_build_id) - int(local_build_id)
        print "Available Build Id: ", jenkin_build_id
    except Exception as e:
        print e.message
    return diff


def download_files():
    files = ['dpcsh.tgz', 'funos.posix-base.tgz', 'qemu.tgz']
    for f in files:
        download_file(web_addr=dockhub_path + f, local_addr=media_path + f)
    download_file(web_addr=fun_cp_path, local_addr=media_path+fun_cp)
    download_file(web_addr=modules_path, local_addr=media_path+modules)
    download_file(web_addr=build_info_url, local_addr=media_path + build_info_file)


if __name__ == '__main__':
    if connect_jenkins():
        # check dir exists
        if not os.path.isdir(media_path):
            os.mkdir(media_path)
        val = compare_build()
        if val > 0:
            download_files()
        else:
            print "At latest build"
            exit(1)
    else:
        print "Unable to connect Jenkins server"
