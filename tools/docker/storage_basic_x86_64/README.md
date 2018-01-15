# storage_basic_x86_64

Purpose:
```
Container containing the following fetched from the latest jenkins build
1. funos-posix
2. dpcsh
3. qemu image

contaning the following fetched from other sources
3. QEMU FS, Kernel
4. Kernel modules
```

Build:
```
sudo docker build . -t storage_basic_x86_64
```

Run:
```
sudo docker run -d -p3220:22 -p2220:2220 --privileged --name="$container_name" storage_basic_x86_64 <build-url>

where build-url=http://dochub.fungible.local/doc/jenkins/funos/latest/
```

