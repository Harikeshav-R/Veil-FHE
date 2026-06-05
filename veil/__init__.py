"""Veil-FHE: an educational FHE inference compiler built on CKKS / OpenFHE.

Public API (see DESIGN.md §9):

    import veil
    fhe_model = veil.compile(model, input_shape=(1, 784), calibration_data=X)
    enc, ctx  = fhe_model.encrypt(x)      # client (holds secret key)
    enc_out   = fhe_model.forward(enc)    # server (no secret key)
    out       = fhe_model.decrypt(enc_out, ctx)
"""

from veil.api import compile
from veil.errors import (
    BackendError,
    CalibrationError,
    ExportError,
    LevelBudgetError,
    OutOfDomainError,
    UnsupportedOpError,
    VeilError,
)
from veil.model import ClientContext, EncryptedTensor, FHEModel
from veil.params import Profile

__all__ = [
    "BackendError",
    "CalibrationError",
    "ClientContext",
    "EncryptedTensor",
    "ExportError",
    "FHEModel",
    "LevelBudgetError",
    "OutOfDomainError",
    "Profile",
    "UnsupportedOpError",
    "VeilError",
    "compile",
]

__version__ = "0.0.0"
