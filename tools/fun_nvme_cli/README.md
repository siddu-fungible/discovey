## Synopsis

Fungible plugin for nvme tool. Adds NVMeoF client support over RDS.

## Build

1. Clone nvme cli: https://github.com/linux-nvme/nvme-cli.git
2. cd into 'nvme-cli' 
3. Clone integtration repo: git@github.com:fungible-inc/Integration.git
4. Apply patch to modify the  nvme Makefile and register plugin:
	 'git apply Integration/tools/fun_nvme_cli/patch'   
5. sudo make install

## Options

fun specific options:

root@qa-temp:/home-local/qa/nvme-cli# nvme fun --help  
nvme-1.3.67.gdfed.dirty 
usage: nvme fun <command> [<device>] [<args>] 

The following are all implemented sub-commands:  
  connect         connect to nqn  
  id-ctrl         identify controller  
  id-ns           identify namespace  
  write           Submit a write command, return results  
  read            Submit a read command, return results  
  show-regs       Shows the controller registers. Requires admin character device  
  create-ns       Creates a namespace with the provided parameters  
  delete-ns       Deletes a namespace from the controller  
  attach-ns       Attaches a namespace to requested controller(s)  
  detach-ns       Detaches a namespace from requested controller(s)  
  version         Shows the program version  
  help            Display this help  

See 'nvme fun help <command>' for more information on a specific command


NOTE: When F1 starts, the first operation should be 'connect' from tool  so that it connect to
the subsystem nqn and enable controller. After connect is successful, other commands can
be executed.

Sample jobs are at: 'Integration/tools/fun_nvme_cli/examples'

## Caveats

1. Not yet supported on mac.


