# FAQ

**Is this production-ready?** No. It is a research/learning project and is not
audited. See [Threat model](threat-model.md).

**Why is it so slow?** FHE inference is inherently orders of magnitude slower than
plaintext. CKKS multiplications consume a limited noise/level budget, and deep
networks need bootstrapping (seconds per call). This is the technique, not a bug.

**Why CKKS and not TFHE/BFV?** CKKS works natively on real numbers, so there is no
quantization pipeline and weights stay as floats. BFV/BGV need quantization; TFHE
targets Boolean/LUT circuits.

**Why must I supply calibration data?** Polynomial activation approximations are
fitted over an interval. The right interval comes from the actual activation
ranges in your model; a ReLU approximated over `[-5, 5]` behaves nothing like one
over `[-50, 50]`. Out-of-domain inputs are clamped with a warning by default, or
raise under `strict=True`.

**Why did compilation raise `LevelBudgetError`?** Your network is deeper than the
chosen profile's multiplicative budget and bootstrapping is disabled (the safe
default). Pick a deeper profile, simplify the model, or pass
`allow_bootstrap="auto"` to accept the bootstrapping cost.

**Does it hide my model from the server?** No. In v1 the model weights are
plaintext on the server; only the input and output are private.
