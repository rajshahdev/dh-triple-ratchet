"""
Triple Session implementation - glues all three ratchet layers together.

Combines macro ratchet, DH ratchet, and symmetric ratchet into a unified
secure messaging session.
"""

import msgpack
from typing import Optional, Tuple
from .macro_ratchet import MacroRatchet
from .dh_ratchet import create_dh_ratchet, dh_ratchet_step, get_dh_keys
from .symm_ratchet import encrypt_message, decrypt_message


class TripleSession:
    """
    Triple ratchet session combining macro, DH, and symmetric ratchets.
    
    Provides a unified interface for secure messaging with automatic
    epoch rotation and chain reset capabilities.
    """
    
    def __init__(self, root_key: Optional[bytes] = None, peer_pk: Optional[bytes] = None):
        """
        Initialize a triple ratchet session.
        
        Args:
            root_key: Initial root key (optional)
            peer_pk: Peer's public key (optional for initiator)
        """
        # Initialize macro ratchet
        self.macro_ratchet = MacroRatchet(root_key)
        
        # Initialize DH ratchet with macro root key
        self.dh_ratchet = create_dh_ratchet(self.macro_ratchet.root_key, peer_pk)
        
        # Store peer's macro public key
        self.peer_macro_pk = None
    
    def encrypt(self, plaintext: bytes, force_rotate: bool = False) -> Tuple[bytes, bytes]:
        """
        Encrypt a message with automatic macro rotation if needed.
        
        Args:
            plaintext: Message to encrypt
            force_rotate: Force macro rotation on this message
            
        Returns:
            Tuple of (ciphertext, serialized_header)
        """
        # Check if macro rotation is due or forced
        if force_rotate or self.macro_ratchet.due():
            self._perform_macro_rotation()
        
        # Encrypt using DH ratchet
        ciphertext, header = encrypt_message(self.dh_ratchet, plaintext)
        
        # Add macro ratchet fields to header
        header["epoch"] = self.macro_ratchet.epoch
        header["macro_pk"] = self.macro_ratchet.pk
        
        # Serialize header with msgpack
        serialized_header = msgpack.packb(header)
        
        return ciphertext, serialized_header
    
    def decrypt(self, ciphertext: bytes, serialized_header: bytes) -> bytes:
        """
        Decrypt a message, catching up on macro rotation if needed.
        
        Args:
            ciphertext: Encrypted message
            serialized_header: Serialized message header
            
        Returns:
            Decrypted plaintext
        """
        # Deserialize header
        header = msgpack.unpackb(serialized_header, raw=False)
        
        # Check if we need to catch up on macro rotation
        if header.get("epoch", 0) > self.macro_ratchet.epoch:
            self._catch_up_macro_rotation(header)
        
        # Decrypt using DH ratchet
        return decrypt_message(self.dh_ratchet, ciphertext, header)
    
    def _perform_macro_rotation(self) -> None:
        """Perform macro rotation and reset DH/symmetric chains."""
        if self.peer_macro_pk is None:
            raise ValueError("Cannot rotate macro ratchet without peer's public key")
        
        # Rotate macro ratchet
        self.macro_ratchet.rotate(self.peer_macro_pk)
        
        # Reset DH ratchet with new root key
        self.dh_ratchet = create_dh_ratchet(self.macro_ratchet.root_key)
        
        print(f"Macro rotation performed - new epoch: {self.macro_ratchet.epoch}")
    
    def _catch_up_macro_rotation(self, header: dict) -> None:
        """Catch up on macro rotation when receiving from higher epoch."""
        peer_macro_pk = header.get("macro_pk")
        if peer_macro_pk is None:
            raise ValueError("Header missing macro_pk for epoch catch-up")
        
        # Store peer's macro public key if not set
        if self.peer_macro_pk is None:
            self.peer_macro_pk = peer_macro_pk
        
        # Rotate macro ratchet to catch up
        self.macro_ratchet.rotate(peer_macro_pk)
        
        # Reset DH ratchet with new root key
        self.dh_ratchet = create_dh_ratchet(self.macro_ratchet.root_key)
        
        print(f"Caught up to epoch {self.macro_ratchet.epoch}")
    
    def set_peer_macro_pk(self, peer_macro_pk: bytes) -> None:
        """
        Set the peer's macro public key.
        
        Args:
            peer_macro_pk: Peer's macro public key
        """
        self.peer_macro_pk = peer_macro_pk
    
    def get_macro_pk(self) -> bytes:
        """
        Get our macro public key.
        
        Returns:
            Our macro public key
        """
        return self.macro_ratchet.pk
    
    def get_epoch(self) -> int:
        """
        Get current epoch.
        
        Returns:
            Current epoch number
        """
        return self.macro_ratchet.epoch 