"""Merge the step-21 tab bar / profile / settings strings into src/i18n/*.json (idempotent)."""

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "src" / "i18n"

# Spec S37 greetings (shown under each language's name).
GREETINGS = {
    "en": "Hello! How can I help?",
    "hi": "नमस्ते! मैं आपकी कैसे मदद करूँ?",
    "mr": "नमस्कार! मी तुमची कशी मदत करू?",
    "ta": "வணக்கம்! நான் எப்படி உதவலாம்?",
}

T = {
    "en": {
        "common": {"comingSoon": "Coming soon in the next update."},
        "settings": {
            "editProfile": "Edit profile", "confidence": "Financial confidence", "notTaken": "Not taken",
            "retake": "Tap to retake the 5 questions", "about": "About Saathi", "version": "Version {{version}}",
            "logout": "Log out", "logoutConfirm": "Log out of Saathi on this phone?", "saved": "Saved",
            "notSaved": "Couldn't save. Please try again.", "eligibilityAnswers": "Your answers for schemes",
            "confidenceLevel": {"low": "Low", "medium": "Medium", "high": "High"},
            "language": {"title": "Language", "header": "Choose your language", "apply": "Apply Language",
                         "bubble": "Saathi will always talk to you in your language."},
            "notifications": {
                "title": "Notifications", "push": "Allow notifications", "pushHint": "Turn off to stop all reminders.",
                "dailyInsight": "Daily money tip", "at": "Time", "incomeReminder": "Reminder to add income",
                "weekly": "Once a week", "goalReminder": "Goal reminders", "schemeDeadline": "Scheme deadlines",
                "leanMonth": "Tight month alerts", "streak": "Learning streak reminder",
            },
            "privacy": {
                "title": "Privacy & data", "consents": "Your consents", "requiredHint": "Needed to use Saathi",
                "yourData": "Your data", "exportHint": "Get a copy of everything Saathi has about you, as a file.",
                "export": "Download my data", "exportShared": "Your data file is ready to share or save.",
                "exportDone": "Your data file has been downloaded.",
                "deleteHint": "Deleting removes your account and all your data. This can't be undone after 30 days.",
                "delete": "Delete my account and data", "deleteTitle": "Delete your account?",
                "deleteWarning": "Your profile, chats, money entries, goals and memories will be deleted. You will be logged out.",
                "typeDelete": "Type DELETE to confirm", "typeDeleteHint": "This is the last step.",
                "typeExactly": "Type DELETE in capital letters.", "deleteNow": "Delete now",
                "deleted": "Your account will be deleted.", "grievance": "Questions or complaints",
                "grievanceHint": "Write to our grievance officer:",
            },
            "memory": {
                "title": "Memory", "intro": "These are things I remember to help you better. Delete anything you like.",
                "empty": "Saathi hasn't remembered anything yet.", "forgetAll": "Forget everything",
                "forgetAllTitle": "Forget everything?", "forgetAllWarning": "Saathi will forget everything it remembers about you.",
                "forgetOneTitle": "Forget this?", "forgotOne": "Forgotten.", "forgotAll": "Saathi has forgotten everything.",
                "category": {"preference": "Preference", "fact": "About you", "goal_context": "Goal",
                             "concern": "Worry", "behavior": "Habit"},
            },
        },
    },
    "hi": {
        "common": {"comingSoon": "अगले अपडेट में आ रहा है।"},
        "settings": {
            "editProfile": "प्रोफ़ाइल बदलें", "confidence": "पैसों को लेकर आत्मविश्वास", "notTaken": "नहीं दिया",
            "retake": "5 सवाल फिर से देने के लिए टैप करें", "about": "साथी के बारे में", "version": "वर्ज़न {{version}}",
            "logout": "लॉग आउट", "logoutConfirm": "इस फ़ोन पर साथी से लॉग आउट करें?", "saved": "सेव हो गया",
            "notSaved": "सेव नहीं हो पाया। कृपया फिर कोशिश करें।", "eligibilityAnswers": "योजनाओं के लिए आपके जवाब",
            "confidenceLevel": {"low": "कम", "medium": "मध्यम", "high": "अच्छा"},
            "language": {"title": "भाषा", "header": "अपनी भाषा चुनें", "apply": "भाषा लागू करें",
                         "bubble": "साथी हमेशा आपसे आपकी भाषा में बात करेगा।"},
            "notifications": {
                "title": "सूचनाएँ", "push": "सूचनाएँ चालू रखें", "pushHint": "सभी याद दिलाने वाले संदेश बंद करने के लिए बंद करें।",
                "dailyInsight": "रोज़ का पैसों का सुझाव", "at": "समय", "incomeReminder": "कमाई जोड़ने की याद",
                "weekly": "हफ़्ते में एक बार", "goalReminder": "लक्ष्य की याद", "schemeDeadline": "योजना की आखिरी तारीख",
                "leanMonth": "तंगी वाले महीने की चेतावनी", "streak": "सीखने के सिलसिले की याद",
            },
            "privacy": {
                "title": "गोपनीयता और डेटा", "consents": "आपकी सहमतियाँ", "requiredHint": "साथी इस्तेमाल करने के लिए ज़रूरी",
                "yourData": "आपका डेटा", "exportHint": "साथी के पास आपकी जो भी जानकारी है, उसकी एक फ़ाइल पाएँ।",
                "export": "मेरा डेटा डाउनलोड करें", "exportShared": "आपकी डेटा फ़ाइल शेयर या सेव करने के लिए तैयार है।",
                "exportDone": "आपकी डेटा फ़ाइल डाउनलोड हो गई।",
                "deleteHint": "हटाने से आपका खाता और सारा डेटा मिट जाएगा। 30 दिन बाद इसे वापस नहीं लाया जा सकता।",
                "delete": "मेरा खाता और डेटा हटाएँ", "deleteTitle": "अपना खाता हटाएँ?",
                "deleteWarning": "आपकी प्रोफ़ाइल, बातचीत, पैसों की एंट्री, लक्ष्य और यादें हटा दी जाएँगी। आप लॉग आउट हो जाएँगे।",
                "typeDelete": "पक्का करने के लिए DELETE लिखें", "typeDeleteHint": "यह आखिरी कदम है।",
                "typeExactly": "DELETE बड़े अंग्रेज़ी अक्षरों में लिखें।", "deleteNow": "अभी हटाएँ",
                "deleted": "आपका खाता हटा दिया जाएगा।", "grievance": "सवाल या शिकायत",
                "grievanceHint": "हमारे शिकायत अधिकारी को लिखें:",
            },
            "memory": {
                "title": "यादें", "intro": "ये बातें मुझे याद हैं ताकि मैं आपकी बेहतर मदद कर सकूँ। जो चाहें हटा दें।",
                "empty": "साथी को अभी तक कुछ याद नहीं है।", "forgetAll": "सब भूल जाओ",
                "forgetAllTitle": "सब भुला दें?", "forgetAllWarning": "साथी आपके बारे में जो कुछ भी याद रखता है, सब भूल जाएगा।",
                "forgetOneTitle": "इसे भुला दें?", "forgotOne": "भुला दिया।", "forgotAll": "साथी ने सब भुला दिया।",
                "category": {"preference": "पसंद", "fact": "आपके बारे में", "goal_context": "लक्ष्य",
                             "concern": "चिंता", "behavior": "आदत"},
            },
        },
    },
    "mr": {
        "common": {"comingSoon": "पुढच्या अपडेटमध्ये येत आहे."},
        "settings": {
            "editProfile": "प्रोफाइल बदला", "confidence": "पैशांबाबत आत्मविश्वास", "notTaken": "दिलेले नाही",
            "retake": "5 प्रश्न पुन्हा देण्यासाठी टॅप करा", "about": "साथीबद्दल", "version": "आवृत्ती {{version}}",
            "logout": "लॉग आउट", "logoutConfirm": "या फोनवर साथीमधून लॉग आउट करायचे?", "saved": "जतन झाले",
            "notSaved": "जतन करता आले नाही. कृपया पुन्हा प्रयत्न करा.", "eligibilityAnswers": "योजनांसाठी तुमची उत्तरे",
            "confidenceLevel": {"low": "कमी", "medium": "मध्यम", "high": "चांगला"},
            "language": {"title": "भाषा", "header": "तुमची भाषा निवडा", "apply": "भाषा लागू करा",
                         "bubble": "साथी नेहमी तुमच्याशी तुमच्या भाषेत बोलेल."},
            "notifications": {
                "title": "सूचना", "push": "सूचना सुरू ठेवा", "pushHint": "सर्व आठवण संदेश बंद करण्यासाठी बंद करा.",
                "dailyInsight": "रोजचा पैशांचा सल्ला", "at": "वेळ", "incomeReminder": "उत्पन्न नोंदवण्याची आठवण",
                "weekly": "आठवड्यातून एकदा", "goalReminder": "ध्येयांची आठवण", "schemeDeadline": "योजनेची अंतिम तारीख",
                "leanMonth": "कठीण महिन्याची सूचना", "streak": "शिकण्याच्या साखळीची आठवण",
            },
            "privacy": {
                "title": "गोपनीयता आणि डेटा", "consents": "तुमच्या संमती", "requiredHint": "साथी वापरण्यासाठी आवश्यक",
                "yourData": "तुमचा डेटा", "exportHint": "साथीकडे तुमची जी काही माहिती आहे, त्याची एक फाइल मिळवा.",
                "export": "माझा डेटा डाउनलोड करा", "exportShared": "तुमची डेटा फाइल शेअर किंवा जतन करण्यासाठी तयार आहे.",
                "exportDone": "तुमची डेटा फाइल डाउनलोड झाली.",
                "deleteHint": "काढून टाकल्यास तुमचे खाते आणि सर्व डेटा पुसला जाईल. 30 दिवसांनंतर ते परत आणता येणार नाही.",
                "delete": "माझे खाते आणि डेटा काढून टाका", "deleteTitle": "तुमचे खाते काढून टाकायचे?",
                "deleteWarning": "तुमची प्रोफाइल, गप्पा, पैशांच्या नोंदी, ध्येये आणि आठवणी काढून टाकल्या जातील. तुम्ही लॉग आउट व्हाल.",
                "typeDelete": "निश्चित करण्यासाठी DELETE लिहा", "typeDeleteHint": "ही शेवटची पायरी आहे.",
                "typeExactly": "DELETE मोठ्या इंग्रजी अक्षरांत लिहा.", "deleteNow": "आत्ता काढून टाका",
                "deleted": "तुमचे खाते काढून टाकले जाईल.", "grievance": "प्रश्न किंवा तक्रार",
                "grievanceHint": "आमच्या तक्रार अधिकाऱ्याला लिहा:",
            },
            "memory": {
                "title": "आठवणी", "intro": "तुम्हाला चांगली मदत करता यावी म्हणून या गोष्टी माझ्या लक्षात आहेत. हवे ते काढून टाका.",
                "empty": "साथीच्या लक्षात अजून काहीही नाही.", "forgetAll": "सर्व विसरून जा",
                "forgetAllTitle": "सर्व विसरायचे?", "forgetAllWarning": "साथी तुमच्याबद्दल जे काही लक्षात ठेवतो ते सर्व विसरेल.",
                "forgetOneTitle": "हे विसरायचे?", "forgotOne": "विसरलो.", "forgotAll": "साथी सर्व विसरला.",
                "category": {"preference": "आवड", "fact": "तुमच्याबद्दल", "goal_context": "ध्येय",
                             "concern": "काळजी", "behavior": "सवय"},
            },
        },
    },
    "ta": {
        "common": {"comingSoon": "அடுத்த புதுப்பிப்பில் வருகிறது."},
        "settings": {
            "editProfile": "சுயவிவரத்தைத் திருத்து", "confidence": "நிதி நம்பிக்கை", "notTaken": "எடுக்கவில்லை",
            "retake": "5 கேள்விகளை மீண்டும் எடுக்கத் தட்டவும்", "about": "சாத்தி பற்றி", "version": "பதிப்பு {{version}}",
            "logout": "வெளியேறு", "logoutConfirm": "இந்த போனில் சாத்தியிலிருந்து வெளியேறவா?", "saved": "சேமிக்கப்பட்டது",
            "notSaved": "சேமிக்க முடியவில்லை. மீண்டும் முயற்சிக்கவும்.", "eligibilityAnswers": "திட்டங்களுக்கான உங்கள் பதில்கள்",
            "confidenceLevel": {"low": "குறைவு", "medium": "நடுத்தரம்", "high": "நன்று"},
            "language": {"title": "மொழி", "header": "உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்", "apply": "மொழியை பயன்படுத்து",
                         "bubble": "சாத்தி எப்போதும் உங்கள் மொழியில் பேசுவார்."},
            "notifications": {
                "title": "அறிவிப்புகள்", "push": "அறிவிப்புகளை அனுமதி", "pushHint": "எல்லா நினைவூட்டல்களையும் நிறுத்த அணைக்கவும்.",
                "dailyInsight": "தினசரி பண ஆலோசனை", "at": "நேரம்", "incomeReminder": "வருமானத்தைச் சேர்க்க நினைவூட்டல்",
                "weekly": "வாரம் ஒருமுறை", "goalReminder": "இலக்கு நினைவூட்டல்கள்", "schemeDeadline": "திட்டக் கடைசி தேதிகள்",
                "leanMonth": "நெருக்கடியான மாத எச்சரிக்கை", "streak": "கற்றல் தொடர் நினைவூட்டல்",
            },
            "privacy": {
                "title": "தனியுரிமை மற்றும் தரவு", "consents": "உங்கள் ஒப்புதல்கள்", "requiredHint": "சாத்தியைப் பயன்படுத்தத் தேவை",
                "yourData": "உங்கள் தரவு", "exportHint": "சாத்தியிடம் உள்ள உங்கள் தகவல்கள் அனைத்தின் நகலை ஒரு கோப்பாகப் பெறுங்கள்.",
                "export": "என் தரவைப் பதிவிறக்கு", "exportShared": "உங்கள் தரவுக் கோப்பு பகிரவோ சேமிக்கவோ தயார்.",
                "exportDone": "உங்கள் தரவுக் கோப்பு பதிவிறக்கப்பட்டது.",
                "deleteHint": "நீக்கினால் உங்கள் கணக்கும் எல்லாத் தரவும் அழிக்கப்படும். 30 நாட்களுக்குப் பிறகு மீட்க முடியாது.",
                "delete": "என் கணக்கையும் தரவையும் நீக்கு", "deleteTitle": "உங்கள் கணக்கை நீக்கவா?",
                "deleteWarning": "உங்கள் சுயவிவரம், உரையாடல்கள், பணப் பதிவுகள், இலக்குகள் மற்றும் நினைவுகள் நீக்கப்படும். நீங்கள் வெளியேற்றப்படுவீர்கள்.",
                "typeDelete": "உறுதிப்படுத்த DELETE என்று தட்டச்சு செய்யவும்", "typeDeleteHint": "இதுவே கடைசிப் படி.",
                "typeExactly": "DELETE என்பதை ஆங்கிலப் பெரிய எழுத்துகளில் தட்டச்சு செய்யவும்.", "deleteNow": "இப்போதே நீக்கு",
                "deleted": "உங்கள் கணக்கு நீக்கப்படும்.", "grievance": "கேள்விகள் அல்லது புகார்கள்",
                "grievanceHint": "எங்கள் குறைதீர்ப்பு அலுவலருக்கு எழுதுங்கள்:",
            },
            "memory": {
                "title": "நினைவுகள்", "intro": "உங்களுக்கு நன்றாக உதவ இவற்றை நினைவில் வைத்துள்ளேன். வேண்டியதை நீக்கலாம்.",
                "empty": "சாத்தி இன்னும் எதையும் நினைவில் வைக்கவில்லை.", "forgetAll": "அனைத்தையும் மறந்துவிடு",
                "forgetAllTitle": "அனைத்தையும் மறக்கவா?", "forgetAllWarning": "சாத்தி உங்களைப் பற்றி நினைவில் வைத்துள்ள அனைத்தையும் மறந்துவிடும்.",
                "forgetOneTitle": "இதை மறக்கவா?", "forgotOne": "மறந்துவிட்டது.", "forgotAll": "சாத்தி அனைத்தையும் மறந்துவிட்டது.",
                "category": {"preference": "விருப்பம்", "fact": "உங்களைப் பற்றி", "goal_context": "இலக்கு",
                             "concern": "கவலை", "behavior": "பழக்கம்"},
            },
        },
    },
}


def deep_merge(dst: dict, src: dict) -> None:
    for k, v in src.items():
        if isinstance(v, dict):
            deep_merge(dst.setdefault(k, {}), v)
        else:
            dst[k] = v


for lang, strings in T.items():
    path = DIR / f"{lang}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    deep_merge(data, strings)
    data["language"]["greeting"] = dict(GREETINGS)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("merged step-21 strings")
