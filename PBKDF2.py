import getpass
from hashlib import sha512, sha384, sha256, sha224
import os
import struct
import sys
import zlib
import bz2
from cStringIO import StringIO as strio
import userinput as usr

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
COMPRESSION = {
	0: None,
	1: zlib,
	2: bz2,
}
CRYPT_EXT = '.phse'
MAGIC = "PBKDF2-HMAC-SHA2"
PWD_HASH_MULT = 20
sha2 = None	# set later

def _exit():
	raw_input("\npress Enter to exit...")
	sys.exit()

def bitPack(algonum, exp_incr, compressornum):
	bitstr = (bin(algonum)[2:].zfill(2)
			+ bin(exp_incr)[2:].zfill(2)
			+ bin(compressornum)[2:].zfill(2)
			+ '00')
	
	r = int('0b' + bitstr, 2)
	return r

def bitUnpack(_int):
	bitstr = bin(_int)[2:].zfill(8)
	algonum = int('0b' + bitstr[:2], 2)
	increment_by = int('0b' + bitstr[2:4], 2)
	compressornum = int('0b' + bitstr[4:6], 2)
	
	r = (algonum, increment_by, compressornum)
	return r 

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

def main():
	global sha2
	_input = open(sys.argv[1], 'rb')
	action = usr.getAction(sys.argv[1])
		
	if action in ('i', 'd'):
		_input = open(sys.argv[1], 'rb')
		## Verify MAGIC
		assert(_input.read(len(MAGIC)) == MAGIC) 
		
		## Extract key derivation parameters from header
		algonum, exp_incr, compressornum = bitUnpack(struct.unpack('<B', _input.read(1))[0])
		_range = xrange(0,4)
		assert(algonum in _range and exp_incr in _range and compressornum in _range)
		sha2 = ALGOS[algonum]
		iter_count = 2 ** (16 + exp_incr)
		digestsz = DIGESTSIZES[algonum]
		compressor = COMPRESSION[compressornum]
		if compressor is not None:
			compr_name = compressor.__name__
		else:
			compr_name = 'none'
		salt = _input.read(digestsz)
		embedded_hash = _input.read(digestsz)
		hashed_password_iters = iter_count * PWD_HASH_MULT
		
		if action == 'i':
			print
			print "This file was encrypted using the following parameters"
			print
			print "hash algorithm:", sha2.__name__
			print "compression:", compr_name
			print "key derivation rounds:", iter_count
			print "password hash rounds:", hashed_password_iters
			print "salt:", salt.encode('hex')
			print "hashed password:", embedded_hash.encode('hex')
			_exit()
	
	if action == 'e':
		algonum = usr.getHashAlgoNum()
		sha2 = ALGOS[algonum]
		exp_incr = usr.getExponentIncrement()
		compressornum = usr.getCompression()
		compressor = COMPRESSION[compressornum]
		_input = strio(compressor.compress(_input.read()))
		iter_count = 2 ** (16 + exp_incr)
		digestsz = DIGESTSIZES[algonum]
		salt = os.urandom(digestsz)
		password = usr.getPassword()
		hdr = MAGIC + struct.pack('<B', bitPack(algonum, exp_incr, compressornum))
		hdr += salt

		hashed_pwd = sha2(salt + password).digest()
		for _ in xrange(iter_count * PWD_HASH_MULT):
			hashed_pwd = sha2(salt + hashed_pwd).digest()
		hdr += hashed_pwd

	elif action == 'd':
		password = getpass.getpass()
		sys.stdout.write("\nHashing password...")
		sys.stdout.flush()
		hashed_pwd = sha2(salt + password).digest()
		for _ in xrange(hashed_password_iters):
			hashed_pwd = sha2(salt + hashed_pwd).digest()
		sys.stdout.write("\ndone...")
		sys.stdout.flush()
		assert(constTimeCompare(embedded_hash, hashed_pwd))

	# # Key stretching
	sys.stdout.write("\nDeriving key...")
	sys.stdout.flush()
	keyblock = genKeyBlock(password, salt)
	for _ in xrange(iter_count):
		keyblock = genKeyBlock(keyblock, salt)
	print "done."
	
	if action == 'e':
		out = open(sys.argv[1] + CRYPT_EXT, 'wb')
		out.write(hdr)
		sys.stdout.write("Encrypting...")
		sys.stdout.flush()
	
	elif action == 'd':
		out = open(sys.argv[1].replace(CRYPT_EXT, ''), 'wb')
		sys.stdout.write("Decrypting...")
		sys.stdout.flush()
	
	while 1:
		in_bytes = _input.read(digestsz)
		if in_bytes:
			keyblock = genKeyBlock(keyblock, salt)
			outstr = ''
			for bytenum in xrange(len(in_bytes)):
				outstr += (chr(ord(keyblock[bytenum]) ^ ord(in_bytes[bytenum])))
			out.write(outstr)
		else:
			out.close()
			break
		
	if action == 'd' and compressor is not None:
		outplain = compressor.decompress(open(sys.argv[1].replace(CRYPT_EXT, ''), 'rb').read())
		open(sys.argv[1].replace(CRYPT_EXT, ''), 'wb').write(outplain)
		
	print "done."
	_exit()

if __name__ == "__main__" and len(sys.argv) == 2:
	try:
		main()
	except AssertionError as e:
		print "Critical assertion failed in function main()!"
		raise e
	exit()
# # EOF
