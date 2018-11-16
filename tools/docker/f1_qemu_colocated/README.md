# storage_x86_64
# Base: integration_base_x86_64

Purpose:
```
Image to create a container with
1. funos-posix
2. dpcsh
3. qemu image
4. functrl plane files
5. kernel modules

QEMU FS, Kernel, Kernel modules are documented in the base image
```

Build:
```
Typically:
docker build . -t storage_x86_64 --build-arg DOCKHUB_FUNGIBLE_LOCAL=10.1.20.99

Special cases:
docker build . -t storage_x86_64 --build-arg DOCKHUB_FUNGIBLE_LOCAL=10.1.20.99 --build-arg X86_64_FS_URL=http://10.1.20.99/doc/jenkins/cc-linux-yocto/latest/x86_64/fun-image-x86-64-qemux86-64.ext4
```

Run:
```
Typically:
docker run -d -p3220:22 -p2220:2220 --privileged --name="$container_name" storage_x86_64 -s <sdk-url>

Special cases:
docker run -d -p3220:22 -p2220:2220 --privileged --name="$container_name" storage_x86_64 -s <sdk-url> <-d dpcsh tgz url> <-f funos tgz url> <-q qemu tgz url> -m <modules tgz url> -c <functrlp tgz url> -h dochub ip



where sdk-url=http://dochub.fungible.local/doc/jenkins/funos/latest/Linux
```

