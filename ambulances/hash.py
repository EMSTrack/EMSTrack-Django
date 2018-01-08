import hashlib, os
from base64 import b64encode, b64decode

def generate_hash(password,
                  salt_length = 12,
                  key_length = 24,
                  hash_function = 'sha256',
                  iterations = 901):
    
    password = password.encode('utf-8')
    salt = b64encode('testtesttest'.encode('utf-8'))
    #salt = b64encode(os.urandom(salt_length))
    
    key = hashlib.pbkdf2_hmac(hash_function,
                              password,
                              salt,
                              iterations,
                              key_length)

    return 'PBKDF2${}${}${}${}'.format(hash_function,
                                       iterations,
                                       salt.decode('utf-8'),
                                       b64encode(key).decode('utf-8'))
