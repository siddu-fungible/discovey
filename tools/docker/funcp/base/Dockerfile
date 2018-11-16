FROM    ubuntu:16.04

ARG     ASIO_VER=1.10.8
ARG     ASIO_REL_TRAIN=Stable
ARG     ASIO_DIR=/fun_external/asio-$ASIO_VER
ARG     ASIO_PKG=/fun_external/asio-$ASIO_VER.tar.bz2
ARG     ASIO_URL=https://sourceforge.net/projects/asio/files/asio/$ASIO_VER%20%28$ASIO_REL_TRAIN%29/asio-$ASIO_VER.tar.bz2
ARG     DEP_INSTALL_DIR=/fun_external/
ARG     REDIS_SO=http://dochub.fungible.local/doc/jenkins/sandbox/frr/libfunjson_redis.so
ARG     REDIS_SO_LOCAL=/usr/local/lib/libfunjson_redis.so

RUN     apt -y update; apt-get -y upgrade; \
        apt-get install --no-install-recommends --no-install-suggests -y \
        gdb python rsync bc procps openssh-client cpio libtool libasan2 less bzip2 vim \
        curl wget libnl-3-dev libnl-route-3-dev libcap2 libpci3 libpng16-16 libpixman-1-0 u-boot-tools \
        iproute2 net-tools openssh-server libsystemd-dev libc-ares-dev \
        texinfo libjson-c-dev openvswitch-switch \
        gcc g++ make gdb python bc git global cscope \
        autoconf bison flex pkg-config \
        libglib2.0-dev libpci-dev libreadline-dev libzlcore-dev \
        libpng16-16 libncurses5-dev libpixman-1-dev u-boot-tools \
        libcap-dev libattr1-dev device-tree-compiler supervisor \
        python-pip perl python3-minimal python-pip python-setuptools sudo iputils-ping \
        build-essential software-properties-common  \
        cmake libboost-dev python-dev libhiredis-dev \
        libpcap-dev automake libsdl-image1.2 language-pack-id \
        libfdt-dev net-tools libc6-dev libncursesw5-dev openvswitch-switch bridge-utils

RUN     add-apt-repository ppa:ubuntu-toolchain-r/test -y && \
        apt-get update && \
        apt-get install gcc-6 g++-6 -y && \
        update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-6 60 --slave /usr/bin/g++ g++ /usr/bin/g++-6 && \
        update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-5 60 --slave /usr/bin/g++ g++ /usr/bin/g++-5; 

RUN     pip install --upgrade pip setuptools 
RUN     pip install --upgrade pyyaml jinja2 gcovr 
RUN     pip install bitstring tabulate pipenv scapy --ignore-installed setuptools
        
RUN     easy_install setuptools_git

# Install needed packages for FunControlPlane
# Add JSON
RUN   mkdir -p $DEP_INSTALL_DIR
RUN   wget -O $DEP_INSTALL_DIR/v3.0.1.tar.gz https://github.com/nlohmann/json/archive/v3.0.1.tar.gz; cd $DEP_INSTALL_DIR; tar xvf v3.0.1.tar.gz;  ln -s json-3.0.1/ json

# Add asio
RUN   cd /fun_external; wget -O $ASIO_PKG $ASIO_URL; \
      tar -xjf $ASIO_PKG -C /fun_external; cd $ASIO_DIR && \
    ./configure --prefix=$DEP_INSTALL_DIR --disable-dependency-tracking --with-boost=no && make -j `nproc` && make install

# Add Gtest and gmock
RUN   cd /fun_external; git clone https://github.com/google/googletest.git;
RUN   mkdir -p /fun_external/googletest/googletest/build; \
      cd /fun_external/googletest/googletest/build; cmake ..; make ; \
      cd /fun_external/googletest/googlemock; cmake CMakeLists.txt ; make

# Add zmq
RUN   cd /fun_external; git clone https://github.com/zeromq/libzmq.git; \
      cd libzmq; git checkout tags/v4.2.2; ./autogen.sh; ./configure; \
      make; make install

# Add Redis
RUN   cd /fun_external; git clone https://github.com/antirez/redis.git; \
      cd redis; git checkout 4.0; \
      sed -i 's/^# unixsocket/unixsocket/g' redis.conf; \
      sed -i 's/^notify-keyspace-events.*/notify-keyspace-events KEA/g' redis.conf; \
      sed -i 's/^# loadmodule.*my.*/loadmodule \/usr\/local\/lib\/libfunjson_redis.so/g' redis.conf; \
      make; make install

# Add hiredis
RUN   cd /fun_external; git clone https://github.com/redis/hiredis.git; \
      cd hiredis; make; make install

# Ydk-gen build requirements
RUN   apt install -y libxml2-dev doxygen graphviz libssh-dev libcurl4-openssl-dev libxslt-dev libtool-bin \
    libpcre3-dev libxslt1-dev python3-dev python-dev devscripts debhelper
RUN   pip install -I pyang==1.6
RUN   pip install -I Sphinx==1.4a1
RUN   pip install -I sphinx-rtd-theme==0.1.9
RUN   pip install -I GitPython==1.0.1
RUN   pip install -I rstr==2.2.6

# Add Tools
RUN   apt install -y gdb tcpdump strace net-tools
# HACK around https://github.com/dotcloud/docker/issues/5490
RUN   mv /usr/sbin/tcpdump /usr/bin/tcpdump

# Set up startup script
COPY  funcp_start_redis.sh /fun_external
RUN   chmod 777 /fun_external/funcp_start_redis.sh
RUN   wget -O $REDIS_SO_LOCAL $REDIS_SO

# Enable root SSH access 
RUN mkdir /var/run/sshd
RUN echo 'root:fun123' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Create FRR user
RUN groupadd -g 92 frr
RUN groupadd -r -g 85 frrvty
RUN adduser --system --ingroup frr --home /var/run/frr/ --gecos "FRRouting suite" --shell /sbin/nologin frr
RUN usermod -a -G frrvty frr

EXPOSE 22

CMD /fun_external/funcp_start_redis.sh
