"""Telefon raqamini normalizatsiya qilish (O'zbekiston)."""
import re


def normalize_phone(phone: str | None) -> str | None:
    """Raqamni 998XXXXXXXXX (12 raqam) formatiga keltiradi."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone.strip())
    if len(digits) == 9 and digits.startswith("9"):
        return "998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        return digits
    if len(digits) == 11 and digits.startswith("8"):
        return "998" + digits[1:]
    return None


def format_phone(phone: str) -> str:
    """Saqlash/ko'rsatish uchun +998 XX XXX XX XX."""
    n = normalize_phone(phone)
    if not n or len(n) != 12:
        return phone.strip()
    return f"+{n[:3]} {n[3:5]} {n[5:8]} {n[8:10]} {n[10:12]}"


def phones_match(a: str | None, b: str | None) -> bool:
    na, nb = normalize_phone(a), normalize_phone(b)
    return bool(na and nb and na == nb)
