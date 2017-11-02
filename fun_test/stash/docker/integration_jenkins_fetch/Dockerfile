FROM ubuntu:17.04

# jabraham@server17:~/docker-fetch-build$ ls qemu/
# bzImage  core-image-full-cmdline-qemux86-64.ext4  funeth.ko  nvme-core.ko  nvme.ko


# ##### All SSH Related stuff
RUN apt-get update && apt-get install -y libasan3 iproute2 libpixman-1-dev libglib2.0-dev net-tools openssh-server curl libpng-dev libsdl1.2debian libfdt-dev
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

# QEMU
ADD qemu qemu

# Add startup script
COPY startup.sh startup.sh

ENTRYPOINT ["./startup.sh"]