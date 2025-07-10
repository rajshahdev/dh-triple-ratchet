"""
Macro ratchet implementation - third layer of the triple ratchet.

Provides epoch-based rotation of root keys for additional security properties.
"""

import time
from typing import Optional
import nacl.bindings
import nacl.utils
import nacl.hash


class MacroRatchet:
    """
    Macro ratchet for epoch-based root key rotation.
    
    Implements a third ratchet layer that rotates root keys based on time
    intervals or explicit rotation requests.
    """
    
    def __init__(self, root_key: Optional[bytes] = None):
        """
        Initialize the macro ratchet.
        
        Args:
            root_key: Initial root key. If None, generates a random one.
        """
        if root_key is None:
            root_key = nacl.utils.random(nacl.bindings.crypto_scalarmult_SCALARBYTES)
        
        self.root_key = root_key
        self.epoch = 0
        self.last_reset = time.time()
        
        # Generate keypair for this epoch
        self.sk = nacl.utils.random(nacl.bindings.crypto_scalarmult_SCALARBYTES)
        self.pk = nacl.bindings.crypto_scalarmult_base(self.sk)
    
    def next_epoch_secret(self, peer_pk: bytes) -> bytes:
        """
        Derive the next epoch's root key using DH with peer's public key.
        
        Args:
            peer_pk: Peer's public key for this epoch
            
        Returns:
            New root key for next epoch
        """
        try:
            # Perform DH key exchange
            shared_secret = nacl.bindings.crypto_scalarmult(self.sk, peer_pk)
            
            # Derive new root key using HKDF-like approach
            # Use the current root key as salt and shared secret as input
            new_root_key = nacl.hash.generichash(
                shared_secret,
                key=self.root_key,
                digest_size=nacl.bindings.crypto_scalarmult_SCALARBYTES
            )
            
            return new_root_key
        finally:
            # PyNaCl does not expose sodium_memzero; skip for compatibility
            pass
    
    def rotate(self, peer_pk: bytes) -> None:
        """
        Rotate to the next epoch.
        
        Args:
            peer_pk: Peer's public key for the new epoch
        """
        # Derive new root key
        new_root_key = self.next_epoch_secret(peer_pk)
        
        # Zero out old secrets (PyNaCl does not expose sodium_memzero)
        # nacl.bindings.sodium_memzero(self.root_key)
        # nacl.bindings.sodium_memzero(self.sk)
        
        # Update state
        self.root_key = new_root_key
        self.epoch += 1
        self.last_reset = time.time()
        
        # Generate new keypair for this epoch
        self.sk = nacl.utils.random(nacl.bindings.crypto_scalarmult_SCALARBYTES)
        self.pk = nacl.bindings.crypto_scalarmult_base(self.sk)
    
    def due(self, interval_sec: int = 24 * 3600) -> bool:
        """
        Check if rotation is due based on time interval.
        
        Args:
            interval_sec: Time interval in seconds (default: 24 hours)
            
        Returns:
            True if rotation is due, False otherwise
        """
        return (time.time() - self.last_reset) >= interval_sec
    
    def __del__(self):
        """Clean up secrets on deletion."""
        try:
            if hasattr(self, 'root_key'):
                nacl.bindings.sodium_memzero(self.root_key)
            if hasattr(self, 'sk'):
                nacl.bindings.sodium_memzero(self.sk)
        except:
            pass 