
def isSpsp(testing, known_prime):
		d = testing - 1
		s = 0
		while d % 2 == 0:
			d = d / 2
			s =  s + 1
		t = pow(known_prime, d, testing)
		if t == 1:
			return True
		while s > 0:
			if t == testing - 1:
				return True
			t = (t * t) % testing
			s = s - 1
		return False

def isPrime(testing):
	known_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41,
		 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
	if testing in known_primes:
		return True
	for prime in known_primes:
		if not isSpsp(testing, prime):
			return False
	return True

