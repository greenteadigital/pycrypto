#include <stdio.h>
#include <stdlib.h>
#include <gmp.h>
#include <windows.h>
#include <wincrypt.h>
#include <string.h>

HCRYPTPROV hProvider;
const int SEED_SZ = 16;	// 128 bits
const int NTHREADS = 4;
void *returnedPrime = NULL;
void *mutex = NULL;

void getRandom(unsigned char *buffer, long numbytes) {
  if (!hProvider) {
	  CryptAcquireContext(&hProvider, 0, 0, PROV_RSA_FULL, CRYPT_VERIFYCONTEXT);
  }
  if (!CryptGenRandom(hProvider, numbytes, buffer)) {
	  puts("CryptGenRandom failed.");
	  ExitProcess((UINT)-1);
  }
}

unsigned int tryPrime(void *bitsize) {

	short PRIME_SZ = *((short*)bitsize);
	unsigned char seed_buff[16];
	unsigned char *seed_buff_p = (void*) seed_buff;

	gmp_randstate_t state;
	mpz_t seed, randnum;

	gmp_randinit_mt(state);
	mpz_init(seed);
	mpz_init(randnum);

	while(1) {
		getRandom(seed_buff_p, SEED_SZ);
		mpz_import(seed, SEED_SZ, 1, 1, 0, 0, seed_buff_p);
		gmp_randseed(state, seed);
		mpz_urandomb(randnum, state, PRIME_SZ);
		if (mpz_probab_prime_p(randnum, 17)) break;
	}

	mutex = CreateMutex(NULL, 1, NULL);
	returnedPrime = malloc(PRIME_SZ / 8);
	mpz_export(returnedPrime, NULL, -1, 2, 0, 0, randnum);

	gmp_printf("%Zd\n\n", randnum);

	gmp_randclear(state);
	mpz_clear(seed);
	mpz_clear(randnum);

	return 0;
}

__declspec(dllexport) void *getPrime(short bitlen) {

	void *threads[NTHREADS];
	void *bitsize = malloc(sizeof(bitlen));
	if (!bitsize) puts("malloc failed");
	memcpy(bitsize, &bitlen, sizeof(bitlen));

	for (int i = 0; i != NTHREADS; i++) {
		threads[i] = CreateThread(NULL, 0, &tryPrime, bitsize, 0, NULL);
	}
	WaitForMultipleObjects(NTHREADS, threads, FALSE, INFINITE);
	for (int i = 0; i != NTHREADS; i++) {
		TerminateThread(threads[i], 0);
	}
	ReleaseMutex(mutex);
	CloseHandle(mutex);
	//printf("\nprime pointer points to address %p\n", returnedPrime);
	return returnedPrime;
}

int main(int argc, char *argv[]) {
	getPrime(atoi(argv[1]));
	return 0;
}
