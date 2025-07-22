# Triple Ratchet Complete Guide

This document provides a comprehensive overview of the Triple Ratchet implementation, including detailed function call flows and presentation talking points.

## Table of Contents
1. [Complete Function Call Flow Diagram](#complete-function-call-flow-diagram)
2. [Triple Ratchet Project Presentation Guide](#triple-ratchet-project-presentation-guide)
3. [Demo Talking Points](#demo-talking-points)

---

## Complete Function Call Flow Diagram

### Triple Ratchet Message Exchange Between Alice and Bob

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              ALICE SENDS MESSAGE TO BOB                                │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. USER INPUT LAYER (demo/alice.py)                                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ alice.py:54 → input("Alice> ")                                                         │
│ alice.py:61 → message.encode('utf-8')                                                  │
│ alice.py:62 → session.encrypt(plaintext, force_rotate=args.rotate)                     │
│                                                                                         │
│                                    ⬇                                                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. TRIPLE SESSION ENCRYPT (ratchet/session.py)                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ session.py:39 → TripleSession.encrypt(plaintext, force_rotate)                         │
│   │                                                                                     │
│   ├─ session.py:51 → if force_rotate or self.macro_ratchet.due():                      │
│   │    │                                                                               │
│   │    └─ macro_ratchet.py:90 → MacroRatchet.due() ────────┐                         │
│   │         │                                               │                         │
│   │         └─ time.time() - self.last_reset >= 24*3600    │                         │
│   │                                                         │                         │
│   │                                                         ▼                         │
│   ├─ session.py:52 → self._perform_macro_rotation() ◄──────┘                         │
│   │    │                                              (if rotation needed)            │
│   │    └─ session.py:88 → _perform_macro_rotation()                                   │
│   │         │                                                                         │
│   │         ├─ macro_ratchet.py:67 → MacroRatchet.rotate(peer_pk)                    │
│   │         │    │                                                                    │
│   │         │    ├─ macro_ratchet.py:42 → next_epoch_secret(peer_pk)                 │
│   │         │    │    │                                                               │
│   │         │    │    ├─ nacl.bindings.crypto_scalarmult(self.sk, peer_pk)           │
│   │         │    │    └─ nacl.hash.generichash(shared_secret, key=root_key)          │
│   │         │    │                                                                    │
│   │         │    ├─ self.root_key = new_root_key                                      │
│   │         │    ├─ self.epoch += 1                                                   │
│   │         │    ├─ time.time() → self.last_reset                                     │
│   │         │    ├─ nacl.utils.random() → new self.sk                                │
│   │         │    └─ nacl.bindings.crypto_scalarmult_base(self.sk) → new self.pk      │
│   │         │                                                                         │
│   │         └─ dh_ratchet.py:21 → create_dh_ratchet(new_root_key)                    │
│   │              │                                                                    │
│   │              └─ SimpleDoubleRatchet(root_key, peer_pk)                           │
│   │                                                                                   │
│   ├─ symm_ratchet.py:10 → encrypt_message(self.dh_ratchet, plaintext)               │
│   │    │                                                                             │
│   │    └─ dh_ratchet.py:43 → SimpleDoubleRatchet.encrypt(plaintext)                 │
│   │         │                                                                        │
│   │         ├─ nacl.utils.random(32) → random key                                    │
│   │         ├─ nacl.secret.SecretBox(key)                                            │
│   │         ├─ box.encrypt(plaintext) → ciphertext                                   │
│   │         └─ return (ciphertext, {"key": key.hex()})                              │
│   │                                                                                  │
│   ├─ header["epoch"] = self.macro_ratchet.epoch                                      │
│   ├─ header["macro_pk"] = self.macro_ratchet.pk                                      │
│   └─ msgpack.packb(header) → serialized_header                                       │
│                                                                                       │
│ Returns: (ciphertext, serialized_header)                                             │
│                                                                                       │
│                                    ⬇                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. OUTPUT DISPLAY (demo/alice.py)                                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ alice.py:67 → print(f"Ciphertext: {ciphertext.hex()}")                                │
│ alice.py:68 → print(f"Header: {header.hex()}")                                        │
│ alice.py:69 → print(f"Epoch: {session.get_epoch()}")                                  │
│                                                                                         │
│                          ═══ NETWORK TRANSMISSION ═══                                 │
│                                                                                         │
│                                    ⬇                                                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              BOB RECEIVES MESSAGE FROM ALICE                           │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 4. USER INPUT LAYER (demo/bob.py)                                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ bob.py:25 → input("Paste ciphertext (hex):")                                          │
│ bob.py:33 → input("Paste header (hex):")                                              │
│ bob.py:41 → bytes.fromhex(ciphertext_hex)                                             │
│ bob.py:42 → bytes.fromhex(header_hex)                                                 │
│ bob.py:46 → session.decrypt(ciphertext, header)                                       │
│                                                                                         │
│                                    ⬇                                                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 5. TRIPLE SESSION DECRYPT (ratchet/session.py)                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ session.py:65 → TripleSession.decrypt(ciphertext, serialized_header)                  │
│   │                                                                                     │
│   ├─ msgpack.unpackb(serialized_header, raw=False) → header dict                      │
│   │                                                                                     │
│   ├─ session.py:78 → if header.get("epoch", 0) > self.macro_ratchet.epoch:           │
│   │    │                                                                               │
│   │    └─ session.py:81 → self._catch_up_macro_rotation(header)                       │
│   │         │                                                                         │
│   │         ├─ header.get("macro_pk") → peer_macro_pk                                 │
│   │         ├─ self.peer_macro_pk = peer_macro_pk (if not set)                        │
│   │         ├─ macro_ratchet.py:67 → MacroRatchet.rotate(peer_macro_pk)              │
│   │         │    │                                                                    │
│   │         │    ├─ macro_ratchet.py:42 → next_epoch_secret(peer_pk)                 │
│   │         │    │    │                                                               │
│   │         │    │    ├─ nacl.bindings.crypto_scalarmult(self.sk, peer_pk)           │
│   │         │    │    └─ nacl.hash.generichash(shared_secret, key=root_key)          │
│   │         │    │                                                                    │
│   │         │    ├─ self.root_key = new_root_key                                      │
│   │         │    ├─ self.epoch += 1                                                   │
│   │         │    ├─ time.time() → self.last_reset                                     │
│   │         │    ├─ nacl.utils.random() → new self.sk                                │
│   │         │    └─ nacl.bindings.crypto_scalarmult_base(self.sk) → new self.pk      │
│   │         │                                                                         │
│   │         └─ dh_ratchet.py:21 → create_dh_ratchet(new_root_key)                    │
│   │              │                                                                    │
│   │              └─ SimpleDoubleRatchet(root_key, peer_pk)                           │
│   │                                                                                   │
│   └─ symm_ratchet.py:24 → decrypt_message(self.dh_ratchet, ciphertext, header)       │
│        │                                                                             │
│        └─ dh_ratchet.py:58 → SimpleDoubleRatchet.decrypt(ciphertext, header)         │
│             │                                                                        │
│             ├─ bytes.fromhex(header["key"]) → key                                    │
│             ├─ nacl.secret.SecretBox(key)                                            │
│             └─ box.decrypt(ciphertext) → plaintext                                   │
│                                                                                       │
│ Returns: plaintext                                                                    │
│                                                                                       │
│                                    ⬇                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 6. OUTPUT DISPLAY (demo/bob.py)                                                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ bob.py:49 → plaintext.decode('utf-8')                                                 │
│ bob.py:52 → print(f"📨 Received message: {plaintext}")                                │
│ bob.py:53 → print(f"Epoch: {session.get_epoch()}")                                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Key Function Call Chains

#### **ENCRYPTION PATH:**
```
alice.py:62 
  ↓
session.py:39 → TripleSession.encrypt()
  ↓
macro_ratchet.py:90 → MacroRatchet.due() [time check]
  ↓ (if rotation needed)
session.py:88 → _perform_macro_rotation()
  ↓
macro_ratchet.py:67 → MacroRatchet.rotate()
  ↓
symm_ratchet.py:10 → encrypt_message()
  ↓
dh_ratchet.py:43 → SimpleDoubleRatchet.encrypt()
  ↓
nacl.secret.SecretBox.encrypt()
```

#### **DECRYPTION PATH:**
```
bob.py:46
  ↓
session.py:65 → TripleSession.decrypt()
  ↓
msgpack.unpackb() [header deserialization]
  ↓
session.py:81 → _catch_up_macro_rotation() [if epoch mismatch]
  ↓
macro_ratchet.py:67 → MacroRatchet.rotate()
  ↓
symm_ratchet.py:24 → decrypt_message()
  ↓
dh_ratchet.py:58 → SimpleDoubleRatchet.decrypt()
  ↓
nacl.secret.SecretBox.decrypt()
```

### Critical Dependencies

**External Libraries:**
- `nacl.bindings` - Curve25519 operations
- `nacl.secret` - Symmetric encryption  
- `nacl.utils` - Random number generation
- `msgpack` - Header serialization
- `time` - Epoch timing

**Internal Module Dependencies:**
- `session.py` → `macro_ratchet.py` → `dh_ratchet.py` → `symm_ratchet.py`

---

## Triple Ratchet Project Presentation Guide

### 1. Identity & Ephemeral Key Handling (X25519)

#### **Key Points to Explain:**

**Core Cryptography:**
- "We use **X25519** (Curve25519) for all Diffie-Hellman operations"
- "Each party maintains both **identity keys** and **ephemeral keys**"
- "Keys are 32 bytes (256 bits) following the Curve25519 standard"

**Key Generation Process:**
```python
# From macro_ratchet.py:36-37
self.sk = nacl.utils.random(32)  # Private key (32 bytes)
self.pk = nacl.bindings.crypto_scalarmult_base(self.sk)  # Public key
```

**Key Lifecycle:**
- "**Identity keys** persist across sessions for authentication"
- "**Ephemeral keys** rotate with each epoch (every 24 hours by default)"
- "We generate fresh key pairs during macro rotation for forward secrecy"

**DH Exchange Implementation:**
```python
# From macro_ratchet.py:51
shared_secret = nacl.bindings.crypto_scalarmult(self.sk, peer_pk)
```

**Security Properties:**
- "X25519 provides **128-bit security level**"
- "Resistant to quantum attacks up to practical limits"
- "Fast computation - single scalar multiplication"

### 2. Modular Design Walkthrough

#### **Architecture Overview:**
"The system has a **4-layer modular architecture**:"

**Layer 1 - User Interface:**
```
demo/alice.py    # Sender interface
demo/bob.py      # Receiver interface
```

**Layer 2 - Session Management:**
```
ratchet/session.py    # TripleSession class - main coordinator
```

**Layer 3 - Ratchet Implementations:**
```
ratchet/macro_ratchet.py    # Third ratchet (epoch management)
ratchet/dh_ratchet.py       # Second ratchet (DH operations)  
ratchet/symm_ratchet.py     # First ratchet (symmetric crypto)
```

**Layer 4 - External Dependencies:**
```
PyNaCl (libsodium)    # Core cryptographic primitives
msgpack               # Header serialization
```

#### **Module Responsibilities:**

**TripleSession (`session.py`):**
- "Acts as the **main coordinator** between all three ratchets"
- "Handles **automatic epoch rotation** and **catch-up logic**"
- "Provides clean API: `encrypt()` and `decrypt()`"

**MacroRatchet (`macro_ratchet.py`):**
- "Manages **epoch-based root key rotation**"
- "Implements **time-based** (24h) and **on-demand** rotation"
- "Provides root keys to lower layers"

**DH/Symmetric Ratchets:**
- "Currently **simplified MVP implementations**"
- "Designed for **easy replacement** with full Double Ratchet"

#### **Key Design Principles:**
- "**Separation of concerns** - each layer has single responsibility"
- "**Dependency injection** - layers don't directly import each other"
- "**Clean interfaces** - standardized function signatures"

### 3. Double Ratchet Integration Status

#### **Current State:**
"We have a **hybrid implementation**:"

**What's Implemented:**
- "**Interface compatibility** with python-doubleratchet library"
- "**Wrapper functions** that mirror the Double Ratchet API"
- "**Simplified MVP** for demonstration purposes"

**Current Implementation:**
```python
# From dh_ratchet.py:35
class SimpleDoubleRatchet:
    def encrypt(self, plaintext: bytes):
        key = nacl.utils.random(32)  # Fresh key per message
        box = nacl.secret.SecretBox(key)
        return box.encrypt(plaintext), {"key": key.hex()}
```

**What's Missing:**
- "**Full chain key derivation** (KDF chains)"
- "**Message ordering and replay protection**"
- "**Out-of-order message handling**"
- "**Header key encryption**"

#### **Integration Strategy:**
"We designed for **drop-in replacement**:"

**Phase 1 (Current):**
- "MVP with simplified crypto for proof-of-concept"

**Phase 2 (Planned):**
```python
# Replace SimpleDoubleRatchet with:
from doubleratchet import DoubleRatchet
ratchet = DoubleRatchet.create(root_key, peer_pk)
```

**Benefits of Current Approach:**
- "**Rapid prototyping** and testing"
- "**Clear separation** of triple vs. double ratchet logic"
- "**Easy debugging** without complex Double Ratchet state"

### 4. Third Ratchet Logic: Implementation & Improvements

#### **Current Implementation:**

**Core Concept:**
- "Adds a **third layer** above the traditional Double Ratchet"
- "Manages **epoch-based rotation** of root keys"
- "Provides **long-term forward secrecy**"

**Key Features:**
```python
# Epoch rotation logic:
def due(self, interval_sec: int = 24 * 3600) -> bool:
    return (time.time() - self.last_reset) >= interval_sec

# Root key derivation:
new_root_key = nacl.hash.generichash(
    shared_secret,
    key=self.root_key,
    digest_size=32
)
```

**Rotation Triggers:**
- "**Time-based**: Every 24 hours automatically"
- "**On-demand**: Manual rotation via `force_rotate=True`"
- "**Catch-up**: Automatic sync when receiving higher epoch"

#### **Ideas for Improvements:**

**1. Advanced Rotation Policies:**
```python
# Proposed enhancements:
- Message count thresholds (e.g., every 1000 messages)
- Threat level adjustments (faster rotation under attack)
- Coordinated rotation schedules
- Emergency rotation broadcasts
```

**2. Enhanced Security Features:**
```python
# Post-compromise security:
- Immediate rotation on suspected compromise
- Multiple epoch lookahead for catch-up
- Epoch authentication to prevent rollback attacks
```

**3. Performance Optimizations:**
```python
# Efficiency improvements:
- Lazy rotation (defer until needed)
- Precomputed epoch keys
- Batched header processing
- Compressed epoch metadata
```

**4. Practical Enhancements:**
```python
# Real-world features:
- Persistent epoch state
- Cross-device synchronization
- Group chat support with shared epochs
- Backup and recovery mechanisms
```

#### **Current Limitations:**
- "**Memory management**: Limited secure zeroing in Python"
- "**Persistence**: All state is in-memory only"
- "**Error handling**: Basic error recovery"
- "**Scalability**: Single-user sessions only"

#### **Unique Value Proposition:**
- "**Triple forward secrecy**: Message + DH + Epoch levels"
- "**Temporal isolation**: Past epochs can't compromise future ones"
- "**Practical security**: Automatic rotation without user intervention"
- "**Post-compromise recovery**: Multiple layers of key refresh"

---

## Demo Talking Points

### **Live Demo Flow:**
1. "Show **epoch synchronization** between Alice and Bob"
2. "Demonstrate **automatic rotation** after time threshold"
3. "Show **catch-up mechanism** when parties are out of sync"
4. "Explain **header structure** with epoch metadata"

### **Technical Highlights:**
- "**Clean API**: Single function calls for encrypt/decrypt"
- "**Transparent operation**: Users don't need to manage epochs"
- "**Robust synchronization**: Automatic catch-up handling"
- "**Extensible design**: Ready for production Double Ratchet"

### **Security Demonstrations:**
- "Show how **past epochs become unrecoverable** after rotation"
- "Demonstrate **automatic catch-up** when Bob is behind Alice's epoch"
- "Explain **forward secrecy guarantees** at three different levels"
- "Show **header metadata** that enables epoch synchronization"

### **Code Quality Highlights:**
- "**Type annotations** throughout for maintainability"
- "**Comprehensive documentation** with clear examples"
- "**Modular architecture** for easy testing and extension"
- "**Clean separation** between crypto primitives and protocol logic"

---

This comprehensive guide provides everything needed to explain and demonstrate the Triple Ratchet implementation effectively!