# ubuntu_template

Purpose:
```
Base image to create a container with ssh access
```

Build:
```
[sudo] docker build . -t ubuntu_template
```

Run:
```
sudo docker run -d -p3220:22 --privileged --name="$container_name" ubuntu_template -b 123


```

