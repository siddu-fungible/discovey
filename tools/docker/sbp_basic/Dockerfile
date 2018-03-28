FROM ubuntu:17.10

# Begin

# Install packages
ARG ZYNQ_SETUP_DIR=/zynq_setup
RUN mkdir -p $ZYNQ_SETUP_DIR
WORKDIR $ZYNQ_SETUP_DIR
RUN rm -vf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y net-tools openssh-server curl sudo rsync xxd
RUN apt-get install -y libpthread-stubs0-dev gcc-multilib g++-multilib cmake cppcheck doxygen python-pip git screen
RUN apt-get install -y libssl-dev gcc libc6-dev-armhf-cross libc6-dev-i386 libssl-dev

# Zynq related
RUN apt-get install -y gcc-arm-linux-gnueabihf
ADD http://codescape.mips.com/components/toolchain/2016.05-03/Codescape.GNU.Tools.Package.2016.05-03.for.MIPS.MTI.Bare.Metal.CentOS-5.x86_64.tar.gz $ZYNQ_SETUP_DIR/
RUN cd $ZYNQ_SETUP_DIR && tar -zxf Codescape.GNU.Tools.Package.2016.05-03.for.MIPS.MTI.Bare.Metal.CentOS-5.x86_64.tar.gz

RUN pip install pycrypto ed25519 curve25519-donna  ecdsa
RUN git clone https://github.com/doegox/python-cryptoplus.git
RUN cd python-cryptoplus && git checkout a5a1f8aecce4ddf476b2d80b586822d9e91eeb7d && python setup.py install
RUN git clone https://github.com/google/googletest.git

# HSM related
RUN apt-get -y install softhsm2 python3 python3-pip

#install the PKCS11 python package
RUN pip3 install python-pkcs11



# ##### All SSH Related stuff
RUN mkdir /var/run/sshd
RUN echo 'root:fun123' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile
EXPOSE 22

ENV MIPS_ELF_ROOT=$ZYNQ_SETUP_DIR/mips-mti-elf/2016.05-03/

RUN shebang='#!/usr/bin/env bash'; \
env_vars="export MIPS_ELF_ROOT=$ZYNQ_SETUP_DIR/mips-mti-elf/2016.05-03"; \
echo $shebang$'\n'$env_vars > /etc/profile.d/env_vars.sh


# Add startup script
COPY startup.sh /startup.sh

ENTRYPOINT ["/startup.sh"]
