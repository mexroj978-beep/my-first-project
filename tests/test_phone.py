"""Telefon normalizatsiya testlari."""
from app.utils.phone import format_phone, normalize_phone, phones_match


def test_normalize_uz_9_digits():
    assert normalize_phone("901234567") == "998901234567"


def test_normalize_uz_full():
    assert normalize_phone("+998 90 123 45 67") == "998901234567"


def test_phones_match():
    assert phones_match("+998901234567", "90 123 45 67")
    assert not phones_match("+998901234567", "909999999")


def test_format_phone():
    assert format_phone("901234567").startswith("+998")
