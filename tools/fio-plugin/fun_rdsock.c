/*
 *  rdsock.c
 *
 *  Created by Jaspal Kohli on 2017-04-15.
 *  Copyright © 2017 Fungible. All rights reserved.
 */

#include "Integration/tools/fio-plugin/fun_utils.h"
#include <unistd.h>
#include <pthread.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <stdlib.h>             // for malloc(), etc...
#include <string.h>             // for memcmp(), etc...
#include <stdio.h>              // for printf()...
#include "Integration/tools/fio-plugin/rdsock.h"
#include <assert.h>


typedef enum {false,true} bool;
/*
 * Implements a reliable datagram by adding message boundries to
 * an underlying TCP (stream) socket.
 */
static uint32_t rdsock_localip;
static uint16_t rdsock_port;
static bool rdsock_running;

#define RDSOCK_MAX	64	/* Max number of sockets supported */

#define RDSOCK_HDR_MAGIC	0xF1FDF1FD
struct rdsock_msghdr {
	uint32_t magic;
	uint16_t msglen;
	uint32_t datalen;
};

struct rdsock_impl;

struct rdsock_impl {
	// TODO - Add Flow component
	pthread_mutex_t recv_lock, send_lock;
	int index;		// into table of active sockets
	int fd;
	bool close_pending;
	uint8_t recvs;		// number of receive messages being handled
	struct rdsock_params params;
};

struct rdsock_listener {
	int fd;
	uint8_t lref;		// used for listen socket
};

// Incoming message with separate receive buffer that can be synchronously
// allocated
struct rdsock_msg_in {
	struct rdsock_msg msg;
	void *data;
	uint32_t datalen;
};

struct rdsock_state {
	pthread_mutex_t lock;
	uint32_t active;		// number of rdsock instances
	uint32_t maxfd;			// highest fd among rdsock instances
	struct rdsock_listener lsock;	// listen socket for server
	struct rdsock_impl *list[RDSOCK_MAX];
	pthread_cond_t idle;
	fd_set rfds;
	struct timeval tv;
};

static struct rdsock_state *rdsstate;

static void
rdsock_free(struct rdsock_impl *rds)
{
	if (rds->fd != -1)
		close(rds->fd);
	free(rds);
}

struct rdsock *
rdsock_open(struct rdsock_params *params)
{
	struct rdsock_impl *rds;
	struct sockaddr_in saddr;
	int ret, flag = 1;

	if (rdsstate->active == RDSOCK_MAX)
		return NULL;

	rds = calloc(1, sizeof(struct rdsock_impl));
	if (rds == NULL)
		return NULL;

	rds->fd = socket(PF_INET, SOCK_STREAM, 0);
	if (rds->fd == -1) {
		SYSLOG(NULL, CRIT, FN, "Failed to create RD socket");
		free(rds);
		return NULL;
	}
	ret = setsockopt(rds->fd, SOL_SOCKET, SO_REUSEADDR,
				(char *)&flag, sizeof(flag));
	memcpy(&rds->params, params, sizeof(struct rdsock_params));
	pthread_mutex_init(&rds->recv_lock, NULL);
	pthread_mutex_init(&rds->send_lock, NULL);
	rds->close_pending = false;

	if (rds->params.role == RDSOCK_SERVER) {
		struct rdsock_listener *ls = &rdsstate->lsock;

		// Check for existing listen socket
		if (ls->fd != -1) {
			ls->lref++;
			close(rds->fd);
			rds->fd = -1;
		} else {
			ls->fd = rds->fd;
			ls->lref = 1;
			rds->fd = -1;
			// saddr.sin_len = sizeof(saddr);
			saddr.sin_family = AF_INET;
			saddr.sin_port = rdsock_port;
			saddr.sin_addr.s_addr = rdsock_localip;

			ret = bind(ls->fd, (struct sockaddr *)&saddr,
					sizeof(saddr));
			if (ret == -1) {
				SYSLOG(NULL, CRIT, FN,
					"Failed to bind RD socket %d",
					ntohs(rdsock_port));
				rdsock_free(rds);
				return NULL;
			}

			ret = listen(ls->fd, 1);
			if (ret == -1) {
				SYSLOG(NULL, CRIT, FN,
					"Failed to bind RD socket %d",
					ntohs(rdsock_port));
				rdsock_free(rds);
				return NULL;
			}
			SYSLOG(NULL, INFO, FN,
				"Listening on RD socket %d",
				ntohs(rdsock_port));
		}
	} else {
		assert(rds->params.role == RDSOCK_CLIENT);
		// saddr.sin_len = sizeof(saddr);
		saddr.sin_family = AF_INET;
		saddr.sin_port = rdsock_port;
		saddr.sin_addr.s_addr = rds->params.remoteip;

		ret = connect(rds->fd, (struct sockaddr *)&saddr,
				sizeof(saddr));
		if (ret == -1) {
			SYSLOG(NULL, CRIT, FN,
				"Failed to connect RD socket %d",
				ntohs(rdsock_port));
			free(rds);
			return NULL;	
		}
		ret = setsockopt(rds->fd, IPPROTO_TCP, TCP_NODELAY,
					(char *)&flag, sizeof(flag));
		if (ret != 0) {
			SYSLOG(NULL, WARNING, FN,
				"Failed to set NODELAY on RD Socket %d",
				ntohs(rdsock_port));
		}

		SYSLOG(NULL, INFO, FN,
			"Connected on RD socket %d",
			ntohs(rdsock_port));
	}
	
	pthread_mutex_lock(&rdsstate->lock);
	if (rdsstate->active == RDSOCK_MAX) {
		rdsock_free(rds);
		pthread_mutex_unlock(&rdsstate->lock);
		return NULL;
	}
	rdsstate->list[rdsstate->active] = rds;
	rds->index = rdsstate->active;
	rdsstate->active++;
	if (rdsstate->active == 1)	// was idle - wakeup server thread
		pthread_cond_signal(&rdsstate->idle);
	pthread_mutex_unlock(&rdsstate->lock);
	return (struct rdsock *)rds;
}

void
rdsock_sendmsg(struct rdsock *sock,
		 struct rdsock_msg *msg)
{
	struct rdsock_impl *rds = (struct rdsock_impl *)sock;
	struct rdsock_msghdr msghdr;
	int ret;
	
	/* TODO - use async IO as part of the rds_server to avoid
	 * blocking a VP on a system call.  This works for now
	 * getting the basic use cases up and running.
	 */
	if ((rds->fd == -1) ||
	    ((msg->msglen == 0) && (msg->buf == NULL)) ||
	    (msg->msglen > RDSOCK_MAXMSGLEN)) {
		msg->resp = RDSOCK_RESP_FAIL;
		return;
	}

	msghdr.magic = htonl(RDSOCK_HDR_MAGIC);
	msghdr.msglen = htons(msg->msglen);

	if (msg->buf) {
		msghdr.datalen = htonl(msg->buf_size);
	} else
		msghdr.datalen = 0;

	msg->resp = RDSOCK_RESP_OK;

	// We need to serialize messages to the same socket to ensure
	// that the datagrams are sent atomically
	pthread_mutex_lock(&rds->send_lock);

	ret = send(rds->fd, &msghdr, sizeof(msghdr), 0);
	if (ret < sizeof(msghdr)) {
		SYSLOG(NULL, WARNING, FN, "Short header write from RDS");
		msg->resp = RDSOCK_RESP_FAIL;
		goto send_failed;
	}

	if (msghdr.msglen) {
		ret = send(rds->fd, msg->msg, msg->msglen, 0);
		if (ret < msg->msglen) {
			SYSLOG(NULL, WARNING, FN, "Short msg write from RDS");
			msg->resp = RDSOCK_RESP_FAIL;
			goto send_failed;
		}
	}

	if (msg->buf_size) {
		ret = send(rds->fd, msg->buf, msg->buf_size, 0);
		if (ret < msg->buf_size) {
			SYSLOG(NULL, WARNING, FN, "Short msg write from RDS");
			msg->resp = RDSOCK_RESP_FAIL;
			goto send_failed;
		}
	}

send_failed:
	pthread_mutex_unlock(&rds->send_lock);
}

/* We assume the caller will not send additional messages, however there could
 * could be pending receives being processed that we need to synchronize with
 */
void
rdsock_close(struct rdsock *sock)
{
	struct rdsock_impl *rds = (struct rdsock_impl *)sock;
	int fd, lfd = -1, index;

	pthread_mutex_lock(&rdsstate->lock);
	assert((rds->index >= 0) && (rds->index < rdsstate->active));
	index = rds->index;
	assert(rdsstate->list[index] == rds);

	// If there are pending receives, the close will be done later
	pthread_mutex_lock(&rds->recv_lock);
	if (rds->recvs) {
		rds->close_pending = true;
		pthread_mutex_unlock(&rds->recv_lock);
		pthread_mutex_unlock(&rdsstate->lock);
		return;
	}
	pthread_mutex_unlock(&rds->recv_lock);

	fd = rds->fd;
	rdsstate->list[index] = NULL;
	// relocate last one to this slot
	if (rdsstate->active > index + 1) {
		rdsstate->list[index] = rdsstate->list[rdsstate->active - 1];
		rdsstate->list[index]->index = index;
	}
	rdsstate->active--;

	// Check for listener
	if (rds->params.role == RDSOCK_SERVER) {
		assert(rdsstate->lsock.lref);
		if (--rdsstate->lsock.lref == 0) {
			lfd = rdsstate->lsock.fd;
			rdsstate->lsock.fd = -1;
			SYSLOG(NULL, INFO, FN,
				"Closing RD listen socket");
		}
	}

	pthread_mutex_unlock(&rdsstate->lock);
	if (fd != -1)
		close(fd);
	if (lfd != -1)
		close(lfd);
	free(rds);
}

static void
setup_fds(struct rdsock_state *state)
{
	pthread_mutex_lock(&state->lock);
	if (state->active == 0)
		pthread_cond_wait(&state->idle, &state->lock);
	FD_ZERO(&state->rfds);

	// Check for listener
	if (state->lsock.fd != -1) {
		FD_SET(state->lsock.fd, &state->rfds);
		if (state->lsock.fd > state->maxfd)
			state->maxfd = state->lsock.fd;
	}

	for (int i=0; i<state->active; i++) {
		struct rdsock_impl *rds = state->list[i];
		int fd = rds->fd;

		// Check active entries
		if (fd == -1)		// not connected
			continue;
		FD_SET(fd, &state->rfds);
		if (fd > state->maxfd)
			state->maxfd = fd;
	}
	pthread_mutex_unlock(&state->lock);
}

static void
rdsock_read_fail(struct rdsock_state *state, struct rdsock_impl *rds)
{
	close(rds->fd);
	rds->fd = -1;
}

void
rdsock_do_recv_wuh(struct rdsock_impl *rds,
			struct rdsock_msg_in *rdmsg_in)
{
	struct rdsock_msg *rdmsg = &rdmsg_in->msg;

	// Check for mbuf allocation failure
	if ((rdmsg_in->data != NULL) &&
	    (rdmsg->buf == NULL)) {
		SYSLOG(NULL, WARNING, FN, "Failed to allocate mbuf in recv");
		return;
	}
	rds->params.recv((struct rdsock *)rds, rdmsg);
}


void
rdsock_recv_done_wuh(struct rdsock_impl *rds,
			struct rdsock_msg_in *rdmsg_in)
{
	bool do_close = false;

	pthread_mutex_lock(&rds->recv_lock);
	rds->recvs--;
	if ((rds->recvs == 0) && rds->close_pending)
		do_close = true;
	pthread_mutex_unlock(&rds->recv_lock);
	if (rdmsg_in->msg.buf != NULL) {
		free(rdmsg_in->msg.buf); 
	}
	if (do_close)
		rdsock_close((struct rdsock *)rds);
}


// Called with rds lock held to avoid race with close.  The lock is released
// as part of this routine
static void
read_fd(struct rdsock_state *state, struct rdsock_impl *rds)
{
	struct rdsock_msg *rdmsg = NULL;
	struct rdsock_msg_in *rdmsg_in;
	struct rdsock_msghdr msghdr;
	int ret;
	bool readfail = false;

	if (!rds->params.recv ||
	    (rds->recvs == rds->params.maxrecv) ||
	    rds->close_pending) {
		pthread_mutex_unlock(&rds->recv_lock);
		return;
	}


	rds->recvs++;
	pthread_mutex_unlock(&rds->recv_lock);

	ret = recv(rds->fd, &msghdr, sizeof(msghdr), MSG_WAITALL);
	if (ret < sizeof(msghdr)) {
		if (ret > 0)
			SYSLOG(NULL, WARNING, FN, "Short header read from RDS");
		readfail = true;
		goto read_fail;
	}
	if (ntohl(msghdr.magic) != RDSOCK_HDR_MAGIC) {
		SYSLOG(NULL, WARNING, FN, "Bad header read from RDS");
		readfail = true;
		goto read_fail;
	}
	msghdr.msglen = ntohs(msghdr.msglen);
	msghdr.datalen = ntohl(msghdr.datalen);

	rdmsg_in = malloc(sizeof(struct rdsock_msg_in));
	rdmsg = &rdmsg_in->msg;

	rdmsg->msg = NULL;
	rdmsg->msglen = msghdr.msglen;
	if (msghdr.msglen) {
		rdmsg->msg = malloc(msghdr.msglen);
		ret = recv(rds->fd, rdmsg->msg, msghdr.msglen, MSG_WAITALL);
		if (ret < msghdr.msglen) {
			if (ret > 0)
				SYSLOG(NULL, WARNING, FN,
					"Short header read from RDS");
			readfail = true;
			goto read_fail;
		}
	}

	rdmsg_in->data = NULL;
	rdmsg->buf = NULL;
	if (msghdr.datalen) {
		rdmsg_in->data = malloc(msghdr.datalen);
		assert(rdmsg_in->data);		// TODO handle this case
		ret = recv(rds->fd, rdmsg_in->data, msghdr.datalen,
				MSG_WAITALL);
		rdmsg_in->datalen = msghdr.datalen;
                rdmsg->buf = rdmsg_in->data;
                rdmsg->buf_size = msghdr.datalen;
		if (ret < msghdr.datalen) {
			if (ret > 0)
				SYSLOG(NULL, WARNING, FN,
					"Short data read from RDS");
			readfail = true;
			goto read_fail;
		}
	}
	rdmsg->context = rds->params.recv_context;
	rdmsg->resp = RDSOCK_RESP_OK;

read_fail:
	if (readfail) {
		rdsock_read_fail(state, rds);
		if (rdmsg && rdmsg->buf) {
			free(rdmsg->buf);
		}
		return;
	}

	rdsock_do_recv_wuh(rds,rdmsg_in);
	rdsock_recv_done_wuh(rds,rdmsg_in);

}

static void
reap_fds(struct rdsock_state *state)
{
	int i;

	// Lock the state to avoid changes in the set of active fds while
	// we scan it.  We can optimize further by releasing the lock
	// while doing the accept, but the simpler approach is ok
	// for now as we are only blocking open/close requests and not
	// a send.
	pthread_mutex_lock(&state->lock);

	// Check for listener
	if ((state->lsock.fd != -1) &&
	    FD_ISSET(state->lsock.fd, &state->rfds)) {
		struct sockaddr_in saddr;
		socklen_t slen = sizeof(saddr);
		int fd;
		bool match = false;

		fd = accept(state->lsock.fd, (struct sockaddr *)&saddr,
				&slen);
		if (fd == -1) {
			SYSLOG(NULL, CRIT, FN, "Accept on RD socket failed");
			goto active_conns;
		}

		for (i = 0; i < state->active; i++) {
			struct rdsock_impl *rds = state->list[i];

			if ((rds->params.role == RDSOCK_SERVER) &&
			    (rds->fd == -1) &&
			    (saddr.sin_addr.s_addr == rds->params.remoteip)) {
				rds->fd = fd;
				match = true;
				SYSLOG(NULL, INFO, FN, "Got RD Connection");
				break;
			}
		}
		if (!match) {
			SYSLOG(NULL, WARNING, FN,
				"Spurious connection RD sock");
			close(fd);
		}
	}

active_conns:
	// Check for active connections
	for (i = 0; i < state->active; i++) {
		struct rdsock_impl *rds = state->list[i];
		int inb;

		if (rds->fd == -1)		// closed on error
			continue;
		if (!FD_ISSET(rds->fd, &state->rfds))
			continue;

		// A select will also trigger of the other end of the
		// socket was closed.
		if ((ioctl(rds->fd, FIONREAD, &inb) < 0) || (inb == 0)) {
			close(rds->fd);
			rds->fd = -1;
			continue;
		}

		// Acquire the rds lock and unlock the state lock during
		// read processing.  The lock is released by read_fd
		// prior to invoking the receive function
		pthread_mutex_lock(&rds->recv_lock);
		pthread_mutex_unlock(&state->lock);
		// input on connected socket
		read_fd(state, rds);
		pthread_mutex_lock(&state->lock);
	}
	pthread_mutex_unlock(&state->lock);
}

static void *
rds_server(void *arg)
{
	struct rdsock_state *state = (struct rdsock_state *)arg;
	int ret;

	assert(state);
	while (rdsock_running) {
		setup_fds(state);
		ret = select(state->maxfd + 1, &state->rfds, 0, 0, &state->tv);
		if (!ret)
			continue;
		if (ret < 0) {
			SYSLOG(NULL, DEBUG, FN, "Error in RDS select with "
				"%d maxfd", state->maxfd);
			continue;
		}
		reap_fds(state);
	}

	SYSLOG(NULL, INFO, FN, "Exiting RDS Server Thread");
	return NULL;
}

void
rdsock_init(uint32_t localip, uint16_t port)
{
	pthread_t rds_thread;

	rdsock_localip = localip;
	rdsock_port = port;

	rdsstate = calloc(1, sizeof(struct rdsock_state));
	assert(rdsstate);
	rdsstate->active = 0;
	pthread_mutex_init(&rdsstate->lock, NULL);
	pthread_cond_init(&rdsstate->idle, NULL);
	rdsstate->tv.tv_sec = 0;
	rdsstate->tv.tv_usec = 100 * 1000;		// 100 msec
	rdsock_running = true;
	rdsstate->lsock.fd = -1;

	/* Start pthread to act as listener/receiver */
	int ret = pthread_create(&rds_thread, NULL, &rds_server, rdsstate);
	if (ret) {
		perror("rdsock pthread create failed");
		exit(1);
	}	
}

void
rdsock_shutdown(void)
{
	// Leave the server thread running for now to avoid having to
	// deallocate the fabric binding.
	// rdsock_running = false;

}
