# Triple-Ratchet MVP

A runnable MVP of a **Triple-Ratchet** secure-messaging library in Python, extending the Signal Double-Ratchet with a third "macro" ratchet layer.

## Features

- **Triple Ratchet Architecture**: Combines macro, DH, and symmetric ratchets
- **Epoch-based Rotation**: Automatic root key rotation with configurable intervals
- **Catch-up Mechanism**: Receivers automatically sync to higher epochs
- **Secure Memory Management**: All secrets are zeroed after use
- **Type Annotations**: Full Python 3.11+ type support

## Quick Setup

```bash
# Create virtual environment
python -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run demo (in separate terminals)
(term 1) python demo/alice.py
(term 2) python demo/bob.py
```

## Project Structure

```
triple_ratchet_mvp/
├── ratchet/
│   ├── __init__.py          # Package exports
│   ├── dh_ratchet.py        # DH ratchet wrapper
│   ├── symm_ratchet.py      # Symmetric ratchet wrapper
│   ├── macro_ratchet.py     # Third-layer macro ratchet
│   └── session.py           # Triple session glue
├── demo/
│   ├── alice.py             # Sender demo
│   └── bob.py               # Receiver demo
├── tests/
│   └── test_macro.py        # Unit tests
└── requirements.txt         # Dependencies
```

## Usage

### Basic Session

```python
from ratchet import TripleSession

# Create sessions
alice = TripleSession()
bob = TripleSession()

# Exchange macro public keys
alice.set_peer_macro_pk(bob.get_macro_pk())
bob.set_peer_macro_pk(alice.get_macro_pk())

# Encrypt and decrypt
ciphertext, header = alice.encrypt(b"Hello, world!")
plaintext = bob.decrypt(ciphertext, header)
```

### Forced Rotation

```python
# Force macro rotation on next message
ciphertext, header = alice.encrypt(b"Secret message", force_rotate=True)
```

## Testing

Run the test suite:

```bash
pytest tests/
```

## Security Notes

- Uses libsodium's `crypto_scalarmult` for DH operations
- All temporary secrets are zeroed with `sodium_memzero`
- Headers are serialized with msgpack (binary format)
- No persistent state storage (in-memory only)

## Dependencies

- `pynacl~=1.5` - Cryptographic primitives
- `python-doubleratchet~=0.4.0` - Double ratchet implementation
- `msgpack~=1.0` - Binary serialization
- `pytest~=8.0` - Testing framework 