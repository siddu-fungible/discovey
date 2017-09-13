/*
 *	nvme.h: NVMe standard definitions
 *
 * 	Created by Pratapa Vaka on 2016-09-30.
 *	Copyright © 2016 Fungible. All rights reserved.
 */

#pragma once

//#include <nucleus/types.h>
//#include <services/services.h> // for syslog

#include "fun_utils.h"

typedef uint64_t size_t;

#define fun_nvme_cpl_is_error(cpl)                    \
    ((cpl)->status.sc != 0 || (cpl)->status.sct != 0)

#define FUN_NVME_ADMIN_QID 0
#define FUN_NVME_ADMIN_QSIZE_MAX 4096

#define FUN_NVME_PAGE_SHIFT 12
#define FUN_NVME_PAGE_SIZE (1 << (FUN_NVME_PAGE_SHIFT))
#define FUN_NVME_PAGE_MASK ((FUN_NVME_PAGE_SIZE) - 1)
#define FUN_NVME_MAX_NSID 0xFFFFFFFF

#define FUN_NVME_PRPS_PER_PAGE ((FUN_NVME_PAGE_SIZE) / sizeof(uint64_t))

#define FUN_NVME_PRPE_SIZE (sizeof(uint64_t))
#define FUN_NVME_PRPE_MASK (FUN_NVME_PRPE_SIZE - 1)
#define FUN_NVME_PRPE_SHIFT (__builtin_ctz(FUN_NVME_PRPE_SIZE))

#define TEST_PATTERN_DEAD_BEEF 0xdeadbeef

#define FUN_NVME_ADM_SQES_LOG2 6
#define FUN_NVME_ADM_CQES_LOG2 4


// NVMe Controller State
enum fun_nvme_ctrlr_state {
	FUN_NVME_CTRLR_STATE_INIT,
	FUN_NVME_CTRLR_STATE_WAIT_READY,
	FUN_NVME_CTRLR_STATE_READY,
};

/* NVMe Controller Doorbell Registers */
enum {
	FUN_NVME_SQ0TDBL = 0x1000, /* SQ 0 Tail Doorbell, 32bit (Admin) */
	FUN_NVME_CQ0HDBL = 0x1004, /* CQ 0 Head Doorbell, 32bit (Admin) */
};

// NVMe NVM command set opcodes
enum fun_nvme_nvm_ops {
	FUN_NVME_FLUSH = 0x00,
	FUN_NVME_WRITE = 0x01,
	FUN_NVME_READ = 0x02,
	FUN_NVME_WRITE_UNCORR = 0x04,
	FUN_NVME_COMPARE = 0x05,
	FUN_NVME_WRITE_ZEROES = 0x08,
	FUN_NVME_DSM = 0x09,
	FUN_NVME_RSV_REG = 0x0d,
	FUN_NVME_RSV_REP = 0x0e,
	FUN_NVME_RSV_ACQ = 0x11,
	FUN_NVME_RSV_REL = 0x15,
	FUN_NVME_NVM_LAST
};

/* Admin Commands Opcodes*/
enum fun_nvme_adm_ops {
	FUN_NVME_DEL_SQ = 0x00,
	FUN_NVME_CREATE_SQ = 0x01,
	FUN_NVME_GET_LOG = 0x02,
	FUN_NVME_DEL_CQ = 0x04,
	FUN_NVME_CREATE_CQ = 0x05,
	FUN_NVME_IDTFY = 0x06,
	FUN_NVME_ABORT = 0x08,
	FUN_NVME_SET_FEAT = 0x09,
	FUN_NVME_GET_FEAT = 0x0a,
	FUN_NVME_ASYNC_REQ = 0x0c,
	FUN_NVME_NS_MGMT = 0x0d,
	FUN_NVME_FW_COMMIT = 0x10,
	FUN_NVME_FW_DOWNLOAD = 0x11,
	FUN_NVME_NS_ATTACH = 0x15,
	FUN_NVME_KEEP_ALIVE = 0x18,
	FUN_NVME_FABRICS = 0x7f,
	FUN_NVME_FMT_NVM = 0x80,
	FUN_NVME_SEC_SEND = 0x81,
	FUN_NVME_SEC_RECV = 0x82,
	FUN_NVME_SANITIZE = 0x84,
	FUN_NVME_VS_API_NO_DATA = 0xc0,
	FUN_NVME_VS_API_SEND = 0xc1,
	FUN_NVME_VS_API_RECV = 0xc2,
	FUN_NVME_VS_API_BIDIR = 0xc3,
	FUN_NVME_ADM_LAST,
};

// Status code types
enum fun_nvme_sct {
	/* Generic Error */
	FUN_NVME_SCT_GEN = 0x0,
	/* Command Specific Error */
	FUN_NVME_SCT_CS = 0x1,
	/* Media Error */
	FUN_NVME_SCT_ME = 0x2,
	/* Vendor Specific Error */
	FUN_NVME_SCT_VS = 0x7,
};

// Generic command status codes
enum fun_nvme_gen_sc {
	FUN_NVME_SC_SUCCESS = 0x00,
	FUN_NVME_SC_INVAL_OP = 0x01,
	FUN_NVME_SC_INVAL_FLD = 0x02,
	FUN_NVME_SC_CMD_ID_CONFLICT = 0x03,
	FUN_NVME_SC_DATA_XFER_ERR = 0x04,
	FUN_NVME_SC_ABORT_PWR_LOSS = 0x05,
	FUN_NVME_SC_INT_DEV_ERR = 0x06,
	FUN_NVME_SC_ABORT_BY_REQ = 0x07,
	FUN_NVME_SC_ABORT_SQ_DEL = 0x08,
	FUN_NVME_SC_ABORT_FAIL_FUSED = 0x09,
	FUN_NVME_SC_ABORT_MISS_FUSED = 0x0a,
	FUN_NVME_SC_INVAL_NS_OR_FMT = 0x0b,
	FUN_NVME_SC_CMD_SEQ_ERR = 0x0c,
	FUN_NVME_SC_INVAL_SGL_SEG_DESC = 0x0d,
	FUN_NVME_SC_INVAL_NUM_SGL_DESCS = 0x0e,
	FUN_NVME_SC_INVAL_DATA_SGL_LEN = 0x0f,
	FUN_NVME_SC_INVAL_META_SGL_LEN = 0x10,
	FUN_NVME_SC_INVAL_SGL_DESC_TYPE = 0x11,
	FUN_NVME_SC_INVAL_CTRLR_MEM_BUF = 0x12,
	FUN_NVME_SC_INVAL_PRP_OFF = 0x13,
	FUN_NVME_SC_ATOMIC_WRUNIT_XEDED = 0x14,
	FUN_NVME_SC_INVAL_SGL_OFF = 0x16,
	FUN_NVME_SC_INVAL_SGL_SUBTYPE = 0x17,
	FUN_NVME_SC_HOSTID_INCONST_FMT = 0x18,
	FUN_NVME_SC_XPIRED_KEEP_ALIVE = 0x19,
	FUN_NVME_SC_INVAL_KEEP_ALIVE = 0x1a,
	FUN_NVME_SC_LBA_OUT_OF_RANGE = 0x80,
	FUN_NVME_SC_CAP_XEDED = 0x81,
	FUN_NVME_SC_NS_NOT_RDY = 0x82,
	FUN_NVME_SC_RSV_CONFLICT = 0x83,
	FUN_NVME_SC_FMT_IN_PROG = 0x84,
};

// Command specific status codes
enum fun_nvme_cs_sc {
	FUN_NVME_SC_INVAL_CQ = 0x00,
	FUN_NVME_SC_INVAL_QID = 0x01,
	FUN_NVME_SC_INVAL_QSIZE = 0x02,
	FUN_NVME_SC_ABORT_LMT_XEDED = 0x03,
	FUN_NVME_SC_ASYNC_LMT_XEDED = 0x05,
	FUN_NVME_SC_INVAL_FW_SLOT = 0x06,
	FUN_NVME_SC_INVAL_FW_IMAGE = 0x07,
	FUN_NVME_SC_INVAL_INTR_VEC = 0x08,
	FUN_NVME_SC_INVAL_LOG_PAGE = 0x09,
	FUN_NVME_SC_INVAL_FMT = 0x0a,
	FUN_NVME_SC_FW_REQ_CONV_RST = 0x0b,
	FUN_NVME_SC_INVAL_Q_DEL = 0x0c,
	FUN_NVME_SC_FEAT_ID_UNSAVEABLE = 0x0d,
	FUN_NVME_SC_FEAT_UNCHANGEABLE = 0x0e,
	FUN_NVME_SC_FEAT_NOT_NS_SPECIFIC = 0x0f,
	FUN_NVME_SC_FW_REQ_NVM_RST = 0x10,
	FUN_NVME_SC_FW_REQ_RST = 0x11,
	FUN_NVME_SC_FW_REQ_MAXTIME_VIOL = 0x12,
	FUN_NVME_SC_FW_ACTI_PROHIBIT = 0x13,
	FUN_NVME_SC_OVERLAP_RANGE = 0x14,
	FUN_NVME_SC_NS_INSUFF_CAP = 0x15,
	FUN_NVME_SC_NS_ID_UNAVAIL = 0x16,
	FUN_NVME_SC_NS_ALRDY_ATTACHED = 0x18,
	FUN_NVME_SC_NS_IS_PRIVATE = 0x19,
	FUN_NVME_SC_NS_NOT_ATTACHED = 0x1a,
	FUN_NVME_SC_TP_UNSUPP = 0x1b,
	FUN_NVME_SC_INVAL_CTRLR_LIST = 0x1c,
	FUN_NVME_SC_CONFLICT_ATTRS = 0x80,
	FUN_NVME_SC_INVAL_PR_INFO = 0x81,
	FUN_NVME_SC_WRITE_TO_RO_PAGE = 0x82,
};

// Media error status codes
enum fun_nvme_me_sc {
	FUN_NVME_SC_WRITE_FAULTS = 0x80,
	FUN_NVME_SC_UNRECOVERED_RD_ERR = 0x81,
	FUN_NVME_SC_GUARD_ERR = 0x82,
	FUN_NVME_SC_APPTAG_ERR = 0x83,
	FUN_NVME_SC_REFTAG_ERR = 0x84,
	FUN_NVME_SC_COMP_FAIL = 0x85,
	FUN_NVME_SC_ACCESS_DENIED = 0x86,
	FUN_NVME_SC_DEALLOC_OR_UNWR_BLOCK = 0x87,
};

// NVMe SGL descriptor type
enum fun_nvme_sgl_desc_type {
	FUN_NVME_SGL_TYPE_DATA_BLOCK = 0x0,
	FUN_NVME_SGL_TYPE_BIT_BUCKET = 0x1,
	FUN_NVME_SGL_TYPE_SEG = 0x2,
	FUN_NVME_SGL_TYPE_LAST_SEG = 0x3,
	FUN_NVME_SGL_TYPE_KEYED_DATA_BLOCK = 0x4,
	FUN_NVME_SGL_TYPE_VENDOR = 0xF,
};

enum fun_nvme_sgl_desc_subtype {
	FUN_NVME_SGL_SUBTYPE_ADDRESS = 0x0,
	FUN_NVME_SGL_SUBTYPE_OFFSET = 0x1,
};

// PSDT (PRP or SGL for Data Transfer) in NVMe command
enum fun_nvme_psdt_value {
	FUN_NVME_PSDT_PRP = 0x0,
	FUN_NVME_PSDT_SGL_MPTR_CONTIG = 0x1,
	FUN_NVME_PSDT_SGL_MPTR_SGL = 0x2,
	FUN_NVME_PSDT_RESERVED = 0x3
};

#define NVME_IS_PSDT_PRP(psdt) ((psdt == FUN_NVME_PSDT_PRP) ?  true : false)

/**
 * True for host to controller data transfer
 */
#define NVME_IS_H2F_XFER(dir) (((dir == FUN_NVME_H2C_XFER) \
	|| (dir == FUN_NVME_BIDIR_XFER)) ? true : false)

/**
 * True for host to controller data transfer
 */
#define NVME_IS_F2H_XFER(dir) (((dir == FUN_NVME_C2H_XFER) \
	|| (dir == FUN_NVME_BIDIR_XFER)) ? true : false)

struct __attribute__ ((packed)) fun_nvme_sgl_desc {

	uint64_t addr;

	union {
		struct {
			uint8_t reserved[7];
			uint8_t subtype:4;
			uint8_t type:4;
		} generic;

		struct {
			uint32_t len;
			uint8_t reserved[3];
			uint8_t subtype:4;
			uint8_t type:4;
		} unkeyed;

		struct {
			uint64_t len:24;
			uint64_t key:32;
			uint64_t subtype:4;
			uint64_t type:4;
		} keyed;
	};
};

static_assert(sizeof(struct fun_nvme_sgl_desc) == 16,
	"Incorrect size of fun_nvme_sgl_desc");

#define FUN_NVME_DIR_MASK 0x3

struct __attribute__ ((packed)) fun_nvme_cmd_cmn {
	/** cdw0 - opcode, fused operation, psdt, and cid */
	union {
		uint8_t opcode;

		struct {
			uint8_t op_6b:6;
			uint8_t dir:2;
		};
	};
	uint8_t fuse:2;
	uint8_t rsvd0:4;
	uint8_t psdt:2;
	uint16_t cid;

	/** cdw1: namespace identifier */
	uint32_t nsid;

	/** cdw2-3 */
	union {
		uint64_t rsvd;

		// for vs_api command
		struct {
			uint8_t vs_ver:4;
			uint8_t vs_rsvd:4;
			uint8_t vs_subop;
			uint16_t vs_hndlr_id;
			uint32_t arg0;
		};
	};

	/** cdw4-5: metadata pointer */
	uint64_t mptr;

	/** cdw6-9: data pointer */
	union {
		struct {
			uint64_t prp1;
			uint64_t prp2;
		};

		struct fun_nvme_sgl_desc sgl;
	};
};

struct __attribute__ ((packed)) fun_nvme_cmd {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t cdw10;
	uint32_t cdw11;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

#define NVME_CMD_SIZE (sizeof(struct fun_nvme_cmd))

static_assert(NVME_CMD_SIZE == 64,
	"Incorrect size of fun_nvme_cmd");

/* Delete CQ or SQ command */
struct __attribute__ ((packed)) fun_nvme_del_sq {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t qid:16;
	uint32_t res1:16;
	uint32_t cdw11;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_del_sq) == 64,
	"Incorrect size of fun_nvme_del_sq");

#define fun_nvme_del_cq fun_nvme_del_sq

struct __attribute__ ((packed)) fun_nvme_create_sq {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t qid:16;
	uint32_t qsize:16;
	/* Physically Contiguous */
	uint32_t pc:1;
	uint32_t qprio:2;
	uint32_t res1:13;
	/* Completion Queue ID */
	uint32_t cqid:16;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_create_sq) == 64,
	"Incorrect size of fun_nvme_create_sq");

struct __attribute__ ((packed)) fun_nvme_create_cq {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t qid:16;
	uint32_t qsize:16;
	uint32_t pc:1;
	/* Interrupts Enabled */
	uint32_t ien:1;	
	uint32_t res1:14;
	/* Interrupt Vector */
	uint32_t iv:16;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_create_cq) == 64,
	"Incorrect size of fun_nvme_create_cq");

// page_id of get_log_page command
enum fun_nvme_log_page_id {
	FUN_NVME_LOG_ERROR = 0x1,
	FUN_NVME_LOG_SMART = 0x2,
	FUN_NVME_LOG_FW_SLOT = 0x3,
};

struct __attribute__ ((packed)) fun_nvme_get_log {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t page_id:16;	
	uint32_t numdwords:12;
	uint32_t res1:4;
	uint32_t cdw11;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_get_log) == 64,
	"Incorrect size of fun_nvme_get_log");

/* cns bit in Identify command */
enum {
	FUN_NVME_IDTFY_NS_ACTIVE_DATA = 0,
	FUN_NVME_IDTFY_CTRLR_DATA = 1,
	FUN_NVME_IDTFY_NS_ACTIVE_LIST = 2,
	FUN_NVME_IDTFY_NS_ALLOC_LIST = 0x10,
	FUN_NVME_IDTFY_NS_ALLOC_DATA = 0x11,
	FUN_NVME_IDTFY_NS_CTRLR_LIST = 0x12,
	FUN_NVME_IDTFY_CTRLR_LIST = 0x13,
};

struct __attribute__ ((packed)) fun_nvme_idtfy {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t cns:8;
	uint32_t res1:8;
	uint32_t cntid:16;
	uint32_t cdw11;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_idtfy) == 64,
	"Incorrect size of fun_nvme_idtfy");

/* oncs(optional nvm cmd support) field in Identify ctrlr data */
enum {
	FUN_NVME_ONCS_COMPARE = 1 << 0,
	FUN_NVME_ONCS_WR_UNCORR = 1 << 1,
	FUN_NVME_ONCS_DSM = 1 << 2,
	FUN_NVME_ONCS_WR_ZERO = 1 << 3,
	FUN_NVME_ONCS_SAVE = 1 << 4,
	FUN_NVME_ONCS_RSRV = 1 << 5,
};

/* oacs(optional adm cmd support) field in Identify ctrlr data */
enum {
	FUN_NVME_OACS_SECURITY = 1 << 0,
	FUN_NVME_OACS_FORMAT = 1 << 1,
	FUN_NVME_OACS_FW_UPD = 1 << 2,
	FUN_NVME_OACS_NS_MGMT = 1 << 3,
};

/* lpa(log page attributes) field in Identify ctrlr data */
enum {
	FUN_NVME_LPA_SMART_PER_NS = 1 << 0,
	FUN_NVME_LPA_CMD_EFFECTS = 1 << 1,
	FUN_NVME_LPA_GETLOG_EXTENDED = 1 << 2,
};

/* fuses(fused operations support) field in Identify ctrlr data */
enum {
	FUN_NVME_FUSES_COMPARE_WRITE = 1 << 0,
};

/* sgls(SGL support) field in Identify ctrlr data */
enum {
	FUN_NVME_SGLS_NVM = 1 << 0,
	FUN_NVME_SGLS_KEYED_DBD = 1 << 2,
	FUN_NVME_SGLS_BBD = 1 << 16,
	FUN_NVME_SGLS_LARGE_LEN = 1 << 17,
	FUN_NVME_SGLS_MPTR_AS_SGLSEG = 1 << 18,
	FUN_NVME_SGLS_ADDR_AS_OFFSET = 1 << 19,
};

/* mc (metadata capabilities) field in Identify ctrlr data */
enum {
	FUN_NVME_MC_CONTIG = 1 << 0,
	FUN_NVME_MC_SEPARATE = 1 << 1,
};

/* dpc (data protection capabilities) field in Identify ns data */
enum {
	FUN_NVME_DPC_TYPE1 = 1 << 0,
	FUN_NVME_DPC_TYPE2 = 1 << 1,
	FUN_NVME_DPC_TYPE3 = 1 << 2,
	FUN_NVME_DPC_FIRST_8B = 1 << 3,
	FUN_NVME_DPC_LAST_8B = 1 << 4,
};

/* dps (data protection settings) field in Identify ns data */
enum {
	FUN_NVME_DPS_TYPE_MASK = 0x7,
	FUN_NVME_DPS_DIS = 0,
	FUN_NVME_DPS_TYPE1 = 1,
	FUN_NVME_DPS_TYPE2 = 2,
	FUN_NVME_DPS_TYPE3 = 3,
	FUN_NVME_DPS_FIRST_OR_LAST = 1 << 3,
};

/* version = 1.2.1 */
//#define NVME_VERSION ((1 << 16) | (2 << 8) | 1)

#define FUN_NVME_CTRLR_DATA_SN_LEN 20
#define FUN_NVME_CTRLR_DATA_MN_LEN 40
#define FUN_NVME_CTRLR_DATA_FR_LEN 8
#define FUN_NVME_CTRLR_DATA_IEEE_LEN 3

#define FUN_NVME_NS_DATA_NUM_LBAFS 16
#define FUN_NVME_LBAF_NUM_MASK 0xF

#define FUN_NVME_CTRLR_DATA_SQES_MIN_M 0xF
#define FUN_NVME_CTRLR_DATA_SQES_MIN_S 0
#define FUN_NVME_CTRLR_DATA_SQES_MAX_M 0xF
#define FUN_NVME_CTRLR_DATA_SQES_MAX_S 4

#define FUN_NVME_CTRLR_DATA_CQES_MIN_M 0xF
#define FUN_NVME_CTRLR_DATA_CQES_MIN_S 0
#define FUN_NVME_CTRLR_DATA_CQES_MAX_M 0xF
#define FUN_NVME_CTRLR_DATA_CQES_MAX_S 4

/* Return data for Identify Controller */
struct fun_nvme_ctrlr_data {
	/* vendor id */
	uint16_t vid;
	/* Subsystem vendor id */
	uint16_t ssvid;
	/* serial number */
	uint8_t sn[FUN_NVME_CTRLR_DATA_SN_LEN];
	/* model number */
	uint8_t mn[FUN_NVME_CTRLR_DATA_MN_LEN];
	/* firmware revision */
	uint8_t fr[FUN_NVME_CTRLR_DATA_FR_LEN];
	/* recommended arbitration burst */
	uint8_t rab;
	/* IEEE OUI id */
	uint8_t ieee[FUN_NVME_CTRLR_DATA_IEEE_LEN];
	/* Controller Multipath IO & NS sharing capabilities */
	uint8_t cmic;
	/* maximum data transfer size */
	uint8_t mdts;
	/* controller id */
	uint16_t cntlid;
	/* version */
	uint32_t ver;
	/* rtd3 resume latency */
	uint32_t rtd3r;
	/* rtd3 entry latency */
	uint32_t rtd3e;
	/* optional async event supported */
	uint32_t oaes;
	/* controller attributes */
	uint32_t ctratt;
	uint8_t rsvd255[156];
	/* optional admin commands supported */
	uint16_t oacs;
	/* abort command limit */
	uint8_t acl;
	/* asynchronous event request limit */
	uint8_t aerl;
	/* firmware update capabilities */
	uint8_t frmw;
	/* log page attributes */
	uint8_t lpa;
	/* error log page entries */
	uint8_t elpe;
	/* number of power states supported */
	uint8_t npss;
	/* admin vendor specific command config */
	uint8_t avscc;
	/* autonomous power state transition attributes */
	uint8_t apsta;
	/* warning composite temperature threshold */
	uint16_t wctemp;
	/* critical composite temperature threshold */
	uint16_t cctemp;
	/* max time for firmware activation */
	uint16_t mtfa;
	/* host memory buffer preferred size */
	uint32_t hmpre;
	/* host memory buffer minimum size */
	uint32_t hmmin;
	/* totoal nvm capacity */
	uint64_t tnvmcap_hi;
	uint64_t tnvmcap_lo;
	/* unallocated nvm capacity */
	uint64_t unvmcap_hi;
	uint64_t unvmcap_lo;
	/* replay protected memory block support */
	uint32_t rpmbs;
	uint8_t rsvd319[4];
	/* keep alive support */
	uint16_t kas;
	uint8_t rsvd511[190];
	/* submission queue entry size */
	uint8_t sqes;
	/* completion queue entry size */
	uint8_t cqes;
	/* maximum outstanding commands */
	uint16_t maxcmd;
	/* number of namespaces */
	uint32_t nn;
	/* optional nvm command support */
	uint16_t oncs;
	/* fused operation support */
	uint16_t fuses;
	/* format NVM attributes */
	uint8_t fna;
	/* volatile write cache */
	uint8_t vwc;
	/* atomic write unit normal */
	uint16_t awun;
	/* atomic write unit power failure */
	uint16_t awupf;
	/* NVM vendor specific command config */
	uint8_t nvscc;
	uint8_t rsvd531;
	/* atomic compare and write unit */
	uint16_t acwu;
	uint8_t rsvd535[2];
	/* SGL support */
	uint32_t sgls;
	uint8_t rsvd767[228];
	/* NVM subsystem NVMe Qualified Name */
	uint8_t subnqn[256];
	uint8_t rsvd2047[1024];
	/* power state descriptors */
	uint8_t psd[1024];
	/* vendor specific data */
	uint8_t vs[1024];
};

static_assert(sizeof(struct fun_nvme_ctrlr_data) == 4096, "Incorrect size");

// LBA format
struct fun_nvme_lbaf {
	/* Metadata size */
	uint16_t ms;
	/* LBA data size in a power of 2 */
	uint8_t lbads;
	/* relative performance */
	uint8_t rp;
};

struct fun_nvme_ns_data {
	/* name space size */
	uint64_t nsze;
	/* name space capacity */
	uint64_t ncap;
	/* name space utilization */
	uint64_t nuse;
	/* name space features */
	uint8_t nsfeat;
	/* Number of LBA Formats */
	uint8_t nlbaf;
	/* Formatted LBA Size */
	uint8_t flbas;
	/* Metadata Capabilities */
	uint8_t mc;
	/* End-2-end Data Protection Capabilities */
	uint8_t dpc;		
	/* End-2-end Data Protection Type Settings */
	uint8_t dps;		
	/* Namespace Multi-path IO and Namespace sharing capabilities */
	uint8_t nmic;
	/* Reservation Capabilities */
	uint8_t rescap;
	/* Format Progress Indicator */
	uint8_t fpi;
	uint8_t res33;
	/* Namespace Atomic Write Unit Normal */
	uint16_t nawun;
	/* Namespace Atomic Write Unit Power Fail */
	uint16_t nawupf;
	/* Namespace Atomic Compare and Write Unit */
	uint16_t nacwu;
	/* Namespace Atomic Boundary Size Normal */
	uint16_t nabsn;
	/* Namespace Atomic Boundary Offset */
	uint16_t nabo;
	/* Namespace Atomic Boundary Size Power Fail */
	uint16_t nabspf;
	uint8_t res47[2];
	/* Namespace NVM Capacity */
	uint64_t nvmcap_hi;
	uint64_t nvmcap_lo;
	uint8_t res103[40];
	/* Namespace Globally Unique Identifier */
	uint64_t nguid_hi;
	uint64_t nguid_lo;
	/* IEEE Extended Unique Identifier EUI64 */
	uint64_t eui64; 
	/* LBA formats */
	struct fun_nvme_lbaf lbafs[FUN_NVME_NS_DATA_NUM_LBAFS];
	uint8_t res383[192];
	/* vendor specific data */
	uint8_t vs[3712];
};

static_assert(sizeof(struct fun_nvme_ns_data) == 4096, "Incorrect size");

enum {
	FUN_NVME_FEAT_ARB = 1,
	FUN_NVME_FEAT_PWR_MGMT = 2,
	FUN_NVME_FEAT_LBA_RANGE_TYPE = 3,
	FUN_NVME_FEAT_TEMP_THRESH = 4,
	FUN_NVME_FEAT_ERR_RECOVERY = 5,
	FUN_NVME_FEAT_VOLATILE_WR_CACHE = 6,
	FUN_NVME_FEAT_NUM_QUEUES = 7,
	FUN_NVME_FEAT_INTR_COALESCING = 8,
	FUN_NVME_FEAT_INTR_VEC_CONF = 9,
	FUN_NVME_FEAT_WR_ATOMICITY = 0x0a,
	FUN_NVME_FEAT_ASYNC_EV_CONF = 0x0b,
	FUN_NVME_FEAT_SW_PROGRESS_MARKER = 0x80,
};

// Common structure for Set or Get Features
struct __attribute__ ((packed)) fun_nvme_feat {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t feat_id:8;
	uint32_t res1:24;
	union {
		uint32_t cdw11;
		struct {
			uint16_t nsqr;
			uint16_t ncqr;
		};
	};
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_feat) == 64,
	"Incorrect size of fun_nvme_feat");

struct __attribute__ ((packed)) fun_nvme_async_evt_req {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t cdw10;
	uint32_t cdw11;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_async_evt_req) == 64,
	"Incorrect size of fun_nvme_async_evt_req");

/* sel field of ns_mgmt command */
enum {
	FUN_NVME_NS_MGMT_SEL_CREATE = 0,
	FUN_NVME_NS_MGMT_SEL_DELETE = 1,
};

struct __attribute__ ((packed)) fun_nvme_ns_mgmt {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t sel:4;
	uint32_t res1:28;
	uint32_t cdw11;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_ns_mgmt) == 64,
	"Incorrect size of fun_nvme_ns_mgmt");

/* sel field of ns_mgmt command */
enum {
	FUN_NVME_NS_ATTACH_SEL_ATTACH = 0,
	FUN_NVME_NS_ATTACH_SEL_DETACH = 1,
};

struct __attribute__ ((packed)) fun_nvme_ctrlr_list {
	uint16_t num_ctrlrs;
	uint16_t ctrlrids[];
};

struct __attribute__ ((packed)) fun_nvme_ns_attach {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t sel:4;
	uint32_t res1:28;
	uint32_t cdw11;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_ns_attach) == 64,
	"Incorrect size of fun_nvme_ns_attach");

struct __attribute__ ((packed)) fun_nvme_abort {
	struct fun_nvme_cmd_cmn cmn;
	/* Submission queue ID */
	uint32_t sqid:16;
	uint32_t cmdid:16;
	uint32_t cdw11;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_abort) == 64,
	"Incorrect size of fun_nvme_abort");

/**
 * fun_nvme_vs_hndlr id enumeration
 * Shared with the control plane code
 */
enum {
	FUN_NVME_VS_API_FLVM_HNDLR_ID = 0,
	FUN_NVME_VS_API_RCNVME_HNDLR_ID = 1,
};

/** rcnvme vs_api subop enum */
enum {
	FUN_NVME_VS_API_SUBOP_RCNVME_TEST = 255
};

enum {
	FUN_NVME_NO_XFER = 0,
	FUN_NVME_H2C_XFER = 1,
	FUN_NVME_C2H_XFER = 2,
	FUN_NVME_BIDIR_XFER = 3,
};

struct __attribute__ ((packed)) fun_nvme_vs_api {
	struct fun_nvme_cmd_cmn cmn;
	uint64_t arg1;
	uint64_t arg2;
	uint64_t arg3;
};

static_assert(sizeof(struct fun_nvme_vs_api) == 64,
	"Incorrect size of fun_nvme_vs_rw");

struct fun_nvme_vs_api_data {
	uint8_t ver:4;
	uint8_t dir:2;
	uint8_t rsvd:2;
	uint8_t subop;
	uint32_t arg0;
	uint64_t arg1;
	uint64_t arg2;
	uint64_t arg3;
};

static_assert(sizeof(struct fun_nvme_vs_api_data) <= 64,
	"Incorrect size of fun_nvme_vs_rw");


/****************************/
/* I/O Commands definitions.*/
/****************************/

struct __attribute__ ((packed)) fun_nvme_rw {
	struct fun_nvme_cmd_cmn cmn;
	/* Start LBA*/
	uint64_t slba;

	/* Number of LBAs -- zero based */
	uint16_t nlb:16;

	uint16_t res1:10;
	/* CDW12[26-29] Protection Information Field */
	uint16_t prinfo:4;
	/* CDW12[30] Force Unit Access */
	uint16_t fua:1;
	/* CDW12[31] Limited Entry */
	uint16_t lr:1;

	/* CDW13[0-7] DataSet Management */
	uint8_t dsm;
	uint8_t res3[3];

	/* Initial Logical Block Reference Tag */
	uint32_t ilbrt;
	/* Logical Block Application Tag */
	uint32_t lbat:16;
	/* Logical Block Application Tag Mask */
	uint32_t lbatm:16;
};

static_assert(sizeof(struct fun_nvme_rw) == 64,
	"Incorrect size of fun_nvme_rw");

struct __attribute__ ((packed)) fun_nvme_fmt_nvm {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t cdw10;
	uint32_t cdw11;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_fmt_nvm) == 64,
	"Incorrect size of fun_nvme_fmt_nvm");

struct __attribute__ ((packed)) fun_nvme_flush {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t cdw10;
	uint32_t cdw11;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_flush) == 64,
	"Incorrect size of fun_nvme_flush");

struct __attribute__ ((packed)) fun_nvme_dsm {
	struct fun_nvme_cmd_cmn cmn;
	uint32_t cdw10;
	uint32_t cdw11;
	uint32_t cdw12;
	uint32_t cdw13;
	uint32_t cdw14;
	uint32_t cdw15;
};

static_assert(sizeof(struct fun_nvme_dsm) == 64,
	"Incorrect size of fun_nvme_dsm");


/******** Completion Queue Entry ********/

struct __attribute__ ((packed)) fun_nvme_status {

	union {

		uint16_t val16;

		struct {

			uint16_t p:1;		/* phase tag */
			uint16_t sc:8;		/* status code */
			uint16_t sct:3;		/* status code type */
			uint16_t rsvd2:2;
			uint16_t m:1;		/* more */
			uint16_t dnr:1;		/* do not retry */
		};
	};
};

static_assert(sizeof(struct fun_nvme_status) == 2, "Incorrect size");

enum {
	FUN_NVME_CQE_ASYNC_EVT_ERROR = 0,
	FUN_NVME_CQE_ASYNC_EVT_SMART = 1,
	FUN_NVME_CQE_ASYNC_EVT_NOTICE = 2,
	FUN_NVME_CQE_ASYNC_EVT_IO_CS_STS = 6,
	FUN_NVME_CQE_ASYNC_EVT_IO_VS = 7,
};

enum {
	FUN_NVME_CQE_NS_ATTR_CHANGED = 0,
	FUN_NVME_CQE_FW_ACT_STARTING = 1,
};

/*
 * Completion queue entry
 */
struct __attribute__ ((packed)) fun_nvme_cpl {
	/** dword 0 -- command-specific */
	union {
		uint32_t cdw0;
		struct {
			uint16_t nsqa;
			uint16_t ncqa;
		};
		struct {
			uint8_t async_evt_type:3;
			uint8_t rsvd1:5;
			uint8_t async_evt_info;
			uint8_t log_page_id;
			uint8_t rsvd2;
		};
	};
	/** dword 1 */
	uint32_t rsvd3;
	/** dword 2 -- submission queue head && id */
	uint16_t sqhd;
	uint16_t sqid;
	/** dword 3 -- command identifier */
	uint16_t cid;
	struct fun_nvme_status status;
};

#define NVME_CPL_SIZE (sizeof(struct fun_nvme_cpl))

static_assert(NVME_CPL_SIZE == 16, "Incorrect size");

/** command sets supported (cap_css and cc_css) */
enum {
	FUN_NVME_CSS_NVM = 1 << 0,
};

/**
 * Data or Meta data buffer
 */
struct fun_nvme_buffer {

	uint8_t *buf;

	size_t size;
};

/**
 * nvme operation type
 * Keeping same as the NVME opcodes so there is no confusion
 */
enum fun_nvme_op_type {

	FUN_NVME_OP_WRITE = 1,

	FUN_NVME_OP_READ = 2
};

/*  NS Create Vendor specific data */
struct fun_nvme_ns_create_vs_data {
	uint8_t volume_type;
	uint64_t pvol_id[8];
	uint8_t num_pvols;
};

/**
 * Stringify the given NVMe operation type
 */
#define FUN_NVME_OP_STRING(type) \
	(((type) == FUN_NVME_OP_READ) ? "Read" : "Write")

char const *fun_nvme_idtfy_cns_str(uint8_t cns);

void fun_nvme_print_io_cmd(struct fun_nvme_cmd *cmd);

void fun_nvme_print_adm_cmd(struct fun_nvme_cmd *cmd);

void fun_nvme_print_cpl(struct fun_nvme_cpl *cpl);

void fun_nvme_create_sq_cmd(struct fun_nvme_create_sq *cmd, uint64_t addr,
	uint16_t qid, uint16_t qsize, uint16_t cqid, uint16_t cid);

void fun_nvme_create_cq_cmd(struct fun_nvme_create_cq *cmd, uint64_t addr,
	uint16_t qid, uint16_t qsize, uint16_t cid);

void fun_nvme_delete_sq_cmd(struct fun_nvme_del_sq *cmd,
	uint16_t qid, uint16_t cid);

void fun_nvme_delete_cq_cmd(struct fun_nvme_del_cq *cmd,
	uint16_t qid, uint16_t cid);

void fun_nvme_idtfy_cmd(struct fun_nvme_idtfy *cmd, uint64_t addr,
	uint8_t cns, uint32_t nsid, uint16_t cid);

int fun_nvme_nsid_zero_chk(uint32_t nsid,
	struct fun_nvme_status *status);

int fun_nvme_nsid_valid_chk(uint32_t nsid, uint32_t num_ns,
	struct fun_nvme_status *status);

int fun_nvme_nsid_special_chk(uint32_t nsid, struct fun_nvme_status *status);

int fun_nvme_qid_chk(uint16_t qid, uint16_t max_qid,
	struct fun_nvme_status *status);

// check if qsize requested is supported by controller
int fun_nvme_qsize_chk(uint16_t qsize, uint16_t mqes,
	struct fun_nvme_status *status);

// check if non-contig queue is requested while controller does not support
int fun_nvme_pc_chk(uint8_t pc, bool cqr, struct fun_nvme_status *status);

int fun_nvme_prp1_chk(uint64_t prp1, struct fun_nvme_status *status);

int fun_nvme_ctrlrid_chk(uint16_t ctrlr_id, struct fun_nvme_status *status);

int fun_nvme_prp1_psdt_chk(uint64_t prp1, uint8_t psdt,
	struct fun_nvme_status *status);

int fun_nvme_sq_chk(struct fun_nvme_create_sq *cmd, uint16_t max_qid,
	bool cqr, uint16_t mqes, uint32_t cc_iosqes, uint8_t ctrlr_sqes,
	struct fun_nvme_status *status);

int fun_nvme_cq_chk(struct fun_nvme_create_cq *cmd, uint16_t max_qid,
	bool cqr, uint16_t mqes, uint32_t cc_iocqes, uint8_t ctrlr_cqes,
	struct fun_nvme_status *status);

int fun_nvme_idtfy_chk(struct fun_nvme_idtfy *cmd,
	uint32_t num_ns, uint16_t ctrlr_id, struct fun_nvme_status *status);

int fun_nvme_ns_mgmt_chk(struct fun_nvme_ns_data *ns_data, uint64_t max_ns_size,
	uint64_t max_ns_cap, struct fun_nvme_lbaf *lbafs,
	uint8_t dpc, uint8_t nmic, struct fun_nvme_status *status);

int fun_nvme_ns_attach_chk(struct fun_nvme_ns_attach *cmd,
	uint32_t num_ns, struct fun_nvme_status *status);

int fun_nvme_ctrlr_list_chk(struct fun_nvme_ctrlr_list *ctrlr_list,
	struct fun_nvme_status *status);

void fun_nvme_set_feat_cmd(struct fun_nvme_feat *cmd,
	uint8_t id, uint16_t num_queues, uint16_t cid);

void fun_nvme_ns_mgmt_create_cmd(struct fun_nvme_ns_mgmt *cmd,
	uint64_t addr, uint16_t cid);

void fun_nvme_ns_mgmt_delete_cmd(struct fun_nvme_ns_mgmt *cmd,
	uint32_t nsid, uint16_t cid);

void fun_nvme_ns_attach_cmd(struct fun_nvme_ns_attach *cmd,
	uint64_t addr, uint32_t nsid, uint16_t cid);

void fun_nvme_ns_detach_cmd(struct fun_nvme_ns_attach *cmd,
	uint64_t addr, uint32_t nsid, uint16_t cid);

void fun_nvme_vs_api_cmd(struct fun_nvme_vs_api *cmd, uint64_t addr,
	uint8_t vs_hndlr_id, uint8_t dir, uint8_t subop, uint16_t cid);

/**
 * return true if there is controller(F1) to host data transfer
 */
bool fun_nvme_is_f2h_xfer(uint8_t dir);

/**
 * return true if there is host to controller(F1) data transfer
 */
bool fun_nvme_is_h2f_xfer(uint8_t dir);

/**
 * returns -1 if the sgl is not valid
 */
int nvme_sgl_chk(struct fun_nvme_cmd_cmn *cmn);

static inline int32_t setup_prp_list(uint64_t data, uint32_t nprps,
	uint32_t page_shift, uint64_t *prp_list0, uint64_t *prp_list1)
{
	assert(prp_list0);
	assert(page_shift <= 31);

	uint32_t cur_seg;
	uint32_t nprps0;
	uint32_t nprps1 = 0;
	uint32_t page_size = 1 << page_shift;
	uint64_t prp2_off;

	if (prp_list0 == NULL) {

		SYSLOG(NULL, DEBUG, FN_NVME,
			"PRP list pointer cannot be NULL");
		return -1;
	}

	if (nprps > (page_size >> FUN_NVME_PRPE_SHIFT)) {

		SYSLOG(NULL, DEBUG, FN_NVME,
			"Invalid number of PRPs %d", nprps);
		return -1;
	}

	if (((uint64_t)prp_list0 & FUN_NVME_PRPE_MASK) != 0) {

		SYSLOG(NULL, DEBUG, FN_NVME,
			"Invalid prp_list ptr (%p) alignment",
			prp_list0);
		return -1;
	}

	prp2_off = (uint64_t)prp_list0 & FUN_NVME_PAGE_MASK;

	nprps0 = (FUN_NVME_PAGE_SIZE - prp2_off) / FUN_NVME_PRPE_SIZE;

	if (nprps > nprps0) {

		nprps0 = nprps0 - 1;

		nprps1 = nprps - nprps0;
	} else {

		nprps0 = nprps;
	}

	for (cur_seg = 0; cur_seg < nprps0;
		cur_seg++, data += page_size) {

		prp_list0[cur_seg] = data;

		SYSLOG(NULL, DEBUG, FN_NVME,
			"setting prp_list0[%d] to %p",
			cur_seg, (void *)prp_list0[cur_seg]);
	}

	if (nprps1) {

		if (prp_list1 == NULL) {

			SYSLOG(NULL, DEBUG, FN_NVME,
				"PRP list pointer cannot be NULL");
			return -1;
		}

		if (((uint64_t)prp_list1 & (page_size - 1)) != 0) {

			SYSLOG(NULL, DEBUG, FN_NVME,
				"2nd PRP list ptr shall be page aligned");
			return -1;
		}

		prp_list0[cur_seg] = (uint64_t)prp_list1;

		for (cur_seg = 0; cur_seg < nprps1;
			cur_seg++, data += page_size) {

			prp_list1[cur_seg] = data;

			SYSLOG(NULL, DEBUG, FN_NVME,
				"setting prp_list1[%d] to %p",
				cur_seg, (void *)prp_list1[cur_seg]);
		}
	}

	return 0;
}

/*
 * Get number of page_size segments for given unalignment and len
 */
static inline int fun_nvme_nprps_u(uint32_t unaligned, uint64_t len,
	uint32_t page_shift, uint32_t page_size)
{
	uint32_t nprps = len >> page_shift;
	uint32_t modulo = len & (page_size - 1);

	if (modulo || unaligned) {
		nprps += 1 + ((modulo + unaligned - 1) >> page_shift);
	}

	return nprps;
}

/*
 * Get number of page_size segments for given data and len while
 * also taking unalignment of data into consideration.
 */
static inline int fun_nvme_nprps(uint64_t data, uint64_t len,
	uint32_t page_shift, uint32_t page_size)
{
	uint32_t unaligned = data & (page_size - 1);

	return fun_nvme_nprps_u(unaligned, len, page_shift, page_size);
}

/*
 * Build PRP list for given physically contiguous payload buffer.
 */
static inline int32_t
build_prp_list(struct fun_nvme_rw *cmd, uint64_t data, uint64_t len,
	uint32_t page_shift, uint64_t *prp_list0, uint64_t *prp_list1)
{
	assert(cmd && data && len && page_shift && "invalid input(s)");

	int32_t rc = 0;
	uint32_t page_size = 1 << page_shift;
	uint32_t unaligned = data & (page_size - 1);
	uint64_t prp2_addr = data + (page_size - unaligned);
	uint32_t nprps = fun_nvme_nprps_u(unaligned, len,
		page_shift, page_size);

	SYSLOG(NULL, DEBUG, FN_NVME, "nprps = %d\n", nprps);

	cmd->cmn.prp1 = data;
	SYSLOG(NULL, DEBUG, FN_NVME,
		"set prp1 to %p\n", (uint64_t *)data);

	if (nprps == 2) {

		cmd->cmn.prp2 = prp2_addr;

		SYSLOG(NULL, DEBUG, FN_NVME, "set prp2 to %p\n",
			(void *)cmd->cmn.prp2);
	} else if (nprps > 2) {

		rc = setup_prp_list(prp2_addr, nprps - 1, page_shift,
			prp_list0, prp_list1);

		cmd->cmn.prp2 = (uint64_t)prp_list0;

		SYSLOG(NULL, DEBUG, FN_NVME,
			"setting prp2 to prp_list_p %p\n", prp_list0);
	} else {
		cmd->cmn.prp2 = 0;
	}

	return rc;
}

static inline void
nvme_set_sgl_unkeyed(struct fun_nvme_sgl_desc *sgl,
	uint64_t addr, size_t len)
{
	sgl->unkeyed.type = FUN_NVME_SGL_TYPE_DATA_BLOCK;
	sgl->addr = addr;
	sgl->unkeyed.len = len;
}

static inline void
nvme_dev_err(struct fun_nvme_status *status)
{
	status->sct = FUN_NVME_SCT_GEN;
	status->sc = FUN_NVME_SC_INT_DEV_ERR;
}

/**
 * For value to string mapping
 */
struct fun_value_str {
	uint16_t value;
	const char *str;
};

/**
 * Get the string associated with given value
 */
char const *fun_get_str(struct fun_value_str const *strings,
	uint16_t value);
