import json
import os
import hashlib

VAULT_PATH = os.path.join(os.path.dirname(__file__), "vault.json")
MASTER_KEY_PATH = os.path.join(os.path.dirname(__file__), "master_key.hash")


def hash_master_key(key: str) -> str:
    return hashlib.sha256(key.encode('utf-8')).hexdigest()


def save_master_key(key: str):
    hashed = hash_master_key(key)
    with open(MASTER_KEY_PATH, "w", encoding="utf-8") as f:
        f.write(hashed)


def verify_master_key(key: str) -> bool:
    if not os.path.exists(MASTER_KEY_PATH):
        return False
    
    with open(MASTER_KEY_PATH, "r", encoding="utf-8") as f:
        stored_hash = f.read().strip()
    
    return hash_master_key(key) == stored_hash


def master_key_exists() -> bool:
    return os.path.exists(MASTER_KEY_PATH)


def load_vault():
    if not os.path.exists(VAULT_PATH):
        return {}
    
    with open(VAULT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_vault(vault):
    with open(VAULT_PATH, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2, ensure_ascii=False)
