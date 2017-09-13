# Use an official Python runtime as a parent image
FROM ubuntu:latest

RUN apt-get update && apt-get install -y python libasan2 libpixman-1-dev libglib2.0-dev ssh net-tools

COPY funos-posix funos-posix
COPY my.py my.py
COPY qemu-system-x86_64 qemu-system-x86_64
COPY ubuntu_min.img  ubuntu_min.img
COPY startup.sh startup.sh
ADD pc-bios .

RUN dd if=/dev/zero of=nvfile bs=4096 count=256
RUN ./funos-posix app=mdt_test nvfile=nvfile
# RUN nohup ./funos-posix app=prem_test nvfile=nvfile &

CMD ["./startup.sh"]