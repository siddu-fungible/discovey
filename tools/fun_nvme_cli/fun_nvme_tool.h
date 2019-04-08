#define FUN_MAX_Q_DEPTH  256

#define log_err(format,...)
#define log_info(format,...)


enum fio_ddir {
        DDIR_READ = 0,
        DDIR_WRITE = 1,
        DDIR_TRIM = 2,
        DDIR_RWDIR_CNT = 3,
        DDIR_SYNC = 3,
        DDIR_DATASYNC,
        DDIR_SYNC_FILE_RANGE,
        DDIR_WAIT,
        DDIR_LAST,
        DDIR_INVAL = -1,
};

struct io_u {
	unsigned int flags;
	enum fio_ddir ddir;

	unsigned long long offset;
	void *buf;

	/*
	 * Initial seed for generating the buffer contents
	 */
	uint64_t rand_seed;

	/*
	 * IO engine state, may be different from above when we get
	 * partial transfers / residual data counts
	 */
	void *xfer_buf;
	unsigned long xfer_buflen;

	/*
	 * Parameter related to pre-filled buffers and
	 * their size to handle variable block sizes.
	 */
	unsigned long buf_filled_len;


	unsigned int resid;
	unsigned int error;

	/*
	 * io engine private data
	 */
	union {
		unsigned int index;
		unsigned int seen;
		void *engine_data;
	};

};

struct fio_thread_struct {
        int queued;
        int completed;
        struct io_u *io_us[FUN_MAX_Q_DEPTH];
	unsigned int head;
        unsigned int tail;
};
int fun_client_start(uint32_t local_addr, uint32_t remote_addr);  
int fun_enable_controller();
int fun_read_write(struct io_u *io_u, uint32_t nsid,\
         void * buf, uint64_t offset, uint64_t xfer_buflen, uint16_t qid);
int fun_admin_io_connect(uint16_t qid, uint8_t sqsize, uint32_t kato, uint16_t cntlid, char *nqn);
void fun_client_stop();
int fun_identify(uint32_t nsid, void *buf, bool present);
int fun_nvme_io(__u32 nsid, __u8 opcode, __u64 slba, __u16 nblocks, __u16 control, \
            __u32 dsmgmt, __u32 reftag, __u16 apptag, __u16 appmask, void *data, \
            void *metadata, __u16 qid);
int fun_property_get(void *buf, uint32_t offset, uint8_t size);
int fun_nvmf_ns_create(__u64 nsze, __u64 ncap, __u8 flbas, \
                   __u8 dps, __u8 nmic, __u32 *result);
int fun_nvmf_ns_attach_or_detach(uint32_t nsid, bool attach);
int fun_nvmf_ns_delete(__u32 nsid);
