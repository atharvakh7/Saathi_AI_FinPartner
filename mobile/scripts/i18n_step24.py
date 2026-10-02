"""Merge the step-24 Plan / Risk Report / Emergency Fund strings into src/i18n/*.json (idempotent)."""

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "src" / "i18n"

T = {
    "en": {
        "plan": {
            "title": "Income Planner", "subtitle": "Built for irregular incomes",
            "empty": "Tell me about your income and I'll plan your months with you.",
            "lean": "lean month", "income": "Income", "spending": "Spending", "likelyRange": "Likely income range",
            "snapshot": "Monthly snapshot", "leanHint": "Amber bars are lean months, well below your usual income.",
            "tightMonths": "Tight months ahead: {{months}}. Keep some money aside now.",
            "outlook": "Cash flow outlook", "outlookHint": "Next {{count}} months, based on your past entries",
            "recommended": "Recommended savings", "saveThisMonth": "Save {{amount}} this month",
            "pctOfIncome": "That's {{pct}}% of the income we plan with",
            "riskEmpty": "Add income and expenses to see this.", "seeReport": "See detailed report",
            "recalculated": "Plan updated", "budget": "Budget for {{month}}",
            "planningIncome": "Planned on an income of {{amount}}", "needs": "Needs", "wants": "Wants",
            "savings": "Savings", "over": "{{amount}} over the limit", "recalculate": "Recalculate",
            "pattern": {"steady": "Steady income", "ups_and_downs": "Income goes up and down", "seasonal": "Seasonal income"},
            "confidence": {"low": "Early estimate", "medium": "Fair estimate", "high": "Good estimate"},
            "mode": {"lean": "Tight month", "normal": "Normal month", "surplus": "Good month"},
            "ef": {
                "title": "Emergency Fund", "setUp": "Set it up", "setUpButton": "Set up emergency fund",
                "update": "Update target",
                "why": "An emergency fund protects you when income stops or a big expense comes up.",
                "covers": "Covers {{months}} months of essentials ({{amount}} a month).",
                "notSet": "Not set up yet. Choose how many months below.",
                "suggest": "Add about {{amount}} a month.", "eta": "Ready by {{date}}",
                "howMany": "How many months should it cover?", "months": "{{count}} months",
                "monthsHint": "3 months if your income is steady, 6 or more if it changes a lot.",
                "essential": "Your essential spending: {{amount}} a month", "target": "Target: {{amount}} ({{count}} months)",
                "needData": "Add some income and expenses first so I can size your fund.",
            },
        },
        "risk": {
            "report": "Risk Report", "empty": "Add income and expenses to see your score.",
            "summary": {
                "low": "Your money is in good shape. Keep it up!",
                "medium": "A few things need attention. Small changes will help.",
                "high": "Your money is under strain. Let's fix the biggest part first.",
            },
            "updated": "Updated {{date}}", "whatAdds": "What adds to your score",
            "whatAddsHint": "Lower is better. Each part adds points out of 5.", "points": "+{{points}}",
            "history": "Last 90 days", "historyA11y": "Score went from {{from}} to {{to}}",
        },
    },
    "hi": {
        "plan": {
            "title": "आमदनी योजना", "subtitle": "अनियमित कमाई के लिए बनी",
            "empty": "मुझे अपनी कमाई के बारे में बताइए, मैं आपके साथ महीनों की योजना बनाऊँगा।",
            "lean": "कम कमाई का महीना", "income": "कमाई", "spending": "खर्च", "likelyRange": "संभावित कमाई",
            "snapshot": "महीने की झलक", "leanHint": "पीले बार कम कमाई वाले महीने हैं।",
            "tightMonths": "आगे तंगी के महीने: {{months}}। अभी से कुछ पैसे अलग रखें।",
            "outlook": "आगे का नकद अनुमान", "outlookHint": "अगले {{count}} महीने, आपकी पिछली एंट्री के आधार पर",
            "recommended": "सुझाई गई बचत", "saveThisMonth": "इस महीने {{amount}} बचाएँ",
            "pctOfIncome": "यह योजना वाली कमाई का {{pct}}% है",
            "riskEmpty": "यह देखने के लिए कमाई और खर्च जोड़ें।", "seeReport": "पूरी रिपोर्ट देखें",
            "recalculated": "योजना अपडेट हो गई", "budget": "{{month}} का बजट",
            "planningIncome": "{{amount}} की कमाई पर योजना", "needs": "ज़रूरतें", "wants": "इच्छाएँ",
            "savings": "बचत", "over": "सीमा से {{amount}} ज़्यादा", "recalculate": "फिर से गणना करें",
            "pattern": {"steady": "स्थिर कमाई", "ups_and_downs": "कमाई ऊपर-नीचे होती है", "seasonal": "मौसमी कमाई"},
            "confidence": {"low": "शुरुआती अनुमान", "medium": "ठीक अनुमान", "high": "अच्छा अनुमान"},
            "mode": {"lean": "तंगी का महीना", "normal": "सामान्य महीना", "surplus": "अच्छा महीना"},
            "ef": {
                "title": "आपातकालीन फंड", "setUp": "शुरू करें", "setUpButton": "आपातकालीन फंड शुरू करें",
                "update": "लक्ष्य अपडेट करें",
                "why": "आपातकालीन फंड तब बचाता है जब कमाई रुक जाए या कोई बड़ा खर्च आ जाए।",
                "covers": "{{months}} महीने के ज़रूरी खर्च ({{amount}} महीना) के लिए।",
                "notSet": "अभी शुरू नहीं किया। नीचे महीने चुनें।",
                "suggest": "हर महीने लगभग {{amount}} जोड़ें।", "eta": "{{date}} तक तैयार",
                "howMany": "कितने महीनों का खर्च रखें?", "months": "{{count}} महीने",
                "monthsHint": "कमाई स्थिर हो तो 3 महीने, ज़्यादा बदलती हो तो 6 या ज़्यादा।",
                "essential": "आपका ज़रूरी खर्च: {{amount}} महीना", "target": "लक्ष्य: {{amount}} ({{count}} महीने)",
                "needData": "पहले कुछ कमाई और खर्च जोड़ें ताकि मैं फंड का आकार तय कर सकूँ।",
            },
        },
        "risk": {
            "report": "जोखिम रिपोर्ट", "empty": "अपना स्कोर देखने के लिए कमाई और खर्च जोड़ें।",
            "summary": {
                "low": "आपके पैसों की हालत अच्छी है। ऐसे ही रखें!",
                "medium": "कुछ बातों पर ध्यान देना है। छोटे बदलाव मदद करेंगे।",
                "high": "आपके पैसों पर दबाव है। पहले सबसे बड़ी समस्या ठीक करें।",
            },
            "updated": "{{date}} को अपडेट", "whatAdds": "आपका स्कोर किससे बढ़ता है",
            "whatAddsHint": "कम स्कोर बेहतर है। हर हिस्सा 5 में से अंक जोड़ता है।", "points": "+{{points}}",
            "history": "पिछले 90 दिन", "historyA11y": "स्कोर {{from}} से {{to}} हुआ",
        },
    },
    "mr": {
        "plan": {
            "title": "उत्पन्न नियोजन", "subtitle": "अनियमित उत्पन्नासाठी तयार केलेले",
            "empty": "मला तुमच्या उत्पन्नाबद्दल सांगा, मी तुमच्यासोबत महिन्यांचे नियोजन करेन.",
            "lean": "कमी उत्पन्नाचा महिना", "income": "उत्पन्न", "spending": "खर्च", "likelyRange": "संभाव्य उत्पन्न",
            "snapshot": "महिन्याची झलक", "leanHint": "पिवळे बार कमी उत्पन्नाचे महिने आहेत.",
            "tightMonths": "पुढे तंगीचे महिने: {{months}}. आत्ताच थोडे पैसे बाजूला ठेवा.",
            "outlook": "पुढील रोख अंदाज", "outlookHint": "पुढील {{count}} महिने, तुमच्या मागील नोंदींवर आधारित",
            "recommended": "सुचवलेली बचत", "saveThisMonth": "या महिन्यात {{amount}} बचत करा",
            "pctOfIncome": "हे नियोजनातील उत्पन्नाच्या {{pct}}% आहे",
            "riskEmpty": "हे पाहण्यासाठी उत्पन्न आणि खर्च जोडा.", "seeReport": "पूर्ण अहवाल पहा",
            "recalculated": "नियोजन अपडेट झाले", "budget": "{{month}} चे बजेट",
            "planningIncome": "{{amount}} उत्पन्नावर नियोजन", "needs": "गरजा", "wants": "इच्छा",
            "savings": "बचत", "over": "मर्यादेपेक्षा {{amount}} जास्त", "recalculate": "पुन्हा गणना करा",
            "pattern": {"steady": "स्थिर उत्पन्न", "ups_and_downs": "उत्पन्न कमी-जास्त होते", "seasonal": "हंगामी उत्पन्न"},
            "confidence": {"low": "सुरुवातीचा अंदाज", "medium": "बरा अंदाज", "high": "चांगला अंदाज"},
            "mode": {"lean": "तंगीचा महिना", "normal": "सामान्य महिना", "surplus": "चांगला महिना"},
            "ef": {
                "title": "आपत्कालीन निधी", "setUp": "सुरू करा", "setUpButton": "आपत्कालीन निधी सुरू करा",
                "update": "ध्येय अपडेट करा",
                "why": "उत्पन्न थांबले किंवा मोठा खर्च आला तर आपत्कालीन निधी तुमचे रक्षण करतो.",
                "covers": "{{months}} महिन्यांच्या आवश्यक खर्चासाठी (महिन्याला {{amount}}).",
                "notSet": "अजून सुरू केलेले नाही. खाली महिने निवडा.",
                "suggest": "दर महिन्याला सुमारे {{amount}} जोडा.", "eta": "{{date}} पर्यंत तयार",
                "howMany": "किती महिन्यांचा खर्च ठेवायचा?", "months": "{{count}} महिने",
                "monthsHint": "उत्पन्न स्थिर असल्यास 3 महिने, खूप बदलत असल्यास 6 किंवा जास्त.",
                "essential": "तुमचा आवश्यक खर्च: महिन्याला {{amount}}", "target": "ध्येय: {{amount}} ({{count}} महिने)",
                "needData": "आधी थोडे उत्पन्न आणि खर्च जोडा म्हणजे मी निधीचा आकार ठरवू शकेन.",
            },
        },
        "risk": {
            "report": "जोखीम अहवाल", "empty": "तुमचा स्कोअर पाहण्यासाठी उत्पन्न आणि खर्च जोडा.",
            "summary": {
                "low": "तुमची आर्थिक स्थिती चांगली आहे. अशीच ठेवा!",
                "medium": "काही गोष्टींकडे लक्ष द्यायला हवे. छोटे बदल मदत करतील.",
                "high": "तुमच्या पैशांवर ताण आहे. आधी सर्वात मोठी अडचण दूर करूया.",
            },
            "updated": "{{date}} रोजी अपडेट", "whatAdds": "तुमचा स्कोअर कशामुळे वाढतो",
            "whatAddsHint": "कमी स्कोअर चांगला. प्रत्येक भाग 5 पैकी गुण जोडतो.", "points": "+{{points}}",
            "history": "मागील 90 दिवस", "historyA11y": "स्कोअर {{from}} वरून {{to}} झाला",
        },
    },
    "ta": {
        "plan": {
            "title": "வருமானத் திட்டம்", "subtitle": "ஒழுங்கற்ற வருமானத்திற்காக",
            "empty": "உங்கள் வருமானத்தைச் சொல்லுங்கள், உங்களுடன் மாதங்களைத் திட்டமிடுகிறேன்.",
            "lean": "குறைந்த வருமான மாதம்", "income": "வருமானம்", "spending": "செலவு", "likelyRange": "எதிர்பார்க்கும் வருமான வரம்பு",
            "snapshot": "மாதச் சுருக்கம்", "leanHint": "மஞ்சள் பட்டைகள் குறைந்த வருமான மாதங்கள்.",
            "tightMonths": "வரவிருக்கும் நெருக்கடி மாதங்கள்: {{months}}. இப்போதே கொஞ்சம் பணம் ஒதுக்குங்கள்.",
            "outlook": "பணப் புழக்க முன்னோட்டம்", "outlookHint": "அடுத்த {{count}} மாதங்கள், உங்கள் முந்தைய பதிவுகளின் அடிப்படையில்",
            "recommended": "பரிந்துரைக்கப்பட்ட சேமிப்பு", "saveThisMonth": "இந்த மாதம் {{amount}} சேமியுங்கள்",
            "pctOfIncome": "இது திட்ட வருமானத்தின் {{pct}}%",
            "riskEmpty": "இதைப் பார்க்க வருமானம், செலவுகளைச் சேர்க்கவும்.", "seeReport": "முழு அறிக்கையைப் பார்",
            "recalculated": "திட்டம் புதுப்பிக்கப்பட்டது", "budget": "{{month}} பட்ஜெட்",
            "planningIncome": "{{amount}} வருமானத்தில் திட்டமிடப்பட்டது", "needs": "தேவைகள்", "wants": "விருப்பங்கள்",
            "savings": "சேமிப்பு", "over": "வரம்பை விட {{amount}} அதிகம்", "recalculate": "மீண்டும் கணக்கிடு",
            "pattern": {"steady": "நிலையான வருமானம்", "ups_and_downs": "ஏறி இறங்கும் வருமானம்", "seasonal": "பருவகால வருமானம்"},
            "confidence": {"low": "ஆரம்ப மதிப்பீடு", "medium": "ஓரளவு மதிப்பீடு", "high": "நல்ல மதிப்பீடு"},
            "mode": {"lean": "நெருக்கடி மாதம்", "normal": "சாதாரண மாதம்", "surplus": "நல்ல மாதம்"},
            "ef": {
                "title": "அவசர நிதி", "setUp": "அமைக்கவும்", "setUpButton": "அவசர நிதியை அமை",
                "update": "இலக்கைப் புதுப்பி",
                "why": "வருமானம் நின்றாலோ பெரிய செலவு வந்தாலோ அவசர நிதி உங்களைக் காக்கும்.",
                "covers": "{{months}} மாத அத்தியாவசியச் செலவுகளுக்கு (மாதம் {{amount}}).",
                "notSet": "இன்னும் அமைக்கவில்லை. கீழே மாதங்களைத் தேர்வு செய்யவும்.",
                "suggest": "மாதம் சுமார் {{amount}} சேர்க்கவும்.", "eta": "{{date}}-க்குள் தயார்",
                "howMany": "எத்தனை மாதங்களுக்கு?", "months": "{{count}} மாதங்கள்",
                "monthsHint": "வருமானம் நிலையானால் 3 மாதங்கள், அதிகம் மாறினால் 6 அல்லது அதற்கு மேல்.",
                "essential": "உங்கள் அத்தியாவசியச் செலவு: மாதம் {{amount}}", "target": "இலக்கு: {{amount}} ({{count}} மாதங்கள்)",
                "needData": "நிதியின் அளவைத் தீர்மானிக்க முதலில் வருமானம், செலவுகளைச் சேர்க்கவும்.",
            },
        },
        "risk": {
            "report": "அபாய அறிக்கை", "empty": "உங்கள் மதிப்பெண்ணைப் பார்க்க வருமானம், செலவுகளைச் சேர்க்கவும்.",
            "summary": {
                "low": "உங்கள் பண நிலை நன்றாக உள்ளது. தொடருங்கள்!",
                "medium": "சில விஷயங்களைக் கவனிக்க வேண்டும். சிறிய மாற்றங்கள் உதவும்.",
                "high": "உங்கள் பணத்தில் அழுத்தம் உள்ளது. முதலில் பெரிய பகுதியைச் சரிசெய்வோம்.",
            },
            "updated": "{{date}} அன்று புதுப்பிக்கப்பட்டது", "whatAdds": "உங்கள் மதிப்பெண்ணை எது உயர்த்துகிறது",
            "whatAddsHint": "குறைவாக இருப்பதே நல்லது. ஒவ்வொரு பகுதியும் 5-க்கு புள்ளிகள் சேர்க்கிறது.", "points": "+{{points}}",
            "history": "கடந்த 90 நாட்கள்", "historyA11y": "மதிப்பெண் {{from}}-இலிருந்து {{to}} ஆனது",
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
