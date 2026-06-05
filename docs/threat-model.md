# Threat model

!!! danger "Not audited"
    Veil-FHE has not been security-audited. Using an FHE library correctly does
    not make a given implementation secure. Treat anything you run as public.

## The model Veil-FHE targets

- **Client** is trusted and holds the CKKS secret key (keygen, encryption,
  decryption are client-side).
- **Server** is *semi-honest*: it runs the protocol correctly but may try to
  learn the input. It gets ciphertexts and the public evaluation keys, never the
  secret key.
- **Model weights are plaintext on the server.** Veil-FHE protects the client's
  **input and output**, not the model.

## What it protects

Confidentiality of the input tensor and the inference output against a
semi-honest server, at the security level of the chosen CKKS parameters
(targeting 128-bit).

## What it does NOT protect against

- **Malicious servers** — no integrity/verifiable-computation guarantee.
- **Model privacy, metadata** (input shape, topology), or timing.
- **Implementation/side-channel attacks** — no constant-time guarantees.
- **CKKS caveat:** returning *decrypted* CKKS output to an adversary who chose the
  ciphertexts can leak secret-key information (IND-CPA-D class). Keep decryption
  client-side; never return decrypted CKKS output to an untrusted party.
