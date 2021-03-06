#!/usr/bin/env python3
import getpass
from hashlib import sha512, sha384, sha256, sha224
import os
import struct
import sys
import zlib
import bz2
from io import BytesIO as _bio
import userinput as usr
import traceback
from nullcompressor import NullCompressor

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
	0: NullCompressor(),
	1: zlib,
	2: bz2
}
CRYPT_EXT = '.phse'
MAGIC = b'PBKDF2-HMAC-SHA2'
PWD_HASH_MULT = 20
sha2 = None	# set later

def _exit():
	input("\npress Enter to exit...")
	sys.exit()

def bitPack(algonum, exp_incr, compressornum):
	bitstr = (bin(algonum)[2:].zfill(2)
			+ bin(exp_incr)[2:].zfill(2)
			+ bin(compressornum)[2:].zfill(2)
			+ '00')	## two bits left for storing metadata
	
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
		result |= x ^ y

	return not result

def genKeyBlock(password, salt):
	blksz = sha2().block_size
	passlen = len(password)
	if passlen < blksz:
		password += (b'\0' * (blksz - passlen))
	else:
		password = sha2(password).digest()
	o_pad = b''.join(bytes([0x5c ^ _byte]) for _byte in password)
	i_pad = b''.join(bytes([0x36 ^ _byte]) for _byte in password)

	return sha2(o_pad + sha2(i_pad + salt).digest()).digest()

def main():
	try:
		global sha2
		_input = open(sys.argv[1], 'rb')
		action = usr.getAction(sys.argv[1])
			
		if action in ('i', 'd'):
			_input = open(sys.argv[1], 'rb')
			## Verify MAGIC
			try:
				hdr = _input.read(len(MAGIC))
				assert(hdr == MAGIC)
			except AssertionError:
				raise AssertionError('File magic number does not match expected value. Aborting operation.') 
			
			## Extract key derivation parameters from header
			algonum, exp_incr, compressornum = bitUnpack(struct.unpack('<B', _input.read(1))[0])
			_range = range(0,4)
			try:
				assert(algonum in _range
					and exp_incr in _range
					and compressornum in _range)
			except AssertionError:
				raise AssertionError('Values unpacked from bitfields are out of range!')
				
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
				print()
				print("This file was encrypted using the following parameters")
				print()
				print("hash algorithm:", sha2.__name__)
				print("compression:", compr_name)
				print("key derivation rounds:", iter_count)
				print("password hash rounds:", hashed_password_iters)
				print("salt:", salt.hex())
				print("hashed password:", embedded_hash.hex())
				_exit()
		
		if action == 'e':
			algonum = usr.getHashAlgoNum()
			sha2 = ALGOS[algonum]
			exp_incr = usr.getExponentIncrement()
			compressornum = usr.getCompression()
			compressor = COMPRESSION[compressornum]
			iter_count = 2 ** (16 + exp_incr)
			digestsz = DIGESTSIZES[algonum]
			salt = os.urandom(digestsz)
			password = usr.getPassword()
			hdr = MAGIC + struct.pack('<B', bitPack(algonum, exp_incr, compressornum))
			hdr += salt
			sys.stdout.write("\nCompressing file...")
			sys.stdout.flush()
			_input = _bio(compressor.compress(_input.read()))
			print("done.")
			sys.stdout.write("Hashing password...")
			sys.stdout.flush()
			hashed_pwd = sha2(salt + password).digest()
			for _ in range(iter_count * PWD_HASH_MULT):
				hashed_pwd = sha2(salt + hashed_pwd).digest()
			print("done.")
			hdr += hashed_pwd

		elif action == 'd':
			password = getpass.getpass().encode()
			sys.stdout.write("\nHashing password...")
			sys.stdout.flush()
			hashed_pwd = sha2(salt + password).digest()
			for _ in range(hashed_password_iters):
				hashed_pwd = sha2(salt + hashed_pwd).digest()
			print("done.")
			try:
				assert(constTimeCompare(embedded_hash, hashed_pwd))
			except AssertionError:
				raise AssertionError('Embedded password hash does not match. Operation aborted.')

		# # Key stretching
		sys.stdout.write("Deriving key...")
		sys.stdout.flush()
		keyblock = genKeyBlock(password, salt)
		for _ in range(iter_count):
			keyblock = genKeyBlock(keyblock, salt)
		print("done.")
		
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
				outbytes = b''
				for bytenum in range(len(in_bytes)):
					outbytes += bytes([ keyblock[bytenum] ^ in_bytes[bytenum] ])
				out.write(outbytes)
			else:
				out.close()
				break
		print("done.")
			
		if action == 'd' and compressor is not None:
			sys.stdout.write("Decompressing file...")
			sys.stdout.flush()
			outplain = compressor.decompress(open(sys.argv[1].replace(CRYPT_EXT, ''), 'rb').read())
			print("done.")
			open(sys.argv[1].replace(CRYPT_EXT, ''), 'wb').write(outplain)
			
		_exit()
	except:
		print(traceback.format_exc())

if __name__ == "__main__" and len(sys.argv) == 2:
	try:
		main()
	except SystemExit:
		pass
	except Exception as e:
		print(str(e))

## EOF