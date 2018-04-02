/* for bugs: jitendra.lulla@fungible.com 
 * in the examples below, 1m is a filename
 * examples sha1/2/3:
 ./sendfile_hash sha1-generic 1m
 ./sendfile_hash sha224-generic 1m
 ./sendfile_hash sha3-256-generic 1m

 * examples hmac
 ./sendfile_hash "hmac(sha3-224-generic)" 1m key_hex_imm "\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b"

 ./sendfile_hash "hmac(sha3-224-generic)" 1m key_text_imm "Jefe"

 ./sendfile_hash "hmac(sha3-224-generic)" 1m key_hex_esc_imm "0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b"

 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <linux/if_alg.h>
#include <linux/socket.h>
#include <sys/sendfile.h>

#define SHA1_DGST_SZ 20 
#define SHA3_224_DGST_SZ 28
#define SHA3_256_DGST_SZ 32
#define SHA3_384_DGST_SZ 48
#define SHA3_512_DGST_SZ 64

#define BFR_SZ 4096
#ifndef SOL_ALG
#define SOL_ALG 279
#endif

//#define DBG
#ifdef DBG
#define jprintf printf
#else
#define jprintf(fmt, args...)
#endif

int open_file_for_reading(char *name)
{
	int read_fd;
	read_fd = open (name, O_RDONLY);
}

int find_dgst_len(unsigned char *digest)
{
	if(strstr(digest, "224"))
		return SHA3_224_DGST_SZ;
	else if(strstr(digest, "256"))
		return SHA3_256_DGST_SZ;
	else if(strstr(digest, "384"))
                return SHA3_384_DGST_SZ;
	else if(strstr(digest, "512"))
                return SHA3_512_DGST_SZ;
	else if(strstr(digest, "sha1"))
		return SHA1_DGST_SZ;
}

int conv(unsigned char *multi_char_str, unsigned char key[], int keylen)
{       
        int i;
        unsigned char two_char_str[2] = {0};
        jprintf("%s input:%c%c keylen:%d\n", __func__, 
                multi_char_str[0], multi_char_str[1], keylen);
        for(i=0; i<keylen; i++) {
                strncpy(two_char_str, (multi_char_str + (2*i)), 2);
                key[i] = strtol(two_char_str, NULL, 16);
        }
        return 0;
}

/* this function assumes the input of type
 * \xde\xad\xbe\xef
 */
void strip_esc(unsigned char *input, unsigned char dest[])
{
        int i, j, len = strlen(input);
        for(i = 0, j=0; i< len; i+=4, j+=2) {
                jprintf("%c%c", *(input+i+2), *(input + i + 3));
                dest[j] = *(input+i+2);
                dest[j+1] = *(input + i + 3);
        }
        jprintf("strlen(dest):%ld\n", strlen(dest));
}

/* this functions expects input of type deadbeaf */
void strip_esc1(unsigned char *input, unsigned char dest[])
{
        int i, j, len = strlen(input);
        for(i = 0, j=0; i< len; i+=2, j+=2) {
                jprintf("%c%c", *(input+i), *(input + i + 1));
                dest[j] = *(input+i);
                dest[j+1] = *(input + i + 1);
        }
        jprintf("strlen(dest):%ld\n", strlen(dest));
}

void populate_imm_key(unsigned char *keyword, unsigned char *passedkey,
			unsigned char *key)
{
	unsigned char str_no_escape_char[256] = {0};
	int i;
	if(strstr(keyword, "hex_esc")){
		jprintf("%s hex immediate key %s len:%ld\n", __func__,
			passedkey, strlen(passedkey));
		strip_esc1(passedkey, str_no_escape_char);
		conv(str_no_escape_char, key, strlen(passedkey)/2);
		for(i=0; i<strlen(passedkey)/4; i++)
			jprintf("%x ", key[i]);
	} else if (strstr(keyword, "hex")){
                jprintf("%s hex immediate key %s len:%ld\n", __func__,
                        passedkey, strlen(passedkey));
                strip_esc(passedkey, str_no_escape_char);
                conv(str_no_escape_char, key, strlen(passedkey)/4);
                for(i=0; i<strlen(passedkey)/4; i++)
                        jprintf("%x ", key[i]);
	} else { 
		jprintf("%s ascii immediate key\n", __func__);	
		strncpy(key, passedkey, strlen(passedkey));
	}
}

void populate_key_file(unsigned char *keyword, unsigned char *keyfile, unsigned char *key)
{
	printf("%s\n", __func__);
}

void parse_input(int argc, char **argv, char *key, int *hmac)
{
	int i;
	jprintf("%s argc:%d argv[2]:%s\n", __func__, argc, argv[2]);
	jprintf("%s argv[4]:%s strlen:%ld\n", __func__, argv[4], strlen(argv[4]));
	if(strstr(argv[1], "hmac")) {
		if(strstr(argv[3], "imm"))
			populate_imm_key(argv[3], argv[4], key);
		else
			populate_key_file(argv[3], argv[4], key);
		*hmac = 1;
	} 
}

int main(int argc, char **argv)
{
	off_t offset = 0;
	int hmac = 0;
	if(argc < 2) {
		printf("usage: digest_hmac <dgst or hmac> <textfile>"
			" [key_text_imm| key_hex_imm "
			" <key>]\n");
		return 1;
	}
	if(strstr(argv[1], "version")) {
		printf("0.1\n");
		return 1;
	}
        struct sockaddr_alg sa = {
        .salg_family = AF_ALG,
        .salg_type = "hash",
        };
	memcpy(&sa.salg_name, argv[1], strlen(argv[1])); 
	unsigned char bfr[BFR_SZ] = {0x0};
	unsigned char key[128] = {0};
	unsigned char digest[SHA3_512_DGST_SZ] = {0};
        long int sockfd, fd;
	long int filesz, dgst_len;
	struct stat stat_buf;
	int read_fd, i;

	parse_input(argc, argv, key, &hmac);

	read_fd = open_file_for_reading(argv[2]);
	fstat (read_fd, &stat_buf);
	filesz = stat_buf.st_size;
	dgst_len = find_dgst_len(argv[1]);
	jprintf("filesize:%ld dgst_len:%ld\n", filesz, dgst_len);


        sockfd = socket(AF_ALG, SOCK_SEQPACKET, 0);
        bind(sockfd, (struct sockaddr *)&sa, sizeof(sa));
	if(hmac)
		setsockopt(sockfd, SOL_ALG, ALG_SET_KEY, key, sizeof(key));
        fd = accept(sockfd, NULL, 0);
	jprintf("accept fd:%ld fd errno:%d %s\n", fd, errno, strerror(errno));
	sendfile (fd, read_fd, &offset, stat_buf.st_size);
	recv(fd, digest, dgst_len, 0);
        close(fd);
        close(sockfd);
	close(read_fd);
        for (i = 0; i < dgst_len; i++)
        printf("%02x", digest[i]);
	printf("\n");
        return 0;
}
