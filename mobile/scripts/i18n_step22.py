"""Merge the step-22 Home / transactions / debts strings into src/i18n/*.json (idempotent)."""

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "src" / "i18n"

T = {
    "en": {
        "form": {"choose": "Choose"},
        "date": {"weekdays": "S,M,T,W,T,F,S", "other": "Other date", "prevMonth": "Previous month", "nextMonth": "Next month"},
        "home": {
            "hello": "Namaste, {{name}} 👋", "helloNoName": "Namaste 👋",
            "morning": "Good morning! Let's make smart money choices today.",
            "afternoon": "Good afternoon! How is your money doing today?",
            "evening": "Good evening! Let's look at your day's money.",
            "empty": "Tell me about your income and spending, and I'll show you where your money goes.",
            "addIncome": "Add income", "addExpense": "Add expense", "quickSummary": "Quick summary",
            "income": "Income", "expenses": "Expenses", "savings": "Savings", "thisMonth": "This month",
            "debt": "Debt", "debtActive": "Active debts: {{count}}", "noDebt": "No debts",
            "goals": "Goals", "goalsActive": "Active goals: {{count}}",
        },
        "finance": {
            "filter": {"all": "All", "income": "Income", "expense": "Expense"},
            "transactions": {"title": "Transactions", "add": "Add entry", "empty": "No entries for this month yet."},
            "form": {
                "addTitle": "Add entry", "editTitle": "Edit entry", "amount": "Amount", "category": "Category",
                "date": "Date", "note": "Note", "notePlaceholder": "e.g. vegetables from the market",
                "saved": "Saved", "deleted": "Deleted", "deleteTitle": "Delete this entry?",
                "deleteMessage": "This can't be undone.", "amountRequired": "Enter an amount more than ₹0.",
                "amountTooLarge": "That amount is too large.", "categoryRequired": "Choose a category.",
                "noFuture": "The date can't be in the future.",
            },
            "parse": {
                "title": "Tell me in words", "placeholder": "e.g. spent 250 on vegetables today",
                "fill": "Fill it for me", "check": "I filled the form. Please check it and save.",
                "notUnderstood": "I couldn't understand that. Please include the amount, like \"spent 250 on food\".",
            },
            "debt": {
                "title": "Debts", "add": "Add debt", "addTitle": "Add debt", "editTitle": "Edit debt",
                "empty": "No debts added. If you owe money to anyone, add it here so I can help you plan.",
                "total": "Total still to pay", "allPaid": "All your debts are paid off. Well done!",
                "paidOffSection": "Paid off", "paidOff": "Paid off", "left": "left to pay",
                "ratePerYear": "{{rate}}% a year", "perMonth": "{{amount}} a month", "dueOn": "Due on day {{day}}",
                "lender": "Who did you borrow from?", "lenderPlaceholder": "e.g. SBI, Ramesh bhai",
                "lenderLength": "Please enter 2 to 80 letters.", "type": "Type of loan", "amountLeft": "Amount still to pay",
                "rate": "Interest", "rateHint": "Per year", "rateRange": "Enter a rate from 0 to 120.",
                "dueDay": "Due day of month", "noDueDay": "Not fixed", "monthly": "Monthly payment",
                "markPaid": "Mark as paid off", "markedPaid": "Marked as paid off", "reopen": "Still paying this",
                "deleteTitle": "Delete this debt?",
            },
        },
        "debttype": {
            "bank_loan": "Bank loan", "kisan_credit_card": "Kisan Credit Card", "credit_card": "Credit card",
            "microfinance": "Microfinance / SHG", "moneylender": "Moneylender", "family_friend": "Family or friend",
            "other": "Other",
        },
    },
    "hi": {
        "form": {"choose": "चुनें"},
        "date": {"weekdays": "र,सो,मं,बु,गु,शु,श", "other": "दूसरी तारीख", "prevMonth": "पिछला महीना", "nextMonth": "अगला महीना"},
        "home": {
            "hello": "नमस्ते, {{name}} 👋", "helloNoName": "नमस्ते 👋",
            "morning": "सुप्रभात! आइए आज पैसों के समझदार फ़ैसले लें।",
            "afternoon": "नमस्कार! आज आपके पैसों का क्या हाल है?",
            "evening": "शुभ संध्या! आइए आज के पैसों पर नज़र डालें।",
            "empty": "मुझे अपनी कमाई और खर्च के बारे में बताइए, मैं दिखाऊँगा कि आपका पैसा कहाँ जाता है।",
            "addIncome": "कमाई जोड़ें", "addExpense": "खर्च जोड़ें", "quickSummary": "एक नज़र में",
            "income": "कमाई", "expenses": "खर्च", "savings": "बचत", "thisMonth": "इस महीने",
            "debt": "कर्ज़", "debtActive": "चालू कर्ज़: {{count}}", "noDebt": "कोई कर्ज़ नहीं",
            "goals": "लक्ष्य", "goalsActive": "चालू लक्ष्य: {{count}}",
        },
        "finance": {
            "filter": {"all": "सभी", "income": "कमाई", "expense": "खर्च"},
            "transactions": {"title": "लेन-देन", "add": "एंट्री जोड़ें", "empty": "इस महीने की कोई एंट्री नहीं है।"},
            "form": {
                "addTitle": "एंट्री जोड़ें", "editTitle": "एंट्री बदलें", "amount": "रकम", "category": "श्रेणी",
                "date": "तारीख", "note": "नोट", "notePlaceholder": "जैसे बाज़ार से सब्ज़ी",
                "saved": "सेव हो गया", "deleted": "हटा दिया गया", "deleteTitle": "यह एंट्री हटाएँ?",
                "deleteMessage": "इसे वापस नहीं लाया जा सकता।", "amountRequired": "₹0 से ज़्यादा रकम डालें।",
                "amountTooLarge": "यह रकम बहुत बड़ी है।", "categoryRequired": "एक श्रेणी चुनें।",
                "noFuture": "आगे की तारीख नहीं चुन सकते।",
            },
            "parse": {
                "title": "मुझे शब्दों में बताइए", "placeholder": "जैसे आज सब्ज़ी पर 250 खर्च किए",
                "fill": "मेरे लिए भर दो", "check": "मैंने फ़ॉर्म भर दिया है। कृपया जाँचकर सेव करें।",
                "notUnderstood": "मैं समझ नहीं पाया। कृपया रकम लिखें, जैसे \"खाने पर 250 खर्च किए\"।",
            },
            "debt": {
                "title": "कर्ज़", "add": "कर्ज़ जोड़ें", "addTitle": "कर्ज़ जोड़ें", "editTitle": "कर्ज़ बदलें",
                "empty": "कोई कर्ज़ नहीं जोड़ा गया। अगर आपने किसी से पैसे लिए हैं, तो यहाँ जोड़ें ताकि मैं योजना बनाने में मदद कर सकूँ।",
                "total": "कुल बाकी रकम", "allPaid": "आपके सारे कर्ज़ चुक गए हैं। शाबाश!",
                "paidOffSection": "चुकाए गए", "paidOff": "चुकाया गया", "left": "चुकाना बाकी",
                "ratePerYear": "{{rate}}% सालाना", "perMonth": "{{amount}} महीना", "dueOn": "हर महीने {{day}} तारीख",
                "lender": "किससे उधार लिया?", "lenderPlaceholder": "जैसे SBI, रमेश भाई",
                "lenderLength": "कृपया 2 से 80 अक्षर लिखें।", "type": "कर्ज़ का प्रकार", "amountLeft": "बाकी रकम",
                "rate": "ब्याज", "rateHint": "सालाना", "rateRange": "0 से 120 के बीच दर डालें।",
                "dueDay": "किस्त की तारीख", "noDueDay": "तय नहीं", "monthly": "महीने की किस्त",
                "markPaid": "पूरा चुका दिया", "markedPaid": "चुकाया गया मान लिया", "reopen": "अभी चुका रहे हैं",
                "deleteTitle": "यह कर्ज़ हटाएँ?",
            },
        },
        "debttype": {
            "bank_loan": "बैंक लोन", "kisan_credit_card": "किसान क्रेडिट कार्ड", "credit_card": "क्रेडिट कार्ड",
            "microfinance": "माइक्रोफ़ाइनेंस / स्वयं सहायता समूह", "moneylender": "साहूकार", "family_friend": "परिवार या दोस्त",
            "other": "अन्य",
        },
    },
    "mr": {
        "form": {"choose": "निवडा"},
        "date": {"weekdays": "र,सो,मं,बु,गु,शु,श", "other": "दुसरी तारीख", "prevMonth": "मागील महिना", "nextMonth": "पुढील महिना"},
        "home": {
            "hello": "नमस्कार, {{name}} 👋", "helloNoName": "नमस्कार 👋",
            "morning": "सुप्रभात! चला, आज पैशांचे शहाणे निर्णय घेऊया.",
            "afternoon": "नमस्कार! आज तुमच्या पैशांचे काय चालले आहे?",
            "evening": "शुभ संध्याकाळ! चला, आजच्या पैशांवर एक नजर टाकूया.",
            "empty": "मला तुमचे उत्पन्न आणि खर्च सांगा, मी दाखवेन की तुमचे पैसे कुठे जातात.",
            "addIncome": "उत्पन्न जोडा", "addExpense": "खर्च जोडा", "quickSummary": "एका नजरेत",
            "income": "उत्पन्न", "expenses": "खर्च", "savings": "बचत", "thisMonth": "या महिन्यात",
            "debt": "कर्ज", "debtActive": "चालू कर्जे: {{count}}", "noDebt": "कर्ज नाही",
            "goals": "ध्येये", "goalsActive": "चालू ध्येये: {{count}}",
        },
        "finance": {
            "filter": {"all": "सर्व", "income": "उत्पन्न", "expense": "खर्च"},
            "transactions": {"title": "व्यवहार", "add": "नोंद जोडा", "empty": "या महिन्यात अजून कोणतीही नोंद नाही."},
            "form": {
                "addTitle": "नोंद जोडा", "editTitle": "नोंद बदला", "amount": "रक्कम", "category": "प्रकार",
                "date": "तारीख", "note": "टीप", "notePlaceholder": "उदा. बाजारातून भाजी",
                "saved": "जतन झाले", "deleted": "काढून टाकले", "deleteTitle": "ही नोंद काढायची?",
                "deleteMessage": "हे परत आणता येणार नाही.", "amountRequired": "₹0 पेक्षा जास्त रक्कम टाका.",
                "amountTooLarge": "ही रक्कम खूप मोठी आहे.", "categoryRequired": "एक प्रकार निवडा.",
                "noFuture": "पुढची तारीख निवडता येणार नाही.",
            },
            "parse": {
                "title": "मला शब्दांत सांगा", "placeholder": "उदा. आज भाजीवर 250 खर्च केले",
                "fill": "माझ्यासाठी भरा", "check": "मी फॉर्म भरला आहे. कृपया तपासून जतन करा.",
                "notUnderstood": "मला समजले नाही. कृपया रक्कम लिहा, उदा. \"जेवणावर 250 खर्च केले\".",
            },
            "debt": {
                "title": "कर्ज", "add": "कर्ज जोडा", "addTitle": "कर्ज जोडा", "editTitle": "कर्ज बदला",
                "empty": "कोणतेही कर्ज जोडलेले नाही. तुम्ही कोणाकडून पैसे घेतले असतील, तर ते येथे जोडा म्हणजे मी नियोजनात मदत करू शकेन.",
                "total": "एकूण बाकी रक्कम", "allPaid": "तुमची सर्व कर्जे फिटली आहेत. छान!",
                "paidOffSection": "फेडलेली", "paidOff": "फेडले", "left": "फेडणे बाकी",
                "ratePerYear": "वार्षिक {{rate}}%", "perMonth": "महिन्याला {{amount}}", "dueOn": "दर महिन्याच्या {{day}} तारखेला",
                "lender": "कोणाकडून कर्ज घेतले?", "lenderPlaceholder": "उदा. SBI, रमेश भाऊ",
                "lenderLength": "कृपया 2 ते 80 अक्षरे लिहा.", "type": "कर्जाचा प्रकार", "amountLeft": "बाकी रक्कम",
                "rate": "व्याज", "rateHint": "वार्षिक", "rateRange": "0 ते 120 दरम्यान दर टाका.",
                "dueDay": "हप्त्याची तारीख", "noDueDay": "ठरलेली नाही", "monthly": "मासिक हप्ता",
                "markPaid": "पूर्ण फेडले", "markedPaid": "फेडले म्हणून नोंदवले", "reopen": "अजून फेडत आहे",
                "deleteTitle": "हे कर्ज काढायचे?",
            },
        },
        "debttype": {
            "bank_loan": "बँक कर्ज", "kisan_credit_card": "किसान क्रेडिट कार्ड", "credit_card": "क्रेडिट कार्ड",
            "microfinance": "मायक्रोफायनान्स / बचत गट", "moneylender": "सावकार", "family_friend": "कुटुंब किंवा मित्र",
            "other": "इतर",
        },
    },
    "ta": {
        "form": {"choose": "தேர்வு செய்யவும்"},
        "date": {"weekdays": "ஞா,தி,செ,பு,வி,வெ,ச", "other": "வேறு தேதி", "prevMonth": "முந்தைய மாதம்", "nextMonth": "அடுத்த மாதம்"},
        "home": {
            "hello": "வணக்கம், {{name}} 👋", "helloNoName": "வணக்கம் 👋",
            "morning": "காலை வணக்கம்! இன்று பணத்தைப் பற்றி புத்திசாலித்தனமான முடிவுகள் எடுப்போம்.",
            "afternoon": "மதிய வணக்கம்! இன்று உங்கள் பணம் எப்படி இருக்கிறது?",
            "evening": "மாலை வணக்கம்! இன்றைய பணத்தைப் பார்ப்போம்.",
            "empty": "உங்கள் வருமானம் மற்றும் செலவுகளைச் சொல்லுங்கள், உங்கள் பணம் எங்கே போகிறது என்று காட்டுகிறேன்.",
            "addIncome": "வருமானம் சேர்", "addExpense": "செலவு சேர்", "quickSummary": "சுருக்கம்",
            "income": "வருமானம்", "expenses": "செலவுகள்", "savings": "சேமிப்பு", "thisMonth": "இந்த மாதம்",
            "debt": "கடன்", "debtActive": "நடப்புக் கடன்கள்: {{count}}", "noDebt": "கடன் இல்லை",
            "goals": "இலக்குகள்", "goalsActive": "நடப்பு இலக்குகள்: {{count}}",
        },
        "finance": {
            "filter": {"all": "அனைத்தும்", "income": "வருமானம்", "expense": "செலவு"},
            "transactions": {"title": "பரிவர்த்தனைகள்", "add": "பதிவு சேர்", "empty": "இந்த மாதத்திற்கு இன்னும் பதிவுகள் இல்லை."},
            "form": {
                "addTitle": "பதிவு சேர்", "editTitle": "பதிவைத் திருத்து", "amount": "தொகை", "category": "வகை",
                "date": "தேதி", "note": "குறிப்பு", "notePlaceholder": "எ.கா. சந்தையில் காய்கறி",
                "saved": "சேமிக்கப்பட்டது", "deleted": "நீக்கப்பட்டது", "deleteTitle": "இந்தப் பதிவை நீக்கவா?",
                "deleteMessage": "இதைத் திரும்பப் பெற முடியாது.", "amountRequired": "₹0-க்கு மேல் ஒரு தொகையை உள்ளிடவும்.",
                "amountTooLarge": "இந்தத் தொகை மிகப் பெரியது.", "categoryRequired": "ஒரு வகையைத் தேர்வு செய்யவும்.",
                "noFuture": "எதிர்காலத் தேதியைத் தேர்வு செய்ய முடியாது.",
            },
            "parse": {
                "title": "வார்த்தைகளில் சொல்லுங்கள்", "placeholder": "எ.கா. இன்று காய்கறிக்கு 250 செலவு",
                "fill": "எனக்காக நிரப்பு", "check": "படிவத்தை நிரப்பிவிட்டேன். சரிபார்த்துச் சேமிக்கவும்.",
                "notUnderstood": "எனக்குப் புரியவில்லை. தொகையைச் சேர்க்கவும், எ.கா. \"சாப்பாட்டுக்கு 250 செலவு\".",
            },
            "debt": {
                "title": "கடன்கள்", "add": "கடன் சேர்", "addTitle": "கடன் சேர்", "editTitle": "கடனைத் திருத்து",
                "empty": "கடன்கள் எதுவும் சேர்க்கப்படவில்லை. யாரிடமாவது பணம் வாங்கியிருந்தால், திட்டமிட உதவ இங்கே சேர்க்கவும்.",
                "total": "மொத்தம் செலுத்த வேண்டியது", "allPaid": "உங்கள் கடன்கள் அனைத்தும் அடைக்கப்பட்டன. அருமை!",
                "paidOffSection": "அடைக்கப்பட்டவை", "paidOff": "அடைக்கப்பட்டது", "left": "செலுத்த வேண்டியது",
                "ratePerYear": "ஆண்டுக்கு {{rate}}%", "perMonth": "மாதம் {{amount}}", "dueOn": "ஒவ்வொரு மாதமும் {{day}}ஆம் தேதி",
                "lender": "யாரிடம் கடன் வாங்கினீர்கள்?", "lenderPlaceholder": "எ.கா. SBI, ரமேஷ் அண்ணா",
                "lenderLength": "2 முதல் 80 எழுத்துகள் உள்ளிடவும்.", "type": "கடன் வகை", "amountLeft": "செலுத்த வேண்டிய தொகை",
                "rate": "வட்டி", "rateHint": "ஆண்டுக்கு", "rateRange": "0 முதல் 120 வரை வட்டி விகிதத்தை உள்ளிடவும்.",
                "dueDay": "தவணைத் தேதி", "noDueDay": "நிர்ணயிக்கப்படவில்லை", "monthly": "மாதத் தவணை",
                "markPaid": "முழுவதும் அடைத்துவிட்டேன்", "markedPaid": "அடைக்கப்பட்டதாகக் குறிக்கப்பட்டது", "reopen": "இன்னும் செலுத்துகிறேன்",
                "deleteTitle": "இந்தக் கடனை நீக்கவா?",
            },
        },
        "debttype": {
            "bank_loan": "வங்கிக் கடன்", "kisan_credit_card": "கிசான் கிரெடிட் கார்டு", "credit_card": "கிரெடிட் கார்டு",
            "microfinance": "நுண்கடன் / சுய உதவிக் குழு", "moneylender": "கந்துவட்டிக்காரர்", "family_friend": "குடும்பம் அல்லது நண்பர்",
            "other": "மற்றவை",
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
