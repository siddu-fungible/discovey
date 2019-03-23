/*
 * Copyright © 2017 Fungible. All rights reserved.
 */

/*
 * @file rds.h
 * @date 05-11-2017
 * @author Pratapa Vaka
 * @brief NVMeoF RDS Transport Binding Common Header
 */

/**
 * Specifies the command type
 */
enum fabrics_rds_conn_type {

	FABRICS_RDS_CONN = 0,
	FABRICS_RDS_ADM_CONN = 1,
	FABRICS_RDS_NVM_CONN = 2,
};

#define RDS_MSG_STR_LEN 8
struct __attribute__ ((packed)) fabrics_rds_msg_hdr{

        uint16_t version;
        uint16_t qid;
        char msg_str[RDS_MSG_STR_LEN];
        enum fabrics_rds_conn_type conn_type;
};
