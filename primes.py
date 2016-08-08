# from random import SystemRandom
# import miller_rabin as m_r
# sysrand = SystemRandom()
import subprocess

# def getPrime(numbits):
# 	while 1:
# 		n = sysrand.getrandbits(numbits) | 1
# 		if m_r.isPrime(n):
# 			return n

def CgetPrime(numbits):
	return int(subprocess.Popen(["/Users/ben/Desktop/primes", numbits], stdout=subprocess.PIPE).communicate()[0])