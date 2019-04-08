FROM ubuntu:18.04

# Begin

# Install packages
RUN rm -vf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y net-tools openssh-server curl 


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


# Add startup script
COPY startup.sh startup.sh

ENTRYPOINT ["./startup.sh"]
