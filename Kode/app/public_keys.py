from ecdsa import NIST192p, SigningKey
from ecdsa.util import randrange_from_seed__trytryagain
import os

def make_key_from_seed(seed, curve=NIST192p):
    secexp = randrange_from_seed__trytryagain(seed, curve.order)
    return SigningKey.from_secret_exponent(secexp, curve)

seed = os.urandom(NIST192p.baselen)

sk1 = make_key_from_seed(os.urandom(NIST192p.baselen))
sk2 = make_key_from_seed(os.urandom(NIST192p.baselen))
sk3 = make_key_from_seed(os.urandom(NIST192p.baselen))

print(sk1.get_verifying_key().to_pem())
print(sk2.get_verifying_key().to_pem())
print(sk3.get_verifying_key().to_pem())