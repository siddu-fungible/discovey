FROM ubuntu:18.04
ARG DOCKHUB_FUNGIBLE_LOCAL=dockhub.fungible.local
ARG QEMU_DIR=qemu

# ##### All SSH Related stuff
RUN rm -vf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y libasan2 iproute2 libpixman-1-dev libglib2.0-dev net-tools openssh-server curl libpng-dev libsdl1.2debian libfdt-dev
# python sudo
RUN mkdir /var/run/sshd
RUN echo 'root:fun123' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile
EXPOSE 22

# Host OS to be loaded by Qemu
ARG HOST_OS_TGZ
COPY $HOST_OS_TGZ /host_os.tgz

RUN echo $QEMU_DIR
RUN mkdir $QEMU_DIR

# Add startup script
COPY startup.sh startup.sh

ENTRYPOINT ["./startup.sh"]
