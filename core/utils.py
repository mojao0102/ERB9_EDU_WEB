from django.conf import settings
from hashids import Hashids

hashids = Hashids(salt=settings.HASHIDS_SALT, min_length=settings.HASHIDS_MIN_LENGTH)

def encode_id(raw_id):
    if not raw_id:
        return None
    return hashids.encode(raw_id)

def decode_id(hash_string):
    if not hash_string:
        return None
    decoded = hashids.decode(hash_string)

    if decoded:
        return decoded[0]
    return None