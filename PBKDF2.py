import getpass
from hashlib import sha512, sha384, sha256, sha224
import os
import struct
import sys

# # Global constants
SELECTED_ALGO = 0  # TODO: let user select algo
ALGOS = {
	0: sha224,
	1: sha256,
	2: sha384,
	3: sha512
}
DIGESTSIZES = {
	0: ALGOS[0]().digest_size,
	1: ALGOS[1]().digest_size,
	2: ALGOS[2]().digest_size,
	3: ALGOS[3]().digest_size
}
DIGESTSZ = DIGESTSIZES[SELECTED_ALGO] 
CRYPT_EXT = '.phse'
MAGIC = "PBKDF2-HMAC-SHA2"
# TODO: allow user input
EXP_INCR = 0; assert(0 <= EXP_INCR <= 4)  # enforce min/max
PWD_HASH_MULT = 20

# # Global variable, may change when decrypting file encrypted with other than selected algo.
sha2 = ALGOS[SELECTED_ALGO]

def bitPack(algonum, EXP_INCR):
	bitstr = bin(algonum)[2:].zfill(4) + bin(EXP_INCR)[2:].zfill(4)

	return int('0b' + bitstr, 2)

def bitUnpack(_int):
	bitstr = bin(_int)[2:].zfill(8)
	algonum = int('0b' + bitstr[:4], 2)
	increment_by = int('0b' + bitstr[4:], 2)

	return (algonum, increment_by)

def constTimeCompare(val1, val2):
	if len(val1) != len(val2):
		return False
	result = 0
	for x, y in zip(val1, val2):
		result |= ord(x) ^ ord(y)

	return not result

def genKeyBlock(password, salt):
	blksz = sha2().block_size
	passlen = len(password)
	if passlen < blksz:
		password += (chr(0) * (blksz - passlen))
	else:
		password = sha2(password).digest()
	o_pad = ''.join(chr(0x5c ^ ord(char)) for char in password)
	i_pad = ''.join(chr(0x36 ^ ord(char)) for char in password)

	return sha2(o_pad + sha2(i_pad + salt).digest()).digest()

def getAction(path):
	print
	print path
	print

	return raw_input("(E)ncrypt or (D)ecrypt? ").lower()

# @profile
def main():
	global sha2
	_input = open(sys.argv[1], 'rb')

	action = getAction(sys.argv[1])
	while action not in ('e', 'd'):
		action = getAction(sys.argv[1])

	if action == 'e':
		iter_count = 2 ** (16 + EXP_INCR)
		salt = os.urandom(DIGESTSZ)
		password = getpass.getpass()
		hdr = MAGIC + struct.pack('<B', bitPack(SELECTED_ALGO, EXP_INCR))
		hdr += salt

		hashed_pwd = sha2(salt + password).digest()
		for unused in xrange(iter_count * PWD_HASH_MULT):
			hashed_pwd = sha2(salt + hashed_pwd).digest()
		hdr += hashed_pwd

	elif action == 'd':
		_input = open(sys.argv[1], 'rb')
		
		# # Verify MAGIC
		assert(_input.read(len(MAGIC)) == MAGIC) 
		
		# # Extract key derivation parameters from header
		algonum, exp_incr = bitUnpack(struct.unpack('<B', _input.read(1))[0])
		sha2 = ALGOS[algonum]
		iter_count = 2 ** (16 + exp_incr)
		salt = _input.read(DIGESTSZ)
		embedded_hash = _input.read(DIGESTSZ)

		password = getpass.getpass()
		hashed_pwd = sha2(salt + password).digest()
		for unused in xrange(iter_count * PWD_HASH_MULT):
			hashed_pwd = sha2(salt + hashed_pwd).digest()
		assert(constTimeCompare(embedded_hash, hashed_pwd))

	# # Key stretching
	sys.stdout.write("\nDeriving key...")
	keyblock = genKeyBlock(password, salt)
	for unused in xrange(iter_count):
		keyblock = genKeyBlock(keyblock, salt)
	print "done."
	
	if action == 'e':
		out = open(sys.argv[1] + CRYPT_EXT, 'wb')
		out.write(hdr)
		sys.stdout.write("Encrypting...")
	
	elif action == 'd':
		out = open(sys.argv[1].replace(CRYPT_EXT, ''), 'wb')
		sys.stdout.write("Decrypting...")
	
	while 1:
		in_bytes = _input.read(DIGESTSZ)
		if in_bytes:
			keyblock = genKeyBlock(keyblock, salt)
			outstr = ''
			for n in xrange(len(in_bytes)):
				outstr += (chr(ord(keyblock[n]) ^ ord(in_bytes[n])))
			out.write(outstr)
		else:
			out.close()
			break
	print "done."

if __name__ == "__main__" and len(sys.argv) == 2:
	
	main()

raw_input("\npress Enter to exit...")
# # EOF
