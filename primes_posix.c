#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <gmp.h>
#include <pthread.h>
#include <sph_md5.h>

int NTHREADS = 4;

unsigned char rand_base[16];
char rand_base_set = 0;

pthread_mutex_t printlock;
pthread_mutex_t randbase_lock;

void md5(sph_md5_context *ctxt_ptr, unsigned char *inbuff, const char inbuffsz, unsigned char *outbuff) {
	
	sph_md5(ctxt_ptr, inbuff, inbuffsz);
	sph_md5_close(ctxt_ptr, outbuff);
}

void getRandom(unsigned char *buffer, const char numbytes, sph_md5_context *ctxt) {
	
	if (!rand_base_set) {
		FILE *randfile = fopen("/dev/urandom", "r");
		int numread = 0;
		while (numread < numbytes) {
			numread += fread((void *) buffer, 1, numbytes, randfile);
		}
		pthread_mutex_lock(&randbase_lock);
		rand_base_set = 1;
		memcpy(rand_base, buffer, numbytes);
		pthread_mutex_unlock(&randbase_lock);
	} else {
		md5(ctxt, &rand_base[0], numbytes, buffer);
		pthread_mutex_lock(&randbase_lock);
		memcpy(rand_base, buffer, numbytes);
		pthread_mutex_unlock(&randbase_lock);
	}
}

void tryPrime(void *bitsize) {

	const char SEED_SZ_BYTES = 16;	// 128 bits for random seed

	short PRIME_SZ = *((short*)bitsize);
	unsigned char seed_buff[SEED_SZ_BYTES];
	unsigned char *seed_buff_p = &seed_buff[0];

	gmp_randstate_t state;
	gmp_randinit_mt(state);

	mpz_t seed, randnum, one;
	mpz_init(seed);
	mpz_init(randnum);
	mpz_init(one);
	
	unsigned char single = 1;
	mpz_import(one, 1, -1, 1, 0, 0, &single);
	
	sph_md5_context ctxt;
	sph_md5_init((void *) &ctxt);
	
	getRandom(seed_buff_p, SEED_SZ_BYTES, &ctxt);
	mpz_import(seed, SEED_SZ_BYTES, -1, 1, 0, 0, seed_buff_p);
	gmp_randseed(state, seed);

	while(1) {
		mpz_urandomb(randnum, state, PRIME_SZ);
		mpz_ior(randnum, randnum, one);	// make sure randnum is odd by bitwise-ORing with 1
		if (mpz_probab_prime_p(randnum, 17)) break;
	}
	
	pthread_mutex_lock(&printlock);
	gmp_printf("%Zd", randnum);
	exit(0);
}

void getPrime(unsigned short bitlen) {

	pthread_mutex_init(&printlock, NULL);
	pthread_mutex_init(&randbase_lock, NULL);
	pthread_t threads[NTHREADS];
	
	for (int i = 0; i != NTHREADS; i++) {
		pthread_t new_thread;
		pthread_create(&new_thread, NULL, (void *) &tryPrime, (void *) &bitlen);
		threads[i] = new_thread;
	}
	
	for (int i = 0; i != sizeof(threads); i++) {
		pthread_join(threads[i], NULL);
	}
	
}

int main(int argc, char *argv[]) {
	if (argc < 2) return 1;
	if (argc == 2) getPrime(atoi(argv[1]));
	if (argc == 3) {
		NTHREADS = atoi(argv[2]);
		getPrime(atoi(argv[1]));
	}
	return 0;
}
