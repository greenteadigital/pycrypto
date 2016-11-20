import subprocess

def getRandPrime(bitlen):
	return int(subprocess.Popen(["/Users/ben/Desktop/primes", '-b', bitlen], stdout=subprocess.PIPE).communicate()[0])

BITS = '2048'

SHARED_BASE = 2
SHARED_MODULUS = getRandPrime(BITS)

ALICE_SECRET = getRandPrime(BITS)
ALICE_SHARED_COMPUTED = 0

BOB_SECRET = getRandPrime(BITS)
BOB_SHARED_COMPUTED = 0

ALICE_SHARED_COMPUTED = pow(SHARED_BASE, ALICE_SECRET, SHARED_MODULUS)
BOB_SHARED_COMPUTED = pow(SHARED_BASE, BOB_SECRET, SHARED_MODULUS)
		
print "\nPublicly Shared Variables:"
print "\tShared Base:  ", SHARED_BASE 
print "\tShared Modulus: " , SHARED_MODULUS 

print "\n-----------------------------------------------"
print "Privately Calculated Shared Secret (%s bits):" % BITS

aliceSharedSecret = pow(BOB_SHARED_COMPUTED, ALICE_SECRET, SHARED_MODULUS)
print "\tAlice: ", aliceSharedSecret

bobSharedSecret = pow(ALICE_SHARED_COMPUTED, BOB_SECRET, SHARED_MODULUS)
print "\tBob:   ", bobSharedSecret

assert bobSharedSecret == aliceSharedSecret
	