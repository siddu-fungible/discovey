/*
 *  rdsock.h
 *
 *  Created by Jaspal Kohli on 2017-04-10.
 *  Copyright © 2017 Fungible. All rights reserved.
 */

#ifndef __RDSOCK_H_
#define __RDSOCK_H_

#include <sys/socket.h>

/*
 * Reliable Datagram API for funOS modules.  Allows for reliable exhange
 * of messages between two F1 nodes - a client and a server.  Ordering is
 * not guaranteed, but messages are typically received in the order sent.
 *
 * This API is currently implemented in a Posix environemnt only but could be
 * incorporated later into the FunOS network stack.  It enables development
 * of other FunOS modules (e.g. remote storage access) prior to the FunOS
 * network stack being available.
 *
 * Currently supports IPv4 addressing only.
 */

struct rdsock;		/* handle for reliable datagram socket */

/* An instance of rdsock can have a Client or Server role.  The Client
 * can send messages immediately upon opening the socket where as the Server
 * can only send messages once it has received one from the Client.
 * When data is received, the specified handler is invoked on a frame
 * managed by rdsock.  Upon completing the the use of the frame for
 * handling the message, the callee must send a completion WU to allow
 * the frame and resources to be released.
 */
typedef enum {
	RDSOCK_CLIENT,
	RDSOCK_SERVER
} rdsock_role_t;

#define RDSOCK_MAXMSGLEN 1024

typedef enum {
	RDSOCK_RESP_NONE,
	RDSOCK_RESP_OK,
	RDSOCK_RESP_FAIL
} rdsock_resp_t;

/* The datagram is composed of a message and an mbuf, one or both can be
 * specified.  For example, the message could be a command structure that
 * is allocated on the WU stack and the mbuf could contain data that is
 * being transferred to be stored in the remote F1.  The context field
 * allows the caller to associate the message with some application
 * specific context in the completion WUH or the receive handler.
 */
struct rdsock_msg {
	char *msg;
	uint16_t msglen;
	uint32_t  *buf;	// single mbuf for now
        uint16_t buf_size;
	void *context;		// user context
	rdsock_resp_t resp;
};

/* Socket create parameters.  The recv handler is optional and allows the
 * caller to receive datagrams on the socket.   It is called on a WU stack
 * managed by the callee and must send a continuation after the receive
 * datagram is consumed.
 */
struct rdsock_params {
	uint32_t remoteip;
	rdsock_role_t role;
	void (*recv)(struct rdsock *sock,
			struct rdsock_msg *msg);
	void *recv_context;	// user context set on recv
	uint8_t maxrecv;	// max concurrent receives
};

/* Create a socket with the specified params.
 */
struct rdsock *
rdsock_open(struct rdsock_params *params);

/* Send a message.  Completes asnychronously be sending a continuation
 * on the frame. The resp field is set to indicate the result.
 */
void rdsock_sendmsg(struct rdsock *sock,
		 struct rdsock_msg *msg);

void rdsock_close(struct rdsock *sock);

void rdsock_init(uint32_t localip, uint16_t port);
void rdsock_shutdown(void);


#endif /* __RDSOCK_H_ */
