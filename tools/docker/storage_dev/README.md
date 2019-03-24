# storage_dev

Purpose:
```
Base image to create a container with the following fetched from the latest jenkins build
1. funos-posix
2. dpcsh
3. qemu image

and the following fetched from other sources
3. QEMU FS, Kernel
4. Kernel modules
```

Build:
```
sudo docker build . -t storage_dev --build-arg DOCKHUB_FUNGIBLE_LOCAL=10.20.1.99
```

Run:
```
sudo docker run -d -p3220:22 -p2220:2220 --privileged --name="$container_name" storage_dev <build-url>

where build-url=http://dochub.fungible.local/doc/jenkins/funos/latest/
```

