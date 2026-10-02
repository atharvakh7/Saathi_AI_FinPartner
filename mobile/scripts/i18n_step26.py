"""Merge the step-26 voice strings and the privacy-notice 1.1 consent summary into src/i18n/*.json (idempotent)."""

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "src" / "i18n"

T = {
    "en": {
        "voice": {
            "open": "Speak to Saathi", "listening": "Listening…", "thinking": "Thinking…", "speaking": "Speaking…",
            "tapToSpeak": "Tap the mic to speak", "prompt": "How can I help you today?", "stopAndSend": "Stop and send",
            "notHeard": "I couldn't hear that clearly. Please try again, a little closer to the phone.",
            "micDenied": "Please allow the microphone so you can talk to Saathi.",
            "micError": "The microphone isn't available right now.", "tooShort": "That was very short. Tap the mic and speak a little longer.",
            "keyboard": "Keyboard", "end": "End",
        },
        "onboarding": {"consent": {"purpose": "To give you money guidance, find schemes for you, and keep you safe from scams. Saathi's replies are written with Google's Gemini AI, which receives your chats and profile details for that."}},
    },
    "hi": {
        "voice": {
            "open": "साथी से बोलें", "listening": "सुन रहा हूँ…", "thinking": "सोच रहा हूँ…", "speaking": "बोल रहा हूँ…",
            "tapToSpeak": "बोलने के लिए माइक दबाएँ", "prompt": "आज मैं आपकी कैसे मदद करूँ?", "stopAndSend": "रोकें और भेजें",
            "notHeard": "मैं साफ़ सुन नहीं पाया। फ़ोन के थोड़ा पास आकर फिर कोशिश करें।",
            "micDenied": "साथी से बात करने के लिए माइक की अनुमति दें।",
            "micError": "अभी माइक उपलब्ध नहीं है।", "tooShort": "यह बहुत छोटा था। माइक दबाकर थोड़ा और बोलें।",
            "keyboard": "कीबोर्ड", "end": "बंद करें",
        },
        "onboarding": {"consent": {"purpose": "पैसों की सलाह देने, आपके लिए योजनाएँ ढूँढने और धोखाधड़ी से बचाने के लिए। साथी के जवाब Google की Gemini AI से लिखे जाते हैं, जिसे इसके लिए आपकी बातचीत और प्रोफ़ाइल की जानकारी मिलती है।"}},
    },
    "mr": {
        "voice": {
            "open": "साथीशी बोला", "listening": "ऐकत आहे…", "thinking": "विचार करत आहे…", "speaking": "बोलत आहे…",
            "tapToSpeak": "बोलण्यासाठी माइक दाबा", "prompt": "आज मी तुमची कशी मदत करू?", "stopAndSend": "थांबा आणि पाठवा",
            "notHeard": "मला नीट ऐकू आले नाही. फोनच्या थोडे जवळ येऊन पुन्हा प्रयत्न करा.",
            "micDenied": "साथीशी बोलण्यासाठी माइकची परवानगी द्या.",
            "micError": "आत्ता माइक उपलब्ध नाही.", "tooShort": "हे खूप छोटे होते. माइक दाबून थोडे जास्त बोला.",
            "keyboard": "कीबोर्ड", "end": "बंद करा",
        },
        "onboarding": {"consent": {"purpose": "पैशांबद्दल मार्गदर्शन देण्यासाठी, तुमच्यासाठी योजना शोधण्यासाठी आणि फसवणुकीपासून वाचवण्यासाठी. साथीची उत्तरे Google च्या Gemini AI ने लिहिली जातात, ज्याला त्यासाठी तुमच्या गप्पा आणि प्रोफाइलची माहिती मिळते."}},
    },
    "ta": {
        "voice": {
            "open": "சாத்தியிடம் பேசுங்கள்", "listening": "கேட்கிறேன்…", "thinking": "யோசிக்கிறேன்…", "speaking": "பேசுகிறேன்…",
            "tapToSpeak": "பேச மைக்கைத் தட்டுங்கள்", "prompt": "இன்று நான் எப்படி உதவலாம்?", "stopAndSend": "நிறுத்தி அனுப்பு",
            "notHeard": "தெளிவாகக் கேட்கவில்லை. போனுக்குச் சற்று அருகில் வந்து மீண்டும் முயலுங்கள்.",
            "micDenied": "சாத்தியிடம் பேச மைக் அனுமதியை வழங்குங்கள்.",
            "micError": "இப்போது மைக் கிடைக்கவில்லை.", "tooShort": "மிகவும் குறுகியது. மைக்கைத் தட்டி இன்னும் கொஞ்சம் பேசுங்கள்.",
            "keyboard": "விசைப்பலகை", "end": "முடி",
        },
        "onboarding": {"consent": {"purpose": "பண வழிகாட்டுதல் தர, உங்களுக்கான திட்டங்களைக் கண்டறிய, மோசடிகளிலிருந்து காக்க. சாத்தியின் பதில்கள் Google-இன் Gemini AI மூலம் எழுதப்படுகின்றன; அதற்காக உங்கள் உரையாடல்களும் சுயவிவர விவரங்களும் அதற்கு அனுப்பப்படுகின்றன."}},
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
