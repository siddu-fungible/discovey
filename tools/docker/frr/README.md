Containerized FRR

In order to build a FRR container, follow these steps:

1. Clone FRR repo (git@github.com:fungible-inc/frr.git)
2. In build.sh set WORKDIR appropriately
3. Execute build.sh script:

   If building FRR for the first time on this host, then:
	./build.sh init <frr-container-image-name>
   else:
        ./build.sh <frr-container-image-name>

Executing build.sh will build FRR and also build the FRR container with the necessary config files/binaries.

To run a single FRR container instance, do this:

	sudo docker run --privileged=true --rm -d --name <container_name> --hostname <container_host_name> -p <host_port_1>:22 -p <host_port_2>:2601 -p <host_port_3>:2605 -p <host_port_4>:2608 -p <frr_container_image_name>

To run a fungible DC topology using FRR container, see here:

	https://github.com/fungible-inc/Integration/tree/master/fun_test/lib/topology/topology_manager 
