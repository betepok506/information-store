import hashlib

def get_hash(text: str):
    return hashlib.sha256(text.encode()).hexdigest()