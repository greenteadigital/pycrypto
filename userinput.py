import getpass
import sys

def getCompression():
    num_selected = askCompression()
    while num_selected not in ('1','2','3'):
        num_selected = askCompression()
    return int(num_selected) - 1

def askCompression():
    return input('''
Select compression:

(1) None
(2) zlib
(3) bz2

Enter 1,2,or 3: ''')
    
def getExponentIncrement():
    num_selected = askIterations()
    while num_selected not in ('1','2','3','4'):
        num_selected = askIterations()
    return int(num_selected) - 1

def askIterations():
    return input('''
Select number of iterations:

 #     Key derivation rounds    Password hashing rounds
---    ---------------------    -----------------------
(1)                   65,536                  1,310,720
(2)                  131,072                  2,621,440
(3)                  262,144                  5,242,880
(4)                  524,288                 10,485,760

Enter 1,2,3 or 4: ''')

def getHashAlgoNum():
    num_selected = askHashAlgo()
    while num_selected not in ('1','2','3','4'):
        num_selected = askHashAlgo()
    return int(num_selected) - 1
    
def askHashAlgo():
    return input('''
Select hash algorithm:
(1) SHA224
(2) SHA256
(3) SHA384
(4) SHA512

Enter 1,2,3 or 4: ''')

def getAction(path):
    print()
    print(path)
    print()
    action = input("(E)ncrypt, (D)ecrypt, or (I)nfo? ").lower()
    while action not in ('e', 'd', 'i'):
        action = getAction(sys.argv[1])
    return action

def getPassword():
    password0 = getpass.getpass()
    password1 = getpass.getpass("Re-enter password: ")
    if password0 == password1:
        return password0.encode()
    else:
        print("Passwords do not match.")
        return getPassword()
