FROM ubuntu:16.04
MAINTAINER Amit Surana <amit.surana@fungible.com>

RUN apt-get update && apt-get install -y libaio1 librdmacm-dev iperf3 openssh-server apache2 supervisor apache2-utils iputils-ping traceroute
RUN mkdir -p /var/lock/apache2 /var/run/apache2 /var/run/sshd /var/run/iperf3 /var/log/supervisor

RUN echo 'root:fun123' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Copy necessary binaries into container
# Please run ./setup_fio.sh before doing docker build
#COPY fio /usr/bin/fio
#ADD http://10.1.20.67:5000/static/media/fio /usr/bin/fio
ADD fio /usr/bin.fio
RUN chmod 777 /usr/bin/fio

ENV PATH "/usr/local/bin/:/sbin:/bin:/usr/sbin:/usr/bin"

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY 1mb /var/www/html
CMD ["/usr/bin/supervisord"]
