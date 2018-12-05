
Follow these steps to build necessary docker images to test FunCP/FRR:

1. Set $WORKSPACE environment variable to your workspace (directory that'll container all the repos)

```
fungible@ayas-ubuntu-1:~/ws$ pwd
/local/fungible/ws
fungible@ubuntu-1:~/ws$ export WORKSPACE=~/ws
```

2. Checkout Integration repo

```
fungible@ubuntu-1:~/ws$ git clone git@github.com:fungible-inc/Integration.git
```

3. Build base docker image that has all the software packages:

```
cd base
docker build . -t nw-reg-base
```

4. Build user docker image. This is needed to download/build FunCP/FRR inside the docker container as a non-root user.

```
cd user
docker build . -t reg-nw-user --build-arg ARG_USER=$USER --build-arg ARG_UID=$UID --build-arg ARG_GID=`id -g`
```

6. To run a FunCP container that pulls FunCP, FunOS and FunSDK source: 

```
docker run --privileged=true --rm -d -v /home/$USER:/home/$USER -v $WORKSPACE:/workspace -e WORKSPACE=/workspace -e DOCKER=TRUE -w /workspace --name frr-img --hostname frr-img -u $USER reg-nw-user:v1 /workspace/Integration/tools/docker/funcp/user/fungible/scripts/parser-test.sh
```

