#!/usr/bin/env python3
"""
Bob - Triple Ratchet Demo Receiver

Simple REPL for receiving and decrypting messages.
"""

import sys
from ratchet import TripleSession


def main():
    print("=== Bob (Triple Ratchet Receiver) ===")
    print("Paste packets from Alice to decrypt (or 'quit' to exit)")
    print()
    
    # Initialize session
    session = TripleSession()
    print(f"Bob's macro public key: {session.get_macro_pk().hex()}")
    print(f"Current epoch: {session.get_epoch()}")
    print()
    
    while True:
        try:
            print("Paste ciphertext (hex):")
            ciphertext_hex = input().strip()
            
            if ciphertext_hex.lower() == 'quit':
                break
            
            if not ciphertext_hex:
                continue
            
            print("Paste header (hex):")
            header_hex = input().strip()
            
            if not header_hex:
                print("Missing header")
                continue
            
            # Decode hex strings
            try:
                ciphertext = bytes.fromhex(ciphertext_hex)
                header = bytes.fromhex(header_hex)
            except ValueError:
                print("Invalid hex string")
                continue
            
            # Decrypt message
            plaintext = session.decrypt(ciphertext, header)
            
            # Print result
            print(f"📨 Received message: {plaintext.decode('utf-8')}")
            print(f"   Epoch: {session.get_epoch()}")
            print()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            print()
    
    print("Goodbye!")


if __name__ == "__main__":
    main() 