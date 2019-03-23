/*
 *	bitmap.c - bitmap implementation
 *
 *	This bitmap implementation serves as resource allocator. Each resource
 *	is tracked by a single bit in the bitmap allocator; a bit being 0
 *	indicates that the resource is not allocated, a bit being 1 indicates
 *	that the resource is allocated.
 *
 *	Created August 2016 by felix.marti@fungible.com.
 *	Copyright © 2016 Fungible. All rights reserved.
 */

#include <string.h>
#include <stdio.h>
#include <stdlib.h>

//#include <types.h>

#include "fun_api.h"	// for FUN_RET_ENOMEM
#include "fun_bitmap.h"

/**
 *	off8_to_index - returns the bitmap memory index for a given offset
 *	@bm  : the bitmap pointer
 *	@off8: the offset in units of 8-bytes
 */
static inline unsigned int off8_to_index(struct bitmap *bm, unsigned int off8)
{
	unsigned int index = bm->bm_mem_size8 - 1 - off8;

	assert((int)index >= 0);

	return index;
}

/**
 *	bitmap_bget - find the next unused (zero) bit in the bitmap
 *		      and return its location
 *	@bm: the bitmap pointer
 *
 *	If a bit is available, the while(1) must eventually find it and exit.
 */
int bitmap_bget(struct bitmap *bm)
{
	unsigned int off8 = bm->bm_mem_off8;
#ifndef NDEBUG
	unsigned int start_off8 = off8;
#endif /* NDEBUG */

	if (!bm->bm_nbits_available) {
		return -FUN_RET_ENOMEM;
	}

	bm->bm_nbits_available--;

	while (1) {
		unsigned int idx = off8_to_index(bm, off8);
		unsigned int ffs;
		uint64_t val;

		/* MIPS features an instruction to find the first bit set to
		 * one... we invert the bitmap value since we are looking for
		 * the first bit set to 0
		 *
		 * we could make use of MIPS load-bonding by reading
		 * bm_mem[idx] and bm_mem[idx + 1] back to back, unrolling the
		 * loop, but the implementation ends up being not as compact
		 */
		val = ~bm->bm_mem[idx];

		ffs = __builtin_ffsl(val);
		if (ffs > 0) {

			ffs -= 1;
			bm->bm_mem_off8 = off8;
			bm->bm_mem[idx] |= 1ULL << ffs;
			return (off8 << 6) + ffs;
		}

		if (++off8 == bm->bm_mem_size8)
			off8 = 0;

		assert(off8 != start_off8);
	}
}

/**
 *	bitmap_bavail - returns true if given bit is available
 *	@bm : the bitmap pointer
 *	@bit: the bit to return
 */
bool bitmap_bavail(struct bitmap *bm, unsigned int bit)
{
	unsigned int off8 = bit >> 6;
	unsigned int idx = off8_to_index(bm, off8);
	uint64_t mask = 1ULL << (bit & 63);

	assert(bit < bm->bm_nbits);

	return ((bm->bm_mem[idx] & mask) == 0);
}

/**
 *	bitmap_bget_bavail - if given bit is available, allocate and
 *		return success (0)
 *	@bm : the bitmap pointer
 *	@bit: the bit to return
 */
int bitmap_bget_avail(struct bitmap *bm, unsigned int bit)
{
	unsigned int off8 = bit >> 6;
	unsigned int idx = off8_to_index(bm, off8);
	uint64_t mask = 1ULL << (bit & 63);

	if ((bm->bm_mem[idx] & mask) == 0) {
		assert(bm->bm_nbits_available);
		bm->bm_nbits_available--;
		bm->bm_mem_off8 = off8;
		bm->bm_mem[idx] |= 1ULL << bit;
		return 0;
	}

	return -1;
}

/**
 *	bitmap_bput - returns a bit to the bitmap
 *	@bm : the bitmap pointer
 *	@bit: the bit to return
 */
int bitmap_bput(struct bitmap *bm, unsigned int bit)
{
	unsigned int off8 = bit >> 6;
	unsigned int idx = off8_to_index(bm, off8);
	uint64_t mask = 1ULL << (bit & 63);

	assert(bit < bm->bm_nbits);
	assert(bm->bm_mem[idx] & mask);

	bm->bm_nbits_available++;

	bm->bm_mem[idx] &= ~mask;

	/* while not a requirement, we start allocating from bit0 again if all
	 * bits have been cleared
	 */
	if (bitmap_bempty(bm))
		bm->bm_mem_off8 = 0;
	else
		bm->bm_mem_off8 = bit >> 6;

	return 0;
}

/**
 *	bitmap_biterate - iterates over set bits
 *	@bm   : the bitmap pointer
 *	@start: the pointer to the start bit location (caller initializes
 *		*start = 0 and the implementation keeps updating *start as
 *		it iterates over the bitmap)
 */
int bitmap_biterate(struct bitmap *bm, unsigned int *start)
{
	unsigned int bit = *start;
	unsigned int shift;
	unsigned int off8;
	unsigned int idx;
	uint64_t val;

	if (bit >= bm->bm_nbits)
		goto not_found;

	shift = bit & 63;
	off8 = bit >> 6;
	idx = off8_to_index(bm, off8);
	val = bm->bm_mem[idx] >> shift;

	while (1) {
		unsigned int ffs = __builtin_ffsl(val);

		if (ffs > 0) {
			unsigned int found = (off8 << 6) + ffs - 1 + shift;

			if (found >= bm->bm_nbits)
				goto not_found;

			*start = found + 1;
			return found;
		}

		if (!idx--)
			break;

		val = bm->bm_mem[idx];
		shift = 0;
		off8++;
	}

not_found:
	return -1;
}

/******************************************************************************
 *   B I T M A P
 ******************/

/**
 *	bitmap_size - returns the size of a bitmap in size
 *	@nbits: the number of bits to store in the bitmap
 */
unsigned int bitmap_size(unsigned int nbits)
{

	return sizeof(struct bitmap) + (ALIGN(nbits, 64) >> 3);
}

/**
 *	bitmap_init - initializes a bitmap
 *	@mem  : the memory location pointer where the bitmap control structure
 *	        and actual bitmap is stored
 *	@nbits: the number of bits in the bitmap
 *
 *	The control structure is immediately followed by the bitmap itself. The
 *	storage of the bitmap is rounded up to the next 64-bits (extra bits are
 *	initialized to one so that they are never allocated
 */
struct bitmap *bitmap_init(void *mem, unsigned int nbits)
{
	struct bitmap *bm = (struct bitmap *)mem;
	unsigned int n = nbits & 63;

	assert(!((unsigned long)mem & (BITMAP_MEMALIGNMENT - 1)));

	memset(mem, 0, bitmap_size(nbits));

	bm->bm_mem_size8 = ALIGN(nbits, 64) >> 6;
	bm->bm_mem_off8 = 0;
	bm->bm_nbits = nbits;
	bm->bm_nbits_available = nbits;

	if (n) {
		bm->bm_mem[0] = ~((1ULL << n) - 1);
	}

	return bm;
}

int bitmap_fini(struct bitmap *bm)
{
	return 0;
}

void bitmap_dump(struct bitmap *bm)
{
	unsigned int start = ALIGN(bm->bm_nbits, 64) - 1;
	unsigned int i;

	printf("bitmap_dump\n");
	printf("\t[%p] mem_size8 %u nbits %u nbits_available %u bit_off8 %u\n",
	       bm, bm->bm_mem_size8, bm->bm_nbits, bm->bm_nbits_available,
	       bm->bm_mem_off8);

	for (i = 0; i < bm->bm_mem_size8; i++, start -= 64) {

		printf("\t[%p] bits[%8u:%8u] 0x%016" PRIx64,
		       &bm->bm_mem[i], start, start - 63, bm->bm_mem[i]);
		if (!i && bm->bm_nbits & 63) {
			printf(", bits [%8u:%8u] are reserved",
			       ALIGN(bm->bm_nbits, 64) - 1, bm->bm_nbits);
		}
		printf("\n");
	}
}

/******************************************************************************
 *   T E S T S
 ****************/

// TODO: THIS TEST CURRENTLY FAILS!
void bitmap_self_test(void) {
	void *p = malloc(4096);
	p = ALIGN(p, 16);

	struct bitmap *bm = bitmap_init(p, 64);
	bitmap_dump(bm);
	unsigned int i;
	for (i = 0; i < 248; i++) {
		printf("%u\n", bitmap_bget(bm));
	}
	bitmap_bput(bm, 32);
	printf("after freeing %u\n", bitmap_bget(bm));
	bitmap_bput(bm, 67);
	printf("after freeing %u\n", bitmap_bget(bm));
	bitmap_bput(bm, 130);
	printf("after freeing %u\n", bitmap_bget(bm));
	bitmap_bput(bm, 199);
	printf("after freeing %u\n", bitmap_bget(bm));
	bitmap_bput(bm, 199);
	printf("after freeing %u\n", bitmap_bget(bm));

	for (i = 0; i < 246; i++) {
		bitmap_bput(bm, i);
	}
	bm->bm_mem_off8 = 0;
	printf("%u\n", bitmap_bget(bm));
	printf("%u\n", bitmap_bget(bm));

	int found = 0;
	unsigned int iter = 0;
	bitmap_dump(bm);
	do {
		found = bitmap_biterate(bm, &iter);
		if (found >= 0)
			printf("FOUND %u\n", found);
	} while (found >= 0);
	free(p);
}

