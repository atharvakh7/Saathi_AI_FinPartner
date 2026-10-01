"""Merge the step-20 onboarding strings into src/i18n/{en,hi,mr,ta}.json (idempotent)."""

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "src" / "i18n"

STATES = {
    "en": ["Andaman & Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chandigarh",
           "Chhattisgarh", "Dadra & Nagar Haveli and Daman & Diu", "Delhi", "Goa", "Gujarat", "Haryana",
           "Himachal Pradesh", "Jammu & Kashmir", "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep",
           "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Puducherry",
           "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
           "West Bengal"],
    "hi": ["अंडमान और निकोबार द्वीपसमूह", "आंध्र प्रदेश", "अरुणाचल प्रदेश", "असम", "बिहार", "चंडीगढ़", "छत्तीसगढ़",
           "दादरा और नगर हवेली और दमन और दीव", "दिल्ली", "गोवा", "गुजरात", "हरियाणा", "हिमाचल प्रदेश",
           "जम्मू और कश्मीर", "झारखंड", "कर्नाटक", "केरल", "लद्दाख", "लक्षद्वीप", "मध्य प्रदेश", "महाराष्ट्र",
           "मणिपुर", "मेघालय", "मिज़ोरम", "नागालैंड", "ओडिशा", "पुडुचेरी", "पंजाब", "राजस्थान", "सिक्किम",
           "तमिलनाडु", "तेलंगाना", "त्रिपुरा", "उत्तर प्रदेश", "उत्तराखंड", "पश्चिम बंगाल"],
    "mr": ["अंदमान आणि निकोबार बेटे", "आंध्र प्रदेश", "अरुणाचल प्रदेश", "आसाम", "बिहार", "चंदीगड", "छत्तीसगड",
           "दादरा आणि नगर हवेली आणि दमण आणि दीव", "दिल्ली", "गोवा", "गुजरात", "हरियाणा", "हिमाचल प्रदेश",
           "जम्मू आणि काश्मीर", "झारखंड", "कर्नाटक", "केरळ", "लडाख", "लक्षद्वीप", "मध्य प्रदेश", "महाराष्ट्र",
           "मणिपूर", "मेघालय", "मिझोराम", "नागालँड", "ओडिशा", "पुदुच्चेरी", "पंजाब", "राजस्थान", "सिक्कीम",
           "तमिळनाडू", "तेलंगणा", "त्रिपुरा", "उत्तर प्रदेश", "उत्तराखंड", "पश्चिम बंगाल"],
    "ta": ["அந்தமான் நிக்கோபார் தீவுகள்", "ஆந்திரப் பிரதேசம்", "அருணாச்சலப் பிரதேசம்", "அசாம்", "பீகார்", "சண்டிகர்",
           "சத்தீஸ்கர்", "தாத்ரா நகர் ஹவேலி மற்றும் டாமன் தியூ", "டெல்லி", "கோவா", "குஜராத்", "ஹரியானா",
           "இமாச்சலப் பிரதேசம்", "ஜம்மு காஷ்மீர்", "ஜார்க்கண்ட்", "கர்நாடகா", "கேரளா", "லடாக்", "லட்சத்தீவு",
           "மத்தியப் பிரதேசம்", "மகாராஷ்டிரா", "மணிப்பூர்", "மேகாலயா", "மிசோரம்", "நாகாலாந்து", "ஒடிசா", "புதுச்சேரி",
           "பஞ்சாப்", "ராஜஸ்தான்", "சிக்கிம்", "தமிழ்நாடு", "தெலங்கானா", "திரிபுரா", "உத்தரப் பிரதேசம்", "உத்தராகண்ட்",
           "மேற்கு வங்காளம்"],
}
CODES = ["AN", "AP", "AR", "AS", "BR", "CH", "CG", "DN", "DL", "GA", "GJ", "HR", "HP", "JK", "JH", "KA", "KL", "LA",
         "LD", "MP", "MH", "MN", "ML", "MZ", "NL", "OD", "PY", "PB", "RJ", "SK", "TN", "TS", "TR", "UP", "UK", "WB"]

T = {
    "en": {
        "errors": {"phone_invalid": "Enter a valid 10-digit mobile number starting with 6, 7, 8 or 9."},
        "form": {
            "required": "Please fill this in.", "range": "Please enter a number in the allowed range.",
            "invalid": "Please check this value.", "nameLength": "Please enter 2 to 80 letters.",
            "ageRange": "Age must be between 18 and 100.", "tooLong": "This is too long.",
            "maxGteMin": "Highest must be more than or equal to lowest.",
            "dependents": "Dependents must be fewer than the people in your household.",
            "dependentsRange": "Enter a number from 0 to 19.", "householdRange": "Enter a number from 1 to 20.",
            "landRange": "Enter land between 0 and 500 hectares.",
        },
        "onboarding": {
            "welcome": {"tagline": "Your Financial Companion", "subtitle": "Understand · Plan · Grow · Protect",
                        "language": "Language", "start": "Get Started"},
            "intro": {
                "slide1": {"title": "See your financial future.", "body": "Simulate decisions before making them."},
                "slide2": {"title": "Guidance you can trust.", "body": "Personalized insights in your own language."},
                "start": "Get Started →",
            },
            "phone": {
                "bubble": "Let's get you started! I'll send a code to your phone.",
                "title": "Your mobile number", "label": "Mobile number",
                "helper": "We use your number only to log you in. No spam.", "send": "Send OTP",
                "waitSeconds": "Too many attempts. Try again in {{count}} seconds.",
            },
            "otp": {
                "title": "Enter the 6-digit code", "sentTo": "Sent by SMS to {{phone}}", "checking": "Checking…",
                "wrongLeft": "Wrong code. {{count}} attempts left.", "locked": "Too many wrong codes. Try again in {{count}} minutes.",
                "resendIn": "Resend code in {{count}} s", "resend": "Resend code", "resent": "A new code has been sent.",
                "changeNumber": "Change number",
            },
            "consent": {
                "title": "Your data, your choice",
                "collectTitle": "What we collect",
                "collect": "Your phone number, your profile, the money entries you add, your chats with Saathi and scam messages you check. Voice recordings are turned into text and then deleted.",
                "purposeTitle": "Why",
                "purpose": "To give you money guidance, find schemes for you, and keep you safe from scams.",
                "retentionTitle": "How long",
                "retention": "Until you delete it. You can delete your chats, memories or your whole account any time.",
                "rightsTitle": "Your rights",
                "rights": "You can see, correct, download or delete your data, and raise a complaint.",
                "readFull": "Read the full Privacy Notice", "privacyTitle": "Privacy Notice",
                "item": {"terms_privacy": "I agree to the Terms and Privacy Notice",
                         "personalization": "Use my data to personalize guidance",
                         "push_notifications": "Send me reminders and insights"},
            },
            "profile": {
                "title": "About you", "step1": "About you", "step2": "Work & income", "step3": "Basics",
                "fullName": "Full name", "choose": "Choose", "district": "District",
                "incomePattern": "How does your income come?",
                "incomeRange": "Roughly how much do you earn in a month? (lowest – highest)",
                "lowest": "Lowest", "highest": "Highest", "householdSize": "People in household",
                "dependents": "Dependents", "socialHelper": "Used only to find schemes for you.",
                "landHectares": "Land (hectares)", "landHelper": "1 hectare ≈ 2.5 acres", "saveContinue": "Save & Continue",
            },
            "confidence": {
                "progress": "Question {{n}} of {{total}}",
                "q1": "How confident are you in making a monthly budget?",
                "q2": "How confident are you in understanding words like SIP, interest or premium?",
                "q3": "How confident are you in spotting a scam message?",
                "q4": "How confident are you in knowing which government schemes you can get?",
                "q5": "How confident are you in saving regularly?",
                "low": "Not at all", "high": "Very confident", "finish": "Finish",
            },
            "goals": {
                "bubble": "What are you saving for? Pick one or more.", "target": "Target amount",
                "targetRequired": "Enter an amount more than ₹0.", "byWhen": "By when?", "noDate": "No fixed date",
                "inMonths": "In {{count}} months", "inYears": "In {{count}} years",
                "customTitle": "Name your goal", "efSuggestion": "Suggested for you: {{amount}}",
                "finish": "Finish", "skip": "Skip for now",
            },
        },
    },
    "hi": {
        "errors": {"phone_invalid": "6, 7, 8 या 9 से शुरू होने वाला सही 10 अंकों का मोबाइल नंबर डालें।"},
        "form": {
            "required": "कृपया इसे भरें।", "range": "कृपया सही सीमा में संख्या डालें।", "invalid": "कृपया यह जानकारी जाँचें।",
            "nameLength": "कृपया 2 से 80 अक्षर लिखें।", "ageRange": "उम्र 18 से 100 के बीच होनी चाहिए।",
            "tooLong": "यह बहुत लंबा है।", "maxGteMin": "सबसे ज़्यादा, सबसे कम से कम नहीं हो सकता।",
            "dependents": "आश्रितों की संख्या परिवार के लोगों से कम होनी चाहिए।",
            "dependentsRange": "0 से 19 के बीच संख्या डालें।", "householdRange": "1 से 20 के बीच संख्या डालें।",
            "landRange": "ज़मीन 0 से 500 हेक्टेयर के बीच डालें।",
        },
        "onboarding": {
            "welcome": {"tagline": "आपका पैसों का साथी", "subtitle": "समझें · योजना बनाएँ · बढ़ें · सुरक्षित रहें",
                        "language": "भाषा", "start": "शुरू करें"},
            "intro": {
                "slide1": {"title": "अपना आर्थिक भविष्य देखें।", "body": "फ़ैसले लेने से पहले उनका असर देखें।"},
                "slide2": {"title": "भरोसेमंद सलाह।", "body": "आपकी अपनी भाषा में आपके लिए सुझाव।"},
                "start": "शुरू करें →",
            },
            "phone": {
                "bubble": "चलिए शुरू करते हैं! मैं आपके फ़ोन पर एक कोड भेजूँगा।",
                "title": "आपका मोबाइल नंबर", "label": "मोबाइल नंबर",
                "helper": "आपका नंबर सिर्फ़ लॉग इन के लिए है। कोई स्पैम नहीं।", "send": "OTP भेजें",
                "waitSeconds": "बहुत ज़्यादा कोशिशें। {{count}} सेकंड बाद फिर कोशिश करें।",
            },
            "otp": {
                "title": "6 अंकों का कोड डालें", "sentTo": "{{phone}} पर SMS से भेजा गया", "checking": "जाँच हो रही है…",
                "wrongLeft": "कोड गलत है। {{count}} कोशिशें बाकी हैं।", "locked": "बहुत बार गलत कोड। {{count}} मिनट बाद कोशिश करें।",
                "resendIn": "{{count}} सेकंड में कोड दोबारा भेजें", "resend": "कोड दोबारा भेजें", "resent": "नया कोड भेज दिया गया है।",
                "changeNumber": "नंबर बदलें",
            },
            "consent": {
                "title": "आपका डेटा, आपकी मर्ज़ी",
                "collectTitle": "हम क्या लेते हैं",
                "collect": "आपका फ़ोन नंबर, आपकी प्रोफ़ाइल, आपकी जोड़ी हुई पैसों की एंट्री, साथी से बातचीत और जाँचे गए धोखाधड़ी वाले मैसेज। आवाज़ की रिकॉर्डिंग को लिखित में बदलकर हटा दिया जाता है।",
                "purposeTitle": "क्यों",
                "purpose": "आपको पैसों की सलाह देने, आपके लिए योजनाएँ खोजने और धोखाधड़ी से बचाने के लिए।",
                "retentionTitle": "कब तक",
                "retention": "जब तक आप उसे न हटाएँ। आप अपनी बातचीत, यादें या पूरा खाता कभी भी हटा सकते हैं।",
                "rightsTitle": "आपके अधिकार",
                "rights": "आप अपना डेटा देख, सुधार, डाउनलोड या हटा सकते हैं, और शिकायत कर सकते हैं।",
                "readFull": "पूरी गोपनीयता सूचना पढ़ें", "privacyTitle": "गोपनीयता सूचना",
                "item": {"terms_privacy": "मैं नियमों और गोपनीयता सूचना से सहमत हूँ",
                         "personalization": "मेरी जानकारी से मुझे मेरे हिसाब से सलाह दें",
                         "push_notifications": "मुझे याद दिलाने वाले संदेश और सुझाव भेजें"},
            },
            "profile": {
                "title": "आपके बारे में", "step1": "आपके बारे में", "step2": "काम और कमाई", "step3": "बुनियादी जानकारी",
                "fullName": "पूरा नाम", "choose": "चुनें", "district": "ज़िला",
                "incomePattern": "आपकी कमाई कैसे आती है?",
                "incomeRange": "महीने में लगभग कितना कमाते हैं? (सबसे कम – सबसे ज़्यादा)",
                "lowest": "सबसे कम", "highest": "सबसे ज़्यादा", "householdSize": "परिवार में लोग",
                "dependents": "आश्रित", "socialHelper": "इसका इस्तेमाल सिर्फ़ आपके लिए योजनाएँ खोजने में होता है।",
                "landHectares": "ज़मीन (हेक्टेयर)", "landHelper": "1 हेक्टेयर ≈ 2.5 एकड़", "saveContinue": "सेव करें और आगे बढ़ें",
            },
            "confidence": {
                "progress": "{{total}} में से सवाल {{n}}",
                "q1": "महीने का बजट बनाने में आप कितने आश्वस्त हैं?",
                "q2": "SIP, ब्याज या प्रीमियम जैसे शब्द समझने में आप कितने आश्वस्त हैं?",
                "q3": "धोखाधड़ी वाला मैसेज पहचानने में आप कितने आश्वस्त हैं?",
                "q4": "यह जानने में आप कितने आश्वस्त हैं कि आपको कौन-सी सरकारी योजनाएँ मिल सकती हैं?",
                "q5": "नियमित बचत करने में आप कितने आश्वस्त हैं?",
                "low": "बिल्कुल नहीं", "high": "पूरा भरोसा", "finish": "पूरा करें",
            },
            "goals": {
                "bubble": "आप किस चीज़ के लिए बचत कर रहे हैं? एक या ज़्यादा चुनें।", "target": "लक्ष्य राशि",
                "targetRequired": "₹0 से ज़्यादा राशि डालें।", "byWhen": "कब तक?", "noDate": "कोई तय तारीख नहीं",
                "inMonths": "{{count}} महीने में", "inYears": "{{count}} साल में",
                "customTitle": "अपने लक्ष्य का नाम", "efSuggestion": "आपके लिए सुझाव: {{amount}}",
                "finish": "पूरा करें", "skip": "अभी छोड़ें",
            },
        },
    },
    "mr": {
        "errors": {"phone_invalid": "6, 7, 8 किंवा 9 ने सुरू होणारा योग्य 10 अंकी मोबाइल नंबर टाका."},
        "form": {
            "required": "कृपया हे भरा.", "range": "कृपया योग्य मर्यादेतील संख्या टाका.", "invalid": "कृपया ही माहिती तपासा.",
            "nameLength": "कृपया 2 ते 80 अक्षरे लिहा.", "ageRange": "वय 18 ते 100 दरम्यान असावे.",
            "tooLong": "हे खूप लांब आहे.", "maxGteMin": "सर्वात जास्त रक्कम सर्वात कमी रकमेपेक्षा कमी असू शकत नाही.",
            "dependents": "अवलंबितांची संख्या कुटुंबातील लोकांपेक्षा कमी असावी.",
            "dependentsRange": "0 ते 19 दरम्यान संख्या टाका.", "householdRange": "1 ते 20 दरम्यान संख्या टाका.",
            "landRange": "जमीन 0 ते 500 हेक्टर दरम्यान टाका.",
        },
        "onboarding": {
            "welcome": {"tagline": "तुमचा आर्थिक साथी", "subtitle": "समजून घ्या · नियोजन करा · वाढा · सुरक्षित राहा",
                        "language": "भाषा", "start": "सुरू करा"},
            "intro": {
                "slide1": {"title": "तुमचे आर्थिक भविष्य पाहा.", "body": "निर्णय घेण्याआधी त्यांचा परिणाम पाहा."},
                "slide2": {"title": "विश्वासार्ह मार्गदर्शन.", "body": "तुमच्याच भाषेत तुमच्यासाठी सल्ला."},
                "start": "सुरू करा →",
            },
            "phone": {
                "bubble": "चला सुरू करूया! मी तुमच्या फोनवर एक कोड पाठवतो.",
                "title": "तुमचा मोबाइल नंबर", "label": "मोबाइल नंबर",
                "helper": "तुमचा नंबर फक्त लॉग इनसाठी वापरला जातो. कोणताही स्पॅम नाही.", "send": "OTP पाठवा",
                "waitSeconds": "खूप प्रयत्न झाले. {{count}} सेकंदांनी पुन्हा प्रयत्न करा.",
            },
            "otp": {
                "title": "6 अंकी कोड टाका", "sentTo": "{{phone}} वर SMS ने पाठवला", "checking": "तपासत आहे…",
                "wrongLeft": "कोड चुकीचा आहे. {{count}} प्रयत्न शिल्लक.", "locked": "खूप वेळा चुकीचा कोड. {{count}} मिनिटांनी प्रयत्न करा.",
                "resendIn": "{{count}} सेकंदांत कोड पुन्हा पाठवा", "resend": "कोड पुन्हा पाठवा", "resent": "नवीन कोड पाठवला आहे.",
                "changeNumber": "नंबर बदला",
            },
            "consent": {
                "title": "तुमचा डेटा, तुमची निवड",
                "collectTitle": "आम्ही काय घेतो",
                "collect": "तुमचा फोन नंबर, तुमची प्रोफाइल, तुम्ही नोंदवलेले पैशांचे व्यवहार, साथीसोबतच्या गप्पा आणि तपासलेले फसवणुकीचे मेसेज. आवाजाचे रेकॉर्डिंग मजकुरात बदलून काढून टाकले जाते.",
                "purposeTitle": "कशासाठी",
                "purpose": "तुम्हाला पैशांबाबत मार्गदर्शन देण्यासाठी, तुमच्यासाठी योजना शोधण्यासाठी आणि फसवणुकीपासून वाचवण्यासाठी.",
                "retentionTitle": "किती काळ",
                "retention": "तुम्ही काढून टाकेपर्यंत. तुम्ही तुमच्या गप्पा, आठवणी किंवा संपूर्ण खाते कधीही काढू शकता.",
                "rightsTitle": "तुमचे हक्क",
                "rights": "तुम्ही तुमचा डेटा पाहू, दुरुस्त करू, डाउनलोड करू किंवा काढू शकता, आणि तक्रार करू शकता.",
                "readFull": "संपूर्ण गोपनीयता सूचना वाचा", "privacyTitle": "गोपनीयता सूचना",
                "item": {"terms_privacy": "मी अटी आणि गोपनीयता सूचनेशी सहमत आहे",
                         "personalization": "माझ्या माहितीवरून मला माझ्यासाठी योग्य सल्ला द्या",
                         "push_notifications": "मला आठवण करून देणारे संदेश आणि सूचना पाठवा"},
            },
            "profile": {
                "title": "तुमच्याबद्दल", "step1": "तुमच्याबद्दल", "step2": "काम आणि उत्पन्न", "step3": "मूलभूत माहिती",
                "fullName": "पूर्ण नाव", "choose": "निवडा", "district": "जिल्हा",
                "incomePattern": "तुमचे उत्पन्न कसे येते?",
                "incomeRange": "महिन्याला साधारण किती कमावता? (सर्वात कमी – सर्वात जास्त)",
                "lowest": "सर्वात कमी", "highest": "सर्वात जास्त", "householdSize": "कुटुंबातील व्यक्ती",
                "dependents": "अवलंबित", "socialHelper": "हे फक्त तुमच्यासाठी योजना शोधण्यासाठी वापरले जाते.",
                "landHectares": "जमीन (हेक्टर)", "landHelper": "1 हेक्टर ≈ 2.5 एकर", "saveContinue": "जतन करा आणि पुढे चला",
            },
            "confidence": {
                "progress": "{{total}} पैकी प्रश्न {{n}}",
                "q1": "महिन्याचे बजेट बनवण्याबाबत तुम्हाला किती खात्री आहे?",
                "q2": "SIP, व्याज किंवा प्रीमियम यांसारखे शब्द समजण्याबाबत तुम्हाला किती खात्री आहे?",
                "q3": "फसवणुकीचा मेसेज ओळखण्याबाबत तुम्हाला किती खात्री आहे?",
                "q4": "तुम्हाला कोणत्या सरकारी योजना मिळू शकतात हे जाणण्याबाबत तुम्हाला किती खात्री आहे?",
                "q5": "नियमित बचत करण्याबाबत तुम्हाला किती खात्री आहे?",
                "low": "अजिबात नाही", "high": "पूर्ण खात्री", "finish": "पूर्ण करा",
            },
            "goals": {
                "bubble": "तुम्ही कशासाठी बचत करत आहात? एक किंवा अधिक निवडा.", "target": "उद्दिष्ट रक्कम",
                "targetRequired": "₹0 पेक्षा जास्त रक्कम टाका.", "byWhen": "कधीपर्यंत?", "noDate": "ठरलेली तारीख नाही",
                "inMonths": "{{count}} महिन्यांत", "inYears": "{{count}} वर्षांत",
                "customTitle": "तुमच्या ध्येयाचे नाव", "efSuggestion": "तुमच्यासाठी सुचवलेले: {{amount}}",
                "finish": "पूर्ण करा", "skip": "आत्ता वगळा",
            },
        },
    },
    "ta": {
        "errors": {"phone_invalid": "6, 7, 8 அல்லது 9 இல் தொடங்கும் சரியான 10 இலக்க மொபைல் எண்ணை உள்ளிடவும்."},
        "form": {
            "required": "இதை நிரப்பவும்.", "range": "அனுமதிக்கப்பட்ட வரம்பில் ஒரு எண்ணை உள்ளிடவும்.", "invalid": "இந்த மதிப்பைச் சரிபார்க்கவும்.",
            "nameLength": "2 முதல் 80 எழுத்துகள் உள்ளிடவும்.", "ageRange": "வயது 18 முதல் 100 வரை இருக்க வேண்டும்.",
            "tooLong": "இது மிக நீளமாக உள்ளது.", "maxGteMin": "அதிகபட்சம் குறைந்தபட்சத்தை விடக் குறைவாக இருக்கக் கூடாது.",
            "dependents": "சார்ந்திருப்போர் எண்ணிக்கை குடும்ப உறுப்பினர்களை விடக் குறைவாக இருக்க வேண்டும்.",
            "dependentsRange": "0 முதல் 19 வரை ஒரு எண்ணை உள்ளிடவும்.", "householdRange": "1 முதல் 20 வரை ஒரு எண்ணை உள்ளிடவும்.",
            "landRange": "நிலத்தை 0 முதல் 500 ஹெக்டேர் வரை உள்ளிடவும்.",
        },
        "onboarding": {
            "welcome": {"tagline": "உங்கள் நிதித் தோழன்", "subtitle": "புரிந்துகொள் · திட்டமிடு · வளர் · பாதுகா",
                        "language": "மொழி", "start": "தொடங்கு"},
            "intro": {
                "slide1": {"title": "உங்கள் நிதி எதிர்காலத்தைப் பாருங்கள்.", "body": "முடிவெடுப்பதற்கு முன் அதன் விளைவைப் பாருங்கள்."},
                "slide2": {"title": "நம்பகமான வழிகாட்டுதல்.", "body": "உங்கள் சொந்த மொழியில் உங்களுக்கான ஆலோசனைகள்."},
                "start": "தொடங்கு →",
            },
            "phone": {
                "bubble": "தொடங்குவோம்! உங்கள் போனுக்கு ஒரு குறியீட்டை அனுப்புகிறேன்.",
                "title": "உங்கள் மொபைல் எண்", "label": "மொபைல் எண்",
                "helper": "உங்கள் எண் உள்நுழைவுக்கு மட்டுமே பயன்படும். ஸ்பேம் இல்லை.", "send": "OTP அனுப்பு",
                "waitSeconds": "அதிக முயற்சிகள். {{count}} வினாடிகளில் மீண்டும் முயற்சிக்கவும்.",
            },
            "otp": {
                "title": "6 இலக்கக் குறியீட்டை உள்ளிடவும்", "sentTo": "{{phone}} க்கு SMS மூலம் அனுப்பப்பட்டது", "checking": "சரிபார்க்கிறது…",
                "wrongLeft": "குறியீடு தவறு. இன்னும் {{count}} முயற்சிகள் உள்ளன.", "locked": "பலமுறை தவறான குறியீடு. {{count}} நிமிடங்களில் முயற்சிக்கவும்.",
                "resendIn": "{{count}} வினாடிகளில் மீண்டும் அனுப்பலாம்", "resend": "குறியீட்டை மீண்டும் அனுப்பு", "resent": "புதிய குறியீடு அனுப்பப்பட்டது.",
                "changeNumber": "எண்ணை மாற்று",
            },
            "consent": {
                "title": "உங்கள் தரவு, உங்கள் விருப்பம்",
                "collectTitle": "நாங்கள் சேகரிப்பவை",
                "collect": "உங்கள் போன் எண், சுயவிவரம், நீங்கள் சேர்க்கும் பணப் பதிவுகள், சாத்தியுடனான உரையாடல்கள், நீங்கள் சரிபார்க்கும் மோசடிச் செய்திகள். குரல் பதிவுகள் எழுத்தாக மாற்றப்பட்டு நீக்கப்படும்.",
                "purposeTitle": "ஏன்",
                "purpose": "உங்களுக்குப் பண வழிகாட்டுதல் தர, உங்களுக்கான திட்டங்களைக் கண்டறிய, மோசடியிலிருந்து பாதுகாக்க.",
                "retentionTitle": "எவ்வளவு காலம்",
                "retention": "நீங்கள் நீக்கும் வரை. உங்கள் உரையாடல்கள், நினைவுகள் அல்லது முழுக் கணக்கையும் எப்போது வேண்டுமானாலும் நீக்கலாம்.",
                "rightsTitle": "உங்கள் உரிமைகள்",
                "rights": "உங்கள் தரவைப் பார்க்க, திருத்த, பதிவிறக்க அல்லது நீக்கலாம், புகாரும் அளிக்கலாம்.",
                "readFull": "முழு தனியுரிமை அறிவிப்பைப் படிக்கவும்", "privacyTitle": "தனியுரிமை அறிவிப்பு",
                "item": {"terms_privacy": "விதிமுறைகள் மற்றும் தனியுரிமை அறிவிப்பை ஏற்கிறேன்",
                         "personalization": "எனக்கேற்ற ஆலோசனைக்கு என் தரவைப் பயன்படுத்துங்கள்",
                         "push_notifications": "நினைவூட்டல்களும் ஆலோசனைகளும் அனுப்புங்கள்"},
            },
            "profile": {
                "title": "உங்களைப் பற்றி", "step1": "உங்களைப் பற்றி", "step2": "வேலை மற்றும் வருமானம்", "step3": "அடிப்படைத் தகவல்",
                "fullName": "முழுப் பெயர்", "choose": "தேர்ந்தெடுக்கவும்", "district": "மாவட்டம்",
                "incomePattern": "உங்கள் வருமானம் எப்படி வருகிறது?",
                "incomeRange": "மாதம் சுமார் எவ்வளவு சம்பாதிக்கிறீர்கள்? (குறைந்தது – அதிகம்)",
                "lowest": "குறைந்தது", "highest": "அதிகம்", "householdSize": "குடும்ப உறுப்பினர்கள்",
                "dependents": "சார்ந்திருப்போர்", "socialHelper": "உங்களுக்கான திட்டங்களைக் கண்டறிய மட்டுமே பயன்படுத்தப்படும்.",
                "landHectares": "நிலம் (ஹெக்டேர்)", "landHelper": "1 ஹெக்டேர் ≈ 2.5 ஏக்கர்", "saveContinue": "சேமித்துத் தொடரவும்",
            },
            "confidence": {
                "progress": "{{total}} இல் கேள்வி {{n}}",
                "q1": "மாத பட்ஜெட் போடுவதில் உங்களுக்கு எவ்வளவு நம்பிக்கை உள்ளது?",
                "q2": "SIP, வட்டி, பிரீமியம் போன்ற சொற்களைப் புரிந்துகொள்வதில் உங்களுக்கு எவ்வளவு நம்பிக்கை உள்ளது?",
                "q3": "மோசடிச் செய்தியைக் கண்டறிவதில் உங்களுக்கு எவ்வளவு நம்பிக்கை உள்ளது?",
                "q4": "உங்களுக்கு எந்த அரசுத் திட்டங்கள் கிடைக்கும் என்பதை அறிவதில் உங்களுக்கு எவ்வளவு நம்பிக்கை உள்ளது?",
                "q5": "தொடர்ந்து சேமிப்பதில் உங்களுக்கு எவ்வளவு நம்பிக்கை உள்ளது?",
                "low": "இல்லவே இல்லை", "high": "மிகுந்த நம்பிக்கை", "finish": "முடி",
            },
            "goals": {
                "bubble": "எதற்காகச் சேமிக்கிறீர்கள்? ஒன்று அல்லது அதற்கு மேல் தேர்ந்தெடுக்கவும்.", "target": "இலக்குத் தொகை",
                "targetRequired": "₹0 க்கு மேல் தொகையை உள்ளிடவும்.", "byWhen": "எப்போதுக்குள்?", "noDate": "குறிப்பிட்ட தேதி இல்லை",
                "inMonths": "{{count}} மாதங்களில்", "inYears": "{{count}} ஆண்டுகளில்",
                "customTitle": "உங்கள் இலக்கின் பெயர்", "efSuggestion": "உங்களுக்கான பரிந்துரை: {{amount}}",
                "finish": "முடி", "skip": "இப்போது தவிர்",
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
    data["state"] = dict(zip(CODES, STATES[lang], strict=True))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("merged step-20 strings into", ", ".join(T))
