# use Python 3 print function
# this allows this code to run on python 2.x and 3.x
from __future__ import print_function
from primes import getPrime
import multiprocessing as multi
import time

if __name__ == '__main__':

	BITS = 1024*2
	SHARED_BASE = 2
	
	SHARED_PRIME = 0
	ALICE_SECRET = 0
	BOB_SECRET = 0
	A = 0
	B = 0
	pool = multi.Pool(3)
	
	def sp(p):
		global SHARED_PRIME
		SHARED_PRIME = p
		print('callback set SHARED_PRIME')
# 		if not ALICE_SECRET:
# 			ALICE_SECRET = pool.apply_async(getPrime, (BITS,)).get()
	
	def sa(p):
		global ALICE_SECRET
		ALICE_SECRET = p
		print('callback set ALICE_SECRET')
# 		if not BOB_SECRET:
# 			BOB_SECRET = pool.apply_async(getPrime, (BITS,)).get()
	
	def sb(p):
		global BOB_SECRET
		BOB_SECRET = p
		print('callback set BOB_SECRET')
# 		if not SHARED_PRIME:
# 			SHARED_PRIME = pool.apply_async(getPrime, (BITS,)).get()
		
	
	pool.apply_async(getPrime, (BITS,), callback=sp)
	pool.apply_async(getPrime, (BITS,), callback=sa)
	pool.apply_async(getPrime, (BITS,), callback=sb)
	
	while 1:
		if SHARED_PRIME:
			if BOB_SECRET:
				B = pow(SHARED_BASE, BOB_SECRET, SHARED_PRIME)
			if ALICE_SECRET:
				A = pow(SHARED_BASE, ALICE_SECRET, SHARED_PRIME)
			if A and B:
				break
		time.sleep(0.1)
		
	# Begin
	print( "Publicly Shared Variables:")
	print( "\tShared Base:  ", SHARED_BASE )
	print( "\tShared Prime: " , SHARED_PRIME )

	print( "\n---------------------------------" )
	print( "Privately Calculated Shared Secret:" )
	# Alice Computes Shared Secret: s = B^a mod p
	aliceSharedSecret = pow(B, ALICE_SECRET, SHARED_PRIME)
	print("\tAlice: ", aliceSharedSecret )
	
	# Bob Computes Shared Secret: s = A^b mod p
	bobSharedSecret = pow(A, BOB_SECRET, SHARED_PRIME)
	print("\tBob:   ", bobSharedSecret )
	
	assert bobSharedSecret == aliceSharedSecret
	