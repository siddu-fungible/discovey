#undef CMD_INC_FILE
#define CMD_INC_FILE Integration/tools/fun_nvme_cli/fun_nvme_plugin

#if !defined(FUN_NVME) || defined(CMD_HEADER_MULTI_READ)
#define FUN_NVME

#include "../../../cmd.h"

PLUGIN(NAME("fun", "Fun specific extensions"),
	COMMAND_LIST(
		ENTRY("connect", "connect to nqn", fun_connect)
		ENTRY("id-ctrl", "identify controller", fun_id_ctrl)
		ENTRY("id-ns", "identify namespace", fun_id_ns)
		ENTRY("write", "Submit a write command, return results", fun_write_cmd)
		ENTRY("read", "Submit a read command, return results", fun_read_cmd)
		ENTRY("show-regs", "Shows the controller registers. Requires admin character device", fun_show_registers)
		ENTRY("create-ns", "Creates a namespace with the provided parameters", fun_create_ns)
		ENTRY("delete-ns", "Deletes a namespace from the controller", fun_delete_ns)
		ENTRY("attach-ns", "Attaches a namespace to requested controller(s)", fun_attach_ns)
		ENTRY("detach-ns", "Detaches a namespace from requested controller(s)", fun_detach_ns)
	)
);

#endif

#include "../../../define_cmd.h"
