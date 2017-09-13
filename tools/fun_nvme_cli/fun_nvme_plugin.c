#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <linux/fs.h>
#include <inttypes.h>
#include <asm/byteorder.h>
#include <arpa/inet.h>
#include "../../../linux/nvme_ioctl.h"
#include <sys/time.h>

#include "../../../nvme.h"
#include "../../../nvme-print.h"
#include "../../../nvme-ioctl.h"
#include "../../../json.h"
#include "../../../plugin.h"

#include "../../../argconfig.h"
#include "../../../suffix.h"

#include "fun_nvme_tool.h"
#include <semaphore.h>

#define CREATE_CMD

#include "fun_nvme_plugin.h"

struct fio_thread_struct fio_thread = {};
sem_t sem_fun1;

pthread_mutex_t fun_mutex;


static const char *output_format = "Output format: normal|json|binary";

static unsigned long long elapsed_utime(struct timeval start_time,
                                        struct timeval end_time)
{
        unsigned long long ret = (end_time.tv_sec - start_time.tv_sec) * 1000000 +
                (end_time.tv_usec - start_time.tv_usec);
        return ret;
}

static int fun_connect(int argc, char **argv, struct command *cmd, struct plugin *plugin)
{
        int rc=1, i;
	char *desc = "Connect to F1";

	struct config {
		char *nqn;
		char *transport;
		char *traddr;
		char *trsvcid;
		char *host_traddr;
		char *hostnqn;
		char *hostid;
		int nr_io_queues;
		int queue_size;
		int keep_alive_tmo;
		int reconnect_delay;
		int ctrl_loss_tmo;
		char *raw;
		char *device;
	} cfg = { NULL };


	const struct argconfig_commandline_options command_line_options[] = {
                {"nqn",             'n', "LIST", CFG_STRING, &cfg.nqn,             required_argument, "nqn name" },
                {"traddr",          'a', "LIST", CFG_STRING, &cfg.traddr,          required_argument, "transport address" },
                {"trsvcid",         's', "LIST", CFG_STRING, &cfg.trsvcid,         required_argument, "transport service id (e.g. IP port)" },
                {"host-traddr",     'w', "LIST", CFG_STRING, &cfg.host_traddr,     required_argument, "host traddr (e.g. FC WWN's)" },
                {"hostnqn",         'q', "LIST", CFG_STRING, &cfg.hostnqn,         required_argument, "user-defined hostnqn" },
                {"hostid",          'I', "LIST", CFG_STRING, &cfg.hostid,      required_argument, "user-defined hostid (if default not used)"},
                {"nr-io-queues",    'i', "LIST", CFG_INT, &cfg.nr_io_queues,    required_argument, "number of io queues to use (default is core count)" },
                {"queue-size",      'Q', "LIST", CFG_INT, &cfg.queue_size,      required_argument, "number of io queue elements to use (default 128)" },
                {"keep-alive-tmo",  'k', "LIST", CFG_INT, &cfg.keep_alive_tmo,  required_argument, "keep alive timeout period in seconds" },
                {"reconnect-delay", 'c', "LIST", CFG_INT, &cfg.reconnect_delay, required_argument, "reconnect timeout period in seconds" },
                {"ctrl-loss-tmo",   'l', "LIST", CFG_INT, &cfg.ctrl_loss_tmo,   required_argument, "controller loss timeout period in seconds" },
                {NULL},
        };

        argconfig_parse(argc, argv, desc, command_line_options, &cfg,
                        sizeof(cfg));

	if (!cfg.traddr) {
		fprintf(stderr, "need an address (-a) argument to specify F1 IP\n");
			return -EINVAL;
	}
	if (!cfg.host_traddr) {
		fprintf(stderr, "need an address (-w) argument to specify Host IP\n");
			return -EINVAL;
	}

	if (!cfg.nqn) cfg.nqn = "nqn.2017-05.com.fungible:nss-uuid1";
	if (!cfg.nr_io_queues) cfg.nr_io_queues = 1;	
	if (!cfg.queue_size) cfg.queue_size = 128;	
	if (!cfg.keep_alive_tmo) cfg.keep_alive_tmo = 100;	

        printf("\nClient IP=%s, F1 IP=%s, number of NS=%d, IO Queues = %d, NQN = %s \n\n",\
                 cfg.host_traddr, cfg.traddr, 1,\
                 cfg.nr_io_queues, cfg.nqn);

        rc = fun_client_start(inet_addr(cfg.host_traddr), inet_addr(cfg.traddr));

        if (rc) goto init_failed;

        sem_init(&sem_fun1, 0, 0);

        rc = fun_admin_io_connect(0,cfg.queue_size, cfg.keep_alive_tmo,0xFFFF,cfg.nqn); 
        if (rc) goto init_failed;
        sem_wait(&sem_fun1);

        rc = fun_enable_controller();
        if (rc) goto init_failed;
        sem_wait(&sem_fun1);

        for(i=1; i<=cfg.nr_io_queues; i++){
                rc = fun_admin_io_connect(i,cfg.queue_size, cfg.keep_alive_tmo,0xFFFF,cfg.nqn); 
                if (rc) goto init_failed;
                sem_wait(&sem_fun1);
        }
        rc = 0;

init_failed:
        //return rc;
        return 0;
}

static int fun_id_ctrl(int argc, char **argv, struct command *cmd, struct plugin *plugin)
{
	const char *desc = "Send an Identify Controller command to "\
		"the given device and report information about the specified "\
		"controller in human-readable or "\
		"binary format. May also return vendor-specific "\
		"controller attributes in hex-dump if requested.";
	const char *vendor_specific = "dump binary vendor infos";
	const char *raw_binary = "show infos in binary format";
	const char *human_readable = "show infos in readable format";
	int err, fmt;
	unsigned int flags = 0;
	struct nvme_id_ctrl ctrl;

	struct config {
		char *traddr;
		char *host_traddr;
		int vendor_specific;
		int raw_binary;
		int human_readable;
		char *output_format;
	};

	struct config cfg = {
		.traddr		= NULL,
		.host_traddr	= NULL,
		.output_format = "normal",
	};

	const struct argconfig_commandline_options command_line_options[] = {
                {"traddr",          'a', "LIST", CFG_STRING, &cfg.traddr,          required_argument, "transport address" },
                {"host-traddr",     'w', "LIST", CFG_STRING, &cfg.host_traddr,     required_argument, "host traddr (e.g. FC WWN's)" },
		{"vendor-specific", 'v', "",    CFG_NONE,   &cfg.vendor_specific, no_argument,       vendor_specific},
		{"raw-binary",      'b', "",    CFG_NONE,   &cfg.raw_binary,      no_argument,       raw_binary},
		{"human-readable",  'H', "",    CFG_NONE,   &cfg.human_readable,  no_argument,       human_readable},
		{"output-format",   'o', "FMT", CFG_STRING, &cfg.output_format,   required_argument, output_format },
		{NULL}
	};

        argconfig_parse(argc, argv, desc, command_line_options, &cfg,
                        sizeof(cfg));
	if (!cfg.traddr) {
		fprintf(stderr, "need an address (-a) argument to specify F1 IP\n");
			return -EINVAL;
	}
	if (!cfg.host_traddr) {
		fprintf(stderr, "need an address (-w) argument to specify Host IP\n");
			return -EINVAL;
	}

	fmt = validate_output_format(cfg.output_format);
	if (fmt < 0)
		return fmt;
	if (cfg.raw_binary) {
		fprintf(stderr, "binary output\n");
		fmt = BINARY;
	}

	if (cfg.vendor_specific)
		flags |= VS;
	if (cfg.human_readable)
		flags |= HUMAN;

        err = fun_client_start(inet_addr(cfg.host_traddr), inet_addr(cfg.traddr));

	if (!err) {
        	sem_init(&sem_fun1, 0, 0);
		err = fun_identify(0,&ctrl,0);
	}

	if (!err) {
        	sem_wait(&sem_fun1);
		if (fmt == BINARY)
			d_raw((unsigned char *)&ctrl, sizeof(ctrl));
		else if (fmt == JSON)
			json_nvme_id_ctrl(&ctrl, flags, NULL);
		else {
			printf("NVME Identify Controller:\n");
			__show_nvme_id_ctrl(&ctrl, flags, NULL);
		}
	}
	else if (err > 0)
		fprintf(stderr, "NVMe Status:%s(%x)\n",
				nvme_status_to_string(err), err);
	else
		perror("identify controller");

	return err;
}

static int fun_id_ns(int argc, char **argv, struct command *cmd, struct plugin *plugin)
{
	const char *desc = "Send an Identify Namespace command to the "\
		"given device, returns properties of the specified namespace "\
		"in either human-readable or binary format. Can also return "\
		"binary vendor-specific namespace attributes.";
	const char *force = "Return this namespace, even if not attaced (1.2 devices only)";
	const char *vendor_specific = "dump binary vendor infos";
	const char *raw_binary = "show infos in binary format";
	const char *human_readable = "show infos in readable format";
	const char *namespace_id = "identifier of desired namespace";
	struct nvme_id_ns ns;
	int err, fmt;
	unsigned int flags = 0;

	struct config {
		__u32 namespace_id;
		char *traddr;
		char *host_traddr;
		int   vendor_specific;
		int   raw_binary;
		int   human_readable;
		int   force;
		char *output_format;
	};

	struct config cfg = {
		.namespace_id    = 0,
		.traddr		= NULL,
		.host_traddr	= NULL,
		.output_format = "normal",
	};

	const struct argconfig_commandline_options command_line_options[] = {
		{"namespace-id",    'n', "NUM", CFG_POSITIVE, &cfg.namespace_id,    required_argument, namespace_id},
                {"traddr",          'a', "LIST", CFG_STRING, &cfg.traddr,          required_argument, "transport address" },
                {"host-traddr",     'w', "LIST", CFG_STRING, &cfg.host_traddr,     required_argument, "host traddr (e.g. FC WWN's)" },
		{"force",           'f', "",    CFG_NONE,     &cfg.force,           no_argument,       force},
		{"vendor-specific", 'v', "",    CFG_NONE,     &cfg.vendor_specific, no_argument,       vendor_specific},
		{"raw-binary",      'b', "",    CFG_NONE,     &cfg.raw_binary,      no_argument,       raw_binary},
		{"human-readable",  'H', "",    CFG_NONE,     &cfg.human_readable,  no_argument,       human_readable},
		{"output-format",   'o', "FMT", CFG_STRING,   &cfg.output_format,   required_argument, output_format },
		{NULL}
	};

        argconfig_parse(argc, argv, desc, command_line_options, &cfg,
                        sizeof(cfg));
	if (!cfg.traddr) {
		fprintf(stderr, "need an address (-a) argument to specify F1 IP\n");
			return -EINVAL;
	}
	if (!cfg.host_traddr) {
		fprintf(stderr, "need an address (-w) argument to specify Host IP\n");
			return -EINVAL;
	}

	if (!cfg.namespace_id) {
		fprintf(stderr, "need namespace id  argument\n");
			return -EINVAL;
	}

	fmt = validate_output_format(cfg.output_format);
	if (fmt < 0)
		return fmt;
	if (cfg.raw_binary)
		fmt = BINARY;
	if (cfg.vendor_specific)
		flags |= VS;
	if (cfg.human_readable)
		flags |= HUMAN;
	if (!cfg.namespace_id)
		cfg.namespace_id = 1;

        err = fun_client_start(inet_addr(cfg.host_traddr), inet_addr(cfg.traddr));

	if (!err) {
        	sem_init(&sem_fun1, 0, 0);
		err = fun_identify(cfg.namespace_id,&ns, cfg.force);
	}

	if (!err) {
        	sem_wait(&sem_fun1);
		if (fmt == BINARY)
			d_raw((unsigned char *)&ns, sizeof(ns));
		else if (fmt == JSON)
			json_nvme_id_ns(&ns, flags);
		else {
			printf("NVME Identify Namespace %d:\n", cfg.namespace_id);
			show_nvme_id_ns(&ns, flags);
		}
	}
	else if (err > 0)
		fprintf(stderr, "NVMe Status:%s(%x) NSID:%d\n",
			nvme_status_to_string(err), err, cfg.namespace_id);
	else
		perror("identify namespace");
	return err;
}


static int fun_submit_io(int opcode, char *command, const char *desc,
		     int argc, char **argv)
{
	struct timeval start_time, end_time;
	void *buffer, *mbuffer = NULL;
	int err = 0;
	int dfd, mfd;
	int flags = opcode & 1 ? O_RDONLY : O_WRONLY | O_CREAT;
	int mode = S_IRUSR | S_IWUSR |S_IRGRP | S_IWGRP| S_IROTH;
	__u16 control = 0;
	int phys_sector_size = 0;
	long long buffer_size = 0;

	const char *start_block = "64-bit addr of first block to access";
	const char *block_count = "number of blocks (zeroes based) on device to access";
	const char *data_size = "size of data in bytes";
	const char *metadata_size = "size of metadata in bytes";
	const char *ref_tag = "reference tag (for end to end PI)";
	const char *data = "data file";
	const char *metadata = "metadata file";
	const char *prinfo = "PI and check field";
	const char *app_tag_mask = "app tag mask (for end to end PI)";
	const char *app_tag = "app tag (for end to end PI)";
	const char *limited_retry = "limit num. media access attempts";
	const char *latency = "output latency statistics";
	const char *force = "force device to commit data before command completes";
	const char *show = "show command before sending";
	const char *dry = "show command instead of sending";
	const char *namespace_id = "desired namespace";

	struct config {
		__u32 namespace_id;
		char *traddr;
		char *host_traddr;
		__u64 start_block;
		__u16 block_count;
		__u64 data_size;
		__u64 metadata_size;
		__u32 ref_tag;
		char  *data;
		char  *metadata;
		__u8  prinfo;
		__u16 app_tag_mask;
		__u16 app_tag;
		int   limited_retry;
		int   force_unit_access;
		int   show;
		int   dry_run;
		int   latency;
	};

	struct config cfg = {
		.namespace_id    = 0,
		.traddr		= NULL,
		.host_traddr	= NULL,
		.start_block     = 0,
		.block_count     = 0,
		.data_size       = 0,
		.metadata_size   = 0,
		.ref_tag         = 0,
		.data            = "",
		.metadata        = "",
		.prinfo          = 0,
		.app_tag_mask    = 0,
		.app_tag         = 0,
	};

	const struct argconfig_commandline_options command_line_options[] = {
		{"namespace-id",    'n', "NUM", CFG_POSITIVE, &cfg.namespace_id,    required_argument, namespace_id},
                {"traddr",          'a', "LIST", CFG_STRING, &cfg.traddr,          required_argument, "transport address" },
                {"host-traddr",     'w', "LIST", CFG_STRING, &cfg.host_traddr,     required_argument, "host traddr (e.g. FC WWN's)" },
		{"start-block",       's', "NUM",  CFG_LONG_SUFFIX, &cfg.start_block,       required_argument, start_block},
		{"block-count",       'c', "NUM",  CFG_SHORT,       &cfg.block_count,       required_argument, block_count},
		{"data-size",         'z', "NUM",  CFG_LONG_SUFFIX, &cfg.data_size,         required_argument, data_size},
		{"metadata-size",     'y', "NUM",  CFG_LONG_SUFFIX, &cfg.metadata_size,     required_argument, metadata_size},
		{"ref-tag",           'r', "NUM",  CFG_POSITIVE,    &cfg.ref_tag,           required_argument, ref_tag},
		{"data",              'd', "FILE", CFG_STRING,      &cfg.data,              required_argument, data},
		{"metadata",          'M', "FILE", CFG_STRING,      &cfg.metadata,          required_argument, metadata},
		{"prinfo",            'p', "NUM",  CFG_BYTE,        &cfg.prinfo,            required_argument, prinfo},
		{"app-tag-mask",      'm', "NUM",  CFG_SHORT,       &cfg.app_tag_mask,      required_argument, app_tag_mask},
		{"app-tag",           'a', "NUM",  CFG_SHORT,       &cfg.app_tag,           required_argument, app_tag},
		{"limited-retry",     'l', "",     CFG_NONE,        &cfg.limited_retry,     no_argument,       limited_retry},
		{"force-unit-access", 'f', "",     CFG_NONE,        &cfg.force_unit_access, no_argument,       force},
		{"show-command",      'v', "",     CFG_NONE,        &cfg.show,              no_argument,       show},
		{"dry-run",           'w', "",     CFG_NONE,        &cfg.dry_run,           no_argument,       dry},
		{"latency",           't', "",     CFG_NONE,        &cfg.latency,           no_argument,       latency},
		{NULL}
	};


        argconfig_parse(argc, argv, desc, command_line_options, &cfg,
                        sizeof(cfg));
	if (!cfg.traddr) {
		fprintf(stderr, "need an address (-a) argument to specify F1 IP\n");
			return -EINVAL;
	}
	if (!cfg.host_traddr) {
		fprintf(stderr, "need an address (-w) argument to specify Host IP\n");
			return -EINVAL;
	}
	if (!cfg.namespace_id) {
		fprintf(stderr, "%s: namespace-id parameter required\n", command);
		return EINVAL;
	}

	dfd = mfd = opcode & 1 ? STDIN_FILENO : STDOUT_FILENO;
	if (cfg.prinfo > 0xf)
		return EINVAL;
	control |= (cfg.prinfo << 10);
	if (cfg.limited_retry)
		control |= NVME_RW_LR;
	if (cfg.force_unit_access)
		control |= NVME_RW_FUA;
	if (strlen(cfg.data)){
		dfd = open(cfg.data, flags, mode);
		if (dfd < 0) {
			perror(cfg.data);
			return EINVAL;
		}
		mfd = dfd;
	}
	if (strlen(cfg.metadata)){
		mfd = open(cfg.metadata, flags, mode);
		if (mfd < 0) {
			perror(cfg.metadata);
			return EINVAL;
		}
	}

	if (!cfg.data_size)	{
		fprintf(stderr, "data size not provided\n");
		return EINVAL;
	}


	phys_sector_size = 4096; //FIX ME

	buffer_size = (cfg.block_count + 1) * phys_sector_size;
	if (cfg.data_size < buffer_size) {
		fprintf(stderr, "Rounding data size to fit block count (%lld bytes)\n",
				buffer_size);
	} else {
		buffer_size = cfg.data_size;
	}

	if (posix_memalign(&buffer, getpagesize(), buffer_size)) {
		fprintf(stderr, "can not allocate io payload\n");
		return ENOMEM;
	}
	memset(buffer, 0, cfg.data_size);

	if (cfg.metadata_size) {
		mbuffer = malloc(cfg.metadata_size);
		if (!mbuffer) {
 			free(buffer);
			fprintf(stderr, "can not allocate io metadata payload\n");
			return ENOMEM;
		}
	}

	if ((opcode & 1) && read(dfd, (void *)buffer, cfg.data_size) < 0) {
		fprintf(stderr, "failed to read data buffer from input file\n");
		err = EINVAL;
		goto free_and_return;
	}

	if ((opcode & 1) && cfg.metadata_size &&
				read(mfd, (void *)mbuffer, cfg.metadata_size) < 0) {
		fprintf(stderr, "failed to read meta-data buffer from input file\n");
		err = EINVAL;
		goto free_and_return;
	}

	if (cfg.show) {
		printf("opcode       : %02x\n", opcode);
		printf("flags        : %02x\n", 0);
		printf("control      : %04x\n", control);
		printf("nblocks      : %04x\n", cfg.block_count);
		printf("rsvd         : %04x\n", 0);
		printf("metadata     : %"PRIx64"\n", (uint64_t)(uintptr_t)mbuffer);
		printf("addr         : %"PRIx64"\n", (uint64_t)(uintptr_t)buffer);
		printf("sbla         : %"PRIx64"\n", (uint64_t)cfg.start_block);
		printf("dsmgmt       : %08x\n", 0);
		printf("reftag       : %08x\n", cfg.ref_tag);
		printf("apptag       : %04x\n", cfg.app_tag);
		printf("appmask      : %04x\n", cfg.app_tag_mask);
		if (cfg.dry_run)
			goto free_and_return;
	}

	gettimeofday(&start_time, NULL);
        err = fun_client_start(inet_addr(cfg.host_traddr), inet_addr(cfg.traddr));

	if (!err) {
        	sem_init(&sem_fun1, 0, 0);
		err = fun_nvme_io(cfg.namespace_id, opcode, cfg.start_block, cfg.block_count, control, 0,
			cfg.ref_tag, cfg.app_tag, cfg.app_tag_mask, buffer, mbuffer, 1); //FIX - get qid from cli
	}
	if(!err) sem_wait(&sem_fun1);

	gettimeofday(&end_time, NULL);
	if (cfg.latency)
		printf(" latency: %s: %llu us\n",
			command, elapsed_utime(start_time, end_time));
	if (err < 0)
		perror("submit-io");
	else if (err)
		printf("%s:%s(%04x)\n", command, nvme_status_to_string(err), err);
	else {
		if (!(opcode & 1) && write(dfd, (void *)buffer, cfg.data_size) < 0) {
			fprintf(stderr, "failed to write buffer to output file\n");
			err = EINVAL;
			goto free_and_return;
		} else if (!(opcode & 1) && cfg.metadata_size &&
				write(mfd, (void *)mbuffer, cfg.metadata_size) < 0) {
			fprintf(stderr, "failed to write meta-data buffer to output file\n");
			err = EINVAL;
			goto free_and_return;
		} else
			fprintf(stderr, "%s: Success\n", command);
	}
 free_and_return:
	free(buffer);
	if (cfg.metadata_size)
		free(mbuffer);
	return err;
}


static int fun_write_cmd(int argc, char **argv, struct command *cmd, struct plugin *plugin)
{
        const char *desc = "Copy from provided data buffer (default "\
                "buffer is stdin) to specified logical blocks on the given "\
                "device.";
        return fun_submit_io(nvme_cmd_write, "write", desc, argc, argv);
}


static int fun_read_cmd(int argc, char **argv, struct command *cmd, struct plugin *plugin)
{
        const char *desc = "Copy specified logical blocks on the given "\
                "device to specified data buffer (default buffer is stdout).";
        return fun_submit_io(nvme_cmd_read, "read", desc, argc, argv);
}

static int fun_show_registers(int argc, char **argv, struct command *cmd, struct plugin *plugin)
{
	const char *desc = "Reads and shows the defined NVMe controller registers "\
					"in binary or human-readable format";
	const char *human_readable = "show info in readable format";
	void *bar = calloc(8192, 1);
	int err = 0;

	struct config {
		char *traddr;
		char *host_traddr;
		int human_readable;
	};

	struct config cfg = {
		.traddr		= NULL,
		.host_traddr	= NULL,
		.human_readable = 0,
	};

	const struct argconfig_commandline_options command_line_options[] = {
                {"traddr",          'a', "LIST", CFG_STRING, &cfg.traddr,          required_argument, "transport address" },
                {"host-traddr",     'w', "LIST", CFG_STRING, &cfg.host_traddr,     required_argument, "host traddr (e.g. FC WWN's)" },
		{"human-readable", 'H', "", CFG_NONE, &cfg.human_readable, no_argument, human_readable},
		{NULL}
	};

        argconfig_parse(argc, argv, desc, command_line_options, &cfg,
                        sizeof(cfg));
	if (!cfg.traddr) {
		fprintf(stderr, "need an address (-a) argument to specify F1 IP\n");
			return -EINVAL;
	}
	if (!cfg.host_traddr) {
		fprintf(stderr, "need an address (-w) argument to specify Host IP\n");
			return -EINVAL;
	}


        err = fun_client_start(inet_addr(cfg.host_traddr), inet_addr(cfg.traddr));

	if (!err) {
        	sem_init(&sem_fun1, 0, 0);
		fun_property_get(bar, 0, 1 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
		fun_property_get((char *) bar+0x8, 0x8, 1 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
		fun_property_get((char *) bar+0x0c, 0x0c, 0 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
		fun_property_get((char *) bar+0x10, 0x10, 0 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
		fun_property_get((char *) bar+0x14, 0x14, 0 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
		fun_property_get((char *) bar+0x18, 0x18, 0 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
		fun_property_get((char *) bar+0x1c, 0x1c, 0 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
		fun_property_get((char *) bar+0x20, 0x20, 0 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
		fun_property_get((char *) bar+0x24, 0x24, 0 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
		fun_property_get((char *) bar+0x28, 0x28, 1 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
		fun_property_get((char *) bar+0x30, 0x30, 1 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
		fun_property_get((char *) bar+0x38, 0x38, 0 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
		fun_property_get((char *) bar+0x3c, 0x3c, 0 /*FABRICS_PROPERTY_ATTRIB_SIZE_8*/ );
		sem_wait(&sem_fun1);
	}
//	if(!err) sem_wait(&sem_fun1);

	show_ctrl_registers(bar, cfg.human_readable ? HUMAN : 0);
	return 0;
}


static int fun_create_ns(int argc, char **argv, struct command *cmd, struct plugin *plugin)
{
	const char *desc = "Send a namespace management command "\
		"to the specified device to create a namespace with the given "\
		"parameters. The next available namespace ID is used for the "\
		"create operation. Note that create-ns does not attach the "\
		"namespace to a controller, the attach-ns command is needed.";
	const char *nsze = "size of ns";
	const char *ncap = "capacity of ns";
	const char *flbas = "FLBA size";
	const char *dps = "data protection capabilities";
	const char *nmic = "multipath and sharing capabilities";

	int err = 0;
	__u32 nsid;

	struct config {
		char *traddr;
		char *host_traddr;
		__u64	nsze;
		__u64	ncap;
		__u8	flbas;
		__u8	dps;
		__u8	nmic;
	};

	struct config cfg = { NULL };

	const struct argconfig_commandline_options command_line_options[] = {
                {"traddr",          'a', "LIST", CFG_STRING, &cfg.traddr,          required_argument, "transport address" },
                {"host-traddr",     'w', "LIST", CFG_STRING, &cfg.host_traddr,     required_argument, "host traddr (e.g. FC WWN's)" },
		{"nsze",  's', "NUM", CFG_LONG_SUFFIX, &cfg.nsze,  required_argument, nsze},
		{"ncap",  'c', "NUM", CFG_LONG_SUFFIX, &cfg.ncap,  required_argument, ncap},
		{"flbas", 'f', "NUM", CFG_BYTE,        &cfg.flbas, required_argument, flbas},
		{"dps",   'd', "NUM", CFG_BYTE,        &cfg.dps,   required_argument, dps},
		{"nmic",  'm', "NUM", CFG_BYTE,        &cfg.nmic,  required_argument, nmic},
		{NULL}
	};

        argconfig_parse(argc, argv, desc, command_line_options, &cfg,
                        sizeof(cfg));
	if (!cfg.traddr) {
		fprintf(stderr, "need an address (-a) argument to specify F1 IP\n");
			return -EINVAL;
	}
	if (!cfg.host_traddr) {
		fprintf(stderr, "need an address (-w) argument to specify Host IP\n");
			return -EINVAL;
	}
	if (!cfg.nsze) cfg.nsze = 4096;
	if (!cfg.ncap) cfg.ncap = cfg.nsze;

        err = fun_client_start(inet_addr(cfg.host_traddr), inet_addr(cfg.traddr));

	if (!err) {
        	sem_init(&sem_fun1, 0, 0);
		err = fun_nvmf_ns_create(cfg.nsze, cfg.ncap, cfg.flbas, cfg.dps, cfg.nmic, &nsid);
	}
	if (!err){
		sem_wait(&sem_fun1);
		printf("%s: Success, created nsid:%d\n", cmd->name, nsid);
	}
	else if (err > 0)
		fprintf(stderr, "NVMe Status:%s(%x)\n",
					nvme_status_to_string(err), err);
	else
		perror("create namespace");
	return err;
}




static int fun_delete_ns(int argc, char **argv, struct command *cmd, struct plugin *plugin)
{
	const char *desc = "Delete the given namespace by "\
		"sending a namespace management command to "\
		"the provided device. All controllers should be detached from "\
		"the namespace prior to namespace deletion. A namespace ID "\
		"becomes inactive when that namespace is detached or, if "\
		"the namespace is not already inactive, once deleted.";
	const char *namespace_id = "namespace to delete";
	int err;

	struct config {
		char *traddr;
		char *host_traddr;
		__u32	namespace_id;
	};

	struct config cfg = {
		.traddr		= NULL,
		.host_traddr	= NULL,
		.namespace_id    = 0,
	};

	const struct argconfig_commandline_options command_line_options[] = {
                {"traddr",          'a', "LIST", CFG_STRING, &cfg.traddr,          required_argument, "transport address" },
                {"host-traddr",     'w', "LIST", CFG_STRING, &cfg.host_traddr,     required_argument, "host traddr (e.g. FC WWN's)" },
		{"namespace-id", 'n', "NUM",  CFG_POSITIVE, &cfg.namespace_id,    required_argument, namespace_id},
		{NULL}
	};

        argconfig_parse(argc, argv, desc, command_line_options, &cfg,
                        sizeof(cfg));
	if (!cfg.traddr) {
		fprintf(stderr, "need an address (-a) argument to specify F1 IP\n");
			return -EINVAL;
	}
	if (!cfg.host_traddr) {
		fprintf(stderr, "need an address (-w) argument to specify Host IP\n");
			return -EINVAL;
	}



	if (!cfg.namespace_id) {
		fprintf(stderr, "%s: namespace-id parameter required\n",
						cmd->name);
		return EINVAL;
	}

        err = fun_client_start(inet_addr(cfg.host_traddr), inet_addr(cfg.traddr));

	if (!err) {
        	sem_init(&sem_fun1, 0, 0);
		err = fun_nvmf_ns_delete(cfg.namespace_id);
	}
	if (!err){
		sem_wait(&sem_fun1);
		printf("%s: Success, deleted nsid:%d\n", cmd->name, cfg.namespace_id);
	} else if (err > 0)
		fprintf(stderr, "NVMe Status:%s(%x)\n",
					nvme_status_to_string(err), err);
	else
		perror("delete namespace");
	return err;
}


static int fun_nvme_attach_ns(int argc, char **argv, int attach, const char *desc, struct command *cmd)
{
	int err;

	const char *namespace_id = "namespace to attach";

	struct config {
		char *traddr;
		char *host_traddr;
		/*char  *cntlist;*/
		__u32 namespace_id;
	};

	struct config cfg = {
		.traddr		= NULL,
		.host_traddr	= NULL,
		.namespace_id = 0,
	};
	const struct argconfig_commandline_options command_line_options[] = {
                {"traddr",          'a', "LIST", CFG_STRING, &cfg.traddr,          required_argument, "transport address" },
                {"host-traddr",     'w', "LIST", CFG_STRING, &cfg.host_traddr,     required_argument, "host traddr (e.g. FC WWN's)" },
		{"namespace-id", 'n', "NUM",  CFG_POSITIVE, &cfg.namespace_id, required_argument, namespace_id},
		/*{"controllers",  'c', "LIST", CFG_STRING,   &cfg.cntlist,      required_argument, cont}, FIX specify NVMF controller*/
		{NULL}
	};

        argconfig_parse(argc, argv, desc, command_line_options, &cfg,
                        sizeof(cfg));
	if (!cfg.traddr) {
		fprintf(stderr, "need an address (-a) argument to specify F1 IP\n");
			return -EINVAL;
	}
	if (!cfg.host_traddr) {
		fprintf(stderr, "need an address (-w) argument to specify Host IP\n");
			return -EINVAL;
	}


	if (!cfg.namespace_id) {
		fprintf(stderr, "%s: namespace-id parameter required\n",
						cmd->name);
		return EINVAL;
	}

        err = fun_client_start(inet_addr(cfg.host_traddr), inet_addr(cfg.traddr));

	if (!err) {
        	sem_init(&sem_fun1, 0, 0);
		err = fun_nvmf_ns_attach_or_detach(cfg.namespace_id, attach);
	}
	if (!err){
		sem_wait(&sem_fun1);
		printf("%s: Success, nsid:%d\n", cmd->name, cfg.namespace_id);
	}
	else if (err > 0)
		fprintf(stderr, "NVMe Status:%s(%x)\n",
					nvme_status_to_string(err), err);
	else
		perror(attach ? "attach namespace" : "detach namespace");
	return err;
}

static int fun_attach_ns(int argc, char **argv, struct command *cmd, struct plugin *plugin)
{
	const char *desc = "Attach the given namespace to the "\
		"given controller or comma-sep list of controllers. ID of the "\
		"given namespace becomes active upon attachment to a "\
		"controller. A namespace must be attached to a controller "\
		"before IO commands may be directed to that namespace.";
	return fun_nvme_attach_ns(argc, argv, 1, desc, cmd);
}

static int fun_detach_ns(int argc, char **argv, struct command *cmd, struct plugin *plugin)
{
	const char *desc = "Detach the given namespace from the "\
		"given controller; de-activates the given namespace's ID. A "\
		"namespace must be attached to a controller before IO "\
		"commands may be directed to that namespace.";
	return fun_nvme_attach_ns(argc, argv, 0, desc, cmd);
}

