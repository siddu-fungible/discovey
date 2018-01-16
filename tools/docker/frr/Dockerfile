FROM ubuntu:16.04
MAINTAINER Amit Surana <amit.surana@fungible.com> 

RUN apt-get update && apt-get install -y \
    openssh-server \
    iputils-ping \
    traceroute \
    sysstat \
    supervisor \
    libasan2

RUN mkdir -p /var/run/sshd /var/run/dpcsh /var/run/funos-posix /var/log/supervisor

RUN echo 'root:fun123' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN groupadd -g 92 frr
RUN groupadd -r -g 85 frrvty
RUN adduser --system --ingroup frr --home /var/run/frr/ --gecos "FRRouting suite" --shell /sbin/nologin frr
RUN usermod -a -G frrvty frr

RUN install -m 755 -o frr -g frr -d /var/log/frr
RUN install -m 755 -o frr -g frr /dev/null /var/log/frr/bgpd.log
RUN install -m 755 -o frr -g frr /dev/null /var/log/frr/isisd.log
RUN install -m 755 -o frr -g frr /dev/null /var/log/frr/zebra.log
RUN install -m 775 -o frr -g frrvty -d /etc/frr
RUN install -m 640 -o frr -g frr /dev/null /etc/frr/zebra.conf
RUN install -m 640 -o frr -g frr /dev/null /etc/frr/bgpd.conf
RUN install -m 640 -o frr -g frr /dev/null /etc/frr/ospfd.conf
RUN install -m 640 -o frr -g frr /dev/null /etc/frr/ospf6d.conf
RUN install -m 640 -o frr -g frr /dev/null /etc/frr/isisd.conf
RUN install -m 640 -o frr -g frr /dev/null /etc/frr/ripd.conf
RUN install -m 640 -o frr -g frr /dev/null /etc/frr/ripngd.conf
RUN install -m 640 -o frr -g frr /dev/null /etc/frr/pimd.conf
RUN install -m 640 -o frr -g frr /dev/null /etc/frr/ldpd.conf
RUN install -m 640 -o frr -g frr /dev/null /etc/frr/nhrpd.conf    
RUN install -m 640 -o frr -g frrvty /dev/null /etc/frr/vtysh.conf

RUN sed -i 's/#net.ipv4.ip_forward=./net.ipv4.ip_forward=1/g' /etc/sysctl.conf 

COPY conf/frr /etc/default/frr
RUN chmod 644 /etc/default/frr
COPY conf/daemons /etc/frr/daemons
RUN chmod 644 /etc/frr/daemons
COPY conf/daemons.conf /etc/frr/daemons.conf
RUN chmod 644 /etc/frr/daemons.conf
COPY conf/zebra.conf /etc/frr/zebra.conf
RUN chmod 644 /etc/frr/zebra.conf
COPY conf/bgpd.conf /etc/frr/bgpd.conf
RUN chmod 644 /etc/frr/bgpd.conf
COPY conf/isisd.conf /etc/frr/isisd.conf
RUN chmod 644 /etc/frr/isisd.conf
RUN chown frr:frrvty /etc/frr/zebra.conf /etc/frr/bgpd.conf /etc/frr/isisd.conf
COPY conf/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN install -m 775 -d /usr/lib/frr
RUN install -m 775 -o frr -g frrvty -d /etc/frr

COPY bin/ /usr/lib/frr
COPY bin/vtysh /usr/bin
COPY libs/ /lib/x86_64-linux-gnu/
COPY frr_lib/ /usr/lib/
ENV PATH "/usr/lib/frr/:/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin"
CMD ["/usr/bin/supervisord"]
