# sbp_basic

Purpose:
```
Base image to create a container with ssh access
```

Build:
```
cp -r <location-of-FunSDK> .
[sudo] docker build . -t sbp_basic
```

Run:
```
sudo docker run -d -p3220:22 --privileged --name=this_container sbp_basic -b 123


```

