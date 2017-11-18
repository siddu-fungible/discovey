from fun_settings import *
from asset.asset_manager import AssetManager
import docker



def get_client():
    asset = AssetManager().get_orchestrator(AssetManager.ORCHESTRATOR_TYPE_DOCKER_HOST)
    client = docker.DockerClient(base_url='tcp://{}:{}'.format(asset.host_ip, DOCKER_REMOTE_API_PORT))
    return client

if __name__ == "__main__":

    # print client.images.list()
    image_name = "integration_yocto_arg"
    # client.containers.run("integration_yocto_arg", command="http://172.17.0.1:8080/fs/funos-posix test", detach=True, ports={"22":"3220", "2220":"2220"}, privileged=True, name=image_name)
    client = get_client()
    container_list = get_client().containers.list(all=True) # filters={"ancestor": image_name})
    for container in container_list:
        try:
            print container.name
            if "integr" in container.name:
                try:
                    container.kill(9)
                except:
                    pass
                print("Killed: {}".format(container.name))
                container.remove()
        except:
            pass

if __name__ == "__main2__":

    client = get_client()
    # print client.images.list()
    image_name = "integration_yocto_arg"
    b1 = 3220
    b2 = 4500
    for i in range(101, 200):
        print ("Container: {}".format(i))
        host_port_ssh = b1 + i
        qemu_port_ssh = b2 + i
        try:
            client.containers.run("integration_yocto_arg", command="http://172.17.0.1:8080/fs/funos-posix test", detach=True, ports={"22":"{}".format(host_port_ssh), "2220":"{}".format(qemu_port_ssh)}, privileged=True, name="{}-{}".format(image_name, i))
        except:
            pass



if __name__ == "__main2__":
    client = get_client()
    image_list = client.images.list()

    for image in image_list:
        if "integration_yocto_arg" in image.tags:
            image.remove()