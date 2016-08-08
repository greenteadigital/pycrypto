#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <gmp.h>
#include <pthread.h>

const int NTHREADS = 2;
void *returnedPrime;
pthread_mutex_t mutex;

void getRandom(unsigned char *buffer, long numbytes) {
	// read from /dev/urandom
	FILE *randfile = fopen("/dev/urandom", "r");
	int numread = 0;
	while (numread < numbytes) {
		numread += fread(buffer, 1, numbytes, randfile);
	}
}

void tryPrime(void *bitsize) {

	const int SEED_SZ_BYTES = 16;	// 128 bits
	const int WORD_SZ_BYTES = __WORDSIZE / 8;

	short PRIME_SZ = *((short*)bitsize);
	unsigned char seed_buff[SEED_SZ_BYTES];
	unsigned char *seed_buff_p = &seed_buff[0];

	gmp_randstate_t state;
	gmp_randinit_mt(state);

	mpz_t seed, randnum;
	mpz_init(seed);
	mpz_init(randnum);

	getRandom(seed_buff_p, SEED_SZ_BYTES);
	mpz_import(seed, (SEED_SZ_BYTES/WORD_SZ_BYTES), -1, WORD_SZ_BYTES, 0, 0, seed_buff_p);
	gmp_randseed(state, seed);

	while(1) {
		mpz_urandomb(randnum, state, PRIME_SZ);
		if (mpz_probab_prime_p(randnum, 17)) break;
	}
	
	pthread_mutex_lock(&mutex);
	returnedPrime = malloc((PRIME_SZ / 8));
	mpz_export(returnedPrime, NULL, -1, WORD_SZ_BYTES, 0, 0, randnum);
	//pthread_mutex_unlock(&mutex);

	gmp_printf("%Zd", randnum);

	//gmp_randclear(state);
	//mpz_clear(seed);
	//mpz_clear(randnum);

	exit(0);
}

void *getPrime(unsigned short bitlen) {

	pthread_mutex_init(&mutex, NULL);
	
	for (int i = 0; i != NTHREADS; i++) {
		pthread_t new_thread;
		pthread_create(&new_thread, NULL, (void *) &tryPrime, (void *) &bitlen);
		int join_result;
		pthread_join(new_thread, (void *) &join_result);
		
	}

	printf("\nprime pointer points to address %p\n", returnedPrime);
	return returnedPrime;
}

int main(int argc, char *argv[]) {
	if (argc < 2) return 1;
	getPrime(atoi(argv[1]));
	return 0;
}
