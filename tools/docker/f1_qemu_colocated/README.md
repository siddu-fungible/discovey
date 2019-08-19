# f1_qemu_colocated  {For Ubuntu on qemu}

Purpose:
```
Image to create a container with
1. funos-posix
2. dpcsh
3. qemu image
4. functrl plane files
5. kernel modules

```

Build:
```
Typically:
docker build . -t f1_colocated_qemu:v04_01 --build-arg DOCKHUB_FUNGIBLE_LOCAL=10.1.20.99 --build-arg HOST_OS_TGZ=fungible_ubuntu.tgz

```

Run:
```
Typically:
docker run -d -p3220:22 -p2220:2220 --privileged --name="$container_name" f1_colocated_qemu -s <sdk-url>

Special cases:
docker run -d -p3220:22 -p2220:2220 --privileged --name="$container_name" f1_colocated_qemu -s <sdk-url> <-d dpcsh tgz url> <-f funos tgz url> <-q qemu tgz url> -m <modules tgz url> -c <functrlp tgz url> -h dochub ip



where sdk-url=http://dochub.fungible.local/doc/jenkins/funos/latest/Linux
Latest run: sudo docker build . -t f1_colocated_qemu:v05_10 --build-arg DOCKHUB_FUNGIBLE_LOCAL=10.1.20.99 --build-arg HOST_OS_TGZ=fungible_ubuntu.tgz

```
Changelog:

f1_qemu_colocated:v04_01 ubuntu kernel 5.x
f1_qemu_colocated:v04_16 support for downloading regex
f1_qemu_colocated:v05_10 qemu.tgz is replaced by FunQemu.tgz
