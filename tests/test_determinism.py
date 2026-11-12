"""
Determinism & algebraic identity tests for DCI-1597 Core
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.dci_1597 import (
    PHI, PHI_INV, ONE,
    build_deterministic_receipt,
    verify_receipt,
    prove_core_identities,
    GF1597,
    Cyclo5,
)


def test_phi_identities():
    prove_core_identities()
    assert PHI * PHI_INV == ONE
    assert PHI * PHI == PHI + ONE


def test_determinism_identical_input():
    payload = {
        "entity": "Test Entity LLC",
        "scope1": "12.5",
        "scope2": "3.1",
        "year": 2025,
    }
    r1 = build_deterministic_receipt(payload)
    r2 = build_deterministic_receipt(payload)
    assert r1 == r2
    assert r1["receipt_id"] == r2["receipt_id"]


def test_verification_passes():
    payload = {"a": 1, "b": "two"}
    receipt = build_deterministic_receipt(payload)
    assert verify_receipt(receipt) is True


def test_tamper_detection():
    payload = {"a": 1}
    receipt = build_deterministic_receipt(payload)
    receipt["payload"]["a"] = 999
    assert verify_receipt(receipt) is False


def test_different_input_different_id():
    r1 = build_deterministic_receipt({"x": 1})
    r2 = build_deterministic_receipt({"x": 2})
    assert r1["receipt_id"] != r2["receipt_id"]


def test_field_arithmetic_basics():
    a = GF1597(100)
    b = GF1597(50)
    assert (a + b).val == 150
    assert (a * b).val == (100 * 50) % 1597


def test_cyclo_addition():
    x = Cyclo5(1, 2, 3, 4)
    y = Cyclo5(4, 3, 2, 1)
    z = x + y
    assert z == Cyclo5(5, 5, 5, 5)
