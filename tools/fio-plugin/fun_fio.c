/*
 * fun engine
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <assert.h>
#include "fio.h"
#include "Integration/tools/fio-plugin/fun_fio.h"
#include "optgroup.h"
#include <semaphore.h>

struct fio_thread_struct fio_thread = {};
sem_t sem_fun1;

pthread_mutex_t fun_mutex;

struct fun_options{
	void *pad;
        char *source_ip;
        char *dest_ip;
        uint16_t io_queues;
        char *nvme_mode;
        char *nqn;
        uint16_t nsid;
};

#define FUN_CREATE_AND_IO 1
#define FUN_CREATE_ONLY 2
#define FUN_IO_ONLY 3

static struct fio_option options[] = {
        {
                .name   = "source_ip",
                .lname  = "Source ip",
                .type   = FIO_OPT_STR_STORE,
                .off1   = offsetof(struct fun_options, source_ip),
                .help   = "Source IP of NVMeOF Client",
                .category = FIO_OPT_C_ENGINE,
                .group  = FIO_OPT_G_FUN,
        },
        {
                .name   = "dest_ip",
                .lname  = "Destination ip",
                .type   = FIO_OPT_STR_STORE,
                .off1   = offsetof(struct fun_options, dest_ip),
                .help   = "IP of F1",
                .category = FIO_OPT_C_ENGINE,
                .group  = FIO_OPT_G_FUN,
        },
        {
                .name   = "io_queues",
                .lname  = "number of IO queues",
                .type   = FIO_OPT_INT,
                .off1   = offsetof(struct fun_options, io_queues),
                .help   = "number of IO queues",
                .category = FIO_OPT_C_ENGINE,
                .group  = FIO_OPT_G_FUN,
        },
        {
                .name   = "nvme_mode",
                .lname  = "create NS and do IO, create only or IO only",
                .type   = FIO_OPT_STR_STORE,
		.def	= "CREATE_AND_IO",
                .off1   = offsetof(struct fun_options, nvme_mode),
                .help   = "create NS and do IO=1, create only = 2 or IO only=3",
                .category = FIO_OPT_C_ENGINE,
                .group  = FIO_OPT_G_FUN,
        },
        {
                .name   = "nqn",
                .lname  = "Subsystem NQN",
                .type   = FIO_OPT_STR_STORE,
                .off1   = offsetof(struct fun_options, nqn),
		.def	= "nqn.2017-05.com.fungible:nss-uuid1",
                .help   = "Subsystem NQN",
                .category = FIO_OPT_C_ENGINE,
                .group  = FIO_OPT_G_FUN,
        },
        {
                .name   = "nsid",
                .lname  = "namespace id",
                .type   = FIO_OPT_INT,
                .off1   = offsetof(struct fun_options, nsid),
		.def	= "1",
                .help   = "namespace id",
                .category = FIO_OPT_C_ENGINE,
                .group  = FIO_OPT_G_FUN,
        },
        {
                .name   = NULL,
        },
};




static struct io_u *fio_fun_event(struct thread_data *td, int event)
{
	unsigned int tail;

	pthread_mutex_lock(&fun_mutex);
	tail = fio_thread.tail;

	fio_thread.tail++;
	if (fio_thread.tail == FUN_MAX_Q_DEPTH) {
		fio_thread.tail = 0; 
	}
	pthread_mutex_unlock(&fun_mutex);
	return fio_thread.io_us[tail];
}

static int fio_fun_getevents(struct thread_data *td, unsigned int min_events,
			      unsigned int fio_unused max,
			      const struct timespec fio_unused *t)
{
	int ret = 0;
	struct timespec t0, t1;
        uint64_t timeout = 0;

        if (t) {
                timeout = t->tv_sec * 1000000000L + t->tv_nsec;

                clock_gettime(CLOCK_MONOTONIC_RAW, &t0);
        } 

	for (;;) {
		if (fio_thread.completed >= min_events) {
			pthread_mutex_lock(&fun_mutex);
			ret = fio_thread.completed;
			fio_thread.completed = 0;	
			pthread_mutex_unlock(&fun_mutex);
			return ret;
		}

		if (t) {
			uint64_t elapse;

                        clock_gettime(CLOCK_MONOTONIC_RAW, &t1);
                        elapse = ((t1.tv_sec - t0.tv_sec) * 1000000000L)
                                 + t1.tv_nsec - t0.tv_nsec;
                        if (elapse > timeout) {
                                break;
                        }
		}
		usleep(100);
        }


	return ret;
}

uint8_t qid = 1;
uint16_t io_queues;
uint16_t nsid;

static int fio_fun_queue(struct thread_data *td, struct io_u *io_u)
{
	int rc = 0;

        switch (io_u->ddir) {
        case DDIR_READ:
        case DDIR_WRITE:
		//rc = fun_read_write( io_u, io_u->file->fileno + 1, io_u->buf, io_u->offset, io_u->xfer_buflen, qid);
		rc = fun_read_write( io_u, nsid, io_u->buf, io_u->offset, io_u->xfer_buflen, qid);
                break;
        default:
                assert(false);
                break;
        }
	if (++qid > io_queues) qid = 1;


	return rc ? FIO_Q_BUSY: FIO_Q_QUEUED;

}


static int fio_fun_init(struct thread_data *td)
{
	uint16_t i;
	int rc = 1;

	struct fun_options *foptions = td->eo;

	if (!foptions->source_ip | !foptions->dest_ip){
		printf("\n Required source and destination IP: --source_ip  and --dest_ip\n");
		return 1;		
	} 
	if (td->o.nr_files > 1){
		printf("\n Only one namespace supported as of now\n");
		return 1;		
	}

	if (!foptions->io_queues) io_queues = 1;
	else io_queues = foptions->io_queues;

	if (!foptions->nsid) nsid = 1;
	else nsid = foptions->nsid;

	printf("\nClient IP=%s, F1 IP=%s, number of NSs=%d, NSID=%d, IO Queues = %d, Mode = %s and NQN = %s \n\n",\
		 foptions->source_ip, foptions->dest_ip, td->o.nr_files,\
		 nsid, io_queues, foptions->nvme_mode, foptions->nqn); 

        rc = fun_client_start(inet_addr(foptions->source_ip), inet_addr(foptions->dest_ip));

	if (rc) goto init_failed;

	sem_init(&sem_fun1, 0, 0);

	rc = fun_admin_io_connect(0,64,100,0xFFFF,foptions->nqn); //qid, sqsize, keep alive, ctrlr id, nqn
	if (rc) goto init_failed;
	sem_wait(&sem_fun1);

       	rc = fun_enable_controller();
	if (rc) goto init_failed;
	sem_wait(&sem_fun1);

	if (!strcmp(foptions->nvme_mode,"IO_ONLY")) {
		for(i=1; i<=io_queues; i++){
			rc = fun_admin_io_connect(i,64,100,0xFFFF,foptions->nqn); //qid, sqsize, kato, ctrlr id, nqn
			if (rc) goto init_failed;
			sem_wait(&sem_fun1);
		}
		return 0;  
	}

	for (i=1; i <= td->o.nr_files; i++){ 
        	rc = fun_nvmf_ns_create();
		if (rc) goto init_failed;
		sem_wait(&sem_fun1);

        	rc = fun_nvmf_ns_attach(i);
		if (rc) goto init_failed;
		sem_wait(&sem_fun1);
	}
	log_info("\nReady for I/O.......\n\n");
	if (!strcmp(foptions->nvme_mode,"CREATE_ONLY")) return 1;  

	rc = 0;

init_failed:
	return rc;
}

static int fio_fun_invalidate(struct thread_data *td, struct fio_file *f)
{
        /* TODO: This should probably send a flush to the device, but for now just return successful. */
        return 0;
}

static int fio_fun_setup(struct thread_data *td)
{
	struct fun_options *foptions = td->eo;

	if (!foptions->source_ip | !foptions->dest_ip){
		printf("\nPlease provide source and destination IP: --source_ip=?  and --dest_ip=?\n");
		exit(1);
	} 

	return 0;
}

static int fio_fun_open(struct thread_data fio_unused *td,
			 struct fio_file fio_unused *f)
{
	return 0;
}

static void fio_fun_cleanup(struct thread_data *td)
{
	fun_client_stop();	
}

static int fio_fun_close(struct thread_data *td, struct fio_file *f)
{
	return 0;
}

static struct ioengine_ops ioengine = {
	.name		= "fun",
	.version	= FIO_IOOPS_VERSION,
	.queue		= fio_fun_queue,
	.getevents	= fio_fun_getevents,
	.event		= fio_fun_event,
	.init		= fio_fun_init,
	.setup		= fio_fun_setup,
	.cleanup	= fio_fun_cleanup,
	.open_file	= fio_fun_open,
	.close_file	= fio_fun_close,
	.invalidate	= fio_fun_invalidate,
	.options	= options,
	.option_struct_size	= sizeof(struct fun_options),
};

static void fio_init fio_fun_register(void)
{
	register_ioengine(&ioengine);
}

static void fio_exit fio_fun_unregister(void)
{
	unregister_ioengine(&ioengine);
}

