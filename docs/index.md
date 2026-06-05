# Veil-FHE

An educational, from-scratch **FHE inference compiler** built on **CKKS / OpenFHE**.
It compiles a `torch.nn.Module` into an encrypted inference graph so a server can
run a forward pass on data it cannot read.

!!! warning "Not audited — do not protect real secrets"
    Veil-FHE is a research and learning project. It is not security-audited and
    makes no production guarantees. See [Threat model](threat-model.md).

!!! info "FHE is slow by nature"
    Encrypted inference is orders of magnitude slower than plaintext. This is
    inherent to the technique. All numbers trace to [Benchmarks](benchmarks.md).

```python
import veil

fhe_model = veil.compile(model, input_shape=(1, 784), calibration_data=X_sample)

enc_input, ctx = fhe_model.encrypt(x)        # client (holds the secret key)
enc_output = fhe_model.forward(enc_input)    # server (no secret key)
output = fhe_model.decrypt(enc_output, ctx)  # client
```

Because CKKS is native floating point, there is **no quantization pipeline** —
weights stay as floats. Start with [Getting started](getting-started.md), then
read the [Architecture](architecture.md).
