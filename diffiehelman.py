# use Python 3 print function
# this allows this code to run on python 2.x and 3.x
from __future__ import print_function
from primes import getPrime
import multiprocessing as multi
import time

if __name__ == '__main__':

	BITS = int(1024 * 1.0)
	POOL_SZ = multi.cpu_count()
	
	SHARED_BASE = 2
	SHARED_PRIME = 0
	
	ALICE_SHARED_COMPUTED = 0
	ALICE_SECRET = 0
	
	BOB_SHARED_COMPUTED = 0
	BOB_SECRET = 0
	
	pool = multi.Pool(POOL_SZ)
	
	def setPrime(p):
		global pool, SHARED_PRIME, ALICE_SECRET, BOB_SECRET
		
		if not SHARED_PRIME:
			SHARED_PRIME = p
			pool.apply_async(getPrime, (BITS,), callback=setPrime)
			print('callback set SHARED_PRIME')
			return
		elif not ALICE_SECRET:
			ALICE_SECRET = p
			pool.apply_async(getPrime, (BITS,), callback=setPrime)
			print('callback set ALICE_SECRET')
			return
		elif not BOB_SECRET:
			BOB_SECRET = p
			print('callback set BOB_SECRET')
			pool.terminate()

		
	for _ in xrange(POOL_SZ):
		pool.apply_async(getPrime, (BITS,), callback=setPrime)
	
	
	while 1:
		if SHARED_PRIME:
			
			if BOB_SECRET and not BOB_SHARED_COMPUTED:
				BOB_SHARED_COMPUTED = pow(SHARED_BASE, BOB_SECRET, SHARED_PRIME)
			
			if ALICE_SECRET and not ALICE_SHARED_COMPUTED:
				ALICE_SHARED_COMPUTED = pow(SHARED_BASE, ALICE_SECRET, SHARED_PRIME)
			
			if ALICE_SHARED_COMPUTED and BOB_SHARED_COMPUTED:
				break
		time.sleep(0.1)
		
	print( "\nPublicly Shared Variables:")
	print( "\tShared Base:  ", SHARED_BASE )
	print( "\tShared Prime: " , SHARED_PRIME )

	print( "\n---------------------------------------------" )
	print( "Privately Calculated Shared Secret (%d bits):" % BITS )
	
	aliceSharedSecret = pow(BOB_SHARED_COMPUTED, ALICE_SECRET, SHARED_PRIME)
	print("\tAlice: ", aliceSharedSecret )
	
	bobSharedSecret = pow(ALICE_SHARED_COMPUTED, BOB_SECRET, SHARED_PRIME)
	print("\tBob:   ", bobSharedSecret )
	
	assert bobSharedSecret == aliceSharedSecret
	