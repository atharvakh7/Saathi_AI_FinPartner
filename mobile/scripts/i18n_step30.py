"""Merge the step-30 Insights / Notifications strings into src/i18n/*.json (idempotent)."""

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "src" / "i18n"

T = {
    "en": {
        "insights": {"title": "Insights for you", "savings": "Savings", "spending": "Spending", "open": "Open",
                     "empty": "No insights yet. Add your income and expenses and I'll share tips here."},
        "notifications": {"title": "Notifications", "readAll": "Mark all read", "unread": "Unread",
                          "unreadCount": "Notifications, {{count}} unread", "empty": "No notifications yet."},
        "settings": {"notifications": {"pushDenied": "Notifications are blocked. Allow them in your phone settings.",
                                       "pushInAppOnly": "Phone alerts aren't available here; you'll see them in the app's notifications."}},
    },
    "hi": {
        "insights": {"title": "आपके लिए सुझाव", "savings": "बचत", "spending": "खर्च", "open": "खोलें",
                     "empty": "अभी कोई सुझाव नहीं। अपनी कमाई और खर्च जोड़ें, मैं यहाँ सुझाव दूँगा।"},
        "notifications": {"title": "सूचनाएँ", "readAll": "सब पढ़ा हुआ करें", "unread": "अनपढ़ा",
                          "unreadCount": "सूचनाएँ, {{count}} अनपढ़ी", "empty": "अभी कोई सूचना नहीं।"},
        "settings": {"notifications": {"pushDenied": "सूचनाएँ बंद हैं। फ़ोन की सेटिंग में अनुमति दें।",
                                       "pushInAppOnly": "यहाँ फ़ोन अलर्ट उपलब्ध नहीं हैं; आप उन्हें ऐप की सूचनाओं में देखेंगे।"}},
    },
    "mr": {
        "insights": {"title": "तुमच्यासाठी सूचना", "savings": "बचत", "spending": "खर्च", "open": "उघडा",
                     "empty": "अजून सूचना नाहीत. तुमचे उत्पन्न आणि खर्च जोडा, मी इथे टिप्स देईन."},
        "notifications": {"title": "सूचना", "readAll": "सर्व वाचलेले करा", "unread": "न वाचलेले",
                          "unreadCount": "सूचना, {{count}} न वाचलेल्या", "empty": "अजून सूचना नाहीत."},
        "settings": {"notifications": {"pushDenied": "सूचना बंद आहेत. फोनच्या सेटिंगमध्ये परवानगी द्या.",
                                       "pushInAppOnly": "इथे फोन अलर्ट उपलब्ध नाहीत; तुम्हाला त्या ॲपमधील सूचनांमध्ये दिसतील."}},
    },
    "ta": {
        "insights": {"title": "உங்களுக்கான குறிப்புகள்", "savings": "சேமிப்பு", "spending": "செலவு", "open": "திற",
                     "empty": "இன்னும் குறிப்புகள் இல்லை. வருமானம், செலவுகளைச் சேர்த்தால் இங்கே குறிப்புகள் தருவேன்."},
        "notifications": {"title": "அறிவிப்புகள்", "readAll": "அனைத்தையும் படித்ததாகக் குறி", "unread": "படிக்காதது",
                          "unreadCount": "அறிவிப்புகள், {{count}} படிக்காதவை", "empty": "இன்னும் அறிவிப்புகள் இல்லை."},
        "settings": {"notifications": {"pushDenied": "அறிவிப்புகள் தடுக்கப்பட்டுள்ளன. போன் அமைப்புகளில் அனுமதி தாருங்கள்.",
                                       "pushInAppOnly": "இங்கே போன் எச்சரிக்கைகள் கிடைக்காது; செயலியின் அறிவிப்புகளில் பார்ப்பீர்கள்."}},
    },
}


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
