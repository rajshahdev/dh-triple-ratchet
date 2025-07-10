"""
Unit tests for macro ratchet functionality.

Tests epoch rotation, catch-up behavior, and root key changes.
"""

import pytest
import time
from ratchet import MacroRatchet, TripleSession


class TestMacroRatchet:
    """Test MacroRatchet class functionality."""
    
    def test_initialization(self):
        """Test macro ratchet initialization."""
        ratchet = MacroRatchet()
        
        assert ratchet.epoch == 0
        assert ratchet.root_key is not None
        assert ratchet.sk is not None
        assert ratchet.pk is not None
        assert len(ratchet.root_key) == 32
        assert len(ratchet.sk) == 32
        assert len(ratchet.pk) == 32
    
    def test_rotation(self):
        """Test macro ratchet rotation."""
        ratchet = MacroRatchet()
        old_root_key = ratchet.root_key[:]
        old_epoch = ratchet.epoch
        
        # Generate a peer public key
        import nacl.utils
        import nacl.bindings
        peer_sk = nacl.utils.random(nacl.bindings.crypto_scalarmult_SCALARBYTES)
        peer_pk = nacl.bindings.crypto_scalarmult_base(peer_sk)
        
        # Rotate
        ratchet.rotate(peer_pk)
        
        # Check state changes
        assert ratchet.epoch == old_epoch + 1
        assert ratchet.root_key != old_root_key
        assert ratchet.sk != old_root_key  # Should be different
        assert ratchet.pk is not None
    
    def test_due_check(self):
        """Test due() method for rotation timing."""
        ratchet = MacroRatchet()
        
        # Should not be due immediately
        assert not ratchet.due(interval_sec=3600)
        
        # Should be due after interval
        ratchet.last_reset = time.time() - 3601
        assert ratchet.due(interval_sec=3600)


class TestTripleSession:
    """Test TripleSession integration."""
    
    def test_session_creation(self):
        """Test session initialization."""
        session = TripleSession()
        
        assert session.macro_ratchet is not None
        assert session.dh_ratchet is not None
        assert session.get_epoch() == 0
    
    def test_encrypt_decrypt_basic(self):
        """Test basic encrypt/decrypt without rotation."""
        alice = TripleSession()
        bob = TripleSession()
        
        # Exchange macro public keys
        alice.set_peer_macro_pk(bob.get_macro_pk())
        bob.set_peer_macro_pk(alice.get_macro_pk())
        
        # Test message
        message = b"Hello, world!"
        
        # Alice encrypts
        ciphertext, header = alice.encrypt(message)
        
        # Bob decrypts
        decrypted = bob.decrypt(ciphertext, header)
        
        assert decrypted == message
    
    def test_forced_rotation(self):
        """Test forced macro rotation."""
        alice = TripleSession()
        bob = TripleSession()
        
        # Exchange macro public keys
        alice.set_peer_macro_pk(bob.get_macro_pk())
        bob.set_peer_macro_pk(alice.get_macro_pk())
        
        # Get initial states
        alice_epoch_before = alice.get_epoch()
        alice_root_before = alice.macro_ratchet.root_key[:]
        
        # Force rotation
        message = b"Force rotation!"
        ciphertext, header = alice.encrypt(message, force_rotate=True)
        
        # Check rotation occurred
        assert alice.get_epoch() == alice_epoch_before + 1
        assert alice.macro_ratchet.root_key != alice_root_before
        
        # Bob should catch up and decrypt
        decrypted = bob.decrypt(ciphertext, header)
        assert decrypted == message
        assert bob.get_epoch() == alice.get_epoch()
    
    def test_epoch_catch_up(self):
        """Test catching up when receiving from higher epoch."""
        alice = TripleSession()
        bob = TripleSession()
        
        # Exchange macro public keys
        alice.set_peer_macro_pk(bob.get_macro_pk())
        bob.set_peer_macro_pk(alice.get_macro_pk())
        
        # Alice forces rotation
        message1 = b"First message"
        ciphertext1, header1 = alice.encrypt(message1, force_rotate=True)
        
        # Alice sends another message (no rotation)
        message2 = b"Second message"
        ciphertext2, header2 = alice.encrypt(message2)
        
        # Bob receives both messages
        decrypted1 = bob.decrypt(ciphertext1, header1)
        decrypted2 = bob.decrypt(ciphertext2, header2)
        
        assert decrypted1 == message1
        assert decrypted2 == message2
        assert bob.get_epoch() == alice.get_epoch()
    
    def test_root_key_difference(self):
        """Test that root keys differ before and after rotation."""
        alice = TripleSession()
        bob = TripleSession()
        
        # Exchange macro public keys
        alice.set_peer_macro_pk(bob.get_macro_pk())
        bob.set_peer_macro_pk(alice.get_macro_pk())
        
        # Get root key before rotation
        root_key_before = alice.macro_ratchet.root_key[:]
        
        # Force rotation
        alice.encrypt(b"test", force_rotate=True)
        
        # Get root key after rotation
        root_key_after = alice.macro_ratchet.root_key[:]
        
        # Keys should be different
        assert root_key_before != root_key_after
    
    def test_multiple_rotations(self):
        """Test multiple consecutive rotations."""
        alice = TripleSession()
        bob = TripleSession()
        
        # Exchange macro public keys
        alice.set_peer_macro_pk(bob.get_macro_pk())
        bob.set_peer_macro_pk(alice.get_macro_pk())
        
        # Perform multiple rotations
        for i in range(3):
            message = f"Message {i}".encode()
            ciphertext, header = alice.encrypt(message, force_rotate=True)
            
            decrypted = bob.decrypt(ciphertext, header)
            assert decrypted == message
            assert alice.get_epoch() == i + 1
            assert bob.get_epoch() == alice.get_epoch()


if __name__ == "__main__":
    pytest.main([__file__]) 