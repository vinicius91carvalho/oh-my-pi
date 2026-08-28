# Hidden scoring test for bug/py-veryhard.
# Copy to: packages/landing-gen/tests/test_py_veryhard.py (inside the worktree)
# Run:     .venv/bin/pytest packages/landing-gen/tests/test_py_veryhard.py -q
#
# D07 (docs/decisions.md): the persona is fictional; "anos de experiencia"
# claims must be blocked by validate_landing_copy in BOTH market languages.
from __future__ import annotations

from infoproduct_landing_gen.copy import validate_landing_copy
from test_landing_gen import _sample_copy


def test_portuguese_experience_claim_is_rejected() -> None:
    copy = _sample_copy()
    copy["persona_bio"] = {
        "heading": "Quem escreve",
        "paragraphs": ["Marina tem 12 anos de experiência organizando casamentos."],
        "signature_line": "- Marina",
    }
    result = validate_landing_copy(copy)
    assert not result.passed
    assert any("credential" in issue for issue in result.issues)


def test_portuguese_experience_claim_without_number_is_rejected() -> None:
    copy = _sample_copy()
    copy["persona_bio"] = {
        "heading": "Quem escreve",
        "paragraphs": ["Marina traz anos de experiencia com casamentos reais."],
        "signature_line": "- Marina",
    }
    result = validate_landing_copy(copy)
    assert not result.passed


def test_spanish_experience_claim_still_rejected() -> None:
    copy = _sample_copy()
    copy["persona_bio"]["paragraphs"] = ["Con 10 años de experiencia ayudando a familias."]
    assert not validate_landing_copy(copy).passed
