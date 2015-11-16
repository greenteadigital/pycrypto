#include <stdio.h>
#include <gmp.h>
#include <windows.h>

HCRYPTPROV hProvider;
const int NTHREADS = 4;
void *returnedPrime;
void *mutex;

void getRandom(unsigned char *buffer, long numbytes) {
	while (!hProvider) {
	  CryptAcquireContext(&hProvider, 0, 0, PROV_RSA_FULL, CRYPT_VERIFYCONTEXT);
	}
	int cryptGenSuccess = 0;
	while (!cryptGenSuccess) {
	  cryptGenSuccess = CryptGenRandom(hProvider, numbytes, buffer);
	}
}

unsigned int tryPrime(void *bitsize) {

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

	WaitForSingleObject(mutex, INFINITE);
	returnedPrime = malloc((PRIME_SZ / 8));
	mpz_export(returnedPrime, NULL, -1, WORD_SZ_BYTES, 0, 0, randnum);

	gmp_printf("%Zd\n\n", randnum);

	gmp_randclear(state);
	mpz_clear(seed);
	mpz_clear(randnum);

	return 0;
}

void *getPrime(unsigned short bitlen) {

	void *bitsize = malloc(sizeof(bitlen));
	if (!bitsize) puts("malloc failed");
	memcpy(bitsize, &bitlen, sizeof(bitlen));
	mutex = CreateMutex(NULL, FALSE, NULL);

	void *threads[NTHREADS];
	for (int i = 0; i != NTHREADS; i++) {
		threads[i] = CreateThread(NULL, 0, &tryPrime, bitsize, 0, NULL);
	}
	WaitForMultipleObjects(NTHREADS, threads, FALSE, INFINITE);
	for (int i = 0; i != NTHREADS; i++) {
		TerminateThread(threads[i], 0);
	}

	CloseHandle(mutex);
	//printf("\nprime pointer points to address %p\n", returnedPrime);
	return returnedPrime;
}

int main(int argc, char *argv[]) {
	if (argc < 2) return 1;
	getPrime(atoi(argv[1]));
	return 0;
}
