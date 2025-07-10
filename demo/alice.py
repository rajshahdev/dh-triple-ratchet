#!/usr/bin/env python3
"""
Alice - Triple Ratchet Demo Sender

Simple REPL for sending encrypted messages with optional macro rotation.
"""

import sys
import argparse
from ratchet import TripleSession


def main():
    parser = argparse.ArgumentParser(description="Alice - Triple Ratchet Demo Sender")
    parser.add_argument("--rotate", action="store_true", 
                       help="Force macro rotation on next send")
    args = parser.parse_args()
    
    print("=== Alice (Triple Ratchet Sender) ===")
    print("Type messages to send (or 'quit' to exit)")
    print("Use --rotate flag to force macro rotation")
    print()
    
    # Initialize session
    session = TripleSession()
    print(f"Alice's macro public key: {session.get_macro_pk().hex()}")
    print(f"Current epoch: {session.get_epoch()}")
    print()
    
    # Get Bob's macro public key
    print("Enter Bob's macro public key (hex):")
    bob_macro_pk_hex = input().strip()
    try:
        bob_macro_pk = bytes.fromhex(bob_macro_pk_hex)
        session.set_peer_macro_pk(bob_macro_pk)
        print("✓ Bob's key set")
    except ValueError:
        print("Invalid hex string, using dummy key for demo")
        session.set_peer_macro_pk(b'\x00' * 32)
    
    print()
    
    while True:
        try:
            message = input("Alice> ").strip()
            
            if message.lower() == 'quit':
                break
            
            if not message:
                continue
            
            # Encrypt message
            ciphertext, header = session.encrypt(
                message.encode('utf-8'), 
                force_rotate=args.rotate
            )
            
            # Print encoded packet
            print(f"📦 Sending packet:")
            print(f"   Ciphertext: {ciphertext.hex()}")
            print(f"   Header: {header.hex()}")
            print(f"   Epoch: {session.get_epoch()}")
            print()
            
            # Reset rotation flag
            args.rotate = False
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Goodbye!")


if __name__ == "__main__":
    main() 