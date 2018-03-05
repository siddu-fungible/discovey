/* for bugs: jitendra.lulla@fungible.com */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <linux/if_alg.h>
#include <linux/socket.h>

#define SHA1_DGST_SZ 20 
#define SHA3_224_DGST_SZ 28
#define SHA3_256_DGST_SZ 32
#define SHA3_384_DGST_SZ 48
#define SHA3_512_DGST_SZ 64

#define BFR_SZ 4096
//#define BFR_SZ 2048 
#ifndef SOL_ALG
#define SOL_ALG 279
#endif

//#define DBG
#ifdef DBG
#define jprintf printf
#else
#define jprintf(fmt, args...)
#endif

FILE *handle;

FILE *open_file_for_reading(char *name)
{
	handle = fopen(name, "r");
}

unsigned int read_file(FILE *handle, unsigned char bfr[], long int start_ofst)
{
	long int ret, i; 
	jprintf("%s entered, start_ofst:%ld\n", __func__, start_ofst);
	fseek(handle, start_ofst, SEEK_SET);
	fflush(handle);
	ret = fread((void*)bfr, 1, BFR_SZ, handle);
	jprintf("%s returning:%ld\n", __func__, ret);
	return ret;
} 

int close_file(FILE *handle)
{
	fclose(handle);
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
        jprintf("strlen(dest):%d\n", strlen(dest));
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
        jprintf("strlen(dest):%d\n", strlen(dest));
}

void populate_imm_key(unsigned char *keyword, unsigned char *passedkey,
			unsigned char *key)
{
	unsigned char str_no_escape_char[256] = {0};
	int i;
	if(strstr(keyword, "hex_esc")){
		jprintf("%s hex immediate key %s len:%d\n", __func__,
			passedkey, strlen(passedkey));
		strip_esc1(passedkey, str_no_escape_char);
		conv(str_no_escape_char, key, strlen(passedkey)/2);
		for(i=0; i<strlen(passedkey)/4; i++)
			jprintf("%x ", key[i]);
	} else if (strstr(keyword, "hex")){
                jprintf("%s hex immediate key %s len:%d\n", __func__,
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
	jprintf("%s argv[4]:%s strlen:%d\n", __func__, argv[4], strlen(argv[4]));
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
	struct stat st;
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
        long int i, sockfd, fd, read_bytes;
	long int filesz, dgst_len, flag = 0, start_ofst = 0;

	parse_input(argc, argv, key, &hmac);

	stat(argv[2], &st);
	filesz = st.st_size;
	dgst_len = find_dgst_len(argv[1]);
	jprintf("filesize:%ld dgst_len:%ld\n", filesz, dgst_len);

	handle = open_file_for_reading(argv[2]);

        sockfd = socket(AF_ALG, SOCK_SEQPACKET, 0);
        bind(sockfd, (struct sockaddr *)&sa, sizeof(sa));
	if(hmac)
		setsockopt(sockfd, SOL_ALG, ALG_SET_KEY, key, sizeof(key));
        fd = accept(sockfd, NULL, 0);
	
	while(start_ofst < filesz) {
		read_bytes =read_file(handle, bfr, start_ofst);
		jprintf("loop start:read_bytes:%ld start_ofst:%ld\n", 
				read_bytes, start_ofst);
		start_ofst += read_bytes;
		if ((read_bytes >= BFR_SZ) && (!feof(handle)))
			flag = MSG_MORE;
		else if ((read_bytes < BFR_SZ) && (feof(handle)))
			flag = 0;
		jprintf("loop: read_bytes:%ld start_ofst:%ld flag:%ld len:%d\n",
				read_bytes, start_ofst, flag, strlen(bfr));
		send(fd, bfr, read_bytes, flag);
		/* clear the buffer */
		memset(bfr, 0, sizeof(bfr));
	}

	recv(fd, digest, dgst_len, 0);
        close(fd);
        close(sockfd);
	close_file(handle);
        for (i = 0; i < dgst_len; i++)
        printf("%02x", digest[i]);
	printf("\n");
        return 0;
}
