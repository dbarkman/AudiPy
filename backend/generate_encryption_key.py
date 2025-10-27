#!/usr/bin/env python3
"""
Generate a new Fernet encryption key for AudiPy
This key will be used to encrypt Audible authentication tokens in the database
"""

from cryptography.fernet import Fernet

def main():
    # Generate a new key
    key = Fernet.generate_key().decode()
    
    print("=" * 70)
    print("🔐 AudiPy Encryption Key Generator")
    print("=" * 70)
    print()
    print("Your new encryption key:")
    print()
    print(f"  {key}")
    print()
    print("=" * 70)
    print()
    print("📋 Next Steps:")
    print()
    print("1. Copy the key above")
    print("2. Add it to your .env file:")
    print(f"   AUDIPY_MASTER_KEY={key}")
    print()
    print("⚠️  IMPORTANT:")
    print("   - Keep this key safe and secure")
    print("   - If you lose this key, you'll lose access to stored Audible tokens")
    print("   - Never commit this key to version control")
    print("   - If you have existing encrypted data, DO NOT generate a new key!")
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()

