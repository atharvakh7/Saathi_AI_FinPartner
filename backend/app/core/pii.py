"""PII redaction for logs (spec §8.2).

Redacts: phone numbers, 12-digit Aadhaar-like numbers, PAN, 9–18 digit account/card
numbers, 4–8 digit codes near "otp"/"pin"/"cvv", 3–4 digit CVVs, and emails. Applied to log output only.
"""

import re

_OTP_NEAR = re.compile(
    r"(?i)\b(otp|pin|cvv|mpin|ओटीपी|पिन|ஓடிபி)\b(\D{0,20}?)(\d{4,8})\b"
)
_CVV_NEAR = re.compile(r"(?i)\b(cvv|cvc)\b(\D{0,10}?)(\d{3,4})\b")
_CODE_BEFORE_OTP = re.compile(r"(?i)\b(\d{4,8})\b(\s{0,3}(?:is\s+)?(?:your\s+)?(?:otp|pin|cvv))\b")
_AADHAAR = re.compile(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)")
_PHONE_INTL = re.compile(r"\+91[ -]?[6-9]\d{4}[ -]?\d{5}(?!\d)")
_PAN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
_PHONE = re.compile(r"(?<!\d)(?:\+?91[ -]?|0)?[6-9]\d{4}[ -]?\d{5}(?!\d)")
_ACCOUNT = re.compile(r"(?<!\d)\d{9,18}(?!\d)")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


def redact_pii(text: str) -> str:
    if not text:
        return text
    text = _OTP_NEAR.sub(lambda m: f"{m.group(1)}{m.group(2)}[CODE]", text)
    text = _CVV_NEAR.sub(lambda m: f"{m.group(1)}{m.group(2)}[CODE]", text)
    text = _CODE_BEFORE_OTP.sub(lambda m: f"[CODE]{m.group(2)}", text)
    text = _PAN.sub("[PAN]", text)
    text = _PHONE_INTL.sub("[PHONE]", text)
    text = _AADHAAR.sub("[AADHAAR]", text)
    text = _PHONE.sub("[PHONE]", text)
    text = _ACCOUNT.sub("[NUMBER]", text)
    text = _EMAIL.sub("[EMAIL]", text)
    return text


def mask_phone(phone_e164: str) -> str:
    """'+919876543210' -> '+91 ••••• 43210' (spec §4.7 S35, §7.3 UserDTO)."""
    if not phone_e164 or len(phone_e164) < 8:
        return "•••••"
    return f"{phone_e164[:3]} ••••• {phone_e164[-5:]}"
