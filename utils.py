# Imports from the built-in library
import pickle
import base64
from os.path import isfile, isdir
from os import mkdir
from hashlib import sha224, sha256

# Third-party package imports
from cryptography.fernet import Fernet
from reedsolo import RSCodec, ReedSolomonError


# Global Parameters
cand_path = "candidates/"  # The path where the candidate list will be stored
vote_path = "votes/"       # The path where the votes will be stored
pin_key = "-#*KEY*#-"      # The key of the dict item where the hash of the pin will be stored. It's best not to change it.
is_debug = False           # Enables debug messages


# Utility stuff - Such as getting the path of a file, get hash of a name & category, etc.
# It is not necessary to fully understand them except the overall effect/result
path = lambda is_cand, name: (cand_path if is_cand else vote_path) + name + ".dat"
ensure_dir = lambda path: mkdir(path) if not isdir(path) else True
get_hash = lambda cat, name: sha224((cat + "::" + name).encode()).digest()
get_pin_hash = lambda pin: sha256(pin).digest()
get_key = lambda pin_hash, pin: (base64.urlsafe_b64encode(pin_hash + pin).decode()[:43] + "=").encode() if get_pin_hash(pin) == pin_hash else False
debug = lambda msg: print("[DEBUG]", msg) if is_debug else None

class PinException(Exception):
    pass
