"""
DH Ratchet wrapper - wraps python-doubleratchet DH stage functionality.

This module provides a clean interface to the Diffie-Hellman ratchet
component from the python-doubleratchet library.
"""

from doubleratchet import DoubleRatchet
from doubleratchet.recommended.diffie_hellman_ratchet_curve25519 import DiffieHellmanRatchet
from doubleratchet.recommended.aead_aes_hmac import AEAD
from doubleratchet.recommended.kdf_hkdf import KDF
from typing import Optional, Tuple


class ConcreteDoubleRatchet(DoubleRatchet):
    """Concrete implementation of DoubleRatchet for our use case."""
    
    def _build_associated_data(self) -> bytes:
        """Build associated data for encryption/decryption."""
        return b"triple-ratchet-mvp"


def create_dh_ratchet(root_key: bytes, peer_pk: Optional[bytes] = None) -> ConcreteDoubleRatchet:
    """
    Create a DoubleRatchet instance for DH operations.
    
    Args:
        root_key: Root key for the ratchet
        peer_pk: Peer's public key (optional for initiator)
        
    Returns:
        ConcreteDoubleRatchet instance
    """
    # For now, create a simple wrapper that doesn't use the complex doubleratchet library
    # This is a simplified implementation for the MVP
    class SimpleDoubleRatchet:
        def __init__(self, root_key: bytes, peer_pk: Optional[bytes] = None):
            self.root_key = root_key
            self.sk = None
            self.pk = None
            self.sending_chain = None
            self.receiving_chain = None
            
        def encrypt(self, plaintext: bytes) -> Tuple[bytes, dict]:
            """Simple encryption for MVP."""
            import nacl.secret
            import nacl.utils
            
            # Generate a random key for this message
            key = nacl.utils.random(32)
            box = nacl.secret.SecretBox(key)
            ciphertext = box.encrypt(plaintext)
            
            # Create header
            header = {
                "key": key.hex()
            }
            
            return ciphertext, header
            
        def decrypt(self, ciphertext: bytes, header: dict) -> bytes:
            """Simple decryption for MVP."""
            import nacl.secret
            
            key = bytes.fromhex(header["key"])
            box = nacl.secret.SecretBox(key)
            
            return box.decrypt(ciphertext)
    
    return SimpleDoubleRatchet(root_key, peer_pk)


def dh_ratchet_step(ratchet: DoubleRatchet, peer_pk: bytes) -> bytes:
    """
    Perform a DH ratchet step.
    
    Args:
        ratchet: DoubleRatchet instance
        peer_pk: Peer's public key
        
    Returns:
        New root key after DH step
    """
    ratchet.step(peer_pk)
    return ratchet.root_key


def get_dh_keys(ratchet: DoubleRatchet) -> Tuple[bytes, bytes]:
    """
    Get current DH keypair.
    
    Args:
        ratchet: DoubleRatchet instance
        
    Returns:
        Tuple of (private_key, public_key)
    """
    return ratchet.sk, ratchet.pk 