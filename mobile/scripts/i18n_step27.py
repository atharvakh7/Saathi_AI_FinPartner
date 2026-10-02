"""Merge the step-27 Learn strings into src/i18n/*.json (idempotent)."""

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "src" / "i18n"

T = {
    "en": {"learn": {
        "title": "Learn", "subtitle": "Money words, made simple", "xp": "XP", "level": "Level", "streak": "Day streak",
        "lessonsDone": "{{done}} of {{total}} lessons done", "toNextLevel": "{{xp}} XP to next level",
        "jargon": "Jargon Explainer", "searchPlaceholder": "Search a term (EMI, SIP, NAV…)",
        "noTerms": "No term found for \"{{q}}\". Try asking Saathi.", "popular": "Popular terms", "lessons": "Lessons",
        "category": {"basics": "Basics", "savings": "Savings", "investing": "Investing", "insurance": "Insurance"},
        "glossaryCategory": {"basics": "Basics", "investing": "Investing", "savings": "Savings", "insurance": "Insurance", "loans": "Loans"},
        "noLessons": "No lessons here yet.", "minutes": "{{count}} min", "difficulty": {"easy": "Easy", "medium": "Medium"},
        "completed": "Completed", "simplifiedByAi": "Simplified by AI", "watch": "Watch ({{sec}} sec)",
        "example": "Example", "thinkOfIt": "Think of it like…", "remember": "Remember", "related": "Related terms",
        "helpful": "Was this helpful?", "thanks": "Thanks for telling us!", "askSaathi": "Ask Saathi about it",
        "lesson": "Lesson", "xpEarned": "+{{xp}} XP! Streak: {{streak}} days", "alreadyDone": "You've already finished this lesson.",
        "markComplete": "Mark as complete (+{{xp}} XP)", "doneBubble": "Well done! Pick another lesson to keep your streak going.",
    }},
    "hi": {"learn": {
        "title": "सीखें", "subtitle": "पैसों के शब्द, आसान भाषा में", "xp": "XP", "level": "लेवल", "streak": "दिन लगातार",
        "lessonsDone": "{{total}} में से {{done}} पाठ पूरे", "toNextLevel": "अगले लेवल के लिए {{xp}} XP",
        "jargon": "शब्द समझें", "searchPlaceholder": "कोई शब्द खोजें (EMI, SIP, NAV…)",
        "noTerms": "\"{{q}}\" के लिए कोई शब्द नहीं मिला। साथी से पूछें।", "popular": "लोकप्रिय शब्द", "lessons": "पाठ",
        "category": {"basics": "बुनियादी", "savings": "बचत", "investing": "निवेश", "insurance": "बीमा"},
        "glossaryCategory": {"basics": "बुनियादी", "investing": "निवेश", "savings": "बचत", "insurance": "बीमा", "loans": "कर्ज़"},
        "noLessons": "यहाँ अभी कोई पाठ नहीं है।", "minutes": "{{count}} मिनट", "difficulty": {"easy": "आसान", "medium": "मध्यम"},
        "completed": "पूरा हुआ", "simplifiedByAi": "AI द्वारा सरल किया गया", "watch": "देखें ({{sec}} सेकंड)",
        "example": "उदाहरण", "thinkOfIt": "ऐसे समझिए…", "remember": "याद रखें", "related": "जुड़े हुए शब्द",
        "helpful": "क्या यह मददगार था?", "thanks": "बताने के लिए धन्यवाद!", "askSaathi": "इसके बारे में साथी से पूछें",
        "lesson": "पाठ", "xpEarned": "+{{xp}} XP! लगातार: {{streak}} दिन", "alreadyDone": "आप यह पाठ पहले ही पूरा कर चुके हैं।",
        "markComplete": "पूरा हुआ चिह्नित करें (+{{xp}} XP)", "doneBubble": "शाबाश! सिलसिला जारी रखने के लिए अगला पाठ चुनें।",
    }},
    "mr": {"learn": {
        "title": "शिका", "subtitle": "पैशांचे शब्द, सोप्या भाषेत", "xp": "XP", "level": "स्तर", "streak": "दिवस सलग",
        "lessonsDone": "{{total}} पैकी {{done}} धडे पूर्ण", "toNextLevel": "पुढील स्तरासाठी {{xp}} XP",
        "jargon": "शब्द समजून घ्या", "searchPlaceholder": "शब्द शोधा (EMI, SIP, NAV…)",
        "noTerms": "\"{{q}}\" साठी शब्द सापडला नाही. साथीला विचारा.", "popular": "लोकप्रिय शब्द", "lessons": "धडे",
        "category": {"basics": "मूलभूत", "savings": "बचत", "investing": "गुंतवणूक", "insurance": "विमा"},
        "glossaryCategory": {"basics": "मूलभूत", "investing": "गुंतवणूक", "savings": "बचत", "insurance": "विमा", "loans": "कर्ज"},
        "noLessons": "इथे अजून धडे नाहीत.", "minutes": "{{count}} मिनिटे", "difficulty": {"easy": "सोपे", "medium": "मध्यम"},
        "completed": "पूर्ण", "simplifiedByAi": "AI ने सोपे केलेले", "watch": "पहा ({{sec}} सेकंद)",
        "example": "उदाहरण", "thinkOfIt": "असे समजा…", "remember": "लक्षात ठेवा", "related": "संबंधित शब्द",
        "helpful": "हे उपयोगी होते का?", "thanks": "सांगितल्याबद्दल धन्यवाद!", "askSaathi": "याबद्दल साथीला विचारा",
        "lesson": "धडा", "xpEarned": "+{{xp}} XP! सलग: {{streak}} दिवस", "alreadyDone": "तुम्ही हा धडा आधीच पूर्ण केला आहे.",
        "markComplete": "पूर्ण म्हणून नोंदवा (+{{xp}} XP)", "doneBubble": "छान! सलग शिकत राहण्यासाठी पुढचा धडा निवडा.",
    }},
    "ta": {"learn": {
        "title": "கற்க", "subtitle": "பணச் சொற்கள், எளிமையாக", "xp": "XP", "level": "நிலை", "streak": "தொடர் நாட்கள்",
        "lessonsDone": "{{total}}-இல் {{done}} பாடங்கள் முடிந்தன", "toNextLevel": "அடுத்த நிலைக்கு {{xp}} XP",
        "jargon": "சொல் விளக்கம்", "searchPlaceholder": "ஒரு சொல்லைத் தேடுங்கள் (EMI, SIP, NAV…)",
        "noTerms": "\"{{q}}\"-க்கு சொல் கிடைக்கவில்லை. சாத்தியிடம் கேளுங்கள்.", "popular": "பிரபலமான சொற்கள்", "lessons": "பாடங்கள்",
        "category": {"basics": "அடிப்படை", "savings": "சேமிப்பு", "investing": "முதலீடு", "insurance": "காப்பீடு"},
        "glossaryCategory": {"basics": "அடிப்படை", "investing": "முதலீடு", "savings": "சேமிப்பு", "insurance": "காப்பீடு", "loans": "கடன்கள்"},
        "noLessons": "இங்கே இன்னும் பாடங்கள் இல்லை.", "minutes": "{{count}} நிமிடம்", "difficulty": {"easy": "எளிது", "medium": "நடுத்தரம்"},
        "completed": "முடிந்தது", "simplifiedByAi": "AI மூலம் எளிமையாக்கப்பட்டது", "watch": "பாருங்கள் ({{sec}} வினாடி)",
        "example": "உதாரணம்", "thinkOfIt": "இப்படி நினைத்துப் பாருங்கள்…", "remember": "நினைவில் கொள்ளுங்கள்", "related": "தொடர்புடைய சொற்கள்",
        "helpful": "இது உதவியாக இருந்ததா?", "thanks": "தெரிவித்ததற்கு நன்றி!", "askSaathi": "இதைப் பற்றி சாத்தியிடம் கேளுங்கள்",
        "lesson": "பாடம்", "xpEarned": "+{{xp}} XP! தொடர்: {{streak}} நாட்கள்", "alreadyDone": "இந்தப் பாடத்தை ஏற்கனவே முடித்துவிட்டீர்கள்.",
        "markComplete": "முடிந்ததாகக் குறி (+{{xp}} XP)", "doneBubble": "அருமை! தொடர்ந்து கற்க அடுத்த பாடத்தைத் தேர்வு செய்யுங்கள்.",
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
