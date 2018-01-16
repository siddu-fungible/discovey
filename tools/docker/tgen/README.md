To build linux traffic-generator container, do the following:

  1. Place necessary binaries/tools into this directory.
  2. Add 'COPY' statements to Dockerfile to copy the binaries.
  3. sudo docker build -t <tgen_image_name> .

To launch the container, do the following:

sudo docker run --privileged=true --rm -d --name <container_name> --hostname <host_name> -p <host_port>:22 <tgen_image_name> 
