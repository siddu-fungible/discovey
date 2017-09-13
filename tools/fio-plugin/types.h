/*
 *  nucleus/types.h
 *
 *  Created by Charles Gray on 2016-05-02.
 *  Moved from funos/ to nucleus/ on 2017-07-14
 *  Copyright © 2016, 2017 Fungible. All rights reserved.
 */

/* Basic types for FunOS */

#pragma once

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>            // for bool
#include <inttypes.h>
#include <assert.h>

// =============== ADDRESSING ===============

/* hardware defined width of an SN message type */
typedef uint8_t sntype_t;

/* FIXME: flat index to specific logical VP number. really belongs in
 * platform?
 */
typedef uint16_t vpnum_t;

/* an F1 SN fabric address. one use if the destination of a WU.
 * 20 bits in two forms.
 * A standard WU is 5.5.8 + 2 reserved
 * An NU WU is 5.15
 * Source addresses are shorter, but we allow for all th bits
 * in a single type and compact in the WU action itself.
 *
 * See nucleus/fabric_address.h for field definitions
 */
typedef uint32_t faddr_t;

/* sending a WU here results in an error */
#define DEST_INVALID (0xffffU)

// =============== WORK UNITS ===============

/* software defined width of a WU table index */
typedef uint16_t wuid_t;

typedef unsigned opcode_t;
#define OPCODE_LEN (6)		// two bits per word
#define OPC_ARG0_MASK  (0x03)
#define OPC_ARG0_SHIFT (0x0)
#define OPC_ARG1_MASK  (0x0c)
#define OPC_ARG1_SHIFT (0x2)
#define OPC_ARG2_MASK  (0x30)
#define OPC_ARG2_SHIFT (0x4)

/* Fundamental work unit. Dispatches a function with context, packet and
 * immediate values. Total 32-byte element.
 */
struct wu {
	/* action field */
	uint64_t action;

	/* 3x argument words -- uint or pointer */
	union {
		uint64_t arg0;
		void *frame;
	};

	union {
		uint64_t arg1;
		void *flow;
	};

	union {
		uint64_t arg2;
		void *packet;
	};
};

static_assert(sizeof(struct wu) == 32, "WU is incorrect size");
#define WU_SZ	(sizeof(struct wu))

// =============== TIMERS ===============

/* identify an allocated timer. FIXME: embed cluster number
 * for added debugability
 */
typedef uint32_t timerid_t;

/* invalid timer */
#define TIMER_INVALID (-1U)

// =============== RESOURCES ===============

/* async resource level check data structure */
struct rlevel {
	uint32_t valid;
	uint32_t level;
};

#define RESOURCE_LEVEL_GREEN  (0)
#define RESOURCE_LEVEL_ORANGE (1)
#define RESOURCE_LEVEL_RED    (2)

#define RESOURCE_LEVEL_IS_GREEN(x)  ((x) == RESOURCE_LEVEL_GREEN)
#define RESOURCE_LEVEL_IS_ORANGE(x) ((x) == RESOURCE_LEVEL_ORANGE)
#define RESOURCE_LEVEL_IS_RED(x)    ((x) == RESOURCE_LEVEL_RED)

// =============== FLOW ===============

/* reserve 0 */
#define FLOW_TYPE_UNKNOWN (0)

/* Common header for flow data structures. Contains the necessary data
 * common to every flow.
 */
struct flow_common {
	/* flow type */
	/* FIXME: Are these statically assigned? Or dynamic? */
	uint32_t type;

	/* VP that owns this flow (root of flow control) */
	faddr_t owner;

	/* where to send on finalisation */
	struct wu output;

	/* FIXME: lots more here. Type information, routing, accounting,
	 * sizing, performance counters, ...
	 */
	uint32_t packet_count;
};

// =============== GENERALLY USEFUL MACROS ===============

/* FIXME: move this some place it won't clash with Qemu */
#ifndef ARRAY_SIZE
// size of the items for arrays.
#define ARRAY_SIZE(x) (sizeof(x) / sizeof(*(x)))
#endif

// =============== API ANNOTATIONS ===============

// Indicate parameter is passed in and also a returned value
#define INOUT

// Indicate parameter is a returned value
#define OUT

// Indicate function will return quickly but do most of its work asynchronously
#define ASYNC

// Indicate argument is a pointer that can be NULL (and then has special meaning)
// On a type, means that everywhere this type is mentioned, NULL is acceptable
#define NULLABLE

// Macro to indicate the caller must call free().
// THIS SHOULD BE AVOIDED.  A better APY style: pass the buffer where the result must be put.
// (But it is understood there are exceptions, such as strdup())
#define CALLER_TO_FREE

// Macro to indicate the caller must release,
// using a domain-specific release function like fun_json_release()
#define CALLER_TO_RELEASE

// =============== COMMON TYPES ===============

// type to carry together data and size.
struct fun_ptr_and_size {
	NULLABLE uint8_t *ptr;
	size_t size;
};

