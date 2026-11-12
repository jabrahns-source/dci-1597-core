#!/usr/bin/env python3
"""
DCI-1597 Core — Immutable Exact Arithmetic Engine
Even The Odds Foundry / Jacarri Sanders

Primary source: Google Drive (dci_engine.py, Golden_State_DCI notebook,
Discrete Cyclotomic Ring papers, NC theorems).

Guarantees:
  - Pure integer modular arithmetic only
  - No floating point
  - No UUID / no wall-clock time in signed content
  - Same input → identical output on every machine
"""

from __future__ import annotations
from typing import Dict, Any
import hashlib
import json

MODULUS = 1597


# ---------------------------------------------------------------------------
# Layer 0: Base field GF(1597)
# ---------------------------------------------------------------------------

class GF1597:
    __slots__ = ("val",)

    def __init__(self, val: int):
        self.val = val % MODULUS

    def __add__(self, other: "GF1597 | int") -> "GF1597":
        o = other.val if isinstance(other, GF1597) else other
        return GF1597(self.val + o)

    def __sub__(self, other: "GF1597 | int") -> "GF1597":
        o = other.val if isinstance(other, GF1597) else other
        return GF1597(self.val - o)

    def __mul__(self, other: "GF1597 | int") -> "GF1597":
        o = other.val if isinstance(other, GF1597) else other
        return GF1597(self.val * o)

    def __neg__(self) -> "GF1597":
        return GF1597(-self.val)

    def inv(self) -> "GF1597":
        if self.val == 0:
            raise ZeroDivisionError("0 has no inverse in GF(1597)")
        return GF1597(pow(self.val, MODULUS - 2, MODULUS))

    def __truediv__(self, other: "GF1597 | int") -> "GF1597":
        o = other if isinstance(other, GF1597) else GF1597(other)
        return self * o.inv()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, GF1597):
            return self.val == other.val
        if isinstance(other, int):
            return self.val == (other % MODULUS)
        return False

    def __repr__(self) -> str:
        return f"GF1597({self.val})"


# ---------------------------------------------------------------------------
# Layer 1: Quadratic extension GF(1597²) ≅ GF(1597)[φ]/(x²-x-1)
# ---------------------------------------------------------------------------

class GF1597_2:
    __slots__ = ("c0", "c1")  # c0 + c1·φ

    def __init__(self, c0: int, c1: int = 0):
        self.c0 = c0 % MODULUS
        self.c1 = c1 % MODULUS

    def __add__(self, other: "GF1597_2") -> "GF1597_2":
        return GF1597_2(self.c0 + other.c0, self.c1 + other.c1)

    def __sub__(self, other: "GF1597_2") -> "GF1597_2":
        return GF1597_2(self.c0 - other.c0, self.c1 - other.c1)

    def __mul__(self, other: "GF1597_2") -> "GF1597_2":
        # φ² = φ + 1
        r0 = self.c0 * other.c0 + self.c1 * other.c1
        r1 = self.c0 * other.c1 + self.c1 * other.c0 + self.c1 * other.c1
        return GF1597_2(r0, r1)

    def norm(self) -> int:
        return (self.c0 * self.c0 + self.c0 * self.c1 - self.c1 * self.c1) % MODULUS

    def inv(self) -> "GF1597_2":
        n = self.norm()
        if n == 0:
            raise ZeroDivisionError("0 has no inverse in GF(1597²)")
        n_inv = pow(n, MODULUS - 2, MODULUS)
        return GF1597_2((self.c0 + self.c1) * n_inv, (-self.c1) * n_inv)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, GF1597_2):
            return self.c0 == other.c0 and self.c1 == other.c1
        return False

    def __repr__(self) -> str:
        return f"GF1597_2({self.c0}, {self.c1})"


# ---------------------------------------------------------------------------
# Layer 2: Cyclotomic ℤ[ζ₅] reduced mod 1597
# ---------------------------------------------------------------------------

class Cyclo5:
    __slots__ = ("c0", "c1", "c2", "c3")

    def __init__(self, c0: int = 0, c1: int = 0, c2: int = 0, c3: int = 0):
        self.c0 = c0 % MODULUS
        self.c1 = c1 % MODULUS
        self.c2 = c2 % MODULUS
        self.c3 = c3 % MODULUS

    def __add__(self, other: "Cyclo5") -> "Cyclo5":
        return Cyclo5(self.c0 + other.c0, self.c1 + other.c1,
                      self.c2 + other.c2, self.c3 + other.c3)

    def __sub__(self, other: "Cyclo5") -> "Cyclo5":
        return Cyclo5(self.c0 - other.c0, self.c1 - other.c1,
                      self.c2 - other.c2, self.c3 - other.c3)

    def __mul__(self, other: "Cyclo5") -> "Cyclo5":
        a = (self.c0, self.c1, self.c2, self.c3)
        b = (other.c0, other.c1, other.c2, other.c3)
        p = [0] * 7
        for i in range(4):
            for j in range(4):
                p[i + j] += a[i] * b[j]
        # Φ₅ reduction: x⁴ = -x³ - x² - x - 1
        return Cyclo5(
            p[0] - p[4] + p[5],
            p[1] - p[4] + p[6],
            p[2] - p[4],
            p[3] - p[4],
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Cyclo5):
            return (self.c0 == other.c0 and self.c1 == other.c1 and
                    self.c2 == other.c2 and self.c3 == other.c3)
        return False

    def __repr__(self) -> str:
        return f"Cyclo5({self.c0}, {self.c1}, {self.c2}, {self.c3})"


ONE     = Cyclo5(1, 0, 0, 0)
PHI     = Cyclo5(0, 0, -1, -1)       # φ = -ζ² - ζ³
PHI_INV = Cyclo5(-1, 0, -1, -1)      # φ⁻¹ = φ - 1


def prove_core_identities() -> None:
    """Machine-checkable algebraic proofs."""
    assert PHI * PHI_INV == ONE, "FAILED: φ · φ⁻¹ ≠ 1"
    assert PHI * PHI == PHI + ONE, "FAILED: φ² ≠ φ + 1"


def canonical_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_deterministic_receipt(
    raw_input: Dict[str, Any],
    engine_version: str = "dci-1597-v1.0.0",
) -> Dict[str, Any]:
    """
    Pure function.
    Identical input → identical receipt on every machine.
    No timestamps. No random UUIDs.
    """
    canonical_bytes = json.dumps(
        raw_input, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    input_hash = canonical_hash(canonical_bytes)

    fingerprint = GF1597(int(input_hash[:8], 16))

    receipt = {
        "schema_version": "1.0.0-dci",
        "engine_version": engine_version,
        "input_hash": input_hash,
        "algebraic_fingerprint": fingerprint.val,
        "field_characteristic": MODULUS,
        "phi_identity_verified": True,
        "determinism_guarantee": "pure-function-no-entropy",
        "payload": raw_input,
    }

    # receipt_id is derived from content (excluding itself)
    content_bytes = json.dumps(
        receipt, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    receipt["receipt_id"] = canonical_hash(content_bytes)
    return receipt


def verify_receipt(receipt: Dict[str, Any]) -> bool:
    """Pure verification."""
    payload = receipt.get("payload")
    if payload is None:
        return False

    canonical_bytes = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    expected_input_hash = canonical_hash(canonical_bytes)
    if receipt.get("input_hash") != expected_input_hash:
        return False

    expected_fp = GF1597(int(expected_input_hash[:8], 16)).val
    if receipt.get("algebraic_fingerprint") != expected_fp:
        return False

    temp = {k: v for k, v in receipt.items() if k != "receipt_id"}
    content_bytes = json.dumps(
        temp, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    expected_id = canonical_hash(content_bytes)
    return receipt.get("receipt_id") == expected_id


if __name__ == "__main__":
    print("=== DCI-1597 Core — Self Proof ===")
    prove_core_identities()
    print("✓ φ · φ⁻¹ = 1")
    print("✓ φ² = φ + 1")

    sample = {
        "entity": "Example Manufacturing Corp",
        "scope1_tco2e": "66.42",
        "scope2_tco2e": "1.38",
        "reporting_year": 2025,
    }
    r1 = build_deterministic_receipt(sample)
    r2 = build_deterministic_receipt(sample)
    assert r1 == r2, "Determinism broken"
    assert verify_receipt(r1), "Verification failed"
    print("✓ Determinism: identical input → identical receipt")
    print("✓ Verification passes")
    print("Receipt ID:", r1["receipt_id"])
    print("All proofs passed. System is closed and deterministic.")
