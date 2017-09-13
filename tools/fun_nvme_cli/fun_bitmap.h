/*
 *	funos/bitmap.h - bitmap header file
 *
 *	Created August 2016 by felix.marti@fungible.com.
 *	Copyright © 2016 Fungible. All rights reserved.
 */

#pragma once

#include "fun_types.h"

#define ALIGN(_val, _boundary)\
    (typeof(_val))(((unsigned long)(_val) +\
                  (_boundary) - 1) & ~((_boundary) - 1))

#define BITMAP(_bm_name, _bm_nbits)\
    struct bitmap _bm_name;\
    uint64_t _bm_name ## _mem[ALIGN(_bm_nbits, 64) >> 6]

enum bitmap_consts {
	BITMAP_MEMALIGNMENT = 8,
};

/*
 *	bitmap structure
 *	NOTE: Do not add pointers in this structure
 *
 */
struct bitmap {
	unsigned int bm_mem_size8;	/* size of the bitmap memory in units
					 * of 8-bytes
					 */
	unsigned int bm_nbits;	/* number of bits in the bitmap
				 * memory
				 */
	unsigned int bm_nbits_available;	/* number of bits that are currently
						 * 0 (unallocated)
						 */
	unsigned int bm_mem_off8;	/* offset in units of 8-bits (or
					 * 64-bits) of last bitmap access
					 */
	uint64_t bm_mem[0];
};

static inline unsigned int bitmap_nbits(struct bitmap *bm)
{

	return bm->bm_nbits;
}

static inline unsigned int bitmap_nbits_available(struct bitmap *bm)
{

	return bm->bm_nbits_available;
}

static inline unsigned int bitmap_nbits_one(struct bitmap *bm)
{
	return bm->bm_nbits - bm->bm_nbits_available;
}

/**
 *	bitmap_bfull - is bitmap full?
 *	@bm: the bitmap pointer
 *
 *	Returns 1 if all bis are set. Returns 0 if not all bits are set.
 */
static inline unsigned int bitmap_bfull(struct bitmap *bm)
{

	return !bm->bm_nbits_available;
}

/**
 *	bitmap_bempty - is bitmap empty?
 *	@bm: the bitmap pointer
 *
 *	Reurns 1 if no bits are set. Returns 0 if bits are set.
 */
static inline unsigned int bitmap_bempty(struct bitmap *bm)
{

	return bm->bm_nbits == bm->bm_nbits_available;
}

// get the next available bit
extern int bitmap_bget(struct bitmap *);
// free a given bit
extern int bitmap_bput(struct bitmap *, unsigned int);
extern int bitmap_bsearch(struct bitmap, unsigned int, unsigned int);

// retrn true if given bit is available. Else, return false.
extern bool bitmap_bavail(struct bitmap *bm, unsigned int bit);
// if given bit is available, allocate it and return 0. Else return -1
extern int bitmap_bget_avail(struct bitmap *bm, unsigned int bit);

extern unsigned int bitmap_size(unsigned int);
extern struct bitmap *bitmap_init(void *, unsigned int);
extern int bitmap_fini(struct bitmap *);
extern void bitmap_dump(struct bitmap *);

extern int bitmap_biterate(struct bitmap *bm, unsigned int *start);

// ===============  SELF TEST ===============

extern void bitmap_self_test(void);
