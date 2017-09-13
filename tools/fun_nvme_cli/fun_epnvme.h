/*
 *	epnvme.h: End Point NVMe API
 *
 *	Created November 2016 by pratapa.vaka@fungible.com
 *	Copyright © 2016 Fungible. All rights reserved.
 */

#pragma once

extern uint64_t nvme_adm_cmd_set[];

// epnvme default values 
#define EPNVME_LBA_SHIFT 12
#define EPNVME_LBA_SIZE (1 << (EPNVME_LBA_SHIFT))
#define EPNVME_LBA_MASK ((EPNVME_LBA_SIZE) - 1)
#define EPNVME_NLB_TO_SIZE(nlb) \
	(((uint64_t)(nlb + 1)) << (EPNVME_LBA_SHIFT))
#define EPNVME_SIZE_TO_NLB(size) \
	((size >> (EPNVME_LBA_SHIFT)) - 1)

//#define EPNVME_TNVMCAP (128ULL << 40)
#define EPNVME_TNVMCAP (1ULL << 30)
//#define EPNVME_UNVMCAP (1ULL << 40)
#define EPNVME_UNVMCAP (1ULL << 30)
#define EPNVME_AWUN ((64 * 1024) >> (EPNVME_LBA_SHIFT))
#define EPNVME_AWUPF ((64 * 1024) >> (EPNVME_LBA_SHIFT))
#define EPNVME_ACWU ((64 * 1024) >> (EPNVME_LBA_SHIFT))
#define EPNVME_SGLS ((FUN_NVME_SGLS_NVM) | \
		     (FUN_NVME_SGLS_KEYED_DBD) | \
		     (FUN_NVME_SGLS_BBD) | \
		     (FUN_NVME_SGLS_LARGE_LEN) | \
		     (FUN_NVME_SGLS_MPTR_AS_SGLSEG) | \
		     (FUN_NVME_SGLS_ADDR_AS_OFFSET))

//#define EPNVME_NSZE ((16ULL << 30) / (EPNVME_LBA_SIZE))
#define EPNVME_NSZE ((1ULL << 30) >> (EPNVME_LBA_SHIFT))
//#define EPNVME_NCAP ((16ULL << 30) / (EPNVME_LBA_SIZE))
#define EPNVME_NCAP ((1ULL << 30) >> (EPNVME_LBA_SHIFT))
#define EPNVME_NVMCAP_NS (EPNVME_NSZE)
#define FUN_OUI 0xDAD // 24-bit OUI
#define EPNVME_EUI64 0
#define EPNVME_NGUID_EXT_ID (0xABCDEULL)
#define EPNVME_NGUID_HI (((EPNVME_NGUID_EXT_ID) << 24) | (FUN_OUI))
#define EPNVME_NGUID_LO (0xAAAABBBBULL)

#define EPNVME_MAX_NSZE (1 << 40)

#define EPNVME_MAX_QID 128

/* Length of key1 and key2 */
#define EPNVME_AES_KEY_LEN 16
#define EPNVME_XTS_KEY_LEN (2 * (EPNVME_AES_KEY_LEN))

#define EPNVME_MDTS 4
#define EPNVME_MAX_IO_SIZE (1 << (12 + (EPNVME_MDTS)))
#define EPNVME_MAX_IO_PRPS (((EPNVME_MAX_IO_SIZE)/(FUN_NVME_PAGE_SIZE)) + 1)

/** We support only one page for PRP list */
#define EPNVME_MAX_PRPS ((FUN_NVME_PRPS_PER_PAGE) + 1)

static_assert(EPNVME_MAX_IO_PRPS <= EPNVME_MAX_PRPS,
	"MAX_IO_PRPS cannot be greater than MAX_PRPS");

#define FUN_NVME_NS_ACTIVE_MAX_REPORTED 1024

#define FUN_VID	0x1DAD

enum epnvme_consts {
	EPNVME_DESC_SIZE = 64,
	EPNVME_DESC_FETCH_MAX = (1024 / EPNVME_DESC_SIZE),
};

struct epnvme_params {
	//error info
	uint64_t dma_address;
	uint32_t dma_size;
};

struct __attribute__ ((packed)) fun_nvme_vs_spl_cmn {
	// cdw0 - opcode, fused operation, psdt, and cmd id
	uint16_t opcode:8;
	uint16_t fuse:2;
	uint16_t rsvd0:4;
	uint16_t psdt:2;
	uint16_t cid;

	// cdw1
	uint8_t version;
	uint8_t subop; // sub opcode
	uint16_t rsvd;
};

// allows upto 14 dwords passed by user
struct __attribute__ ((packed)) fun_nvme_vs_spl {
	struct fun_nvme_vs_spl_cmn cmn;
	uint32_t cdw[14];
};

static_assert(sizeof(struct fun_nvme_vs_spl) == 64,
	"Incorrect size of fun_nvme_vs_spl");


uint32_t epnvme_nsid_avail(struct bitmap *bm, uint32_t nsid);

// FIXME: use generated fn if there is one. else move this
void fun_setup_bind_cmd(struct fun_admin_bind_cmd *bind_cmd,
	uint16_t sqid, uint32_t nsid);

// FIXME: use generated fn if there is one. else move this
void fun_setup_sq_alloc(struct fun_admin_sq_alloc *sq_alloc, uint32_t sqid,
	uint32_t cqid, uint16_t qsize, uint64_t addr, uint8_t pc,
	uint8_t qprio, uint32_t cc_iosqes);

int epnvme_init(uint32_t huid, uint32_t ctlid, uint32_t fnid);
int epnvme_reset(void);

