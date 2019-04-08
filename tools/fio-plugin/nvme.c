/*
 *  funos/nvme.c
 *
 * Common NVMe functions
 *
 *  Created by Pratapa Vaka on 2016-09-30.
 *  Copyright © 2016 Fungible. All rights reserved.
 */

#include "Integration/tools/fio-plugin/fun_utils.h"
#include "Integration/tools/fio-plugin/types.h"
#include <stdint.h>
#include <string.h>
#include <stdio.h>

//#include <services/services.h>

#include "nvme.h"

static const struct fun_value_str io_opcode[] = {
	{FUN_NVME_WRITE, "WRITE"},
	{FUN_NVME_READ, "READ"},
	{FUN_NVME_FLUSH, "FLUSH"},
	{0xFFFF, "UNKNOWN IO COMMAND"}
};

static const struct fun_value_str admin_opcode[] = {
	{FUN_NVME_DEL_SQ, "DEL_SQ"},
	{FUN_NVME_CREATE_SQ, "CREATE_SQ"},
	{FUN_NVME_GET_LOG, "GET_LOG"},
	{FUN_NVME_DEL_CQ, "DEL_CQ"},
	{FUN_NVME_CREATE_CQ, "CREATE_CQ"},
	{FUN_NVME_IDTFY, "IDTFY"},
	{FUN_NVME_ABORT, "ABORT"},
	{FUN_NVME_SET_FEAT, "SET_FEAT"},
	{FUN_NVME_GET_FEAT, "GET_FEAT"},
	{FUN_NVME_ASYNC_REQ, "ASYNC_REQ"},
	{FUN_NVME_NS_MGMT, "NS_MGMT"},
	{FUN_NVME_FW_COMMIT, "FW_COMMIT"},
	{FUN_NVME_FW_DOWNLOAD, "FW_DOWNLOAD"},
	{FUN_NVME_NS_ATTACH, "NS_ATTACH"},
	{FUN_NVME_KEEP_ALIVE, "KEEP_ALIVE"},
	{FUN_NVME_FABRICS, "FABRICS"},
	{FUN_NVME_FMT_NVM, "FMT_NVM"},
	{FUN_NVME_SEC_SEND, "SEC_SEND"},
	{FUN_NVME_SEC_RECV, "SEC_RECV"},
	{FUN_NVME_SANITIZE, "SANITIZE"},
	{FUN_NVME_VS_API_NO_DATA, "VS_API_NO_DATA"},
	{FUN_NVME_VS_API_SEND, "VS_API_SEND"},
	{FUN_NVME_VS_API_RECV, "VS_API_RECV"},
	{FUN_NVME_VS_API_BIDIR, "VS_API_BIDIR"},
	{0xFFFF, "UNKNOWN ADMIN COMMAND"}
};

static const struct fun_value_str generic_status[] = {
	{FUN_NVME_SC_SUCCESS, "SUCCESS"},
	{FUN_NVME_SC_INVAL_OP, "INVAL_OP"},
	{FUN_NVME_SC_INVAL_FLD, "INVAL_FLD"},
	{FUN_NVME_SC_CMD_ID_CONFLICT, "CMD_ID_CONFLICT"},
	{FUN_NVME_SC_DATA_XFER_ERR, "DATA_XFER_ERR"},
	{FUN_NVME_SC_ABORT_PWR_LOSS, "ABORT_PWR_LOSS"},
	{FUN_NVME_SC_INT_DEV_ERR, "INT_DEV_ERR"},
	{FUN_NVME_SC_ABORT_BY_REQ, "ABORT_BY_REQ"},
	{FUN_NVME_SC_ABORT_SQ_DEL, "ABORT_SQ_DEL"},
	{FUN_NVME_SC_ABORT_FAIL_FUSED, "ABORT_FAIL_FUSED"},
	{FUN_NVME_SC_ABORT_MISS_FUSED, "ABORT_MISS_FUSED"},
	{FUN_NVME_SC_INVAL_NS_OR_FMT, "INVA_ NS_OR_FMT"},
	{FUN_NVME_SC_CMD_SEQ_ERR, "CMD_SEQ_ERR"},
	{FUN_NVME_SC_INVAL_SGL_SEG_DESC, "INVAL_SGL_SEG_DESC"},
	{FUN_NVME_SC_INVAL_NUM_SGL_DESCS, "INVAL_NU_SGL_DESCS"},
	{FUN_NVME_SC_INVAL_DATA_SGL_LEN, "INVAL_DATA_SGL_LEN"},
	{FUN_NVME_SC_INVAL_META_SGL_LEN, "INVAL_META_SGL_LEN"},
	{FUN_NVME_SC_INVAL_SGL_DESC_TYPE, "INVAL_SGL_DES_TYPE"},
	{FUN_NVME_SC_INVAL_CTRLR_MEM_BUF, "INVAL_CTRLR_MEM_BUF"},
	{FUN_NVME_SC_INVAL_PRP_OFF, "INVAL_PRP_OFF"},
	{FUN_NVME_SC_ATOMIC_WRUNIT_XEDED, "ATOMIC_WRUNIT_XEDED"},
	{FUN_NVME_SC_LBA_OUT_OF_RANGE, "LBA_OUT_OF_RANGE"},
	{FUN_NVME_SC_CAP_XEDED, "CAP_XEDED"},
	{FUN_NVME_SC_NS_NOT_RDY, "NS_NOT_RDY"},
	{FUN_NVME_SC_RSV_CONFLICT, "RSV_CONFLICT"},
	{FUN_NVME_SC_FMT_IN_PROG, "FMT_IN_PROG"},
	{0xFFFF, "RESERVED GENERIC SC"}
};

static const struct fun_value_str cmd_specific_status[] = {
	{FUN_NVME_SC_INVAL_CQ, "INVAL_CQ"},
	{FUN_NVME_SC_INVAL_QID, "INVAL_QID"},
	{FUN_NVME_SC_INVAL_QSIZE, "INVAL_QSIZE"},
	{FUN_NVME_SC_ABORT_LMT_XEDED, "ABORT_LMT_XEDED"},
	{FUN_NVME_SC_ASYNC_LMT_XEDED, "ASYNC_LMT_XEDED"},
	{FUN_NVME_SC_INVAL_FW_SLOT, "INVAL_FW_SLOT"},
	{FUN_NVME_SC_INVAL_FW_IMAGE, "INVAL_FW_IMAGE"},
	{FUN_NVME_SC_INVAL_INTR_VEC, "INVAL_INTR_VEC"},
	{FUN_NVME_SC_INVAL_LOG_PAGE, "INVAL_LOG_PAGE"},
	{FUN_NVME_SC_INVAL_FMT, "INVAL FORMAT"},
	{FUN_NVME_SC_FW_REQ_CONV_RST, "FW_REQ_CONV_RST"},
	{FUN_NVME_SC_INVAL_Q_DEL, "INVAL_Q_DEL"},
	{FUN_NVME_SC_FEAT_ID_UNSAVEABLE, "FEAT_ID_UNSAVEABLE"},
	{FUN_NVME_SC_FEAT_UNCHANGEABLE, "FEAT_UNCHANGEABLE"},
	{FUN_NVME_SC_FEAT_NOT_NS_SPECIFIC, "FEAT_NOT_NS_SPECIFIC"},
	{FUN_NVME_SC_FW_REQ_NVM_RST, "FW_REQ_NVM_RST"},
	{FUN_NVME_SC_FW_REQ_RST, "FW_REQ_RST"},
	{FUN_NVME_SC_FW_REQ_MAXTIME_VIOL, "FW_REQ_MAXTIME_VIOL"},
	{FUN_NVME_SC_FW_ACTI_PROHIBIT, "FW_ACTI_PROHIBIT"},
	{FUN_NVME_SC_OVERLAP_RANGE, "OVERLAP_RANGE"},
	{FUN_NVME_SC_NS_INSUFF_CAP, "NS_INSUFF_CAP"},
	{FUN_NVME_SC_NS_ID_UNAVAIL, "NS_ID_UNAVAIL"},
	{FUN_NVME_SC_NS_ALRDY_ATTACHED, "NS_ALRDY_ATTACHED"},
	{FUN_NVME_SC_NS_IS_PRIVATE, "NS_IS_PRIVATE"},
	{FUN_NVME_SC_NS_NOT_ATTACHED, "NS_NOT_ATTACHED"},
	{FUN_NVME_SC_TP_UNSUPP, "TP_UNSUPP"},
	{FUN_NVME_SC_INVAL_CTRLR_LIST, "INVAL_CTRLR_LIST"},
	{FUN_NVME_SC_CONFLICT_ATTRS, "CONFLICT_ATTRS"},
	{FUN_NVME_SC_INVAL_PR_INFO, "INVAL_PR_INFO"},
	{FUN_NVME_SC_WRITE_TO_RO_PAGE, "WRITE_TO_RO_PAGE"},
	{0xFFFF, "RESERVED COMMAND SPECIFIC SC"}
};

static const struct fun_value_str media_error_status[] = {
	{FUN_NVME_SC_WRITE_FAULTS, "WRITE_FAULTS"},
	{FUN_NVME_SC_UNRECOVERED_RD_ERR, "UNRECOVERED_RD_ERR"},
	{FUN_NVME_SC_GUARD_ERR, "GUARD_ERR"},
	{FUN_NVME_SC_APPTAG_ERR, "APPTAG_ERR"},
	{FUN_NVME_SC_REFTAG_ERR, "REFTAG_ERR"},
	{FUN_NVME_SC_COMP_FAIL, "COMP_FAIL"},
	{FUN_NVME_SC_ACCESS_DENIED, "ACCESS_DENIED"},
	{FUN_NVME_SC_DEALLOC_OR_UNWR_BLOCK, "DEALLOC_OR_UNWR_BLOCK"},
	{0xFFFF, "RESERVED MEDIA ERROR SC"}
};

static const struct fun_value_str idtfy_cns_str[] = {
	{FUN_NVME_IDTFY_NS_ACTIVE_DATA, "NS_ACTIVE_DATA"},
	{FUN_NVME_IDTFY_CTRLR_DATA, "CTRLR_DATA"},
	{FUN_NVME_IDTFY_NS_ACTIVE_LIST, "NS_ACTIVE_LIST"},
	{FUN_NVME_IDTFY_NS_ALLOC_LIST, "NS_ALLOC_LIST"},
	{FUN_NVME_IDTFY_NS_ALLOC_DATA, "NS_ALLOC_DATA"},
	{FUN_NVME_IDTFY_NS_CTRLR_LIST, "NS_CTRLR_LIST"},
	{FUN_NVME_IDTFY_CTRLR_LIST, "CTRLR_LIST"},
	{0xFFFF, "RESERVED CNS"}
};

// Return the string associated with the given value
char const *fun_get_str(struct fun_value_str const *strings,
	uint16_t value)
{
	struct fun_value_str const *entry;

	assert(strings);

	entry = strings;

	while (entry->value != 0xFFFF) {
		if (entry->value == value) {
			return entry->str;
		}
		entry++;
	}

	return entry->str;
}

// Get the status string for given status code
static char const *fun_nvme_get_status_str(uint16_t sct, uint16_t sc)
{
	struct fun_value_str const *entry;

	switch (sct) {
	case FUN_NVME_SCT_GEN:
		entry = generic_status;
		break;
	case FUN_NVME_SCT_CS:
		entry = cmd_specific_status;
		break;
	case FUN_NVME_SCT_ME:
		entry = media_error_status;
		break;
	case FUN_NVME_SCT_VS:
		return "VENDOR SPECIFIC";
	default:
		return "RESERVED";
	}

	return fun_get_str(entry, sc);
}

// Get the identify cns type string
char const *fun_nvme_idtfy_cns_str(uint8_t cns)
{
	struct fun_value_str const *entry = idtfy_cns_str;

	return fun_get_str(entry, cns);
}

void fun_nvme_print_adm_cmd(struct fun_nvme_cmd *cmd)
{
	SYSLOG(NULL, INFO, FN_NVME,
	       "%s (%02x) cid:%d nsid:%d lba:%llu nlb:%d\n,"
	       "prp1 0x%lu prp2 0x%lu",
	       fun_get_str(admin_opcode, cmd->cmn.opcode),
	       cmd->cmn.opcode, cmd->cmn.cid, cmd->cmn.nsid,
	       ((unsigned long long)cmd->cdw11 << 32) + cmd->cdw10,
	       cmd->cdw12 & 0xFFFF, cmd->cmn.prp1, cmd->cmn.prp2);
}

const char *fun_nvme_get_io_str(uint8_t opcode)
{
	return fun_get_str(io_opcode, opcode);
}

void fun_nvme_print_io_cmd(struct fun_nvme_cmd *cmd)
{
	assert(cmd);

	SYSLOG(NULL, INFO, FN_NVME,
	       "%s (%02x) cid:%d nsid:%d lba:%llu nlb:%d\n,"
	       "prp1 0x%lu prp2 0x%lu",
	       fun_nvme_get_io_str(cmd->cmn.opcode),
	       cmd->cmn.opcode, cmd->cmn.cid, cmd->cmn.nsid,
	       ((unsigned long long)cmd->cdw11 << 32) + cmd->cdw10,
	       cmd->cdw12 & 0xFFFF, cmd->cmn.prp1, cmd->cmn.prp2);
}

void fun_nvme_print_cpl(struct fun_nvme_cpl *cpl)
{
	assert(cpl != NULL);

	SYSLOG(NULL, DEBUG, FN_NVME, "%s (%02x/%02x) sqid:%d cid:%d cdw0:%x "
		"sqhd:%04x p:%x m:%x dnr:%x\n",
		fun_nvme_get_status_str(cpl->status.sct, cpl->status.sc),
		cpl->status.sct, cpl->status.sc, cpl->sqid, cpl->cid, cpl->cdw0,
		cpl->sqhd, cpl->status.p, cpl->status.m, cpl->status.dnr);
}

int fun_nvme_nsid_special_chk(uint32_t nsid,
	struct fun_nvme_status *status)
{
	if ((nsid == FUN_NVME_MAX_NSID) || (nsid == FUN_NVME_MAX_NSID - 1)) {
		status->sct = FUN_NVME_SCT_GEN;
		status->sc = FUN_NVME_SC_INVAL_NS_OR_FMT;
		SYSLOG(NULL, ERR, FN_NVME, "" "invalid name space id");
		return -1;
	}

	return 0;
}

int fun_nvme_nsid_valid_chk(uint32_t nsid, uint32_t num_ns,
	struct fun_nvme_status *status)
{
	if (nsid == 0 || nsid > num_ns) {
		status->sct = FUN_NVME_SCT_GEN;
		status->sc = FUN_NVME_SC_INVAL_NS_OR_FMT;
		SYSLOG(NULL, ERR, FN_NVME, "" "invalid name space id");
		return -1;
	}

	return 0;
}

int fun_nvme_nsid_zero_chk(uint32_t nsid, struct fun_nvme_status *status)
{
	if (nsid != 0) {
		status->sct = FUN_NVME_SCT_GEN;
		status->sc = FUN_NVME_SC_INVAL_NS_OR_FMT;
		SYSLOG(NULL, ERR, FN_NVME, "" "invalid name space id");
		return -1;
	}

	return 0;
}

int fun_nvme_qid_chk(uint16_t qid, uint16_t max_qid,
	struct fun_nvme_status *status)
{
	if (qid == 0 || qid > max_qid) {
		status->sct = FUN_NVME_SCT_CS;
		status->sc = FUN_NVME_SC_INVAL_QID;
		SYSLOG(NULL, ERR, FN_NVME, "" "Invalid QID");
		return -1;
	}

	return 0;
}

/* check if qsize requested is supported by controller */
int fun_nvme_qsize_chk(uint16_t qsize, uint16_t mqes,
	struct fun_nvme_status *status)
{
	if ((qsize == 0) | (qsize > mqes)) {
		status->sct = FUN_NVME_SCT_CS;
		status->sc = FUN_NVME_SC_INVAL_QSIZE;
		SYSLOG(NULL, ERR, FN_NVME,
			"requested qsize exceeded max supported qsize");
		return -1;
	}

	return 0;
}

/** check if non-contig queue is requested while ctrlr does not support */
int fun_nvme_pc_chk(uint8_t pc, bool cqr, struct fun_nvme_status *status)
{
	if ((pc == 0) && cqr) {
		status->sct = FUN_NVME_SCT_GEN;
		status->sc = FUN_NVME_SC_INVAL_FLD;
		SYSLOG(NULL, ERR, FN_NVME,
			"" "non-contiguous queue is not supported");
		return -1;
	}

	return 0;
}

static int fun_nvme_qes_chk(uint32_t qes, uint32_t min_qes,
	uint32_t max_qes, struct fun_nvme_status *status)
{
	if ((qes < min_qes) || (qes > max_qes)) {

		status->sct = FUN_NVME_SCT_CS;
		status->sc = FUN_NVME_SC_INVAL_QSIZE;
		SYSLOG(NULL, ERR, FN_NVME,
			"qes %d is not in inclusive range [%d,%d]",
			qes, min_qes, max_qes);

		return -1;
	}

	return 0;
}

/** check if cc_iosqes is set properly */
int fun_nvme_sqes_chk(uint32_t cc_iosqes, uint8_t ctrlr_sqes,
	struct fun_nvme_status *status)
{
	uint32_t min_sqes = (ctrlr_sqes >> FUN_NVME_CTRLR_DATA_SQES_MIN_S) &
		FUN_NVME_CTRLR_DATA_SQES_MIN_M;
	uint32_t max_sqes = (ctrlr_sqes >> FUN_NVME_CTRLR_DATA_SQES_MAX_S) &
		FUN_NVME_CTRLR_DATA_SQES_MAX_M;

	return fun_nvme_qes_chk(cc_iosqes, min_sqes, max_sqes, status);
}

/** check if cc_iosqes is set properly */
int fun_nvme_cqes_chk(uint32_t cc_iocqes, uint8_t ctrlr_cqes,
	struct fun_nvme_status *status)
{
	uint32_t min_cqes = (ctrlr_cqes >> FUN_NVME_CTRLR_DATA_CQES_MIN_S) &
		FUN_NVME_CTRLR_DATA_CQES_MIN_M;
	uint32_t max_cqes = (ctrlr_cqes >> FUN_NVME_CTRLR_DATA_CQES_MAX_S) &
		FUN_NVME_CTRLR_DATA_CQES_MAX_M;

	return fun_nvme_qes_chk(cc_iocqes, min_cqes, max_cqes, status);
}

int fun_nvme_prp1_chk(uint64_t prp1, struct fun_nvme_status *status)
{
	if (prp1 == 0) {
		status->sct = FUN_NVME_SCT_GEN;
		status->sc = FUN_NVME_SC_INVAL_FLD;
		SYSLOG(NULL, ERR, FN_NVME, "PRP1 cannot be 0");
		return -1;
	}

	return 0;
}

int fun_nvme_psdt_chk(uint8_t psdt, struct fun_nvme_status *status)
{
	if (psdt != FUN_NVME_PSDT_PRP) {
		status->sct = FUN_NVME_SCT_GEN;
		status->sc = FUN_NVME_SC_INVAL_FLD;
		SYSLOG(NULL, ERR, FN_NVME, "Only PRP is supported");
		return -1;
	}

	return 0;
}

int fun_nvme_prp1_psdt_chk(uint64_t prp1, uint8_t psdt,
	struct fun_nvme_status *status)
{
	int ret = fun_nvme_prp1_chk(prp1, status);

	if (!ret) {
		ret = fun_nvme_psdt_chk(psdt, status);
	}

	return ret;
}

int nvme_sgl_chk(struct fun_nvme_cmd_cmn *cmn)
{
	//For now, support only separate metadata buffer
	if ((cmn->psdt != FUN_NVME_PSDT_SGL_MPTR_CONTIG) &&
		(cmn->psdt != FUN_NVME_PSDT_SGL_MPTR_SGL)) {

		SYSLOG(NULL, ERR, FN_NVME,
			"Unsupported psdt %d", cmn->psdt);
		return -1;
	}

	//For now, support only SGL with single data block descriptor
	if (cmn->sgl.generic.type != FUN_NVME_SGL_TYPE_DATA_BLOCK) {

		SYSLOG(NULL, ERR, FN_NVME,
			"SGL type is not supported");
		return -1;
	}

	return 0;
}

int fun_nvme_ctrlrid_chk(uint16_t ctrlrid, struct fun_nvme_status *status)
{
	return 0;
}

int fun_nvme_sq_chk(struct fun_nvme_create_sq *cmd, uint16_t max_qid,
	bool cqr, uint16_t mqes, uint32_t cc_iosqes, uint8_t ctrlr_sqes,
	struct fun_nvme_status *status)
{
	int ret = fun_nvme_nsid_zero_chk(cmd->cmn.nsid, status);

	if (!ret) {
		ret = fun_nvme_qid_chk(cmd->qid, max_qid, status);
	}

	if (!ret) {
		ret = fun_nvme_qid_chk(cmd->cqid, max_qid, status);
	}

	if (!ret) {
		ret = fun_nvme_pc_chk(cmd->pc, cqr, status);
	}

	if (!ret) {
		ret = fun_nvme_qsize_chk(cmd->qsize, mqes, status);
	}

	if (!ret) {
		ret = fun_nvme_sqes_chk(cc_iosqes, ctrlr_sqes, status);
	}

	return ret;
}

int fun_nvme_cq_chk(struct fun_nvme_create_cq *cmd, uint16_t max_qid,
	bool cqr, uint16_t mqes, uint32_t cc_iocqes, uint8_t ctrlr_cqes,
	struct fun_nvme_status *status)
{
	int ret = fun_nvme_nsid_zero_chk(cmd->cmn.nsid, status);

	if (!ret) {
		ret = fun_nvme_qid_chk(cmd->qid, max_qid, status);
	}

	if (!ret) {
		ret = fun_nvme_pc_chk(cmd->pc, cqr, status);
	}

	if (!ret) {
		ret = fun_nvme_qsize_chk(cmd->qsize, mqes, status);
	}

	if (!ret) {
		ret = fun_nvme_cqes_chk(cc_iocqes, ctrlr_cqes, status);
	}

	return ret;
}

int fun_nvme_idtfy_chk(struct fun_nvme_idtfy *cmd,
	uint32_t num_ns, uint16_t ctrlrid, struct fun_nvme_status *status)
{
	int ret = fun_nvme_prp1_chk(cmd->cmn.prp1, status);

	if (!ret) {
		switch (cmd->cns) {
		case FUN_NVME_IDTFY_NS_ACTIVE_DATA:
		case FUN_NVME_IDTFY_NS_ALLOC_DATA:
		case FUN_NVME_IDTFY_NS_CTRLR_LIST:
			ret = fun_nvme_nsid_valid_chk(cmd->cmn.nsid,
				num_ns, status);
			break;

		case FUN_NVME_IDTFY_NS_ACTIVE_LIST:
		case FUN_NVME_IDTFY_NS_ALLOC_LIST:
			ret = fun_nvme_nsid_special_chk(cmd->cmn.nsid, status);
			break;

		case FUN_NVME_IDTFY_CTRLR_LIST:
			ret = fun_nvme_ctrlrid_chk(ctrlrid, status);
			if (ret) {
				break;
			}
			/* fall through */
		case FUN_NVME_IDTFY_CTRLR_DATA:
			ret = fun_nvme_nsid_zero_chk(cmd->cmn.nsid, status);
			break;

		default:
			SYSLOG(NULL, ERR, FN_NVME,
				"Invalid cns value %d", cmd->cns);
			ret = -1;
			break;
		}
	}

	return ret;
}

int fun_nvme_flbas_chk(uint8_t flbas, struct fun_nvme_lbaf *lbaf,
	struct fun_nvme_status *status)
{
	if (flbas & 0xD0) {
		status->sct = FUN_NVME_SCT_CS;
		status->sc = FUN_NVME_SC_INVAL_FMT;
		SYSLOG(NULL, ERR, FN_NVME,
			"Invalid LBA format number %d", flbas);
		return -1;
	}

	if (lbaf->lbads == 0) {
		status->sc = FUN_NVME_SC_INVAL_FMT;
		SYSLOG(NULL, ERR, FN_NVME,
			"given namespace capacity exceeded max supported");
		return -1;
	}

	return 0;
}

int fun_nvme_dps_chk(uint8_t dps, uint8_t dpc, struct fun_nvme_status *status)
{
	if ((dps & FUN_NVME_DPS_TYPE_MASK) == 0) {
		return 0;
	}

	if (((dps == FUN_NVME_DPS_TYPE1) && !(dpc & FUN_NVME_DPC_TYPE1)) ||
	    ((dps == FUN_NVME_DPS_TYPE2) && !(dpc & FUN_NVME_DPC_TYPE2)) ||
	    ((dps == FUN_NVME_DPS_TYPE3) && !(dpc & FUN_NVME_DPC_TYPE3)) ||
	    ((dps & FUN_NVME_DPS_FIRST_OR_LAST) && !(dpc & FUN_NVME_DPC_FIRST_8B)) ||
	    (!(dps & FUN_NVME_DPS_FIRST_OR_LAST) && !(dpc & FUN_NVME_DPC_LAST_8B))) {
		status->sct = FUN_NVME_SCT_CS;
		status->sc = FUN_NVME_SC_INVAL_FMT;
		SYSLOG(NULL, ERR, FN_NVME,
			"Invalid dps 0x%x (dpc = 0x%x)", dps, dpc);
		return -1;
	}

	return 0;
}

int fun_nvme_ns_mgmt_chk(struct fun_nvme_ns_data *ns_data, uint64_t max_ns_size,
	uint64_t max_ns_cap, struct fun_nvme_lbaf *lbafs,
	uint8_t dpc, uint8_t nmic, struct fun_nvme_status *status)
{
	if (ns_data->nsze > max_ns_size) {
		status->sct = FUN_NVME_SCT_GEN;
		status->sc = FUN_NVME_SC_INVAL_FLD;
		SYSLOG(NULL, ERR, FN_NVME,
			"given ns size %"PRId64" exceeds max %"PRId64"",
			ns_data->nsze, max_ns_size);
		return -1;
	}

	if (ns_data->ncap > max_ns_cap) {
		status->sct = FUN_NVME_SCT_CS;
		status->sc = FUN_NVME_SC_NS_INSUFF_CAP;
		SYSLOG(NULL, ERR, FN_NVME,
			"given ns cap %"PRId64" exceeds max %"PRId64"",
			ns_data->ncap, max_ns_cap);
		return -1;
	}

	if (fun_nvme_flbas_chk(ns_data->flbas,
		&lbafs[ns_data->flbas & FUN_NVME_LBAF_NUM_MASK], status)) {
		return -1;
	}

	if (fun_nvme_dps_chk(ns_data->dps, dpc, status)) {
		return -1;
	}

	return 0;
}

int fun_nvme_ctrlr_list_chk(struct fun_nvme_ctrlr_list *ctrlr_list,
	struct fun_nvme_status *status)
{
	return 0;
}

int fun_nvme_ns_attach_chk(struct fun_nvme_ns_attach *cmd,
	uint32_t num_ns, struct fun_nvme_status *status)
{
	int ret = 0;

	if ((cmd->sel != FUN_NVME_NS_ATTACH_SEL_ATTACH) &&
		(cmd->sel != FUN_NVME_NS_ATTACH_SEL_DETACH)) {
		status->sct = FUN_NVME_SCT_GEN;
		status->sc = FUN_NVME_SC_INVAL_FLD;
		SYSLOG(NULL, ERR, FN_NVME,
			"Invalid sel (%d) in ns_attach command", cmd->sel);
		return -1;
	}

	ret = fun_nvme_nsid_valid_chk(cmd->cmn.nsid,
		num_ns, status);

	return ret;
}

/*
 * Set prp1 and prp2 for given buffer of 1 page size
 */
static inline void fun_nvme_set_prps(struct fun_nvme_cmd *cmd,
	uint64_t addr)
{
	uint64_t off;

	cmd->cmn.prp1 = addr;

	off = cmd->cmn.prp1 & FUN_NVME_PAGE_MASK;

	if (off) {
		cmd->cmn.prp2 = addr + (FUN_NVME_PAGE_SIZE - off);
	} else {
		cmd->cmn.prp2 = 0;
	}
}

static inline void fun_nvme_create_cmn(struct fun_nvme_create_cq *cmd,
	uint64_t addr, uint16_t qid, uint16_t qsize, uint16_t cid,
	uint8_t opcode)
{
	cmd->cmn.opcode = opcode;
	cmd->cmn.nsid = 0;
	cmd->qid = qid;
	cmd->qsize = qsize - 1;
	cmd->pc = 1;
	cmd->cmn.cid = cid;
	fun_nvme_set_prps((struct fun_nvme_cmd *)cmd, addr);
}

void fun_nvme_create_cq_cmd(struct fun_nvme_create_cq *cmd, uint64_t addr,
	uint16_t qid, uint16_t qsize, uint16_t cid)
{
	assert(cmd && qsize);

	memset(cmd, 0, sizeof(struct fun_nvme_cmd));
	fun_nvme_create_cmn(cmd, addr, qid, qsize, cid, FUN_NVME_CREATE_CQ);
}

void fun_nvme_create_sq_cmd(struct fun_nvme_create_sq *cmd, uint64_t addr,
	uint16_t qid, uint16_t qsize, uint16_t cqid, uint16_t cid)
{
	assert(cmd && qsize);

	memset(cmd, 0, sizeof(struct fun_nvme_cmd));

	fun_nvme_create_cmn((struct fun_nvme_create_cq *)cmd, addr, qid,
		qsize, cid, FUN_NVME_CREATE_SQ);

	cmd->cqid = cqid;
}

static inline void fun_nvme_delete_cmn(struct fun_nvme_del_cq *cmd,
	uint16_t qid, uint16_t cid, uint8_t opcode)
{
	cmd->cmn.opcode = opcode;
	cmd->cmn.nsid = 0;
	cmd->qid = qid;
	cmd->cmn.cid = cid;
}

void fun_nvme_delete_cq_cmd(struct fun_nvme_del_cq *cmd,
	uint16_t qid, uint16_t cid)
{
	assert(cmd);

	memset(cmd, 0, sizeof(struct fun_nvme_cmd));

	fun_nvme_delete_cmn(cmd, qid, cid, FUN_NVME_DEL_CQ);
}

void fun_nvme_delete_sq_cmd(struct fun_nvme_del_sq *cmd,
	uint16_t qid, uint16_t cid)
{
	assert(cmd);

	memset(cmd, 0, sizeof(struct fun_nvme_cmd));

	fun_nvme_delete_cmn((struct fun_nvme_del_cq *)cmd, qid,
		cid, FUN_NVME_DEL_SQ);
}

void fun_nvme_set_feat_cmd(struct fun_nvme_feat *cmd,
	uint8_t id, uint16_t num_queues, uint16_t cid)
{
	assert(cmd);

	memset(cmd, 0, sizeof(struct fun_nvme_cmd));

	cmd->cmn.opcode = FUN_NVME_SET_FEAT;
	cmd->feat_id = id;
	cmd->nsqr = num_queues;
	cmd->ncqr = num_queues;
	cmd->cmn.cid = cid;
}

void fun_nvme_idtfy_cmd(struct fun_nvme_idtfy *cmd,
	uint64_t addr, uint8_t cns, uint32_t nsid, uint16_t cid)
{
	assert(cmd && addr);

	memset(cmd, 0, sizeof(struct fun_nvme_cmd));

	cmd->cmn.opcode = FUN_NVME_IDTFY;
	cmd->cmn.nsid = nsid;
	cmd->cns = cns;
	cmd->cmn.cid = cid;
	fun_nvme_set_prps((struct fun_nvme_cmd *)cmd, addr);
}

void fun_nvme_ns_mgmt_create_cmd(struct fun_nvme_ns_mgmt *cmd,
	uint64_t addr, uint16_t cid)
{
	assert(cmd);

	memset(cmd, 0, sizeof(struct fun_nvme_cmd));

	cmd->cmn.opcode = FUN_NVME_NS_MGMT;
	cmd->cmn.cid = cid;
	cmd->sel = FUN_NVME_NS_MGMT_SEL_CREATE;
	fun_nvme_set_prps((struct fun_nvme_cmd *)cmd, addr);
}

void fun_nvme_ns_mgmt_delete_cmd(struct fun_nvme_ns_mgmt *cmd,
	uint32_t nsid, uint16_t cid)
{
	assert(cmd);

	memset(cmd, 0, sizeof(struct fun_nvme_cmd));

	cmd->cmn.opcode = FUN_NVME_NS_MGMT;
	cmd->cmn.nsid = nsid;
	cmd->cmn.cid = cid;
	cmd->sel = FUN_NVME_NS_MGMT_SEL_DELETE;
}

void fun_nvme_ns_attach_cmd(struct fun_nvme_ns_attach *cmd,
	uint64_t addr, uint32_t nsid, uint16_t cid)
{
	assert(cmd);

	memset(cmd, 0, sizeof(struct fun_nvme_cmd));

	cmd->cmn.opcode = FUN_NVME_NS_ATTACH;
	cmd->cmn.nsid = nsid;
	fun_nvme_set_prps((struct fun_nvme_cmd *)cmd, addr);
	cmd->cmn.cid = cid;
	cmd->sel = FUN_NVME_NS_ATTACH_SEL_ATTACH;
}

void fun_nvme_ns_detach_cmd(struct fun_nvme_ns_attach *cmd,
	uint64_t addr, uint32_t nsid, uint16_t cid)
{
	assert(cmd);

	memset(cmd, 0, sizeof(struct fun_nvme_cmd));

	cmd->cmn.opcode = FUN_NVME_NS_ATTACH;
	cmd->cmn.nsid = nsid;
	fun_nvme_set_prps((struct fun_nvme_cmd *)cmd, addr);
	cmd->cmn.cid = cid;
	cmd->sel = FUN_NVME_NS_ATTACH_SEL_DETACH;
}

void fun_nvme_vs_api_cmd(struct fun_nvme_vs_api *cmd, uint64_t addr,
	uint8_t vs_hndlr_id, uint8_t dir, uint8_t subop, uint16_t cid)
{
	cmd->cmn.opcode = FUN_NVME_VS_API_NO_DATA | (dir & FUN_NVME_DIR_MASK);
	cmd->cmn.cid = cid;
	fun_nvme_set_prps((struct fun_nvme_cmd *)cmd, addr);

	cmd->cmn.vs_hndlr_id = vs_hndlr_id;
	cmd->cmn.vs_subop = subop;
	cmd->cmn.vs_ver = 1;
}
