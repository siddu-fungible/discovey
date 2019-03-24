/**
 * Copyright © 2017 Fungible. All rights reserved.
 */

/**
 * @file fabrics.h
 * @author Pratapa Vaka (pratapa.vaka@fungible.com)
 */

#pragma once

#define FABRICS_TR_SVCID_MAX_LEN (32)
#define FABRICS_TR_ADDR_MAX_LEN (256)
#define NQN_MAX_LENGTH (256)

/**
 * Enumeration of fabrics command type
 */
enum fabrics_cmd_type {

	FABRICS_PROPERTY_SET = 0x00,

	FABRICS_CONNECT = 0x01,

	FABRICS_PROPERTY_GET = 0x04,

	FABRICS_AUTH_SEND = 0x05,

	FABRICS_AUTH_RECV = 0x06,

	FABRICS_VS_START = 0xC0,
};

struct __attribute__ ((packed)) fabrics_cmd_cmn {

	/** Opcode */
	uint8_t opcode;

	uint8_t rsvd1;

	/** Command Identifier */
	uint16_t cid;

	/** Fabrics Command Type */
	uint8_t fctype;
};

struct __attribute__ ((packed)) fabrics_cmd{

	struct fabrics_cmd_cmn cmn;

	uint8_t rsvd1[59];
};

#define FABRICS_CMD_SIZE (sizeof(struct fabrics_cmd))

static_assert(FABRICS_CMD_SIZE == 64,
	"Incorrect size of fabrics_cmd");

struct __attribute__ ((packed)) fabrics_capsule_cmd {

	struct fabrics_cmd_cmn cmn;

	uint8_t rsvd2[35];

	uint8_t fabrics_specific[24];
};

struct __attribute__ ((packed)) fabrics_auth_recv_cmd {

	struct fabrics_cmd_cmn cmn;

	uint8_t rsvd1[19];

	struct fun_nvme_sgl_desc sgl1;

	uint8_t rsvd2;

	uint8_t spsp0;

	uint8_t spsp1;

	uint8_t secp;

	uint32_t al;

	uint8_t rsvd4[16];
};

struct __attribute__ ((packed)) fabrics_auth_send_cmd {

	struct fabrics_cmd_cmn cmn;

	uint8_t rsvd1[19];

	struct fun_nvme_sgl_desc sgl1;

	uint8_t rsvd2;

	uint8_t spsp0;

	uint8_t spsp1;

	uint8_t secp;

	uint32_t tl;

	uint8_t rsvd4[16];
};

struct __attribute__ ((packed)) fabrics_connect_data {

	/** Host Identifier */
	uint8_t hostid[16];

	/** Controller Identifier */
	uint16_t cntlid;

	uint8_t rsvd1[238];

	/** NVMe Sub System NQN */
	uint8_t subnqn[256];

	/** Host NQN */
	uint8_t hostnqn[256];

	uint8_t rsvd2[256];
};

struct __attribute__ ((packed)) fabrics_connect_cmd {

	struct fabrics_cmd_cmn cmn;

	uint8_t rsvd1[19];

	struct fun_nvme_sgl_desc sgl;

	/** Record format */
	uint16_t recfmt;

	/** Queue Identifier - 0: Admin; else IO */
	uint16_t qid;

	/** Submission Queue Size */
	uint16_t sqsize;

	/** Connect Attributes */
	uint8_t cattr;

	uint8_t rsvd2;

	/** Keep Alive Time Out */
	uint32_t kato;

	uint8_t rsvd4[12];
};

struct __attribute__ ((packed)) fabrics_resp {

	/** Fabrics response type specific field */
	uint64_t cmd_specific;

	/** Current SQ head pointer */
	uint16_t sqhd;

	uint16_t rsvd2;

	/** Command identifier of the command being completed */
	uint16_t cid;

	/** Status of the command being completed */
	struct fun_nvme_status status;
};

#define FABRICS_RESP_SIZE (sizeof(struct fabrics_resp))

static_assert(FABRICS_RESP_SIZE == 16,
	"Incorrect size of fabrics_resp");

struct __attribute__ ((packed)) fabrics_connect_resp {

	union {

		struct {

			/** Controller id allocated */
			uint16_t cntlid;

			/** In-band authentication requirement */
			uint16_t authreq;
		};

		struct {

			/** Invalid Parameter Offset */
			uint16_t ipo;

			/** Attributes of Invalid Parameter Offset */
			/**
			 * If bit-0 is 0, invalid param offset is
			 *  from start of SQE. Else, it is from
			 *  start of data.
			 */
			uint8_t iattr;

			uint8_t rsvd1;
		};

		uint32_t raw;
	};

	uint32_t rsvd2;

	/** Submission Queue Head Pointer */
	uint16_t sqhd;

	uint16_t rsvd3;

	/* Command Identifier */
	uint16_t cid;

	struct fun_nvme_status status;
};

/**
 * Enumeration of attrib size for prop set/get
 */
enum fabrics_prop_size_type {

	FABRICS_PROPERTY_ATTRIB_SIZE_4 = 0,

	FABRICS_PROPERTY_ATTRIB_SIZE_8 = 1,
};

struct __attribute__ ((packed)) fabrics_prop_get_cmd {

	struct fabrics_cmd_cmn cmn;

	uint8_t rsvd1[35];

	struct {

		uint8_t size:2;

		uint8_t rsvd2:6;
	} attrib;

	uint8_t rsvd3[3];

	uint32_t offset;

	uint8_t rsvd4[16];
};

struct fabrics_status {

	uint16_t p:1;

	/** Status Code */
	uint16_t sc:8;

	/** Status Code Type */
	uint16_t sct:3;

	uint16_t rsvd1:2;

	uint16_t m:1;

	/** Do not Retry */
	uint16_t dnr:1;
};

struct __attribute__ ((packed)) fabrics_prop_get_resp {

	union {

		uint64_t u64;

		struct {

			uint32_t low;

			uint32_t high;
		};
	} val;

	/** Submission Queue Head */
	uint16_t sqhd;

	uint16_t rsvd1;

	/* Command Identifier */
	uint16_t cid;

	struct fabrics_status status;
};

struct __attribute__ ((packed)) fabrics_prop_set_cmd {

	struct fabrics_cmd_cmn cmn;

	uint8_t rsvd1[35];

	struct {

		uint8_t size:2;

		uint8_t rsvd2:6;
	} attrib;

	uint8_t rsvd3[3];

	/* Offset */
	uint32_t offset;

	union {

		uint64_t u64;

		struct {

			uint32_t low;

			uint32_t high;
		};
	} val;

	uint8_t rsvd4[8];
};

/**
 * NVMe-oF status code
 */
enum fabrics_status_code {

	FABRICS_SC_CONN_INCOMPAT_FMT = 0x80,

	FABRICS_SC_CONN_CTRLR_BUSY = 0x81,

	FABRICS_SC_CONN_INVAL_PARAMS = 0x82,

	FABRICS_SC_CONN_RESTART_DISC = 0x83,

	FABRICS_SC_CONN_INVAL_HOST = 0x84,

	FABRICS_SC_DISC_LOG_RESTART = 0x90,

	FABRICS_SC_AUTH_REQD = 0x91,
};

/**
 * Indicate whether connections need fabric secure channel
 */
enum fabrics_secure_channel {

	SECURE_CHANNEL_NOT_SPECIFIED = 0x0,

	SECURE_CHANNEL_REQUIRED = 0x1,

	SECURE_CHANNEL_NOT_REQUIRED = 0x2,
};

/**
 * NVMe-oF transport type
 */
enum fabrics_transport_type {

	/** RDMA transport */
	FABRICS_TRANSPORT_RDMA = 1,

	/** TCP transport */
	/** FIXME: Change this when NVMe-oF has TCP */
	FABRICS_TRANSPORT_TCP = 3,

	/** Vendor Specific RDS Transport */
	FABRICS_TRANSPORT_RDS = 253,

	/** Intra-host transort - For use by host software */
	FABRICS_TRANSPORT_LOOPBACK = 254,
};

/**
 * NVMe-oF Address family
 */
enum fabrics_addr_family {

	/** IPv4 address family */
	FABRICS_ADDR_FAMILY_AF_INET_IPV4 = 1,

	/** IPv6 address family */
	FABRICS_ADDR_FAMILY_AF_INET_IPV6 = 2,

	/** InfiniBand address family */
	FABRICS_ADDR_FAMILY_AF_INET_IB = 3,

	/** Intra-host transort - For use by host software */
	FABRICS_ADDR_FAMILY_LOOPBACK = 254,
};

/**
 * NVMe-oF Subsystem Type
 */
enum fabrics_subtype {

	/** NVM subsystem */
	FABRICS_SUBTYPE_NVM = 0x0,

	/** Discovery subsystem */
	FABRICS_SUBTYPE_DISCOVERY = 0x1,
};

struct fabrics_subsystem {

	uint32_t id;

	char subnqn[NQN_MAX_LENGTH];

	enum fabrics_subtype subtype;

	TAILQ_HEAD(, fabrics_session) sessions;

	uint32_t num_hosts;

	TAILQ_HEAD(, fabrics_host) hosts;

	TAILQ_ENTRY(fabrics_subsytem) entries;
};

/**
 * NVMe-oF Subsystem Type
 * @note: var names are per spec
 */
struct fabrics_disc_log_page_entry {

	/** enum fabrics_transport_type */
	uint8_t trtype;

	/** enum fabrics_addr_family */
	uint8_t adrfam;

	/** enum fabrics_subsytem_type */
	uint8_t subtype;

	/** transport requirements */
	struct {

		/** enum fabrics_secure_channel */
		uint8_t secure_channel:2;

		uint8_t rsvd:6;
	} treq;

	/** NVM subsystem port */
	uint16_t portid;

	/** NVM controller identifier */
	uint16_t cntlid;

	/** Maximum size of Admin Submission Queue */
	uint16_t asqsz;

	uint8_t rsvd1[22];

	/** NVMe Transport service identifier as an ASCII string */
	char trsvcid[FABRICS_TR_SVCID_MAX_LEN];

	uint8_t rsvd2[192];

	/**
	 * NVMe Subsystem Qualified Name that uniquely identifies
	 * the NVM subsystem
	 */
	char subnqn[256];

	/** Transport address as an ASCII string */
	char traddr[FABRICS_TR_ADDR_MAX_LEN];

	/**
	 * Transport Specific Address Subtype: Specifies NVMe Transport
	 * specific information about the address.
	 */
	uint8_t tsas[256];
};

struct disc_log_page {

	uint64_t gen_ctr;

	uint64_t num_rec;

	uint16_t rec_fmt;

	uint8_t rsvd1[1006];

	struct fabrics_disc_log_page_entry entries[0];
};
