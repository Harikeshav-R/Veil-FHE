# Security Policy

## ⚠️ Veil-FHE is not audited. Do not use it to protect real secrets.

Veil-FHE is a research and learning project. It has not undergone any security
audit, and its implementation has not been reviewed for correctness against the
threats that real deployments face (side channels, key-management failures,
implementation bugs that weaken the cryptography). **Using a homomorphic
encryption library correctly does not make a particular implementation of it
secure.** Treat anything you run through Veil-FHE as if it were public.

## Threat model (summary)

The full threat model is in [`DESIGN.md` §3](DESIGN.md#3-threat-model) and
[`docs/threat-model.md`](docs/threat-model.md). In brief:

- **Client** is trusted and holds the CKKS secret key (keygen, encryption,
  decryption happen client-side).
- **Server** is assumed *semi-honest* (honest-but-curious): it follows the
  protocol but may try to learn the input. It receives ciphertexts and the public
  evaluation keys, never the secret key.
- **Model weights are plaintext on the server.** Veil-FHE protects the
  confidentiality of the client's **input and output**, not the model.

### What Veil-FHE does NOT protect against

- Malicious (actively dishonest) servers — there is no integrity/verifiable-
  computation guarantee.
- Model privacy, metadata (input shape, topology), or timing.
- Implementation-level and side-channel attacks; no constant-time guarantees.
- **CKKS approximate-FHE caveat:** handing *decrypted* CKKS results back to an
  adversary who chose the ciphertexts can leak secret-key information
  (IND-CPA-D class). Veil-FHE's design keeps decryption client-side; do not build
  protocols that return decrypted CKKS output to an untrusted party.

## Reporting a vulnerability

This is a personal research project, not a maintained security product. If you
find a security-relevant issue, please open a GitHub issue describing it, or
contact the maintainer through the repository. There is no SLA, bounty, or
guaranteed response time. Please do not report vulnerabilities expecting the
guarantees of a production project.

## Supported versions

Only the latest `main` is worked on. No backported security fixes.
