# integration_base_x86_64

Purpose:
```
Base image to create a container with the following fetched from various sources
1. QEMU FS, Kernel

The image also provides a basic SSH service
```

Build:
```
sudo docker build . -t integration_base_x86_64 --build-arg DOCKHUB_FUNGIBLE_LOCAL=10.1.20.99
```

Run:
```
Intended as a base image. Not for running

```

