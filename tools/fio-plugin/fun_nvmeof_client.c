/**
 * Created by Pratapa Vaka on 05-18-2017
 * Copyright © 2017 Fungible. All rights reserved.
 */

/**
 * @file apps/nvmeof_test.c
 * NVMe-oF target driver unit test app
 */

#include "fio.h"
#include "Integration/tools/fio-plugin/types.h"
#include <stdint.h>
#include <time.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "Integration/tools/fio-plugin/queue.h"
#include "Integration/tools/fio-plugin/rdsock.h"
#include "Integration/tools/fio-plugin/nvme.h"
#include "Integration/tools/fio-plugin/fabrics.h"
#include "Integration/tools/fio-plugin/fun_api.h"
#include "Integration/tools/fio-plugin/fun_rds.h"
#include "Integration/tools/fio-plugin/bitmap.h"
#include "Integration/tools/fio-plugin/epnvme.h"
#include <stdlib.h>
#include <endian.h>
#include <netinet/in.h>
#include <unistd.h>
#include <semaphore.h>
#include "Integration/tools/fio-plugin/fun_fio.h"

extern sem_t sem_fun1;
extern pthread_mutex_t fun_mutex;
pthread_mutex_t bitmap_mutex;

#define NVMEOF_RDS_HDR_SIZE sizeof(struct fabrics_rds_msg_hdr)

struct fun_fio_req_struct {
	struct io_u *io_u[FUN_MAX_Q_DEPTH];
	struct rdsock_msg *sent_msg[FUN_MAX_Q_DEPTH];
	BITMAP(cid_bm, FUN_MAX_Q_DEPTH);
};

static struct fun_fio_req_struct fun_fio_req[NVMEOF_MAX_QUEUES];
extern struct fio_thread_struct fio_thread;
struct rdsock *rdsock_client;

static uint16_t get_cid(uint16_t qid)
{
	uint16_t cid;
	pthread_mutex_lock(&bitmap_mutex);
	cid =  bitmap_bget(&fun_fio_req[qid].cid_bm);
	assert(cid >= 0);
	pthread_mutex_unlock(&bitmap_mutex);

	return cid;
}

static int 
nvmeof_send_msg(struct rdsock_msg *msg, uint32_t *mb,
		enum fabrics_rds_conn_type conn_type,
		uint16_t qid, uint16_t buf_size)
{
	msg->buf = mb;
	msg->buf_size = buf_size;
	msg->context = (void *)mb;

	struct fabrics_rds_msg_hdr *hdr = (void *)msg->msg;
	hdr->conn_type = conn_type;
	hdr->qid = qid;

	rdsock_sendmsg(rdsock_client, msg);

	return 0;
}

static char const *hostid_g = "host1";
//static char const *subnqn_g = "nqn.2017-05.com.fungible:nss-uuid1";
static char const *hostnqn_g = "nqn.2017-05.com.fungible:host1";


static void
fabrics_common(struct fabrics_cmd *fcmd, uint32_t fctype, uint32_t cid)
{
	struct fun_nvme_cmd *cmd = (void *)fcmd;

	memset(cmd, 0, NVME_CMD_SIZE);
	cmd->cmn.opcode = FUN_NVME_FABRICS;
	cmd->cmn.cid = htole16(cid);
	cmd->cmn.nsid = htole32(0);
	fcmd->cmn.fctype = fctype;
}

static void
nvmeof_test_free_msg(struct rdsock_msg *msg)
{
	if (msg->buf) {
		free(msg->buf);
	}
	free(msg);
}

static bool
handle_nvme_io_resp(struct fabrics_rds_msg_hdr *hdr, struct fabrics_resp *resp,
		    uint32_t *buf, uint16_t buf_size)
{
	uint16_t qid = hdr->qid;
	uint16_t resp_cid = le16toh(resp->cid);
	struct io_u *io_u = (struct io_u *)fun_fio_req[qid].io_u[resp_cid];
	struct rdsock_msg *sent_msg = fun_fio_req[qid].sent_msg[resp_cid];

	switch (io_u->ddir) {

	case DDIR_READ:
		if (buf_size != io_u->xfer_buflen) {
			log_err("Data received has wrong length: Offset = %llu, \
				Expected: %lu  Actual: %u\n", io_u->offset, \
				io_u->xfer_buflen, buf_size);
		}
			
		memcpy((uint8_t *)io_u->buf, (uint8_t *)buf, buf_size);
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

	nvmeof_test_free_msg(sent_msg);

	pthread_mutex_lock(&bitmap_mutex);
	bitmap_bput(&fun_fio_req[qid].cid_bm, resp_cid);
	pthread_mutex_unlock(&bitmap_mutex);
	return true;
}

static void
nvmeof_test_fabric_recv(struct rdsock *sock, struct fabrics_rds_msg_hdr *hdr,
		        struct fabrics_resp *resp, struct rdsock_msg *msg)
{
	uint16_t qid = hdr->qid;
	uint16_t resp_cid = le16toh(resp->cid);
	assert(resp);
	assert(resp_cid < FUN_MAX_Q_DEPTH);
	struct fun_nvme_status *status = &resp->status;
	struct rdsock_msg *sent_msg = fun_fio_req[qid].sent_msg[resp_cid];
	struct fabrics_cmd *cmd = (void *)sent_msg->msg + NVMEOF_RDS_HDR_SIZE;
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
	       	log_info("Received Property Get Response\n");
	       	break;

       	default:
		log_err("Response for unknown fabric command %d\n",
			cmd->cmn.fctype);
       	}

	nvmeof_test_free_msg(sent_msg);
	bitmap_bput(&fun_fio_req[qid].cid_bm, resp_cid);
}

static void
nvmeof_test_admin_recv(struct rdsock *sock, struct fabrics_rds_msg_hdr *hdr,
		       struct fabrics_resp *resp, struct rdsock_msg *msg)
{
	uint16_t qid = hdr->qid;
	uint16_t resp_cid = le16toh(resp->cid);
	assert(resp);
	assert(resp_cid < FUN_MAX_Q_DEPTH);
	struct fun_nvme_status *status = &resp->status;
	struct rdsock_msg *sent_msg = fun_fio_req[qid].sent_msg[resp_cid];
	struct fabrics_cmd *cmd = (void *)sent_msg->msg + NVMEOF_RDS_HDR_SIZE;
	uint16_t cmd_cid = le16toh(cmd->cmn.cid);
	assert(cmd);
	assert(resp_cid == cmd_cid);
	assert(status->sc == 0);
	assert(cmd->cmn.opcode != FUN_NVME_FABRICS);

	switch (cmd->cmn.opcode) {
	case FUN_NVME_IDTFY:
		log_info("Identify Response received\n");
		break;

	case FUN_NVME_NS_ATTACH:
		log_info("NS Attach Response received\n");
		break;

	case FUN_NVME_NS_MGMT:
		log_info("NS Mgmt Response received\n");
		break;

	default:
		log_err("Response for unknown admin command %d received\n", cmd->cmn.opcode);

		break;
	}

	nvmeof_test_free_msg(sent_msg);
	bitmap_bput(&fun_fio_req[qid].cid_bm, resp_cid);
}

void
nvmeof_test_nvm_recv(struct rdsock *sock, struct fabrics_rds_msg_hdr *hdr,
		     struct fabrics_resp *resp, struct rdsock_msg *msg)
{
	uint16_t resp_cid = le16toh(resp->cid);
	assert(resp);
	assert(resp_cid < FUN_MAX_Q_DEPTH);
	struct fun_nvme_status *status = &resp->status;
	assert(status->sc == 0);

	handle_nvme_io_resp(hdr, resp, msg->buf, msg->buf_size);
}

static void
nvmeof_test_recv(struct rdsock *sock, struct rdsock_msg *msg)
{
	struct fabrics_resp *resp = (void *)msg->msg + NVMEOF_RDS_HDR_SIZE;
	struct fabrics_rds_msg_hdr *hdr =
		(struct fabrics_rds_msg_hdr *)msg->msg;

	switch (hdr->conn_type) {

	case FABRICS_RDS_CONN:
		assert(hdr->qid == 0);
		nvmeof_test_fabric_recv(sock, hdr, resp, msg);
		sem_post(&sem_fun1); 
		break;

	case FABRICS_RDS_ADM_CONN:
		assert(hdr->qid == 0);
		nvmeof_test_admin_recv(sock, hdr, resp, msg);
		sem_post(&sem_fun1); 
		break;

	case FABRICS_RDS_NVM_CONN:
		assert(hdr->qid != 0);
		nvmeof_test_nvm_recv(sock, hdr, resp, msg);
		break;

	default:
		assert(0);
		break;
	}
}

int fun_client_start(uint32_t local_addr, uint32_t remote_addr)
{
	struct rdsock_params sock;

	//initialize bitmap for managing qid and IO depth
	for (int qid = 0; qid < NVMEOF_MAX_QUEUES; qid++) {
		//memset(&fun_fio_req[qid], 0, sizeof(struct fun_fio_req_struct));
		bitmap_init(&fun_fio_req[qid].cid_bm, FUN_MAX_Q_DEPTH);
	}

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

struct rdsock_msg* fun_nvmf_alloc_msg()
{
	size_t hdr_size = sizeof(struct fabrics_rds_msg_hdr);
	size_t msglen = hdr_size + FABRICS_CMD_SIZE;

	struct rdsock_msg *msg = malloc(sizeof(struct rdsock_msg) + msglen);
	if (!msg) {
		return NULL;
	}
	msg->msglen = msglen;
	msg->msg = (char *)(msg + 1);

	return msg;
}

int fun_nvmf_ns_create()
{
	uint32_t buf_size, *mb, cid, qid = 0;
	struct fun_nvme_ns_mgmt *cmd;
	struct fun_nvme_ns_data *ns_data;

	log_info("Sending NS create command\n");

	buf_size = FUN_NVME_PAGE_SIZE;
	mb = calloc(1, buf_size);
	if (!mb) return 1;

	struct rdsock_msg *msg = fun_nvmf_alloc_msg();
	if (!msg) {
		free(mb);
		return -1;
	}
	cmd = (void *)msg->msg + NVMEOF_RDS_HDR_SIZE;

	cid = get_cid(qid);
	fun_fio_req[qid].sent_msg[cid] = msg;

	memset(cmd, 0, NVME_CMD_SIZE);
	cmd->cmn.opcode = FUN_NVME_NS_MGMT;
	cmd->cmn.cid = htole16(0);
	cmd->cmn.nsid = htole32(0);

	ns_data = (void *)mb;
	ns_data->nsze = EPNVME_NSZE;
	ns_data->ncap = EPNVME_NCAP;

	fun_nvme_ns_mgmt_create_cmd(cmd, (uint64_t)ns_data, cid);

	nvmeof_send_msg(msg, mb, FABRICS_RDS_ADM_CONN, qid, buf_size);
	return 0;
}

int fun_nvmf_ns_attach(uint32_t nsid)
{
	uint32_t buf_size, *mb, cid, qid = 0;
	struct fun_nvme_ns_attach *cmd;

	buf_size = FUN_NVME_PAGE_SIZE;
	mb = calloc(1, buf_size);
	if (!mb) return 1;

	struct rdsock_msg *msg = fun_nvmf_alloc_msg();

	if (!msg) {
		free(mb);
		return -1;
	}

	cmd = (void *)msg->msg + NVMEOF_RDS_HDR_SIZE;
	cid = get_cid(qid);
	fun_fio_req[qid].sent_msg[cid] = msg;

	memset(cmd, 0, NVME_CMD_SIZE);
	cmd->cmn.opcode = FUN_NVME_NS_ATTACH;
	cmd->cmn.cid = htole16(cid);
	cmd->cmn.nsid = htole32(nsid);

	fun_nvme_ns_attach_cmd(cmd, 0, nsid, cid);

	log_info( "Sending NS %d attach command\n", nsid);
	nvmeof_send_msg(msg, mb, FABRICS_RDS_ADM_CONN, qid, buf_size);
	return 0;
}

int
fun_admin_io_connect(uint16_t qid, uint8_t sqsize, uint32_t kato,
		     uint16_t cntlid, char *nqn)
{
	uint16_t adm_qid = 0;
	uint32_t buf_size, *mb, cid;
	struct fabrics_connect_cmd *cmd = NULL;
	struct fabrics_connect_data *data = NULL;

	buf_size = FUN_NVME_PAGE_SIZE;
	mb = calloc(1, buf_size);
	if (!mb) return 1;

	struct rdsock_msg *msg = fun_nvmf_alloc_msg();
	if (!msg) {
		free(mb);
		return -1;
	}
	cmd = (void *)msg->msg + NVMEOF_RDS_HDR_SIZE;

	cid = get_cid(adm_qid);
	fun_fio_req[adm_qid].sent_msg[cid] = msg;

	fabrics_common((struct fabrics_cmd *)cmd, FABRICS_CONNECT, cid); 

	cmd->recfmt = 0;
	cmd->qid = htole16(qid); // qid = 0 admin, > 0 is IO
	cmd->sqsize = htole16(sqsize-1 ); // 0 based value 64 = 63
	cmd->cattr = 0;
	cmd->kato = htole32(kato);

	data = (struct fabrics_connect_data *)mb;
	strcpy((char *)data->hostid, hostid_g);
	data->cntlid = cntlid;
	strcpy((char *)data->subnqn, nqn);
	strcpy((char *)data->hostnqn, hostnqn_g);

	if (qid) {
		log_info("Initiating  I/O connection for queue %u mb %p\n",
			 qid, mb);
	} else {
		log_info( "Initiating  ADMIN connection\n") ;
	}
	nvmeof_send_msg(msg, mb, FABRICS_RDS_CONN, adm_qid, buf_size);
	return 0;
}

int
fun_read_write(struct io_u *io_u, uint32_t nsid, void *buf, uint64_t offset,
	       uint64_t xfer_buflen, uint16_t qid)
{
	uint32_t *mb;
	uint16_t cid;
	struct fun_nvme_rw *cmd;
	uint64_t buf_size;
	int rc = 1;

	buf_size = xfer_buflen;
	mb = malloc(buf_size);
	if (!mb) goto read_write_failed;
	
	struct rdsock_msg *msg = fun_nvmf_alloc_msg();
	if (!msg) {
		free(mb);
		return -1;
	}
	cmd = (void *)msg->msg + NVMEOF_RDS_HDR_SIZE;

	cid = get_cid(qid);

	memset(cmd, 0, NVME_CMD_SIZE);	
	cmd->cmn.opcode = (io_u->ddir == DDIR_READ) ? FUN_NVME_READ : FUN_NVME_WRITE;
	cmd->cmn.cid = htole16(cid);
	cmd->cmn.nsid = htole32(nsid);

	if(io_u->ddir == DDIR_READ) {
		cmd->cmn.opcode = FUN_NVME_READ;
	} else {
		cmd->cmn.opcode = FUN_NVME_WRITE;
		memcpy((uint8_t *)mb, (uint8_t *)buf, buf_size);
	}
 	cmd->slba = htole64(offset >> EPNVME_LBA_SHIFT);
	cmd->nlb = htole16(EPNVME_SIZE_TO_NLB(buf_size));
	cmd->cmn.psdt = FUN_NVME_PSDT_SGL_MPTR_CONTIG;

	fun_fio_req[qid].sent_msg[cid] = msg;
	fun_fio_req[qid].io_u[cid] = io_u;
	rc = nvmeof_send_msg(msg, mb, FABRICS_RDS_NVM_CONN, qid, buf_size);

read_write_failed:
	return rc;
}

int fun_prop_set(uint32_t offset, uint8_t size, uint64_t value)
{
	uint16_t qid = 0, cid;
	struct rdsock_msg *msg = fun_nvmf_alloc_msg();

	if (!msg) {
		return -1;
	}
	struct fabrics_prop_set_cmd *cmd = (void *)msg->msg + NVMEOF_RDS_HDR_SIZE;

	cid = get_cid(qid);
	fun_fio_req[qid].sent_msg[cid] = msg;
	fabrics_common((struct fabrics_cmd *)cmd, FABRICS_PROPERTY_SET, cid);
	cmd->attrib.size = size;
	cmd->offset = htole32(offset);
	cmd->val.low = htole32(value);

	log_info( "Sending Fabric Property Set Command\n");
	nvmeof_send_msg(msg, NULL, FABRICS_RDS_CONN, qid, 0);

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
	//return fun_prop_set(FUN_REG_CC, FABRICS_PROPERTY_ATTRIB_SIZE_4, 1);
	return fun_prop_set(FUN_REG_CC, FABRICS_PROPERTY_ATTRIB_SIZE_4, NVME_CC_ENABLE_VAL);
}

