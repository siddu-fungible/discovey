import os
import requests
import json
# Require docker host spec file

print "Environment:\n"

if not "DOCKER_HOSTS_SPEC_FILE" in os.environ:
    raise Exception("Please set the variable DOCKER_HOSTS_SPEC_FILE. For ex: DOCKER_HOSTS_SPEC_FILE=/home/jabraham/my-docker-host.json")
else:
    print "DOCKER_HOSTS_SPEC_FILE={}".format(os.environ["DOCKER_HOSTS_SPEC_FILE"])

# Check if docker host is reachable and healthy

with open(os.environ["DOCKER_HOSTS_SPEC_FILE"], "r") as docker_hosts_spec_file:
    docker_hosts_spec = json.loads(docker_hosts_spec_file.read())
    # Today we support only one docker host
    docker_info = docker_hosts_spec[0]
    host_ip = docker_info["host_ip"]
    remote_api_port = docker_info["remote_api_port"]
    docker_host_string = "{}:{}/version".format(host_ip, remote_api_port)

    response = requests.get("http://{}".format(docker_host_string))
    if response.status_code == 200:
        print "Docker Host: {} is reachable".format(docker_host_string)
    else:
        raise Exception("Unable to reach Docker Host: {}".format(docker_host_string))


    # Require setting BUILD_URL


#