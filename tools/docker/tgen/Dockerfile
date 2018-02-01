FROM ubuntu:16.04
MAINTAINER Alagarswamy Devaraj <alagarswamy.devaraj@fungible.com>

RUN apt-get update && apt-get install -y libaio1 librdmacm-dev iperf3 openssh-server apache2 supervisor apache2-utils net-tools gcc make
RUN mkdir -p /var/lock/apache2 /var/run/apache2 /var/run/sshd /var/run/iperf3 /var/log/supervisor

RUN echo 'root:fun123' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY 1mb /var/www/html
RUN mkdir /root/tools
ADD fio /root/tools/fio

WORKDIR "/root/tools/fio"
RUN make install

RUN apt-get remove -y gcc make
RUN apt autoremove -y

ENV PATH "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

CMD ["/usr/bin/supervisord"]
