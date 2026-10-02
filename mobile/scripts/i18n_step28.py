"""Merge the step-28 Scheme Scout strings into src/i18n/*.json (idempotent)."""

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "src" / "i18n"

T = {
    "en": {"schemes": {
        "title": "Scheme Scout", "subtitle": "Find schemes you qualify for", "profileMatch": "Your profile match",
        "found": "{{eligible}} eligible, {{possibly}} possibly eligible", "checkTitle": "Check my eligibility",
        "checkHint": "{{count}} quick questions to find more schemes.", "checkButton": "Start the questions",
        "searchPlaceholder": "Search schemes (PM Kisan, pension…)", "categories": "Categories", "count": "{{count}} schemes",
        "seeResults": "See my results", "noQuestions": "Nothing more to ask. Your matches are up to date.",
        "seeMatches": "See my matches", "questionOf": "Question {{n}} of {{total}}", "affects": "Helps check {{count}} schemes",
        "matchesTitle": "Your matches", "noneYet": "No matches yet. Answer a few questions so I can find schemes for you.",
        "answerMore": "Answer more questions", "possiblyHint": "You may qualify. Answer the questions shown to be sure.",
        "showNot": "Show schemes I don't qualify for ({{count}})", "hideNot": "Hide schemes I don't qualify for",
        "resultsFor": "\"{{q}}\"", "all": "All schemes", "noResults": "No schemes found.", "detailTitle": "Scheme details",
        "loadingDetail": "Getting the details in your language…", "benefit": "What you get",
        "deadline": "Apply by {{date}}", "yourMatch": "Your match", "about": "About this scheme",
        "howToApply": "How to apply", "documents": "Documents you need", "official": "Open official website",
        "verified": "Last checked {{date}}",
        "track": {"saved": "Save", "applied": "I've applied", "dismissed": "Not for me",
                  "savedDone": "Saved", "appliedDone": "Marked as applied", "dismissedDone": "Hidden from your list", "cleared": "Removed"},
    }},
    "hi": {"schemes": {
        "title": "योजना खोज", "subtitle": "वे योजनाएँ खोजें जिनके आप हकदार हैं", "profileMatch": "आपकी प्रोफ़ाइल से मेल",
        "found": "{{eligible}} योग्य, {{possibly}} संभवतः योग्य", "checkTitle": "मेरी पात्रता जाँचें",
        "checkHint": "और योजनाएँ खोजने के लिए {{count}} छोटे सवाल।", "checkButton": "सवाल शुरू करें",
        "searchPlaceholder": "योजना खोजें (पीएम किसान, पेंशन…)", "categories": "श्रेणियाँ", "count": "{{count}} योजनाएँ",
        "seeResults": "मेरे नतीजे देखें", "noQuestions": "और कुछ पूछना नहीं है। आपके मिलान अपडेट हैं।",
        "seeMatches": "मेरे मिलान देखें", "questionOf": "सवाल {{n}} / {{total}}", "affects": "{{count}} योजनाएँ जाँचने में मदद",
        "matchesTitle": "आपके मिलान", "noneYet": "अभी कोई मिलान नहीं। कुछ सवालों के जवाब दें ताकि मैं योजनाएँ खोज सकूँ।",
        "answerMore": "और सवालों के जवाब दें", "possiblyHint": "आप योग्य हो सकते हैं। पक्का करने के लिए दिखाए गए सवालों के जवाब दें।",
        "showNot": "जिनके लिए मैं योग्य नहीं, वे दिखाएँ ({{count}})", "hideNot": "जिनके लिए मैं योग्य नहीं, वे छिपाएँ",
        "resultsFor": "\"{{q}}\"", "all": "सभी योजनाएँ", "noResults": "कोई योजना नहीं मिली।", "detailTitle": "योजना की जानकारी",
        "loadingDetail": "आपकी भाषा में जानकारी ला रहा हूँ…", "benefit": "आपको क्या मिलेगा",
        "deadline": "{{date}} तक आवेदन करें", "yourMatch": "आपका मिलान", "about": "इस योजना के बारे में",
        "howToApply": "आवेदन कैसे करें", "documents": "ज़रूरी दस्तावेज़", "official": "आधिकारिक वेबसाइट खोलें",
        "verified": "आखिरी बार {{date}} को जाँचा गया",
        "track": {"saved": "सेव करें", "applied": "मैंने आवेदन किया", "dismissed": "मेरे लिए नहीं",
                  "savedDone": "सेव हो गया", "appliedDone": "आवेदन किया चिह्नित", "dismissedDone": "आपकी सूची से छिपाया गया", "cleared": "हटाया गया"},
    }},
    "mr": {"schemes": {
        "title": "योजना शोध", "subtitle": "तुम्ही पात्र असलेल्या योजना शोधा", "profileMatch": "तुमच्या प्रोफाइलशी जुळणाऱ्या",
        "found": "{{eligible}} पात्र, {{possibly}} कदाचित पात्र", "checkTitle": "माझी पात्रता तपासा",
        "checkHint": "आणखी योजना शोधण्यासाठी {{count}} छोटे प्रश्न.", "checkButton": "प्रश्न सुरू करा",
        "searchPlaceholder": "योजना शोधा (पीएम किसान, पेन्शन…)", "categories": "श्रेण्या", "count": "{{count}} योजना",
        "seeResults": "माझे निकाल पहा", "noQuestions": "आणखी काही विचारायचे नाही. तुमच्या जुळण्या अद्ययावत आहेत.",
        "seeMatches": "माझ्या जुळण्या पहा", "questionOf": "प्रश्न {{n}} / {{total}}", "affects": "{{count}} योजना तपासण्यास मदत",
        "matchesTitle": "तुमच्या जुळण्या", "noneYet": "अजून जुळणी नाही. काही प्रश्नांची उत्तरे द्या म्हणजे मी योजना शोधू शकेन.",
        "answerMore": "आणखी प्रश्नांची उत्तरे द्या", "possiblyHint": "तुम्ही पात्र असू शकता. खात्रीसाठी दिलेल्या प्रश्नांची उत्तरे द्या.",
        "showNot": "मी पात्र नसलेल्या योजना दाखवा ({{count}})", "hideNot": "मी पात्र नसलेल्या योजना लपवा",
        "resultsFor": "\"{{q}}\"", "all": "सर्व योजना", "noResults": "योजना सापडली नाही.", "detailTitle": "योजनेची माहिती",
        "loadingDetail": "तुमच्या भाषेत माहिती आणत आहे…", "benefit": "तुम्हाला काय मिळेल",
        "deadline": "{{date}} पर्यंत अर्ज करा", "yourMatch": "तुमची जुळणी", "about": "या योजनेबद्दल",
        "howToApply": "अर्ज कसा करावा", "documents": "आवश्यक कागदपत्रे", "official": "अधिकृत वेबसाइट उघडा",
        "verified": "शेवटचे {{date}} रोजी तपासले",
        "track": {"saved": "जतन करा", "applied": "मी अर्ज केला", "dismissed": "माझ्यासाठी नाही",
                  "savedDone": "जतन झाले", "appliedDone": "अर्ज केला म्हणून नोंदवले", "dismissedDone": "तुमच्या यादीतून लपवले", "cleared": "काढले"},
    }},
    "ta": {"schemes": {
        "title": "திட்டத் தேடல்", "subtitle": "உங்களுக்குத் தகுதியான திட்டங்களைக் கண்டறியுங்கள்", "profileMatch": "உங்கள் சுயவிவரப் பொருத்தம்",
        "found": "{{eligible}} தகுதி, {{possibly}} தகுதியாக இருக்கலாம்", "checkTitle": "என் தகுதியைச் சரிபார்",
        "checkHint": "மேலும் திட்டங்களைக் கண்டறிய {{count}} சிறு கேள்விகள்.", "checkButton": "கேள்விகளைத் தொடங்கு",
        "searchPlaceholder": "திட்டங்களைத் தேடுங்கள் (பிஎம் கிசான், ஓய்வூதியம்…)", "categories": "வகைகள்", "count": "{{count}} திட்டங்கள்",
        "seeResults": "என் முடிவுகளைப் பார்", "noQuestions": "இனி கேட்க எதுவும் இல்லை. உங்கள் பொருத்தங்கள் புதுப்பிக்கப்பட்டுள்ளன.",
        "seeMatches": "என் பொருத்தங்களைப் பார்", "questionOf": "கேள்வி {{n}} / {{total}}", "affects": "{{count}} திட்டங்களைச் சரிபார்க்க உதவும்",
        "matchesTitle": "உங்கள் பொருத்தங்கள்", "noneYet": "இன்னும் பொருத்தங்கள் இல்லை. சில கேள்விகளுக்குப் பதிலளித்தால் திட்டங்களைக் கண்டறிவேன்.",
        "answerMore": "மேலும் கேள்விகளுக்குப் பதிலளி", "possiblyHint": "நீங்கள் தகுதியாக இருக்கலாம். உறுதிசெய்ய காட்டப்பட்ட கேள்விகளுக்குப் பதிலளியுங்கள்.",
        "showNot": "நான் தகுதியில்லாத திட்டங்களைக் காட்டு ({{count}})", "hideNot": "நான் தகுதியில்லாத திட்டங்களை மறை",
        "resultsFor": "\"{{q}}\"", "all": "அனைத்துத் திட்டங்களும்", "noResults": "திட்டங்கள் கிடைக்கவில்லை.", "detailTitle": "திட்ட விவரங்கள்",
        "loadingDetail": "உங்கள் மொழியில் விவரங்களைப் பெறுகிறேன்…", "benefit": "உங்களுக்குக் கிடைப்பது",
        "deadline": "{{date}}-க்குள் விண்ணப்பிக்கவும்", "yourMatch": "உங்கள் பொருத்தம்", "about": "இந்தத் திட்டம் பற்றி",
        "howToApply": "எப்படி விண்ணப்பிப்பது", "documents": "தேவையான ஆவணங்கள்", "official": "அதிகாரப்பூர்வ இணையதளத்தைத் திற",
        "verified": "கடைசியாக {{date}} அன்று சரிபார்க்கப்பட்டது",
        "track": {"saved": "சேமி", "applied": "விண்ணப்பித்தேன்", "dismissed": "எனக்கு வேண்டாம்",
                  "savedDone": "சேமிக்கப்பட்டது", "appliedDone": "விண்ணப்பித்ததாகக் குறிக்கப்பட்டது", "dismissedDone": "உங்கள் பட்டியலிலிருந்து மறைக்கப்பட்டது", "cleared": "நீக்கப்பட்டது"},
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
