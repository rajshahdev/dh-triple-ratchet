# Triple-Ratchet MVP Code Explanation

## Overview

This is a **Triple-Ratchet** secure messaging system that extends the Signal Double-Ratchet protocol with a third "macro" ratchet layer. The system provides enhanced security through epoch-based root key rotation.

## Architecture

The system consists of three layers of ratchets:

1. **Macro Ratchet** (Third Layer) - Epoch-based root key rotation
2. **DH Ratchet** (Diffie-Hellman) - Key exchange and forward secrecy
3. **Symmetric Ratchet** - Message encryption/decryption

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TRIPLE-RATCHET SYSTEM                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   MACRO RATCHET                             │    │
│  │                  (Third Layer)                              │    │
│  │                                                             │    │
│  │  ┌─────────────┐    DH Exchange    ┌─────────────┐          │    │
│  │  │   Alice     │ ◄─────────────────► │     Bob     │          │    │
│  │  │  Macro PK   │                    │  Macro PK   │          │    │
│  │  │  Macro SK   │                    │  Macro SK   │          │    │
│  │  │  Epoch: N   │                    │  Epoch: N   │          │    │
│  │  └─────────────┘                    └─────────────┘          │    │
│  │                                                             │    │
│  │  Root Key Rotation: Every 24hrs or on-demand               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                  │                                  │
│                                  │ Provides Root Key               │
│                                  ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    DH RATCHET                               │    │
│  │                  (Second Layer)                             │    │
│  │                                                             │    │
│  │  Uses root key from Macro Ratchet                          │    │
│  │  Provides forward secrecy through DH key exchange          │    │
│  │  Resets when macro rotation occurs                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                  │                                  │
│                                  │ Provides Message Keys           │
│                                  ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                 SYMMETRIC RATCHET                           │    │
│  │                  (First Layer)                              │    │
│  │                                                             │    │
│  │  Encrypts/Decrypts actual messages                         │    │
│  │  Uses keys derived from DH Ratchet                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Message Flow Diagram

```
   Alice                                                    Bob
     │                                                      │
     │ 1. Exchange Macro Public Keys                        │
     │◄─────────────────────────────────────────────────────┤
     │                                                      │
     │ 2. Encrypt Message                                   │
     │ ┌─────────────────────────────────────────────────┐  │
     │ │ Check if macro rotation needed                  │  │
     │ │ ├─ If due/forced: Rotate macro ratchet          │  │
     │ │ ├─ Reset DH ratchet with new root key           │  │
     │ │ └─ Encrypt with DH/Symmetric ratchets           │  │
     │ └─────────────────────────────────────────────────┘  │
     │                                                      │
     │ 3. Send (Ciphertext + Header)                        │
     ├─────────────────────────────────────────────────────►│
     │                                                      │
     │                                                      │ 4. Decrypt Message
     │                                                      │ ┌─────────────────────────────────────────────────┐
     │                                                      │ │ Check header epoch                              │
     │                                                      │ │ ├─ If higher: Catch up macro rotation           │
     │                                                      │ │ ├─ Reset DH ratchet with new root key           │
     │                                                      │ │ └─ Decrypt with DH/Symmetric ratchets           │
     │                                                      │ └─────────────────────────────────────────────────┘
     │                                                      │
```

## Key Components Explained

### 1. TripleSession (`session.py`)

**Purpose**: Main coordinator that combines all three ratchet layers.

**Key Methods**:
- `encrypt()`: Encrypts messages with automatic macro rotation
- `decrypt()`: Decrypts messages with automatic catch-up
- `set_peer_macro_pk()`: Sets peer's macro public key
- `get_macro_pk()`: Returns own macro public key

**Flow**:
```python
# Encryption Flow
def encrypt(self, plaintext: bytes, force_rotate: bool = False):
    # 1. Check if macro rotation needed
    if force_rotate or self.macro_ratchet.due():
        self._perform_macro_rotation()
    
    # 2. Use DH ratchet for encryption
    ciphertext, header = encrypt_message(self.dh_ratchet, plaintext)
    
    # 3. Add macro info to header
    header["epoch"] = self.macro_ratchet.epoch
    header["macro_pk"] = self.macro_ratchet.pk
    
    return ciphertext, msgpack.packb(header)
```

### 2. MacroRatchet (`macro_ratchet.py`)

**Purpose**: Third layer providing epoch-based root key rotation.

**Key Features**:
- **Epoch Management**: Tracks current epoch number
- **Time-based Rotation**: Automatic rotation every 24 hours
- **On-demand Rotation**: Can be forced manually
- **Catch-up Mechanism**: Receivers can sync to higher epochs

**Key Methods**:
- `rotate()`: Performs DH exchange and generates new root key
- `due()`: Checks if rotation is needed based on time
- `next_epoch_secret()`: Derives next epoch's root key

**Security Properties**:
- Uses Curve25519 for DH operations
- Derives new root keys using HKDF-like approach
- Zeros out old secrets (when possible)

### 3. DH Ratchet (`dh_ratchet.py`)

**Purpose**: Provides forward secrecy through Diffie-Hellman key exchange.

**Implementation Note**: This is a simplified version for the MVP. In a full implementation, it would use the `python-doubleratchet` library.

**Key Features**:
- Uses root key from macro ratchet
- Provides message-level key derivation
- Resets when macro rotation occurs

### 4. Symmetric Ratchet (`symm_ratchet.py`)

**Purpose**: Handles actual message encryption/decryption.

**Key Methods**:
- `encrypt_message()`: Encrypts plaintext
- `decrypt_message()`: Decrypts ciphertext

## Security Properties

### 1. **Triple Forward Secrecy**
- **Macro Level**: Past epochs cannot be recovered
- **DH Level**: Past DH keys cannot be recovered  
- **Symmetric Level**: Past message keys cannot be recovered

### 2. **Epoch-based Security**
- Root keys rotate periodically (24 hours default)
- Compromise of current state doesn't affect past epochs
- Automatic catch-up for out-of-sync parties

### 3. **Post-Compromise Security**
- New DH exchanges after compromise restore security
- Macro rotation provides additional recovery mechanism

## Usage Example

```python
# Initialize sessions
alice = TripleSession()
bob = TripleSession()

# Exchange macro public keys
alice.set_peer_macro_pk(bob.get_macro_pk())
bob.set_peer_macro_pk(alice.get_macro_pk())

# Normal messaging
ciphertext, header = alice.encrypt(b"Hello, Bob!")
plaintext = bob.decrypt(ciphertext, header)

# Force macro rotation
ciphertext, header = alice.encrypt(b"Secret message", force_rotate=True)
plaintext = bob.decrypt(ciphertext, header)  # Bob automatically catches up
```

## Demo Files

### `alice.py` - Sender Demo
- Interactive REPL for sending messages
- Supports forced macro rotation via `--rotate` flag
- Shows packet structure (ciphertext + header)

### `bob.py` - Receiver Demo  
- Interactive REPL for receiving messages
- Automatically handles macro rotation catch-up
- Displays decrypted messages

## Key Advantages

1. **Enhanced Security**: Three layers of protection
2. **Automatic Rotation**: Time-based and on-demand
3. **Catch-up Mechanism**: Handles out-of-sync scenarios
4. **Simple API**: Easy to use interface
5. **Type Safety**: Full Python type annotations

## Security Considerations

- This is an MVP implementation with simplified components
- Production use would require full Double-Ratchet implementation
- Memory zeroing is limited due to PyNaCl constraints
- No persistent storage (in-memory only)
- Headers are serialized in binary format (msgpack)

## Dependencies

- `pynacl` - Cryptographic primitives (libsodium bindings)
- `python-doubleratchet` - Double ratchet reference (used in full version)
- `msgpack` - Binary serialization for headers
- `pytest` - Testing framework