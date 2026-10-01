"""Reply post-check (spec §5.3 step 9).

Rejects replies that promise returns ("guaranteed return", "sure profit", "risk-free", and the same in
Hindi/Marathi/Tamil) or ask for secrets. A negated mention ("there is no guaranteed return", "never
share your OTP") is fine: warning people about these phrases is part of Saathi's job.
"""

import re

_PROMISES = re.compile(
    r"guaranteed\s+(returns?|profits?|income)|sure[- ]?(shot\s+)?profits?|risk[- ]?free|assured\s+returns?|"
    r"double\s+your\s+money|गारंटीड\s*(रिटर्न|मुनाफ़ा|मुनाफा)|पक्का\s*(मुनाफ़ा|मुनाफा)|बिना\s*जोखिम|"
    r"हमखास\s*नफा|हमी\s*परतावा|जोखीममुक्त|உத்தரவாத\s*(லாபம்|வருமானம்)|அபாயமில்லாத",
    re.IGNORECASE,
)
_ASKS_SECRET = re.compile(
    r"(share|send|tell|give|enter)\s+(me\s+)?(your\s+)?(otp|pin|cvv|password|aadhaar\s+number)|"
    r"(ओटीपी|OTP|पिन|PIN)\s*(बताएं|बताइए|भेजें|शेअर करा|सांगा)",
    re.IGNORECASE,
)
_NEGATION = re.compile(
    r"\b(no|not|never|don'?t|doesn'?t|isn'?t|aren'?t|cannot|can'?t|avoid|beware|nothing)\b|"
    r"नहीं|नही|न\s|मत|कभी|नाही|नका|कधीही|இல்லை|வேண்டாம்|கூடாது",
    re.IGNORECASE,
)


def _unnegated(pattern: re.Pattern, reply: str) -> bool:
    for m in pattern.finditer(reply):
        window = reply[max(0, m.start() - 40): m.end() + 25]
        if not _NEGATION.search(window):
            return True
    return False


def violation(reply: str) -> str | None:
    if _unnegated(_PROMISES, reply):
        return "promises returns"
    if _unnegated(_ASKS_SECRET, reply):
        return "asks for secrets"
    return None


STRICTER = (
    "IMPORTANT: Your previous answer broke a safety rule. Do not mention or promise guaranteed, sure, assured or "
    "risk-free returns or profits, do not name products to invest in, and never ask for OTP, PIN, CVV, passwords "
    "or Aadhaar numbers. Answer again, educational only."
)
