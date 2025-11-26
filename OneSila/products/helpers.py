from hashlib import shake_256
import shortuuid


def generate_sku():
    return shake_256(shortuuid.uuid().encode('utf-8')).hexdigest(7)
