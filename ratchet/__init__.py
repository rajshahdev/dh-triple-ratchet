"""
Triple-Ratchet secure messaging library.

Extends the Signal Double-Ratchet with a third "macro" ratchet layer
for additional security properties.
"""

from .session import TripleSession
from .macro_ratchet import MacroRatchet

__all__ = ["TripleSession", "MacroRatchet"]
__version__ = "0.1.0" 