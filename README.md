# DCI-1597 Core

**Immutable, 100% deterministic exact-arithmetic engine**  
Even The Odds Foundry · Jacarri Sanders

Primary mathematical source: Google Drive research (Discrete Cyclotomic Ring, Golden State DCI, dci_engine.py, NC theorems).

## Guarantees

- **Zero floating-point** — all arithmetic is pure integer modular
- **Zero external entropy** — no UUID, no timestamps, no OS randomness in signed content
- **Bit-for-bit identical** — same input bytes → same output bytes on every machine
- **Algebraically derived identifiers** — receipt_id is a pure function of content
- **Machine-checked identities** — φ · φ⁻¹ = 1 and φ² = φ + 1 hold exactly

Characteristic: **1597** (Fibonacci prime F₁₇)

## Quick Start (Local)

```bash
pip install -r requirements.txt
python -m core.dci_1597          # runs self-proofs
python -m pytest tests/ -v
```

## API (Vercel)

Once deployed:

```
POST /api/attest
Content-Type: application/json

{
  "entity": "Example Manufacturing Corp",
  "scope1_tco2e": "66.42",
  "scope2_tco2e": "1.38",
  "reporting_year": 2025
}
```

Returns a fully deterministic receipt.

```
POST /api/verify
```

Body = the receipt object. Returns `{ "valid": true/false }`.

## Structure

```
core/
  dci_1597.py          # exact field arithmetic + receipt builder
api/
  index.py             # Vercel serverless entry (attest / verify / health)
tests/
  test_determinism.py  # bit-for-bit + identity proofs
vercel.json
requirements.txt
```

## Mathematical Foundation

- Base field: GF(1597)
- Quadratic: GF(1597²) ≅ GF(1597)[φ] / (x² − x − 1)
- Cyclotomic: elements of ℤ[ζ₅] reduced mod 1597
- Division-free reciprocal: φ⁻¹ = φ − 1

All proofs are executed at import / test time.

## License

Proprietary — Even The Odds Foundry LLC
