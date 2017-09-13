/*
 * Copyright © 2017 Fungible. All rights reserved.
 */

/*
 * @file rds.h
 * @date 05-11-2017
 * @author Pratapa Vaka
 * @brief NVMeoF Target Implementation
 */

#include "host_rds.h"

#define fabricst_rds_transport_info fabrics_disc_log_page_entry

struct fabricst_rds_transport {

	/** transport name */
	const char *trname;

	/* max depth of submission queue */
	uint16_t max_qdepth;

	/** max io size */
	uint32_t max_io_size;

	/** Info needed for transport connection */
	struct fabricst_rds_transport_info tr_info;
};

struct fabricst_rds_params {

	struct rdsock *sock;
	struct rdsock_msg *in;
	struct rdsock_msg *out;
	int64_t rc;
};

#if 0
/*
 * Allows a transport to register
 * @return non-zero if the transport is already registered
 */
int nvmeoft_register_transport(struct fabrics_transport *tr);

/*
 * Allows a transport to un-register
 */
void nvmeoft_unregister_transport(struct fabrics_transport *tr);
#endif

struct frame *fabricst_rds_open_push(struct frame *frame,
	void *flow, uint32_t remote_addr);

struct frame *fabricst_rds_close_push(struct frame *frame,
	void *flow, int64_t *ret);

void fabricst_rds_init(uint32_t addr);

void fabricst_rds_fini(void);

