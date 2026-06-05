"""FHEModel: the compiled, executable artifact (DESIGN.md §6 Stage E/F, §9)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch


class EncryptedTensor:
    """Opaque wrapper over backend ciphertext handle(s) + slot layout. No secret material."""


class ClientContext:
    """Holds the secret key + decryption metadata. NEVER crosses to the server."""


class FHEModel:
    """A compiled inference graph runnable on ciphertexts."""

    def encrypt(self, x: torch.Tensor) -> tuple[EncryptedTensor, ClientContext]:
        """Client-side: CKKS-pack and encrypt an input. Returns (ciphertext, client context)."""
        raise NotImplementedError("Phase 5.")

    def forward(self, enc_x: EncryptedTensor) -> EncryptedTensor:
        """Server-side: run the encrypted forward pass. Requires only public eval keys."""
        raise NotImplementedError("Phase 5.")

    def decrypt(self, enc_out: EncryptedTensor, ctx: ClientContext) -> torch.Tensor:
        """Client-side: decrypt and unpack the result to a torch.Tensor."""
        raise NotImplementedError("Phase 5.")

    def save(self, path: str, *, bundle: bool = False) -> None:
        """Persist the compiled graph + crypto params. Eval keys only if bundle=True (decision 5)."""
        raise NotImplementedError("Phase 5.")

    def save_eval_keys(self, path: str) -> None:
        """Persist the (large) rotation/relinearization/bootstrap keys separately."""
        raise NotImplementedError("Phase 5.")

    @classmethod
    def load(cls, path: str) -> FHEModel:
        """Load a compiled model artifact."""
        raise NotImplementedError("Phase 5.")
