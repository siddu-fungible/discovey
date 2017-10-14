import os, django, time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
django.setup()
from lib.utilities.test_dpcsh_tcp_proxy import DpcshClient
import hashlib, json, os
from fun_settings import *
from web.tools.models import Session, F1, IkvVideoTask
from fun_global import RESULTS
import subprocess, glob



def get_sha256_hex(value):
    m = hashlib.sha256()
    m.update(value)
    return get_hex(value=m.digest())

def get_md5_hex(value):
    m = hashlib.md5()
    m.update(value)
    return get_hex(value=m.digest())

def get_hex(value):
    return ''.join(x.encode('hex') for x in value)

def get_file_binary(file_name):
    contents = None
    with open(file_name, "rb") as f:
        contents = f.read()
    return contents

def verifiy_md5sum(file_name1, file_name2):
    file_name1_md5 = get_md5_hex(get_file_binary(file_name1))
    file_name2_md5 = get_md5_hex(get_file_binary(file_name2))
    return file_name1_md5 == file_name2_md5


def send_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error_logs = process.communicate()
    print "Output: " + output
    print "Error Logs:" + error_logs
    return output, error_logs

def convert_to_ts(file_name, session_id):
    ts_file_name = WEB_UPLOADS_DIR + "/{}.ts".format(session_id)
    try:
        os.remove(ts_file_name)
    except:
        pass
    command = "ffmpeg -i {} -c copy -bsf h264_mp4toannexb {}".format(file_name, ts_file_name)
    output, error_logs = send_command(command)
    result = {}
    result["status"] = False
    result["ts_file_name"] = ts_file_name
    result["output"] = output
    result["error_logs"] = error_logs
    if os.path.exists(ts_file_name):
        result["status"] = True
    return result

def prepare_manifest(keys, session_id, f1_id):
    key_urls = ""
    for k in keys:
        key_urls += """#EXTINF:2,
http://35.197.93.68:5000/tools/tg/ikv_video_get/{}/{}/{}.ts\n""".format(session_id, f1_id, k)
        #key_urls += """#EXTINF:2,
#http://35.197.93.68:5000/static/uploads/{}\n""".format(k)

    key_urls = key_urls.strip()
    s = """#EXTM3U
#EXT-X-VERSION:6
#EXT-X-TARGETDURATION:12
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXT-X-INDEPENDENT-SEGMENTS
{}
#EXT-X-ENDLIST""".format(key_urls)
    return s


def segmenting_ts(ts_file_name, session_id):
    files = glob.glob(WEB_UPLOADS_DIR + "/ikv_{}_*ts".format(session_id))
    for f in files:
        try:
            os.remove(f)
        except:
            pass
    print("Segmenting ts file_name")
    command = "ffmpeg -i {} -c copy -f segment -segment_time 2 {}/ikv_{}_%02d.ts".format(ts_file_name, WEB_UPLOADS_DIR, session_id)
    output, error_logs = send_command(command)
    result = {}
    result["status"] = False
    result["output"] = output
    result["error_logs"] = error_logs
    files = glob.glob(WEB_UPLOADS_DIR + "/ikv_{}_*ts".format(session_id))
    if len(files) > 0:
        result["status"] = True
    return files

def ikv_video_put(f1_info, session_id):
    video_task = IkvVideoTask.objects.get(session_id=session_id)
    logs = []

    out = ""
    video_file = WEB_UPLOADS_DIR + "/video.mp4"
    result = convert_to_ts(file_name=video_file, session_id=session_id)
    keys = []
    server_ip = f1_info["ip"]
    server_port = f1_info["dpcsh_port"]
    ikv_create(server_ip=server_ip, server_port=server_port)
    relative_paths = []
    if result["status"]:
        files = segmenting_ts(ts_file_name=result["ts_file_name"], session_id=session_id)
        files.sort(key=os.path.getmtime)
        if files:
            print("IKV files to put: {}".format(len(files)))
            for f in files:
                #relative_paths.append(os.path.basename(f))
                relative_paths.append(os.path.basename(f))
                with open(f, "rb") as infile:
                    contents = infile.read()
                    keys.append(ikv_put(bite=contents, server_ip=server_ip, server_port=server_port, create=False))
                    print("IKV files put: {}".format(f))
    video_task.status = RESULTS["PASSED"]
    video_task.logs = json.dumps(keys)
    # print("Keys:" + json.dumps(keys))
    # manifest = prepare_manifest(relative_paths, session_id, f1_info["name"])
    manifest = prepare_manifest(keys, session_id, f1_info["name"])
    with open(WEB_UPLOADS_DIR + "/manifest.m3u8", "w") as outfile:
        outfile.write(manifest)
    #video_task.logs = manifest
    video_task.logs = "/static/uploads/manifest.m3u8"
    video_task.save()


def ikv_create(server_ip, server_port):
    client_obj = DpcshClient(server_address=server_ip, server_port=server_port)
    create_d = {"init_lvs_bytes": 1048576,
		"max_keys": 16384,
		"max_lvs_bytes": 1073741824,
		"init_keys": 4096,
		"volume_id": 0}
    print client_obj.command("likv create " + json.dumps(create_d))
    open_d = {"volume_id": 0}

    print client_obj.command("likv open " + json.dumps(open_d))

def ikv_put(bite, server_ip, server_port, create=True):
    client_obj = DpcshClient(server_address=server_ip, server_port=server_port)
    input_value = get_hex(bite)
    key_hex = get_sha256_hex(value=input_value)
    if create:
	    create_d = {"init_lvs_bytes": 1048576,
			"max_keys": 16384,
			"max_lvs_bytes": 1073741824,
			"init_keys": 4096,
			"volume_id": 0}
	    print client_obj.command("likv create " + json.dumps(create_d))
	    open_d = {"volume_id": 0}

	    print client_obj.command("likv open " + json.dumps(open_d))

    put_d = {"key_hex": key_hex, "value": input_value, "volume_id": 0}
    client_obj.command("likv put " + json.dumps(put_d, ensure_ascii=False))
    return key_hex

def ikv_get(key_hex, server_ip, server_port, get_bytes=False):
    client_obj = DpcshClient(server_address=server_ip, server_port=server_port)
    get_d = {"key_hex": key_hex, "volume_id": 0}
    result = client_obj.command("likv get " + json.dumps(get_d))
    print result
    ba = bytearray.fromhex(result["data"]["value"])
    relative_path =  UPLOADS_RELATIVE_DIR + key_hex
    output_file_name = WEB_UPLOADS_DIR + key_hex
    with open(output_file_name, "wb") as f:
        f.write(ba)
    if get_bytes:
        return ba
    return relative_path
