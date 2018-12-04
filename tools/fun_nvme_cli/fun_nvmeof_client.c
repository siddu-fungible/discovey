/**
 * Created by Pratapa Vaka on 05-18-2017
 * Copyright © 2017 Fungible. All rights reserved.
 */

/**
 * @file apps/nvmeof_test.c
 * NVMe-oF target driver unit test app
 */

#include "fun_types.h"
#include <stdint.h>
#include <time.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "fun_queue.h"
#include "fun_rdsock.h"
#include "fun_nvme.h"
#include "fun_fabrics.h"
#include "fun_api.h"
#include "fun_bitmap.h"
#include "fun_rdst.h"
#include "fun_epnvme.h"
#include <stdlib.h>
#include <endian.h>
#include <netinet/in.h>
#include <unistd.h>
#include <semaphore.h>
#include "fun_nvme_tool.h"
#include <pthread.h>

extern sem_t sem_fun1;
extern pthread_mutex_t fun_mutex;

struct fun_fio_req_struct {
	struct io_u *io_u[FUN_MAX_Q_DEPTH];	
	void *return_buffer[FUN_MAX_Q_DEPTH];	
	void *original_request[FUN_MAX_Q_DEPTH];	
	BITMAP(cid_bm, FUN_MAX_Q_DEPTH);
};

struct fun_fio_req_struct fun_fio_req = {}; 
extern struct fio_thread_struct fio_thread;
struct rdsock *rdsock_client;

static uint16_t get_cid(void)
{
	uint16_t cid;

	cid =  bitmap_bget(&fun_fio_req.cid_bm);
	assert(cid >= 0);

	return cid;
}

static int nvmeof_send_msg(uint32_t *mb,
	enum fabrics_rds_conn_type conn_type, uint16_t qid, uint16_t buf_size)
{
	struct rdsock_msg *msg = NULL;
	size_t hdr_size = sizeof(struct fabrics_rds_msg_hdr);
	struct fabrics_rds_msg_hdr *hdr;

	int rc = 1;
	
	msg = malloc(sizeof(struct rdsock_msg));
	if (!msg) goto send_failed;

	msg->buf = mb;
	msg->buf_size = buf_size;
	msg->context = (void *)mb;

	msg->msglen = hdr_size;
	msg->msg = malloc(msg->msglen);
	if(!msg->msg) goto send_failed;

	hdr = (struct fabrics_rds_msg_hdr *)msg->msg;
	hdr->conn_type = conn_type;
	hdr->qid = qid;

	rdsock_sendmsg(rdsock_client, msg);

	rc = 0;

send_failed:
	return rc;
}

static char const *hostid_g = "host1";
//static char const *subnqn_g = "nqn.2017-05.com.fungible:nss-uuid1";
static char const *hostnqn_g = "nqn.2017-05.com.fungible:host1";


static void fabrics_common(struct fabrics_cmd *cmd,
	uint32_t fctype, uint32_t cid)
{
	struct fun_nvme_cmd *nvme_cmd = (struct fun_nvme_cmd *) cmd;

	memset(nvme_cmd, 0, NVME_CMD_SIZE);
	nvme_cmd->cmn.opcode = FUN_NVME_FABRICS;
	nvme_cmd->cmn.cid = htole16(cid);
	nvme_cmd->cmn.nsid = htole32(0);

	cmd->cmn.fctype = fctype;
}

static bool handle_nvme_io_resp(struct fabrics_resp *resp, uint16_t buf_size)
{
	uint16_t resp_cid = le16toh(resp->cid);

	struct io_u * io_u = (struct io_u *)fun_fio_req.io_u[resp_cid];

	if (!io_u) { //nvme tool
		struct fun_nvme_rw *cmd = (struct fun_nvme_rw *)fun_fio_req.original_request[resp_cid];
		switch (cmd->cmn.opcode){
		
		case FUN_NVME_READ:
			assert(buf_size - NVME_CPL_SIZE);
			memcpy((uint8_t *)fun_fio_req.return_buffer[resp_cid], (uint8_t *)resp + NVME_CPL_SIZE,
				 buf_size - NVME_CPL_SIZE );

		case FUN_NVME_WRITE:
			break;
		}

		bitmap_bput(&fun_fio_req.cid_bm, resp_cid);
		sem_post(&sem_fun1); 

		return true;
	}
	
	//fio only
	switch (io_u->ddir) {

	case DDIR_READ:

		if ((buf_size - NVME_CPL_SIZE) != io_u->xfer_buflen)
			log_err("Data received has wrong length: Offset = %llu, \
				Expected: %lu  Actual: %lu\n", io_u->offset, \
				io_u->xfer_buflen, buf_size - NVME_CPL_SIZE );
			
		memcpy((uint8_t *)io_u->buf, (uint8_t *)resp + NVME_CPL_SIZE, buf_size - NVME_CPL_SIZE );

		break;

	case DDIR_WRITE:

		break;
	default:
		//FIX handle TRIM and any other actions 
                assert(false);
                break;
	}

	pthread_mutex_lock(&fun_mutex);
	fio_thread.io_us[fio_thread.head] = io_u;
	fio_thread.head++;
	if (fio_thread.head == FUN_MAX_Q_DEPTH) {
		fio_thread.head = 0; 
	}
	fio_thread.completed++;
	pthread_mutex_unlock(&fun_mutex);

	bitmap_bput(&fun_fio_req.cid_bm, resp_cid);
	return true;
}


static void
nvmeof_test_fabric_recv(struct rdsock *sock,
	struct rdsock_msg *msg)
{
	if (msg->buf == NULL) {
		log_err("Response data not present for fabric command \n");
	} else {

		struct fabrics_resp *resp =
			(struct fabrics_resp *)msg->buf;

		uint16_t resp_cid = le16toh(resp->cid);

		assert(resp);
		assert(resp_cid < FUN_MAX_Q_DEPTH);

		struct fun_nvme_status *status = &resp->status;

		struct fabrics_cmd *cmd = (struct fabrics_cmd *)
                        fun_fio_req.original_request[resp_cid];
                uint16_t cmd_cid = le16toh(cmd->cmn.cid);
                assert(cmd);
                assert(resp_cid == cmd_cid);
                assert(status->sc == 0);
                assert(cmd->cmn.opcode == FUN_NVME_FABRICS);
		
		switch (cmd->cmn.fctype) {

        	case FABRICS_CONNECT:

                	if (((struct fabrics_connect_cmd *)cmd)->qid == 0) {

                        	log_info("Received Admin Connect Response\n");
                	} else {

                        	log_info("Received IO Connect Response\n");
                	}

                	break;

        	case FABRICS_PROPERTY_SET:

                	log_info("Received Property Set Response\n");

                	break;

        	case FABRICS_PROPERTY_GET:
			memcpy((uint8_t *)fun_fio_req.return_buffer[resp_cid],\
				 (uint8_t *)resp, 8/* 8 bytes */ );

                	log_info("Received Property Get Response\n");

                	break;

        	default:

                	log_err("Response for unknown fabric command %d\n", cmd->cmn.fctype);
        	}

		free(fun_fio_req.original_request[resp_cid]);
		bitmap_bput(&fun_fio_req.cid_bm, resp_cid);
	}

}

void
nvmeof_test_admin_recv( struct rdsock *sock,
	struct rdsock_msg *msg)
{

	if (msg->buf == NULL) {
		log_err("Response data not present for admin command \n");
	} else {

		struct fabrics_resp *resp =
			(struct fabrics_resp *)msg->buf;
		uint16_t resp_cid = le16toh(resp->cid);

		assert(resp);
		assert(resp_cid < FUN_MAX_Q_DEPTH);

		struct fun_nvme_status *status = &resp->status;
                struct fabrics_cmd *cmd = (struct fabrics_cmd *)
                        fun_fio_req.original_request[resp_cid];
		struct fun_nvme_ns_mgmt * ns_cmd =  (struct fun_nvme_ns_mgmt * )cmd;
                uint16_t cmd_cid = le16toh(cmd->cmn.cid);

                assert(cmd);
                assert(resp_cid == cmd_cid);
                assert(status->sc == 0);
                assert(cmd->cmn.opcode != FUN_NVME_FABRICS);

		switch (cmd->cmn.opcode) {

        	case FUN_NVME_IDTFY:

			memcpy((uint8_t *)fun_fio_req.return_buffer[resp_cid],\
				 (uint8_t *)resp + NVME_CPL_SIZE, msg->buf_size - NVME_CPL_SIZE );
                	log_info("Identify Response received\n");
                	break;

        	case FUN_NVME_NS_ATTACH:

                	log_info("NS Attach Response received\n");
                	break;

        	case FUN_NVME_NS_MGMT:
			if (ns_cmd->sel == FUN_NVME_NS_MGMT_SEL_CREATE) {
				memcpy((uint8_t *)fun_fio_req.return_buffer[resp_cid],\
				 	(uint8_t *)resp, 4/*dword 0 = NSID*/);
                		log_info("NS Create Response received\n");
			} else log_info("NS Delete received\n");

                	break;

        	default:
                	log_err("Response for unknown admin command %d received\n", cmd->cmn.opcode);

                break;
        	}
		free(fun_fio_req.original_request[resp_cid]);
		bitmap_bput(&fun_fio_req.cid_bm, resp_cid);
	}
}


void
nvmeof_test_nvm_recv(struct rdsock *sock,
		struct rdsock_msg *msg)
{

	if (msg->buf == NULL) {
		log_err("Missing data buffer \n");
	} else {
		struct fabrics_resp *resp =
			(struct fabrics_resp *)msg->buf;
		uint16_t resp_cid = le16toh(resp->cid);

		assert(resp);
		assert(resp_cid < FUN_MAX_Q_DEPTH);

		struct fun_nvme_status *status = &resp->status;

		assert(status->sc == 0);

		handle_nvme_io_resp(resp, msg->buf_size);

	}
}

static void
nvmeof_test_recv(struct rdsock *sock,
	struct rdsock_msg *msg)
{
	struct fabrics_rds_msg_hdr *hdr =
		(struct fabrics_rds_msg_hdr *)msg->msg;

	switch (hdr->conn_type) {

	case FABRICS_RDS_CONN:
		nvmeof_test_fabric_recv(sock, msg);
		sem_post(&sem_fun1); 
		break;

	case FABRICS_RDS_ADM_CONN:
		nvmeof_test_admin_recv( sock, msg);
		sem_post(&sem_fun1); 
		break;

	case FABRICS_RDS_NVM_CONN:
		nvmeof_test_nvm_recv( sock, msg);
		break;

	default:
		assert(0);
		break;
	}
}


int fun_client_start(uint32_t local_addr, uint32_t remote_addr)
{
	struct rdsock_params sock;
	
	//initialize structure to receive and return io_u
	memset(&fun_fio_req, 0, sizeof(struct fun_fio_req_struct));

	//initializa bitmap for managing qid and IO depth 
	bitmap_init(&fun_fio_req.cid_bm, FUN_MAX_Q_DEPTH);

	//start rdsock thread
        rdsock_init(local_addr, htons(1099));

	//create fabric rdsocket
	sock.remoteip = remote_addr;
	sock.role = RDSOCK_CLIENT;
	sock.recv = nvmeof_test_recv;
	sock.maxrecv = 3;
	sock.recv_context = (void *)&sock;

	rdsock_client = rdsock_open(&sock);
	if (rdsock_client == NULL) {
		log_err("failed to open client\n");
		return 1;
	}

	return 0;

}

void fun_client_stop()
{
	rdsock_close(rdsock_client);

}

int fun_nvmf_ns_create(__u64 nsze, __u64 ncap, __u8 flbas,
                   __u8 dps, __u8 nmic, __u32 *result)
{
        uint32_t len, buf_size, *mb, cid, qid;
        struct fun_nvme_ns_mgmt *cmd;
        struct fun_nvme_ns_data *ns_data;

	qid = 0;
	
	len = FUN_NVME_PAGE_SIZE;
        buf_size = len + NVME_CMD_SIZE;
        mb = malloc(buf_size);
	if (!mb) return 1;

        cmd = (struct fun_nvme_ns_mgmt *)mb;
        cid = get_cid();

	fun_fio_req.original_request[cid] = cmd;
	fun_fio_req.return_buffer[cid] = result;

        log_info("Sending NS create command...");

        ns_data = (void *)((uint8_t *)cmd + NVME_CMD_SIZE);

        memset(ns_data, 0, sizeof(struct fun_nvme_ns_data));
        ns_data->nsze = htole64(nsze);
        ns_data->ncap = htole64(ncap);
	ns_data->flbas = flbas;
	ns_data->dps = dps;
	ns_data->nmic = nmic;

	memset(cmd, 0, NVME_CMD_SIZE);

	fun_nvme_ns_mgmt_create_cmd(cmd, (uint64_t)ns_data, cid);

        nvmeof_send_msg(mb, FABRICS_RDS_ADM_CONN, qid, buf_size);
	return 0;
}

int fun_nvmf_ns_delete(__u32 nsid)
{
        uint32_t len, buf_size, *mb, cid, qid;
        struct fun_nvme_ns_mgmt *cmd;

	qid = 0;
	
	len = FUN_NVME_PAGE_SIZE;
        buf_size = len + NVME_CMD_SIZE;
        mb = malloc(buf_size);
	if (!mb) return 1;

        cmd = (struct fun_nvme_ns_mgmt *)mb;
        cid = get_cid();

	fun_fio_req.original_request[cid] = cmd;

        log_info("Sending NS delete command...");

	memset(cmd, 0, sizeof(struct fun_nvme_cmd));

        cmd->cmn.opcode = FUN_NVME_NS_MGMT;
        cmd->cmn.cid = cid;
        cmd->cmn.nsid = nsid;
        cmd->sel = FUN_NVME_NS_MGMT_SEL_DELETE;

        nvmeof_send_msg(mb, FABRICS_RDS_ADM_CONN, qid, buf_size);
	return 0;
}

int fun_nvmf_ns_attach_or_detach(uint32_t nsid, bool attach)
{
        uint32_t len, buf_size, *mb, cid, qid;

	qid = 0;
	
	len = FUN_NVME_PAGE_SIZE;
        buf_size = len + NVME_CMD_SIZE;
        mb = malloc(buf_size);
	if (!mb) return 1;

        struct fun_nvme_ns_attach *cmd = (struct fun_nvme_ns_attach *)mb;
        cid = get_cid();
	fun_fio_req.original_request[cid] = cmd;

	if (attach){
		fun_nvme_ns_attach_cmd(cmd, 0, nsid, cid);
        	log_info( "Sending NS %d attach command...", nsid);
	} else {
		fun_nvme_ns_detach_cmd(cmd, 0, nsid, cid);
        	log_info( "Sending NS %d detach command...", nsid);
	}

        nvmeof_send_msg(mb, FABRICS_RDS_ADM_CONN, qid, buf_size);
	return 0;
}


int fun_admin_io_connect(uint16_t qid, uint8_t sqsize, uint32_t kato, uint16_t cntlid, char *nqn)
{
        uint32_t len, buf_size, *mb, cid;

        struct fabrics_connect_cmd *cmd = NULL;
        struct fabrics_connect_data *data = NULL;


        len = FUN_NVME_PAGE_SIZE;
        buf_size = len + NVME_CMD_SIZE;
        mb = malloc(buf_size);
	if (!mb) return 1;

        cmd = (struct fabrics_connect_cmd *)mb;
        cid = get_cid();
	fun_fio_req.original_request[cid] = cmd;

        fabrics_common((struct fabrics_cmd *)cmd,
                FABRICS_CONNECT, cid); 

        cmd->recfmt = 0;
        cmd->qid = htole16(qid); // qid = 0 admin, > 0 is IO
        cmd->sqsize = htole16(sqsize-1 ); // 0 based value 64 = 63
        cmd->cattr = 0;
        cmd->kato = htole32(kato);

        data = (struct fabrics_connect_data *)
                ((uint8_t *)cmd + NVME_CMD_SIZE);

        memset(data, 0, sizeof(struct fabrics_connect_data));

        strcpy((char *)data->hostid, hostid_g);
        data->cntlid = cntlid;
        strcpy((char *)data->subnqn, nqn);
        strcpy((char *)data->hostnqn, hostnqn_g);

	if (qid) log_info( "Initiating  I/O connection %d...", qid);
	else log_info( "Initiating  ADMIN connection...") ;
        nvmeof_send_msg(mb, FABRICS_RDS_CONN, qid, buf_size);
	return 0;
}


int fun_read_write(struct io_u *io_u, \
		uint32_t nsid, void * buf, uint64_t offset, uint64_t xfer_buflen, uint16_t qid)
{
        uint32_t *mb;
	uint16_t cid;
        struct fun_nvme_rw *cmd;
        uint64_t len, buf_size;
	int rc = 1;

        cid = get_cid();
	fun_fio_req.io_u[cid] = io_u;

	len = xfer_buflen;

        buf_size = len + NVME_CMD_SIZE;
        mb = malloc(buf_size);
	if (!mb) goto read_write_failed;
	
	cmd = (struct fun_nvme_rw *)mb;

	memset(cmd, 0, NVME_CMD_SIZE);	
	
	cmd->cmn.opcode = (io_u->ddir == DDIR_READ) ? FUN_NVME_READ : FUN_NVME_WRITE;
        cmd->cmn.cid = htole16(cid);
        cmd->cmn.nsid = htole32(nsid);

	if(io_u->ddir == DDIR_READ) cmd->cmn.opcode = FUN_NVME_READ;
	else {
		cmd->cmn.opcode = FUN_NVME_WRITE;
        	memcpy((uint8_t *)cmd + NVME_CMD_SIZE, (uint8_t *) buf, len);
	}
 	cmd->slba = htole64(offset >> EPNVME_LBA_SHIFT);
        cmd->nlb = htole16(EPNVME_SIZE_TO_NLB(len));
        cmd->cmn.psdt = FUN_NVME_PSDT_SGL_MPTR_CONTIG;

        rc = nvmeof_send_msg(mb, FABRICS_RDS_NVM_CONN, qid, buf_size);

read_write_failed:
	return rc;
}

int fun_nvme_io(__u32 nsid, __u8 opcode, __u64 slba, __u16 nblocks, __u16 control,
            __u32 dsmgmt, __u32 reftag, __u16 apptag, __u16 appmask, void *data,
            void *metadata, __u16 qid)
{
        uint32_t *mb;
	uint16_t cid;
        struct fun_nvme_rw *cmd;
        uint64_t len, buf_size;
	int rc = 1;

        cid = get_cid();
	fun_fio_req.io_u[cid] = NULL; // not from fio 
	fun_fio_req.return_buffer[cid] = data; // from nvme tool

	len = (nblocks + 1 ) *  4096; //FIX - blocksize not fixed?

        buf_size = len + NVME_CMD_SIZE;
        mb = malloc(buf_size);
	if (!mb) goto io_failed;
	
	cmd = (struct fun_nvme_rw *)mb;
	fun_fio_req.original_request[cid] = cmd;

	memset(cmd, 0, NVME_CMD_SIZE);	
	
	cmd->cmn.opcode = opcode;
        cmd->cmn.cid = htole16(cid);
        cmd->cmn.nsid = htole32(nsid);

	if (opcode == FUN_NVME_WRITE){
        	memcpy((uint8_t *)cmd + NVME_CMD_SIZE, (uint8_t *) data, len);
	}
 	cmd->slba = slba;
        cmd->nlb = nblocks;
        cmd->cmn.psdt = FUN_NVME_PSDT_SGL_MPTR_CONTIG;

        rc = nvmeof_send_msg(mb, FABRICS_RDS_NVM_CONN, qid, buf_size);

io_failed:
	return rc;

}
int fun_property_get(void *buf, uint32_t offset, uint8_t size)
{
        uint32_t len, buf_size, *mb;
	uint16_t qid, cid;

	len = FUN_NVME_PAGE_SIZE;
        buf_size = len + NVME_CMD_SIZE;
        mb = malloc(buf_size);
	
	if (!mb) return 1;

	qid = 0;

        struct fabrics_prop_get_cmd *cmd =
        (struct fabrics_prop_get_cmd *)mb;

        cid = get_cid();
	fun_fio_req.original_request[cid] = cmd;
	fun_fio_req.return_buffer[cid] = buf;

        log_info( "Sending Fabric Property Get Command ...");

        fabrics_common((struct fabrics_cmd *)cmd,
                FABRICS_PROPERTY_GET, cid);

        cmd->attrib.size = size;
        cmd->offset = htole32(offset);

        nvmeof_send_msg(mb, FABRICS_RDS_CONN, qid, buf_size);

	return 0;
}

int fun_prop_set(uint32_t offset, uint8_t size, uint64_t value)
{
        uint32_t len, buf_size, *mb;
	uint16_t qid, cid;

	len = FUN_NVME_PAGE_SIZE;
        buf_size = len + NVME_CMD_SIZE;
        mb = malloc(buf_size);
	
	if (!mb) return 1;

	qid = 0;

        struct fabrics_prop_set_cmd *cmd =
        (struct fabrics_prop_set_cmd *)mb;

        cid = get_cid();
	fun_fio_req.original_request[cid] = cmd;

        log_info( "Sending Fabric Property Set Command ...");

        fabrics_common((struct fabrics_cmd *)cmd,
                FABRICS_PROPERTY_SET, cid);

        cmd->attrib.size = size;
        cmd->offset = htole32(offset);
        cmd->val.low = htole32(value);

        nvmeof_send_msg(mb, FABRICS_RDS_CONN, qid, buf_size);

	return 0;
}

#define NVME_SQES_LOG2 6
#define NVME_CC_IOSQES_S 16
#define NVME_CQES_LOG2 4
#define NVME_CC_IOCQES_S 20
#define NVME_CC_ENABLE 1
#define NVME_CC_ENABLE_VAL (((NVME_SQES_LOG2) << (NVME_CC_IOSQES_S)) | \
							((NVME_CQES_LOG2) << (NVME_CC_IOCQES_S)) | \
							(NVME_CC_ENABLE))

int fun_enable_controller()
{
	// return fun_prop_set(FUN_REG_CC, FABRICS_PROPERTY_ATTRIB_SIZE_4, 1);
	return fun_prop_set(FUN_REG_CC, FABRICS_PROPERTY_ATTRIB_SIZE_4, NVME_CC_ENABLE_VAL);
}

int fun_identify(uint32_t nsid, void *buf, bool present)
{
        uint32_t len, buf_size, *mb;
	uint16_t qid, cid;

	len = FUN_NVME_PAGE_SIZE;
        buf_size = len + NVME_CMD_SIZE;
        mb = malloc(buf_size);
	
	if (!mb) return 1;

	qid = 0;

	struct fun_nvme_idtfy *cmd =
                (struct fun_nvme_idtfy *)mb;

        cid = get_cid();

	fun_fio_req.original_request[cid] = cmd;
	fun_fio_req.return_buffer[cid] = buf;


	memset(cmd, 0, NVME_CMD_SIZE);
        cmd->cmn.opcode = FUN_NVME_IDTFY;
        cmd->cmn.cid = htole16(cid);
        cmd->cmn.nsid = htole32(nsid);

	if(nsid)//get NS data
		cmd->cns = present ? FUN_NVME_IDTFY_NS_ALLOC_DATA : FUN_NVME_IDTFY_NS_ACTIVE_DATA;
	else	//get controller data
		cmd->cns = FUN_NVME_IDTFY_CTRLR_DATA;

        log_info( "Sending Identify Command ...");

        nvmeof_send_msg(mb, FABRICS_RDS_ADM_CONN, qid, buf_size);

	return 0;
}
