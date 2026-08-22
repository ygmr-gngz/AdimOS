import pytest

from app.modules.content.infographic_generator import (
    _amount_value,
    validate_account_card_storyboard,
)


def _card(code: str, name: str, nature: str, amount: str = "1.000") -> dict:
    return {
        "component": "AccountCardScene",
        "accountCode": code,
        "accountName": name,
        "nature": nature,
        "journalEntry": [
            {"side": "debit", "amount": amount},
            {"side": "credit", "amount": amount},
        ],
    }


def test_account_card_storyboard_accepts_catalogued_balanced_cards() -> None:
    storyboard = {"scenes": [
        _card("100", "Kasa", "A"),
        _card("320", "Satıcılar", "P"),
        _card("600", "Yurt İçi Satışlar", "G"),
    ]}

    validate_account_card_storyboard(storyboard)


@pytest.mark.parametrize("amount, expected", [("10.000", 10000), ("10.000,50 ₺", 10000.5)])
def test_amount_value_parses_turkish_format(amount: str, expected: float) -> None:
    assert _amount_value(amount) == expected


def test_account_card_storyboard_rejects_duplicate_accounts() -> None:
    card = _card("100", "Kasa", "A")
    with pytest.raises(RuntimeError, match="mükerrer hesap"):
        validate_account_card_storyboard({"scenes": [card, card, _card("320", "Satıcılar", "P")]})


def test_account_card_storyboard_rejects_unbalanced_entry() -> None:
    bad = _card("100", "Kasa", "A")
    bad["journalEntry"][1]["amount"] = "999"
    with pytest.raises(RuntimeError, match="math_validation_failed"):
        validate_account_card_storyboard({"scenes": [
            bad,
            _card("320", "Satıcılar", "P"),
            _card("600", "Yurt İçi Satışlar", "G"),
        ]})
