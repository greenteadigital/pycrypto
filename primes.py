from random import SystemRandom
import miller_rabin as m_r

sysrand = SystemRandom()

def getPrime(numbits):
	while 1:
		n = sysrand.getrandbits(numbits) | 1
		if m_r.isPrime(n):
			return n