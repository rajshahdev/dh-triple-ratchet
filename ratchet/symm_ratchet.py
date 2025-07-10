"""
Symmetric Ratchet wrapper - wraps python-doubleratchet chain/key ratchets.

This module provides a clean interface to the symmetric ratchet
components (sending/receiving chains) from the python-doubleratchet library.
"""

from typing import Tuple, Any


def encrypt_message(ratchet: Any, plaintext: bytes) -> Tuple[bytes, dict]:
    """
    Encrypt a message using the symmetric ratchet.
    
    Args:
        ratchet: Ratchet instance
        plaintext: Message to encrypt
        
    Returns:
        Tuple of (ciphertext, header)
    """
    return ratchet.encrypt(plaintext)


def decrypt_message(ratchet: Any, ciphertext: bytes, header: dict) -> bytes:
    """
    Decrypt a message using the symmetric ratchet.
    
    Args:
        ratchet: Ratchet instance
        ciphertext: Encrypted message
        header: Message header
        
    Returns:
        Decrypted plaintext
    """
    return ratchet.decrypt(ciphertext, header)


def get_chain_lengths(ratchet: Any) -> Tuple[int, int]:
    """
    Get current chain lengths.
    
    Args:
        ratchet: Ratchet instance
        
    Returns:
        Tuple of (sending_chain_length, receiving_chain_length)
    """
    # For the simple implementation, return dummy values
    return 0, 0 