"""Merge the step-25 Saathi chat strings into src/i18n/*.json (idempotent)."""

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "src" / "i18n"

T = {
    "en": {"chat": {
        "subtitle": "Your money friend · ask in your language", "typing": "Saathi is thinking…",
        "history": "Past chats", "newChat": "New chat", "placeholder": "Ask Saathi anything about money…",
        "send": "Send", "fallbackGreeting": "Namaste! Ask me about saving, loans, schemes or a message you're unsure about.",
        "disclaimer": "Saathi explains and guides. It is not a SEBI-registered adviser.",
        "historyEmpty": "No chats yet. Say hello to Saathi!", "untitled": "Chat",
        "deleteTitle": "Delete this chat?", "deleteMessage": "Its messages will be removed. Things Saathi remembers stay in Memory.",
    }},
    "hi": {"chat": {
        "subtitle": "आपका पैसों का दोस्त · अपनी भाषा में पूछें", "typing": "साथी सोच रहा है…",
        "history": "पुरानी बातचीत", "newChat": "नई बातचीत", "placeholder": "पैसों के बारे में साथी से कुछ भी पूछें…",
        "send": "भेजें", "fallbackGreeting": "नमस्ते! बचत, कर्ज़, योजनाओं या किसी शक वाले मैसेज के बारे में पूछिए।",
        "disclaimer": "साथी समझाता और राह दिखाता है। यह SEBI-पंजीकृत सलाहकार नहीं है।",
        "historyEmpty": "अभी कोई बातचीत नहीं। साथी को नमस्ते कहें!", "untitled": "बातचीत",
        "deleteTitle": "यह बातचीत हटाएँ?", "deleteMessage": "इसके मैसेज हट जाएँगे। साथी की याद रखी बातें मेमोरी में रहेंगी।",
    }},
    "mr": {"chat": {
        "subtitle": "तुमचा पैशांचा मित्र · तुमच्या भाषेत विचारा", "typing": "साथी विचार करत आहे…",
        "history": "जुन्या गप्पा", "newChat": "नवीन गप्पा", "placeholder": "पैशांबद्दल साथीला काहीही विचारा…",
        "send": "पाठवा", "fallbackGreeting": "नमस्कार! बचत, कर्ज, योजना किंवा शंका असलेल्या मेसेजबद्दल विचारा.",
        "disclaimer": "साथी समजावतो आणि मार्गदर्शन करतो. तो SEBI-नोंदणीकृत सल्लागार नाही.",
        "historyEmpty": "अजून गप्पा नाहीत. साथीला नमस्कार करा!", "untitled": "गप्पा",
        "deleteTitle": "या गप्पा काढायच्या?", "deleteMessage": "यातील मेसेज काढले जातील. साथीने लक्षात ठेवलेल्या गोष्टी मेमरीत राहतील.",
    }},
    "ta": {"chat": {
        "subtitle": "உங்கள் பண நண்பன் · உங்கள் மொழியில் கேளுங்கள்", "typing": "சாத்தி யோசிக்கிறது…",
        "history": "பழைய உரையாடல்கள்", "newChat": "புதிய உரையாடல்", "placeholder": "பணம் பற்றி சாத்தியிடம் எதையும் கேளுங்கள்…",
        "send": "அனுப்பு", "fallbackGreeting": "வணக்கம்! சேமிப்பு, கடன், திட்டங்கள் அல்லது சந்தேகமான செய்தி பற்றிக் கேளுங்கள்.",
        "disclaimer": "சாத்தி விளக்கி வழிகாட்டும். இது SEBI-பதிவு பெற்ற ஆலோசகர் அல்ல.",
        "historyEmpty": "இன்னும் உரையாடல்கள் இல்லை. சாத்திக்கு வணக்கம் சொல்லுங்கள்!", "untitled": "உரையாடல்",
        "deleteTitle": "இந்த உரையாடலை நீக்கவா?", "deleteMessage": "இதன் செய்திகள் நீக்கப்படும். சாத்தி நினைவில் வைத்தவை நினைவகத்தில் இருக்கும்.",
    }},
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
