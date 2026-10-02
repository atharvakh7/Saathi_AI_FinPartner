"""Merge the step-23 Goals strings and the wireframe UI pass strings into src/i18n/*.json (idempotent)."""

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "src" / "i18n"

T = {
    "en": {
        "onboarding": {"intro": {"slide0": {"title": "Finance made simple.", "body": "Understand money without confusing jargon."}}},
        "home": {
            "viewAll": "View All", "topGoals": "Top Goals", "setGoal": "Set your first goal",
            "setGoalHint": "Saving is easier with a target.", "goodGoing": "Good going!",
        },
        "goals": {
            "title": "Your Goals", "subtitle": "Small steps. Big future.", "new": "New goal", "create": "Create goal",
            "editTitle": "Edit goal", "tab": {"active": "Active", "completed": "Completed"},
            "totalSaved": "Saved across your goals", "pctComplete": "{{pct}}% complete",
            "empty": "No goals yet. What are you saving for?", "emptyCompleted": "Goals you finish will show here.",
            "byDate": "By {{date}}", "onTrack": "On track", "behind": "Needs more",
            "status": {"paused": "Paused", "completed": "Completed"},
            "saved": "Saved", "target": "Target", "left": "Still needed",
            "proj": {
                "done": "Goal reached. Well done!",
                "paused": "This goal is paused. Resume it when you're ready.",
                "onTrack": "You're on track to reach this by {{date}}.",
                "behind": "Save about {{amount}} a month to reach this by {{date}}.",
                "atPace": "At {{rate}} a month, you'll reach this by {{date}}.",
                "start": "Add money regularly and I'll show when you'll reach this goal.",
            },
            "reached": "You reached your goal!", "withdrawn": "Money taken out", "added": "Money added",
            "completedBubble": "You did it! Raise the target if you want to keep saving.",
            "addMoney": "Add money", "withdraw": "Withdraw", "history": "History",
            "noHistory": "No money added yet.", "pause": "Pause goal", "resume": "Resume goal", "delete": "Delete goal",
            "withdrawHint": "You have {{amount}} saved in this goal.",
            "tooMuch": "You can't take out more than you have saved.",
            "deleteTitle": "Delete this goal?", "deleteMessage": "The goal and its history will be removed.",
            "efNoDelete": "Your emergency fund goal can't be deleted. You can pause it instead.",
            "form": {
                "whatFor": "What are you saving for?", "name": "Goal name", "namePlaceholder": "e.g. New bike",
                "hasDate": "Set a target date", "alreadySaved": "Already saved",
                "pickCategory": "Choose what you're saving for.", "dateFuture": "Choose a date after today.",
            },
        },
    },
    "hi": {
        "onboarding": {"intro": {"slide0": {"title": "पैसा, आसान भाषा में।", "body": "बिना उलझे शब्दों के पैसों को समझें।"}}},
        "home": {
            "viewAll": "सब देखें", "topGoals": "मुख्य लक्ष्य", "setGoal": "अपना पहला लक्ष्य बनाएँ",
            "setGoalHint": "लक्ष्य हो तो बचत आसान होती है।", "goodGoing": "बहुत बढ़िया!",
        },
        "goals": {
            "title": "आपके लक्ष्य", "subtitle": "छोटे कदम, बड़ा भविष्य।", "new": "नया लक्ष्य", "create": "लक्ष्य बनाएँ",
            "editTitle": "लक्ष्य बदलें", "tab": {"active": "चालू", "completed": "पूरे हुए"},
            "totalSaved": "सभी लक्ष्यों में बचत", "pctComplete": "{{pct}}% पूरा",
            "empty": "अभी कोई लक्ष्य नहीं। आप किसके लिए बचत कर रहे हैं?", "emptyCompleted": "पूरे हुए लक्ष्य यहाँ दिखेंगे।",
            "byDate": "{{date}} तक", "onTrack": "सही राह पर", "behind": "और बचत चाहिए",
            "status": {"paused": "रुका हुआ", "completed": "पूरा हुआ"},
            "saved": "बचत", "target": "लक्ष्य", "left": "अभी चाहिए",
            "proj": {
                "done": "लक्ष्य पूरा हुआ। शाबाश!",
                "paused": "यह लक्ष्य रुका हुआ है। तैयार हों तो फिर शुरू करें।",
                "onTrack": "आप {{date}} तक यह लक्ष्य पूरा करने की राह पर हैं।",
                "behind": "{{date}} तक पहुँचने के लिए हर महीने लगभग {{amount}} बचाएँ।",
                "atPace": "हर महीने {{rate}} बचाने पर आप {{date}} तक पहुँच जाएँगे।",
                "start": "नियमित रूप से पैसे जोड़ें, मैं बताऊँगा कि लक्ष्य कब पूरा होगा।",
            },
            "reached": "आपने अपना लक्ष्य पूरा कर लिया!", "withdrawn": "पैसे निकाले गए", "added": "पैसे जोड़े गए",
            "completedBubble": "आपने कर दिखाया! और बचत करनी हो तो लक्ष्य बढ़ाएँ।",
            "addMoney": "पैसे जोड़ें", "withdraw": "पैसे निकालें", "history": "इतिहास",
            "noHistory": "अभी तक कोई पैसा नहीं जोड़ा गया।", "pause": "लक्ष्य रोकें", "resume": "लक्ष्य फिर शुरू करें", "delete": "लक्ष्य हटाएँ",
            "withdrawHint": "इस लक्ष्य में आपकी {{amount}} की बचत है।",
            "tooMuch": "आप बचत से ज़्यादा पैसे नहीं निकाल सकते।",
            "deleteTitle": "यह लक्ष्य हटाएँ?", "deleteMessage": "लक्ष्य और उसका इतिहास हटा दिया जाएगा।",
            "efNoDelete": "आपातकालीन फंड का लक्ष्य हटाया नहीं जा सकता। आप इसे रोक सकते हैं।",
            "form": {
                "whatFor": "आप किसके लिए बचत कर रहे हैं?", "name": "लक्ष्य का नाम", "namePlaceholder": "जैसे नई बाइक",
                "hasDate": "पूरा करने की तारीख तय करें", "alreadySaved": "पहले से बचत",
                "pickCategory": "चुनें कि आप किसके लिए बचत कर रहे हैं।", "dateFuture": "आज के बाद की तारीख चुनें।",
            },
        },
    },
    "mr": {
        "onboarding": {"intro": {"slide0": {"title": "पैसा, सोप्या भाषेत.", "body": "गोंधळात टाकणाऱ्या शब्दांशिवाय पैसा समजून घ्या."}}},
        "home": {
            "viewAll": "सर्व पहा", "topGoals": "मुख्य ध्येये", "setGoal": "तुमचे पहिले ध्येय ठरवा",
            "setGoalHint": "ध्येय असले की बचत सोपी होते.", "goodGoing": "छान चालले आहे!",
        },
        "goals": {
            "title": "तुमची ध्येये", "subtitle": "छोटी पावले, मोठे भविष्य.", "new": "नवीन ध्येय", "create": "ध्येय तयार करा",
            "editTitle": "ध्येय बदला", "tab": {"active": "चालू", "completed": "पूर्ण"},
            "totalSaved": "सर्व ध्येयांमधील बचत", "pctComplete": "{{pct}}% पूर्ण",
            "empty": "अजून कोणतेही ध्येय नाही. तुम्ही कशासाठी बचत करत आहात?", "emptyCompleted": "पूर्ण झालेली ध्येये येथे दिसतील.",
            "byDate": "{{date}} पर्यंत", "onTrack": "योग्य मार्गावर", "behind": "अजून बचत हवी",
            "status": {"paused": "थांबवलेले", "completed": "पूर्ण"},
            "saved": "बचत", "target": "ध्येय", "left": "अजून हवे",
            "proj": {
                "done": "ध्येय पूर्ण झाले. छान!",
                "paused": "हे ध्येय थांबवले आहे. तयार असाल तेव्हा पुन्हा सुरू करा.",
                "onTrack": "तुम्ही {{date}} पर्यंत हे ध्येय गाठण्याच्या मार्गावर आहात.",
                "behind": "{{date}} पर्यंत पोहोचण्यासाठी दर महिन्याला सुमारे {{amount}} बचत करा.",
                "atPace": "दर महिन्याला {{rate}} बचत केल्यास तुम्ही {{date}} पर्यंत पोहोचाल.",
                "start": "नियमितपणे पैसे जोडा, ध्येय कधी पूर्ण होईल ते मी सांगेन.",
            },
            "reached": "तुम्ही तुमचे ध्येय गाठले!", "withdrawn": "पैसे काढले", "added": "पैसे जोडले",
            "completedBubble": "तुम्ही करून दाखवले! अजून बचत करायची असल्यास ध्येय वाढवा.",
            "addMoney": "पैसे जोडा", "withdraw": "पैसे काढा", "history": "इतिहास",
            "noHistory": "अजून कोणतेही पैसे जोडलेले नाहीत.", "pause": "ध्येय थांबवा", "resume": "ध्येय पुन्हा सुरू करा", "delete": "ध्येय काढा",
            "withdrawHint": "या ध्येयात तुमची {{amount}} बचत आहे.",
            "tooMuch": "बचतीपेक्षा जास्त पैसे काढता येणार नाहीत.",
            "deleteTitle": "हे ध्येय काढायचे?", "deleteMessage": "ध्येय आणि त्याचा इतिहास काढला जाईल.",
            "efNoDelete": "आपत्कालीन निधीचे ध्येय काढता येत नाही. तुम्ही ते थांबवू शकता.",
            "form": {
                "whatFor": "तुम्ही कशासाठी बचत करत आहात?", "name": "ध्येयाचे नाव", "namePlaceholder": "उदा. नवीन बाईक",
                "hasDate": "पूर्ण करण्याची तारीख ठरवा", "alreadySaved": "आधीची बचत",
                "pickCategory": "तुम्ही कशासाठी बचत करत आहात ते निवडा.", "dateFuture": "आजनंतरची तारीख निवडा.",
            },
        },
    },
    "ta": {
        "onboarding": {"intro": {"slide0": {"title": "பணம், எளிமையாக.", "body": "குழப்பமான சொற்கள் இல்லாமல் பணத்தைப் புரிந்துகொள்ளுங்கள்."}}},
        "home": {
            "viewAll": "அனைத்தும்", "topGoals": "முக்கிய இலக்குகள்", "setGoal": "உங்கள் முதல் இலக்கை அமையுங்கள்",
            "setGoalHint": "இலக்கு இருந்தால் சேமிப்பது எளிது.", "goodGoing": "நன்றாகப் போகிறது!",
        },
        "goals": {
            "title": "உங்கள் இலக்குகள்", "subtitle": "சிறிய அடிகள், பெரிய எதிர்காலம்.", "new": "புதிய இலக்கு", "create": "இலக்கை உருவாக்கு",
            "editTitle": "இலக்கைத் திருத்து", "tab": {"active": "நடப்பு", "completed": "முடிந்தவை"},
            "totalSaved": "அனைத்து இலக்குகளிலும் சேமிப்பு", "pctComplete": "{{pct}}% முடிந்தது",
            "empty": "இன்னும் இலக்குகள் இல்லை. எதற்காகச் சேமிக்கிறீர்கள்?", "emptyCompleted": "முடித்த இலக்குகள் இங்கே தெரியும்.",
            "byDate": "{{date}}-க்குள்", "onTrack": "சரியான பாதையில்", "behind": "இன்னும் தேவை",
            "status": {"paused": "நிறுத்தப்பட்டது", "completed": "முடிந்தது"},
            "saved": "சேமிப்பு", "target": "இலக்கு", "left": "இன்னும் தேவை",
            "proj": {
                "done": "இலக்கை அடைந்துவிட்டீர்கள். அருமை!",
                "paused": "இந்த இலக்கு நிறுத்தப்பட்டுள்ளது. தயாரானதும் மீண்டும் தொடங்குங்கள்.",
                "onTrack": "{{date}}-க்குள் இதை அடையும் பாதையில் இருக்கிறீர்கள்.",
                "behind": "{{date}}-க்குள் அடைய மாதம் சுமார் {{amount}} சேமியுங்கள்.",
                "atPace": "மாதம் {{rate}} சேமித்தால் {{date}}-க்குள் அடைவீர்கள்.",
                "start": "தொடர்ந்து பணம் சேருங்கள், இலக்கை எப்போது அடைவீர்கள் என்று காட்டுகிறேன்.",
            },
            "reached": "உங்கள் இலக்கை அடைந்தீர்கள்!", "withdrawn": "பணம் எடுக்கப்பட்டது", "added": "பணம் சேர்க்கப்பட்டது",
            "completedBubble": "நீங்கள் சாதித்தீர்கள்! தொடர்ந்து சேமிக்க இலக்கை உயர்த்துங்கள்.",
            "addMoney": "பணம் சேர்", "withdraw": "பணம் எடு", "history": "வரலாறு",
            "noHistory": "இன்னும் பணம் சேர்க்கப்படவில்லை.", "pause": "இலக்கை நிறுத்து", "resume": "இலக்கைத் தொடர்", "delete": "இலக்கை நீக்கு",
            "withdrawHint": "இந்த இலக்கில் {{amount}} சேமித்துள்ளீர்கள்.",
            "tooMuch": "சேமித்ததை விட அதிகமாக எடுக்க முடியாது.",
            "deleteTitle": "இந்த இலக்கை நீக்கவா?", "deleteMessage": "இலக்கும் அதன் வரலாறும் நீக்கப்படும்.",
            "efNoDelete": "அவசர நிதி இலக்கை நீக்க முடியாது. அதை நிறுத்தி வைக்கலாம்.",
            "form": {
                "whatFor": "எதற்காகச் சேமிக்கிறீர்கள்?", "name": "இலக்கின் பெயர்", "namePlaceholder": "எ.கா. புதிய பைக்",
                "hasDate": "இலக்குத் தேதியை அமை", "alreadySaved": "ஏற்கனவே சேமித்தது",
                "pickCategory": "எதற்காகச் சேமிக்கிறீர்கள் என்று தேர்வு செய்யவும்.", "dateFuture": "இன்றைக்குப் பிறகு ஒரு தேதியைத் தேர்வு செய்யவும்.",
            },
        },
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
