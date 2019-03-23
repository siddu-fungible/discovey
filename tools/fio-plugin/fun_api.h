/*
 *	Fungible Host Interface API
 *
 *	Created August 2016 by felix.marti@fungible.com
 *	Copyright © 2016 Fungible. All rights reserved.
 */

#ifndef __FUN_API_H__
#define __FUN_API_H__

#include <stdint.h>

typedef uint8_t __u8;
typedef uint16_t __u16;
typedef uint32_t __u32;
//typedef uint64_t __u64; /*  conflicts with fio */
__extension__
typedef unsigned long long int __u64;

enum fun_ret {
	FUN_RET_OK = 0x00,
	FUN_RET_EINVAL = 0x01,
	FUN_RET_ENOMEM = 0x0c,
};

enum fun_cmdsets {
	FUN_CMDSET_FUN_ADM = 0x01,
	FUN_CMDSET_ETH = 0x02,
	FUN_CMDSET_TOE,
	FUN_CMDSET_RDMA,	// can i bind the rdma command set to iwarp or roce flow?
	FUN_CMDSET_NVME_ADM,
	FUN_CMDSET_NVME_NVM,
	FUN_CMDSET_CRYPTO
};

/******************************************************************************
 *   R E G I S T E R s
 ************************/

enum fun_regs {
	FUN_REG_CAP = 0x0000,	/* controller capabilities */
	FUN_REG_VS = 0x0008,	/* version */
	FUN_REG_INTMS = 0x000c,	/* interrupt mask set */
	FUN_REG_INTMC = 0x0010,	/* interrupt mask clear */
	FUN_REG_CC = 0x0014,	/* controller configuration */
	FUN_REG_RSVD = 0x0018,	/* reserved */
	FUN_REG_CSTS = 0x001c,	/* controller status */
	FUN_REG_NSSR = 0x0020,	/* nvm susbsystem reset */
	FUN_REG_AQA = 0x0024,	/* admin queue attributes */
	FUN_REG_ASQ = 0x0028,	/* admin submission queue base addr
				 */
	FUN_REG_ACQ = 0x0030,	/* admin completion queue base addr
				 */
	FUN_REG_CMBLOC = 0x0038,	/* controller memory buffer location
					 */
	FUN_REG_CMBSZ = 0x003c,	/* controller memory buffer size */
};

#define FUN_REG_CAP_MPSMAX_S	52
#define FUN_REG_CAP_MPSMAX_M	0xf
#define FUN_REG_CAP_MPSMAX_P(cap) ((__u64)(cap) << FUN_REG_CAP_MPSMAX_S)
#define FUN_REG_CAP_MPSMAX_G(cap) \
    (((cap) >> FUN_REG_CAP_MPSMAX_S) & FUN_REG_CAP_MPSMAX_M)

#define FUN_REG_CAP_MPSMIN_S	48
#define FUN_REG_CAP_MPSMIN_M	0xf
#define FUN_REG_CAP_MPSMIN_P(cap) ((__u64)(cap) << FUN_REG_CAP_MPSMIN_S)
#define FUN_REG_CAP_MPSMIN_G(cap) \
    (((cap) >> FUN_REG_CAP_MPSMIN_S) & FUN_REG_CAP_MPSMIN_M)

enum fun_reg_cap_css {
	FUN_REG_CAP_CSS_FUN = 1 << 7,
	FUN_REG_CAP_CSS_NVM = 1 << 0,
};

#define FUN_REG_CAP_CSS_S	37
#define FUN_REG_CAP_CSS_M	0xff
#define FUN_REG_CAP_CSS_P(cap)	((__u64)(cap) << FUN_REG_CAP_CSS_S)
#define FUN_REG_CAP_CSS_G(cap) \
    (((cap) >> FUN_REG_CAP_CSS_S) & FUN_REG_CAP_CSS_M)

#define FUN_REG_CAP_NSSRS_S	36
#define FUN_REG_CAP_NSSRS_M	0x1
#define FUN_REG_CAP_NSSRS_P(cap) ((__u64)(cap) << FUN_REG_CAP_NSSRS_S)
#define FUN_REG_CAP_NSSRS_G(cap) \
    (((cap) >> FUN_REG_CAP_NSSRS_S) & FUN_REG_CAP_NSSRS_M)

#define FUN_REG_CAP_DSTRD_S	32
#define FUN_REG_CAP_DSTRD_M	0xf
#define FUN_REG_CAP_DSTRD_P(cap) ((__u64)(cap) << FUN_REG_CAP_DSTRD_S)
#define FUN_REG_CAP_DSTRD_G(cap) \
    (((cap) >> FUN_REG_CAP_DSTRD_S) & FUN_REG_CAP_DSTRD_M)

#define FUN_REG_CAP_TO_S	24
#define FUN_REG_CAP_TO_M	0xff
#define FUN_REG_CAP_TO_P(cap)	((cap) << FUN_REG_CAP_TO_S)
#define FUN_REG_CAP_TO_G(cap)	\
    (((cap) >> FUN_REG_TO_AMS_S) & FUN_REG_CAP_TO_M)

#define FUN_REG_CAP_AMS_S	17
#define FUN_REG_CAP_AMS_M	0x3
#define FUN_REG_CAP_AMS_P(cap)	((cap) << FUN_REG_CAP_AMS_S)
#define FUN_REG_CAP_AMS_G(cap)	\
    (((cap) >> FUN_REG_CAP_AMS_S) & FUN_REG_CAP_AMS_M)

#define FUN_REG_CAP_CQR_S	16
#define FUN_REG_CAP_CQR_M	0x1
#define FUN_REG_CAP_CQR_P(cap)	((cap) << FUN_REG_CAP_CQR_S)
#define FUN_REG_CAP_CQR_G(cap)	\
    (((cap) >> FUN_REG_CAP_CQR_S) & FUN_REG_CAP_CQR_M)

#define FUN_REG_CAP_MQES_S	0
#define FUN_REG_CAP_MQES_M	0xffff
#define FUN_REG_CAP_MQES_P(cap)	((cap) << FUN_REG_CAP_MQES_S)
#define FUN_REG_CAP_MQES_G(cap)	\
    (((cap) >> FUN_REG_CAP_MQES_S) & FUN_REG_CAP_MQES_M)

#define FUN_REG_VS_MJR_S	16
#define FUN_REG_VS_MJR_M	0xffff
#define FUN_REG_VS_MJR_P(vs)	((vs) << FUN_REG_VS_MJR_S)
#define FUN_REG_VS_MJR_G(vs)	\
    (((vs) >> FUN_REG_VS_MJR_S) & FUN_REG_VS_MJR_M)

#define FUN_REG_VS_MNR_S	8
#define FUN_REG_VS_MNR_M	0xff
#define FUN_REG_VS_MNR_P(vs)	((vs) << FUN_REG_VS_MNR_S)
#define FUN_REG_VS_MNR_G(vs)	\
    (((vs) >> FUN_REG_VS_MNR_S) & FUN_REG_VS_MNR_M)

#define FUN_REG_VS_TER_S	0
#define FUN_REG_VS_TER_M	0xff
#define FUN_REG_VS_TER_P(vs)	((vs) << FUN_REG_VS_TER_S)
#define FUN_REG_VS_TER_G(vs)	\
    (((vs) >> FUN_REG_VS_TER_S) & FUN_REG_VS_TER_M)

#define FUN_REG_CC_IOCQES_S	20
#define FUN_REG_CC_IOCQES_M	0xf
#define FUN_REG_CC_IOCQES_P(cc) ((cc) << FUN_REG_CC_IOCQES_S)
#define FUN_REG_CC_IOCQES_G(cc) \
    (((cc) >> FUN_REG_CC_IOCQES_S) & FUN_REG_CC_IOCQES_M)

enum fun_reg_cc_iocqes {
	FUN_REG_CC_IOCQES_16 = 4,
	FUN_REG_CC_IOCQES_64 = 6,
	FUN_REG_CC_IOCQES_128 = 7,
};

#define FUN_REG_CC_IOSQES_S	16
#define FUN_REG_CC_IOSQES_M	0xf
#define FUN_REG_CC_IOSQES_P(cc) ((cc) << FUN_REG_CC_IOSQES_S)
#define FUN_REG_CC_IOSQES_G(cc) \
    (((cc) >> FUN_REG_CC_IOSQES_S) & FUN_REG_CC_IOSQES_M)

enum fun_reg_cc_iosqes {
	FUN_REG_CC_IOSQES_64 = 6,
	FUN_REG_CC_IOSQES_128 = 7,
};

#define FUN_REG_CC_SHN_S	14
#define FUN_REG_CC_SHN_M	0x3
#define FUN_REG_CC_SHN_P(cc)	((cc) << FUN_REG_CC_SHN_S)
#define FUN_REG_CC_SHN_G(cc)	\
    (((cc) >> FUN_REG_CC_SHN_S) & FUN_REG_CC_SHN_M)

enum fun_reg_cc_shn {
	FUN_REG_CC_SHN_NONE = 0x0,
	FUN_REG_CC_SHN_NORMAL = 0x1,
	FUN_REG_CC_SHN_ABRUPT = 0x2,
};

#define FUN_REG_CC_AMS_S	11
#define FUN_REG_CC_AMS_M	0x7
#define FUN_REG_CC_AMS_P(cc)	((cc) << FUN_REG_CC_AMS_S)
#define FUN_REG_CC_AMS_G(cc)	\
    (((cc) >> FUN_REG_CC_AMS_S) & FUN_REG_CC_AMS_M)

enum fun_reg_cc_ams {
	FUN_REG_CC_AMS_RR = 0x0,
	FUN_REG_CC_AMS_WRR = 0x1,
};

#define FUN_REG_CC_MPS_S	7
#define FUN_REG_CC_MPS_M	0xf
#define FUN_REG_CC_MPS_P(cc)	((cc) << FUN_REG_CC_MPS_S)
#define FUN_REG_CC_MPS_G(cc)	\
    (((cc) >> FUN_REG_CC_MPS_S) & FUN_REG_CC_MPS_M)

#define FUN_REG_CC_CSS_S	4
#define FUN_REG_CC_CSS_M	0x7
#define FUN_REG_CC_CSS_P(cc)	((cc) << FUN_REG_CC_CSS_S)
#define FUN_REG_CC_CSS_G(cc)	\
    (((cc) >> FUN_REG_CC_CSS_S) & FUN_REG_CC_CSS_M)

#define FUN_REG_CC_EN_S		0
#define FUN_REG_CC_EN_M		0x1
#define FUN_REG_CC_EN_P(cc)	((cc) << FUN_REG_CC_EN_S)
#define FUN_REG_CC_EN_G(cc)	\
    (((cc) >> FUN_REG_CC_EN_S) & FUN_REG_CC_EN_M)

enum fun_reg_csts_shst {
	FUN_REG_CSTS_SHST_NONE = 0x0,
	FUN_REG_CSTS_SHST_OCCURRING = 0x1,
	FUN_REG_CSTS_SHST_COMPLETE = 0x2,
};

#define FUN_REG_CSTS_PP_S	5
#define FUN_REG_CSTS_PP_M	0x1
#define FUN_REG_CSTS_PP_P(csts)	((csts) << FUN_REG_CSTS_PP_S)
#define FUN_REG_CSTS_PP_G(csts)	\
    (((csts) >> FUN_REG_CSTS_PP_S) & FUN_REG_CSTS_PP_M)

#define FUN_REG_CSTS_NSSRO_S	4
#define FUN_REG_CSTS_NSSRO_M	0x1
#define FUN_REG_CSTS_NSSRO_P(csts) ((csts) << FUN_REG_CSTS_NSSRO_S)
#define FUN_REG_CSTS_NSSRO_G(csts) \
    (((csts) >> FUN_REG_CSTS_NSSRO_S) & FUN_REG_CSTS_NSSRO_M)

#define FUN_REG_CSTS_SHST_S	2
#define FUN_REG_CSTS_SHST_M	0x3
#define FUN_REG_CSTS_SHST_P(csts) ((csts) << FUN_REG_CSTS_SHST_S)
#define FUN_REG_CSTS_SHST_G(csts) \
    (((csts) >> FUN_REG_CSTS_SHST_S) & FUN_REG_CSTS_SHST_M)

#define FUN_REG_CSTS_CFS_S	1
#define FUN_REG_CSTS_CFS_M	0x1
#define FUN_REG_CSTS_CFS_P(csts) ((csts) << FUN_REG_CSTS_CFS_S)
#define FUN_REG_CSTS_CFS_G(csts) \
    (((csts) >> FUN_REG_CSTS_CFS_S) & FUN_REG_CSTS_CFS_M)

#define FUN_REG_CSTS_RDY_S	0
#define FUN_REG_CSTS_RDY_M	0x1
#define FUN_REG_CSTS_RDY_P(csts) ((csts) << FUN_REG_CSTS_RDY_S)
#define FUN_REG_CSTS_RDY_G(csts) \
    (((csts) >> FUN_REG_CSTS_RDY_S) & FUN_REG_CSTS_RDY_M)

#define FUN_REG_AQA_ACQS_S	16
#define FUN_REG_AQA_ACQS_M	0xfff
#define FUN_REG_AQA_ACQS_P(aqa) ((aqa) << FUN_REG_AQA_ACQS_S)
#define FUN_REG_AQA_ACQS_G(aqa) \
    (((aqa) >> FUN_REG_AQA_ACQS_S) & FUN_REG_AQA_ACQS_M)

#define FUN_REG_AQA_ASQS_S	0
#define FUN_REG_AQA_ASQS_M	0xfff
#define FUN_REG_AQA_ASQS_P(aqa) ((aqa) << FUN_REG_AQA_ASQS_S)
#define FUN_REG_AQA_ASQS_G(aqa) \
    (((aqa) >> FUN_REG_AQA_ASQS_S) & FUN_REG_AQA_ASQS_M)

#define FUN_REG_CMBLOC_OFST_S	12
#define FUN_REG_CMBLOC_OFST_M	0xfffff
#define FUN_REG_CMBLOC_OFST_P(cmbloc) ((cmbloc) << FUN_REG_CMBLOC_OFST_S)
#define FUN_REG_CMBLOC_OFST_G(cmbloc) \
    (((cmbloc) >> FUN_REG_CMBLOC_OFST_S) & FUN_REG_CMBLOC_OFST_M)

#define FUN_REG_CMBLOC_BIR_S	0
#define FUN_REG_CMBLOC_BIR_M	0x3
#define FUN_REG_CMBLOC_BIR_P(cmbloc) ((cmbloc) << FUN_REG_CMBLOC_BIR_S)
#define FUN_REG_CMBLOC_BIR_G(cmbloc) \
    (((cmbloc) >> FUN_REG_CMBLOC_BIR_S) & FUN_REG_CMBLOC_BIR_M)

#define FUN_REG_CMBSZ_SZ_S	12
#define FUN_REG_CMBSZ_SZ_M	0xfffff
#define FUN_REG_CMBSZ_SZ_P(cmbsz) ((cmbsz) << FUN_REG_CMBSZ_SZ_S)
#define FUN_REG_CMBSZ_SZ_G(cmbsz) \
    (((cmbsz) >> FUN_REG_CMBSZ_SZ_S) & FUN_REG_CMBSZ_SZ_M)

#define FUN_REG_CMBSZ_SZU_S	8
#define FUN_REG_CMBSZ_SZU_M	0xf
#define FUN_REG_CMBSZ_SZU_P(cmbsz) ((cmbsz) << FUN_REG_CMBSZ_SZU_S)
#define FUN_REG_CMBSZ_SZU_G(cmbsz) \
    (((cmbsz) >> FUN_REG_CMBSZ_SZU_S) & FUN_REG_CMBSZ_SZU_M)

#define FUN_REG_CMBSZ_WDS_S	4
#define FUN_REG_CMBSZ_WDS_M	0x1
#define FUN_REG_CMBSZ_WDS_P(cmbsz) ((cmbsz) << FUN_REG_CMBSZ_WDS_S)
#define FUN_REG_CMBSZ_WDS_G(cmbsz) \
    (((cmbsz) >> FUN_REG_CMBSZ_WDS_S) & FUN_REG_CMBSZ_WDS_M)

#define FUN_REG_CMBSZ_RDS_S	3
#define FUN_REG_CMBSZ_RDS_M	0x1
#define FUN_REG_CMBSZ_RDS_P(cmbsz) ((cmbsz) << FUN_REG_CMBSZ_RDS_S)
#define FUN_REG_CMBSZ_RDS_G(cmbsz) \
    (((cmbsz) >> FUN_REG_CMBSZ_RDS_S) & FUN_REG_CMBSZ_RDS_M)

#define FUN_REG_CMBSZ_LISTS_S	2
#define FUN_REG_CMBSZ_LISTS_M	0x1
#define FUN_REG_CMBSZ_LISTS_P(cmbsz) ((cmbsz) << FUN_REG_CMBSZ_LISTS_S)
#define FUN_REG_CMBSZ_LISTS_G(cmbsz) \
    (((cmbsz) >> FUN_REG_CMBSZ_LISTS_S) & FUN_REG_CMBSZ_LISTS_M)

#define FUN_REG_CMBSZ_CQS_S	1
#define FUN_REG_CMBSZ_CQS_M	0x1
#define FUN_REG_CMBSZ_CQS_P(cmbsz) ((cmbsz) << FUN_REG_CMBSZ_CQS_S)
#define FUN_REG_CMBSZ_CQS_G(cmbsz) \
    (((cmbsz) >> FUN_REG_CMBSZ_CQS_S) & FUN_REG_CMBSZ_RDS_M)

#define FUN_REG_CMBSZ_SQS_S	0
#define FUN_REG_CMBSZ_SQS_M	0x1
#define FUN_REG_CMBSZ_SQS_P(cmbsz) ((cmbsz) << FUN_REG_CMBSZ_SQS_S)
#define FUN_REG_CMBSZ_SQS_G(cmbsz) \
    (((cmbsz) >> FUN_REG_CMBSZ_SQS_S) & FUN_REG_CMBSZ_SQS_M)

/**********************************
 *   A D M I N   C O M M A N D S
 **********************************/

enum fun_admin_ops {
	FUN_ADMIN_OP_INVALID = 0x00,
	FUN_ADMIN_OP_SQ = 0x01,	/* Submission Queue Flow Operation */
	FUN_ADMIN_OP_CQ = 0x02,	/* Completion Queue Flow Operation */
	FUN_ADMIN_OP_ETH = 0x03, /* Ethernet Flow Operation */
	FUN_ADMIN_OP_VI = 0x04,	/* Virtual Interface Flow Operation */
	FUN_ADMIN_OP_NSS = 0x05, /* NVMe Sub System Flow Operation */
	FUN_ADMIN_OP_CRYPTO = 0x06, /* Crypto Flow Operation */
	FUN_ADMIN_OP_VOL = 0x07, /* Volume Flow Operation */
	FUN_ADMIN_OP_RCNVME = 0x08, /* RC NVMe Flow Operation */
	FUN_ADMIN_OP_BIND = 0x20,	/* Flow Bind Operation */
};

enum fun_admin_flags {
	fun_admin_flag_compl = 0x80,
};

struct fun_admin_common {
	__u8 opcode;
	__u8 flags;
	__u16 cmdid;
	__u8 rsvd[2];
	__u8 ret;
	__u8 len16;
};

enum fun_admin_subops {
	FUN_ADMIN_SUBOP_ALLOC = 0x01,
	FUN_ADMIN_SUBOP_FREE = 0x02,
};

struct fun_admin_subcommon {
	__u8 subopcode;
};
/*	Send Queue (SQ)
 */

struct fun_admin_sq_alloc {
	__u8 subopcode;
	__u8 flags;
	__u8 cmd_set;
	__u8 rsvd0;
	__u32 sqid;
	__u32 cqid;
	__u32 esize_log2;
	__u16 int_vectorid;
	__u16 cmd_dma_nentry;   /* NVMe 4.1.3, 0 based queue size, number of entries */
	__u64 cmd_dma_address;
	__u64 head_tail_dma_address;
	__u8 pc;
	__u8 prio;
};

struct fun_admin_sq_free {
	__u8 subopcode;
	__u8 reserved[3];
	__u32 sqid;
	__u16 head;
	__u16 tail;
};

struct fun_admin_sq_cmd {
	struct fun_admin_common sq_common;
	union {
		struct fun_admin_sq_alloc sq_alloc;
		struct fun_admin_sq_free sq_free;
	} u;
} __attribute__ ((aligned(64)));

/*	Completion Queue (CQ)
 */
struct fun_admin_cq_alloc {
	__u8 subopcode;
	__u8 flags;
	__u8 cmd_set;
	__u8 pc;
	__u32 cqid;
	__u16 esize_log2;
	__u16 int_vectorid;
	__u16 cmd_dma_nentry;   /* 0 based queue size, number of entries */
                            /*
                             * NVMe 4.1.3:
                             * The Queue Size is indicated in a 16-bit 0’s based field
                             * that indicates the number of entries in the queue
                             */
	__u64 cmd_dma_address;
	__u64 head_tail_dma_address;
};

struct fun_admin_cq_free {
	__u8 subopcode;
	__u8 reserved[3];
	__u32 cqid;
	__u16 head;
	__u16 tail;
};

struct fun_admin_cq_cmd {
	struct fun_admin_common cq_common;
	union {
		struct fun_admin_cq_alloc cq_alloc;
		struct fun_admin_cq_free cq_free;
	} u;
} __attribute__ ((aligned(64)));

/*	Ethernet
 */

struct fun_admin_eth_alloc {
	__u8 subopcode;
	__u8 flags;

	__u32 ethid;
};

struct fun_admin_eth_free {
	__u8 subopcode;
	__u8 flags;
	__u16 rsvd;
	__u32 ethid;
};

struct fun_admin_eth_cmd {
	struct fun_admin_common eth_common;
	union {
		struct fun_admin_eth_alloc eth_alloc;
		struct fun_admin_eth_alloc eth_free;
	} u;
} __attribute__ ((aligned(64)));

/*	Virtual Interface (VI)
 */

enum fun_admin_vi_subops {

	FUN_ADMIN_VI_SUBOP_CTRL = 0x10,
	FUN_ADMIN_VI_SUBOP_STATS = 0x11,
};

struct fun_admin_vi_alloc {
	__u8 subopcode;
	__u8 flags;

	__u32 viid;
};

struct fun_admin_vi_free {
	__u8 subopcode;
	__u8 flags;

	__u32 viid;
};

struct fun_admin_vi_ctrl {
	__u8 subopcode;
};

struct fun_admin_vi_macstats {
	__u64 octets;
	__u64 pkts;
	__u64 broadcast_pkts;
	__u64 multicast_pkts;
	__u64 pkts_64octets;
	__u64 pkts_65_to_127octets;
	__u64 pkts_128_to_255octets;
	__u64 pkts_256_to_511octets;

	__u64 pkts_512_to_1023octets;
	__u64 pkts_1024_to_1518octets;
	__u64 pkts_1519_to_9600octets;
	__u64 rsvd0;
	__u64 rsvd1;
	__u64 rsvd2;
	__u64 rsvd3;
	__u64 rsvd4;
} __attribute__ ((aligned(64)));

struct fun_admin_vi_rxtx_stats {
	struct fun_admin_vi_macstats tx;
	struct fun_admin_vi_macstats rx;
} __attribute__ ((aligned(64)));

struct fun_admin_vi_stats {
	__u8 subopcode;
	__u8 rsvd[7];
};

struct fun_admin_vi_cmd {
	struct fun_admin_common vi_common;
	union {
		struct fun_admin_vi_alloc vi_alloc;
		struct fun_admin_vi_free vi_free;
		struct fun_admin_vi_ctrl vi_ctrl;
		struct fun_admin_vi_stats vi_stats;
	} u;
} __attribute__ ((aligned(64)));

/* 	Crypto
 */
struct fun_admin_crypto_alloc {
	__u8 subopcode;
	__u8 flags;

	__u32 cryptoid;
};

struct fun_admin_crypto_free {
	__u8 subopcode;
	__u8 flags;
	__u16 rsvd;
	__u32 cryptoid;
};

struct fun_admin_crypto_cmd {
	struct fun_admin_common crypto_common;
	union {
		struct fun_admin_crypto_alloc crypto_alloc;
		struct fun_admin_crypto_free crypto_free;
	} u;
} __attribute__ ((aligned(64)));

enum fun_admin_bind_consts {
	FUN_ADMIN_BIND_NFLOWS = 4,
};

enum fun_admin_bind_type {
	FUN_ADMIN_BIND_TYPE_SQ = FUN_ADMIN_OP_SQ,
	FUN_ADMIN_BIND_TYPE_CQ = FUN_ADMIN_OP_CQ,
	FUN_ADMIN_BIND_TYPE_ETH = FUN_ADMIN_OP_ETH,
	FUN_ADMIN_BIND_TYPE_VI = FUN_ADMIN_OP_VI,
	FUN_ADMIN_BIND_TYPE_NSS = FUN_ADMIN_OP_NSS,
	FUN_ADMIN_BIND_TYPE_CRYPTO = FUN_ADMIN_OP_CRYPTO,
	FUN_ADMIN_BIND_TYPE_VOL = FUN_ADMIN_OP_VOL,
	FUN_ADMIN_BIND_TYPE_RCNVME = FUN_ADMIN_OP_RCNVME,
};

struct fun_admin_bind_flow {
	__u32 type_id;
};

struct fun_admin_bind_cmd {
	struct fun_admin_common bind_common;
	unsigned int bind_nflows;
	struct fun_admin_bind_flow flow[3];
} __attribute__ ((aligned(64)));

struct fun_admin_syslog_entry {

};
struct fun_admin_syslog_ctrl {
	unsigned int x;
};

struct fun_admin_syslog_cmd {
	struct fun_admin_common sl_common;
	struct fun_admin_syslog_ctrl sl_ctrl;
};

enum fun_data_subops {
	FUN_DATA_SUBOP_IMMEDIATE,
	FUN_DATA_SUBOP_SGL,
};

struct fun_subcmd_immediate {
	__u8 subopcode;
	__u8 imm_flags;
	__u16 rsvd;
	__u32 imm_len;
	__u8 imm_data[0];
};

struct fun_subcmd_sgl {
	__u8 subopcode;
	__u8 sgl_flags;
	__u8 sgl_nfrags;
	__u8 rsvd;
	__u32 sgl0_len;
	__u64 sgl0_dmaaddr;
};

struct fun_cqe_info {
	__u16 sqhd;		/* sq head pointer value */
	__u16 sqid;		/* associated submission queue identifier or 0xffff */
	__u16 cid;		/* command identifier */
	__u16 sf_p;		/* status field and phase-bit */
};

struct fun_cqe_16 {
	__u64 value[1];

	__u16 sqhd;		/* sq head pointer value */
	__u16 sqid;		/* associated submission queue identifier or 0xffff */
	__u16 cid;		/* command identifier */
	__u16 sf_p;		/* status field and phase-bit */
};

struct fun_cqe_64 {
	__u64 value[7];

	__u16 sqhd;		/* sq head pointer value */
	__u16 sqid;		/* associated submission queue identifier or 0xffff */
	__u16 cid;		/* command identifier */
	__u16 sf_p;		/* status field and phase-bit */
};

struct fun_cqe_128 {
	__u64 value[15];

	__u16 sqhd;		/* sq head pointer value */
	__u16 sqid;		/* associated submission queue identifier or 0xffff */
	__u16 cid;		/* command identifier */
	__u16 sf_p;		/* status field and phase-bit */
};

/******************************************************************************
 *   E T H E R N E T   C O M M A N D S
 ****************************************/

enum fun_eth_cmd_ops {
	FUN_ETH_CMD_OP_PACKET = 0x01,	/* Packet Operation */
	FUN_ETH_CMD_OP_GSO = 0x02,	/* Generic Send Offload
					 * Operation
					 */
};

enum fun_eth_cmd_flags {
	FUN_ETH_CMD_FLAG_COMPL_CQ = (1 << 7),
	FUN_ETH_CMD_FLAG_COMPL_SQ = (1 << 6),
};

struct fun_eth_packet_cmd {
	__u8 ecmd_opcode;
	__u8 ecmd_flags;
	__u16 ecmd_id;
	__u8 rsvd[2];
	__u8 ret;
	__u8 len16;
	__u32 pktlen;
	__u32 rsvd1;
};

struct fun_eth_packets_cmd {
	__u8 ecmd_opcode;
};

/******************************************************************************
 *   C R Y P T O
 ******************/

enum fun_crypto_cmd_ops {
	FUN_CRYPTO_CMD_OP_AES = 0x01,	/* AES Operation */
};

struct fun_crypto_cmd {
	__u8 ccmd_opcode;
	__u8 ccmd_flags;
	__u16 ccmd_id;
	__u8 rsvd[2];
	__u8 ret;
	__u8 len16;
};

extern const char *fun_admin_ops_strings[];


/******************************************************************************
 *   UTILS
 ******************/

static inline struct fun_cqe_info *get_fun_cqe_info(uint8_t *buffer,
	unsigned int sqe_esize, unsigned int cqe_esize)
{
	return (struct fun_cqe_info *)(buffer + sqe_esize + cqe_esize
			- sizeof(struct fun_cqe_info));
}

#endif /* __FUN_API_H__ */
