FROM    nw-reg-base:v2

ARG  ARG_USER
ARG  ARG_UID
ARG  ARG_GID

RUN  groupadd -g $ARG_GID $ARG_USER; \
     useradd  -g $ARG_GID -u $ARG_UID $ARG_USER -p 9UCUTMOhVIT9o; \
     usermod -aG sudo $ARG_USER; \
     usermod -aG frr $ARG_USER; \
     usermod -aG frrvty $ARG_USER;

RUN  echo "$ARG_USER ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers.d/local
COPY fungible.conf   /etc/ld.so.conf.d/
ENV  PATH "${PATH}:/opt/fungible/bin/frr:/opt/fungible/sbin/frr:/opt/fungible/bin/funcp:/opt/fungible/bin/funos:/opt/fungible/bin/qemu:/opt/fungible/bin/funcp:/opt/fungible/bin/dpcsh"
ENV  LD_LIBRARY_PATH "${LD_LIBRARY_PATH}:/opt/fungible/lib"
COPY environment     /etc/environment
RUN  mkdir -p /opt/fungible/; chmod 777 /opt/fungible/
COPY fungible /opt/fungible

CMD ["/bin/bash"]
