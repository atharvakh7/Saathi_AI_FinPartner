"""Merge the UI-refresh strings (Services tab, Goals tab, Home hero) into src/i18n/*.json (idempotent)."""

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "src" / "i18n"

ITEMS = {
    "en": {"planner": ("Income Planner", "Budget and next 6 months"), "risk": ("Risk Report", "Your money risk score"),
           "emergency": ("Emergency Fund", "Your safety cushion"), "fraud": ("Fraud Shield", "Check a suspicious message"),
           "schemes": ("Scheme Scout", "Government schemes for you"), "learn": ("Learn", "Money words and lessons"),
           "insights": ("Insights", "Tips about your money"), "transactions": ("Transactions", "Income and expenses"),
           "debts": ("Debts", "Loans and what's left"), "addEntry": ("Add entry", "Log income or an expense")},
    "hi": {"planner": ("आमदनी योजना", "बजट और अगले 6 महीने"), "risk": ("जोखिम रिपोर्ट", "आपका पैसों का जोखिम स्कोर"),
           "emergency": ("आपातकालीन फंड", "आपकी सुरक्षा गद्दी"), "fraud": ("फ़्रॉड शील्ड", "शक वाला मैसेज जाँचें"),
           "schemes": ("योजना खोज", "आपके लिए सरकारी योजनाएँ"), "learn": ("सीखें", "पैसों के शब्द और पाठ"),
           "insights": ("सुझाव", "आपके पैसों पर सुझाव"), "transactions": ("लेन-देन", "कमाई और खर्च"),
           "debts": ("कर्ज़", "लोन और बाकी रकम"), "addEntry": ("एंट्री जोड़ें", "कमाई या खर्च लिखें")},
    "mr": {"planner": ("उत्पन्न नियोजन", "बजेट आणि पुढील 6 महिने"), "risk": ("जोखीम अहवाल", "तुमचा पैशांचा जोखीम स्कोअर"),
           "emergency": ("आपत्कालीन निधी", "तुमची सुरक्षा उशी"), "fraud": ("फ्रॉड शील्ड", "शंकास्पद मेसेज तपासा"),
           "schemes": ("योजना शोध", "तुमच्यासाठी सरकारी योजना"), "learn": ("शिका", "पैशांचे शब्द आणि धडे"),
           "insights": ("सूचना", "तुमच्या पैशांबद्दल टिप्स"), "transactions": ("व्यवहार", "उत्पन्न आणि खर्च"),
           "debts": ("कर्ज", "कर्जे आणि बाकी रक्कम"), "addEntry": ("नोंद जोडा", "उत्पन्न किंवा खर्च लिहा")},
    "ta": {"planner": ("வருமானத் திட்டம்", "பட்ஜெட் மற்றும் அடுத்த 6 மாதங்கள்"), "risk": ("அபாய அறிக்கை", "உங்கள் பண அபாய மதிப்பெண்"),
           "emergency": ("அவசர நிதி", "உங்கள் பாதுகாப்புக் கவசம்"), "fraud": ("மோசடிக் கவசம்", "சந்தேகமான செய்தியைச் சரிபார்"),
           "schemes": ("திட்டத் தேடல்", "உங்களுக்கான அரசுத் திட்டங்கள்"), "learn": ("கற்க", "பணச் சொற்களும் பாடங்களும்"),
           "insights": ("குறிப்புகள்", "உங்கள் பணம் பற்றிய குறிப்புகள்"), "transactions": ("பரிவர்த்தனைகள்", "வருமானமும் செலவுகளும்"),
           "debts": ("கடன்கள்", "கடன்களும் மீதித் தொகையும்"), "addEntry": ("பதிவு சேர்", "வருமானம் அல்லது செலவைப் பதிவு செய்")},
}

T = {
    "en": {"tabs": {"services": "Services", "goals": "Goals"},
           "services": {"title": "Services", "subtitle": "Everything Saathi can help with", "planProtect": "Plan & protect",
                        "discover": "Discover", "yourMoney": "Your money"},
           "home": {"spentShare": "You've spent {{pct}}% of this month's income"}},
    "hi": {"tabs": {"services": "सेवाएँ", "goals": "लक्ष्य"},
           "services": {"title": "सेवाएँ", "subtitle": "साथी किन-किन चीज़ों में मदद कर सकता है", "planProtect": "योजना और सुरक्षा",
                        "discover": "खोजें", "yourMoney": "आपका पैसा"},
           "home": {"spentShare": "आपने इस महीने की कमाई का {{pct}}% खर्च किया है"}},
    "mr": {"tabs": {"services": "सेवा", "goals": "ध्येये"},
           "services": {"title": "सेवा", "subtitle": "साथी कशाकशात मदत करू शकतो", "planProtect": "नियोजन आणि सुरक्षा",
                        "discover": "शोधा", "yourMoney": "तुमचे पैसे"},
           "home": {"spentShare": "तुम्ही या महिन्याच्या उत्पन्नाचा {{pct}}% खर्च केला आहे"}},
    "ta": {"tabs": {"services": "சேவைகள்", "goals": "இலக்குகள்"},
           "services": {"title": "சேவைகள்", "subtitle": "சாத்தி உதவக்கூடிய அனைத்தும்", "planProtect": "திட்டமிடல் & பாதுகாப்பு",
                        "discover": "கண்டறி", "yourMoney": "உங்கள் பணம்"},
           "home": {"spentShare": "இந்த மாத வருமானத்தில் {{pct}}% செலவழித்துள்ளீர்கள்"}},
}
for lang, items in ITEMS.items():
    T[lang]["services"]["item"] = {k: {"title": a, "hint": b} for k, (a, b) in items.items()}


def merge(dst: dict, src: dict) -> None:
    for k, v in src.items():
        if isinstance(v, dict):
            merge(dst.setdefault(k, {}), v)
        else:
            dst[k] = v


for lang, strings in T.items():
    path = DIR / f"{lang}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    merge(data, strings)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{lang}: merged")
