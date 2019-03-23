int fun_nvmf_ns_create();
int fun_nvmf_ns_attach();
int fun_admin_connect(char *nqn);
int fun_enable_controller();
int fun_read_write(struct io_u *io_u, uint32_t nsid,\
         void * buf, uint64_t offset, uint64_t xfer_buflen, uint16_t qid);
int fun_admin_io_connect(uint16_t qid, uint8_t sqsize, uint32_t kato, uint16_t cntlid, char *nqn);
