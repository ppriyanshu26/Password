import os
import hashlib

MASTER_KEY_PATH = os.path.join(os.path.dirname(__file__), "master_key.hash")


def hash_master_key(key: str) -> str:
    return hashlib.sha256(key.encode('utf-8')).hexdigest()


def main():
    print("=" * 50)
    print("  Password Manager - Master Key Setup")
    print("=" * 50)
    print()
    
    if os.path.exists(MASTER_KEY_PATH):
        print("⚠️  A master key already exists!")
        response = input("Do you want to replace it? (yes/no): ").strip().lower()
        if response != "yes":
            print("Cancelled. Existing master key preserved.")
            return
        print()
    
    while True:
        key = input("Enter new master key (min 4 characters): ").strip()
        
        if len(key) < 4:
            print("❌ Master key must be at least 4 characters. Try again.\n")
            continue
        
        confirm = input("Confirm master key: ").strip()
        
        if key != confirm:
            print("❌ Keys don't match. Try again.\n")
            continue
        
        break
    
    hashed = hash_master_key(key)
    with open(MASTER_KEY_PATH, "w", encoding="utf-8") as f:
        f.write(hashed)
    
    print()
    print("✅ Master key saved successfully!")
    print(f"   Hash stored in: {MASTER_KEY_PATH}")
    print()
    print("You can now run the password manager with: python main.py")


if __name__ == "__main__":
    main()
