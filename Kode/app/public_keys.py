from ecdsa import NIST192p, SigningKey
from ecdsa.util import randrange_from_seed__trytryagain
import os

def make_key_from_seed(seed, curve=NIST192p):
    secexp = randrange_from_seed__trytryagain(seed, curve.order)
    return SigningKey.from_secret_exponent(secexp, curve)


sk1 = make_key_from_seed(os.urandom(NIST192p.baselen))
sk2 = make_key_from_seed(os.urandom(NIST192p.baselen))
vk1 = sk1.get_verifying_key()
vk2 = sk2.get_verifying_key()

msg = ['nodeid', 'price', 'min']

signature = sk1.sign(str(msg).encode('utf-8'))
signature2 = sk2.sign(signature)
print(vk2.verify(signature2, signature))
print(vk1.verify(signature, str(msg).encode('utf-8')))
