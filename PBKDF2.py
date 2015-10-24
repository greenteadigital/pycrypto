import getpass
from hashlib import sha512, sha384, sha256, sha224
import os
import struct
import sys

algos = {
	0: sha224,
	1: sha256,
	2: sha384,
	3: sha512
}

digestsz = {
	0: algos[0]().digest_size,
	1: algos[1]().digest_size,
	2: algos[2]().digest_size,
	3: algos[3]().digest_size
}

# TODO: let user select algo
selected_algo = 3
_hash = algos[selected_algo]

crypt_ext = '.phse'
magic = "PBKDF2-HMAC-SHA2"

# TODO: allow user input
exp_incr = 0
assert(0 <= exp_incr <= 4)  # enforce min/max
iter_count = 2 ** (16 + exp_incr)
pwd_hash_mult = 20

def genSalt():
	salt = ''
	while len(salt) < digestsz[selected_algo]:
		salt += os.urandom(1)

	return salt

def bitPack(algonum, exp_incr):
	bitstr = bin(algonum)[2:].zfill(4) + bin(exp_incr)[2:].zfill(4)

	return int('0b' + bitstr, 2)

def bitUnpack(_int):
	bitstr = bin(_int)[2:].zfill(8)
	algonum = int('0b' + bitstr[:4], 2)
	exp_incr = int('0b' + bitstr[4:], 2)

	return (algonum, exp_incr)

def constTimeCompare(val1, val2):
	if len(val1) != len(val2):
		return False
	result = 0
	for x, y in zip(val1, val2):
		result |= ord(x) ^ ord(y)

	return not result

def genKeyBlock(password, salt):
	blksz = _hash().block_size
	passlen = len(password)
	if passlen < blksz:
		password += (chr(0) * (blksz - passlen))
	else:
		password = _hash(password).digest()
	o_pad = ''.join(chr(0x5c ^ ord(char)) for char in password)
	i_pad = ''.join(chr(0x36 ^ ord(char)) for char in password)

	return _hash(o_pad + _hash(i_pad + salt).digest()).digest()

def getAction(path):
	print
	print path
	print

	return raw_input("(E)ncrypt or (D)ecrypt? ").lower()

if len(sys.argv) == 2:
	_input = open(sys.argv[1], 'rb')

	action = getAction(sys.argv[1])
	while action not in ('e', 'd'):
		action = getAction(sys.argv[1])

	if action == 'e':
		salt = genSalt()
		password = getpass.getpass()
		hdr = magic + struct.pack('<B', bitPack(selected_algo, exp_incr))
		hdr += salt

		hashed_pwd = _hash(salt + password).digest()
		for unused in xrange(iter_count * pwd_hash_mult):
			hashed_pwd = _hash(salt + hashed_pwd).digest()
		hdr += hashed_pwd

	elif action == 'd':
		_input = open(sys.argv[1], 'rb')
		
		# # Verify magic
		assert(_input.read(len(magic)) == magic) 
		
		# # Extract key derivation parameters from header
		selected_algo, exp_incr = bitUnpack(struct.unpack('<B', _input.read(1))[0])
		hash_algo = algos[selected_algo]
		iter_count = 2 ** (16 + exp_incr)
		len_salt = digestsz[selected_algo]
		salt = _input.read(len_salt)
		pwd_hash = _input.read(len_salt)

		password = getpass.getpass()
		hashed_pwd = hash_algo(salt + password).digest()
		for unused in xrange(iter_count * pwd_hash_mult):
			hashed_pwd = hash_algo(salt + hashed_pwd).digest()
		assert(constTimeCompare(pwd_hash, hashed_pwd))

	# # Key stretching
	sys.stdout.write("\nDeriving key...")
	keyblock = genKeyBlock(password, salt)
	for unused in xrange(iter_count):
		keyblock = genKeyBlock(keyblock, salt)
	print "done."
	
	if action == 'e':
		out = open(sys.argv[1] + crypt_ext, 'wb')
		out.write(hdr)
		sys.stdout.write("Encrypting...")
	
	elif action == 'd':
		out = open(sys.argv[1].replace(crypt_ext, ''), 'wb')
		sys.stdout.write("Decrypting...")
	
	while 1:
		in_bytes = _input.read(digestsz[selected_algo])
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
raw_input("\npress Enter to exit...")
# # EOF
