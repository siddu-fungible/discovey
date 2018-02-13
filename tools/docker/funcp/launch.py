#!/usr/bin/env python

import os, sys
import subprocess
import getpass
import pexpect
import errno

ws = os.environ.get('WORKSPACE')
base_dockerfile = ws+"/Integration/tools/docker/funcp/base/Dockerfile"
funcp_dockerfile = ws+"/Integration/tools/docker/funcp/dev/Dockerfile"
startup = ws+"/Integration/tools/docker/funcp/dev/startup.sh"

user = os.environ.get('USER')
uid = str(os.getuid())
gid = str(os.getgid())

def run_shell_cmd(command):
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
    out, error = proc.communicate()
    return out, error

def check_docker_image(image_name):
    cmd = "docker images -q " + image_name
    out, error = run_shell_cmd(cmd)
    return out

def check_docker_container(container_name):
    cmd = "docker ps -a | grep " + container_name
    out, error = run_shell_cmd(cmd)
    return out

def cleanup_docker_container(container_name):
    cmd1 = "docker kill " + container_name 
    cmd2 = "docker rm " + container_name
    out, error = run_shell_cmd(cmd1)
    out, error = run_shell_cmd(cmd2)

def build_docker_image(image_name, base=True):
    if base:
        build_cmd = "docker build . -t " + image_name + "-f " + base_dockerfile 
    else:
        build_cmd = "docker build . -t %s -f %s --build-arg ARG_USER=%s --build-arg ARG_UID=%s \
                     --build-arg ARG_GID=%s" % (image_name, funcp_dockerfile, user, uid, gid)

    out, error = run_shell_cmd(build_cmd)
 
def run_docker_container(image_name, container_name):
    cmd = "docker run --rm -d --privileged -v /home/%s:/home/%s -v %s:/workspace \
           -e WORKSPACE=/workspace -e DOCKER=TRUE -w /workspace --name %s -u %s %s %s" % \
           (user, user, ws, container_name, user, image_name, startup) 

    child = pexpect.spawn(cmd)
    child.interact()

def main():

    base_image_name = "reg-nw-base:v1"

    if len(sys.argv) == 1: 
        image_name = "reg-nw-funcp:v1"
        container_name = "funcp-container" 
    elif len(sys.argv) == 3:
        image_name = sys.argv[1]
        container_name = sys.argv[2] 
    else:
        print "Usage: ./launch.py <image_name> <container_name>"
        sys.exit()

    if not check_docker_image(base_image_name):
        build_docker_image(base_image_name)

    if not check_docker_image(image_name):
        build_docker_image(image_name, False) 
   
    if check_docker_container(container_name):
        cleanup_docker_container(container_name)

    run_docker_container(image_name, container_name)

if __name__ == '__main__':
    main()
