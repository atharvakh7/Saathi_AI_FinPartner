"""Merge the step-29 Fraud Shield strings (incl. the 15 red-flag reasons) into src/i18n/*.json (idempotent)."""

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "src" / "i18n"

REASONS = {
    "en": {
        "unrealistic_returns": ("Promises unrealistic returns", "Offers like 'Earn ₹50,000 daily' are usually fake. Real jobs and investments don't pay like this."),
        "asks_personal_info": ("Asks for personal or payment information", "Banks and government offices never ask for your OTP, PIN, CVV or password by message or call."),
        "urgency": ("Uses urgency to pressure you", "Scammers rush you so you don't stop to think or check with someone."),
        "suspicious_link": ("Contains a suspicious link", "The link hides where it really goes or is not secure. Don't open it."),
        "fake_brand_link": ("Link pretends to be a trusted brand", "The website name looks like a bank or government site but it is not the official one."),
        "install_app": ("Asks you to install an unknown app", "Apps sent through messages can read your OTPs and steal money. Install apps only from the Play Store or App Store."),
        "advance_fee": ("Asks for money before giving a loan or prize", "Genuine lenders and prizes don't ask you to pay a fee first."),
        "account_threat": ("Threatens to block your account", "Banks don't block accounts through random messages. Check directly with your bank branch or official app."),
        "fake_prize": ("Says you won a prize you never entered for", "You can't win a lottery or draw you never joined."),
        "impersonation": ("Pretends to be a government office or bank", "Government offices never threaten arrest or ask for money on calls or chats. 'Digital arrest' is not real."),
        "fake_job": ("Typical fake job/task scam", "Paying you for likes or small tasks is a trap. Later they ask you to 'invest' to unlock bigger payouts."),
        "remote_access": ("Asks for remote access to your phone", "Screen-sharing apps let strangers see and control your phone, including your bank app."),
        "investment_tips": ("Unregistered investment tips", "Tip groups promising sure profits are usually not SEBI-registered and often vanish with your money."),
        "upi_trick": ("Trick to make you send money by UPI", "You never need to scan a QR code or enter your UPI PIN to receive money."),
        "unknown_number": ("Pushes you to contact an unknown number", "Moving the chat to a personal number is how scammers avoid official checks."),
    },
    "hi": {
        "unrealistic_returns": ("अविश्वसनीय कमाई का वादा", "'रोज़ ₹50,000 कमाएँ' जैसे ऑफ़र अक्सर झूठे होते हैं। असली नौकरी या निवेश ऐसे पैसे नहीं देते।"),
        "asks_personal_info": ("निजी या भुगतान की जानकारी माँगता है", "बैंक और सरकारी दफ़्तर कभी मैसेज या कॉल पर OTP, PIN, CVV या पासवर्ड नहीं माँगते।"),
        "urgency": ("जल्दबाज़ी का दबाव डालता है", "ठग जल्दी कराते हैं ताकि आप रुककर सोचें नहीं या किसी से पूछें नहीं।"),
        "suspicious_link": ("संदिग्ध लिंक है", "यह लिंक असली पता छिपाता है या सुरक्षित नहीं है। इसे न खोलें।"),
        "fake_brand_link": ("लिंक भरोसेमंद ब्रांड होने का दिखावा करता है", "वेबसाइट का नाम बैंक या सरकारी साइट जैसा दिखता है पर वह आधिकारिक नहीं है।"),
        "install_app": ("अनजान ऐप डाउनलोड करने को कहता है", "मैसेज से भेजे गए ऐप आपके OTP पढ़कर पैसे चुरा सकते हैं। ऐप सिर्फ़ Play Store या App Store से लें।"),
        "advance_fee": ("लोन या इनाम से पहले पैसे माँगता है", "असली लोन देने वाले या इनाम पहले फ़ीस नहीं माँगते।"),
        "account_threat": ("खाता बंद करने की धमकी देता है", "बैंक अनजान मैसेज से खाता बंद नहीं करते। सीधे बैंक शाखा या आधिकारिक ऐप से जाँचें।"),
        "fake_prize": ("ऐसा इनाम जिसके लिए आपने भाग नहीं लिया", "जिस लॉटरी या ड्रॉ में आपने भाग नहीं लिया, उसे आप जीत नहीं सकते।"),
        "impersonation": ("सरकारी दफ़्तर या बैंक होने का दिखावा", "सरकारी दफ़्तर कॉल या चैट पर गिरफ़्तारी की धमकी नहीं देते, न पैसे माँगते हैं। 'डिजिटल अरेस्ट' असली नहीं है।"),
        "fake_job": ("नकली नौकरी/टास्क ठगी", "लाइक या छोटे काम के पैसे देना एक जाल है। बाद में बड़े भुगतान के लिए 'निवेश' माँगा जाता है।"),
        "remote_access": ("आपके फ़ोन का रिमोट एक्सेस माँगता है", "स्क्रीन-शेयरिंग ऐप से अजनबी आपका फ़ोन और बैंक ऐप देख व चला सकते हैं।"),
        "investment_tips": ("बिना पंजीकरण के निवेश टिप्स", "पक्का मुनाफ़ा बताने वाले टिप ग्रुप अक्सर SEBI-पंजीकृत नहीं होते और पैसे लेकर गायब हो जाते हैं।"),
        "upi_trick": ("UPI से पैसे भिजवाने की चाल", "पैसे पाने के लिए कभी QR कोड स्कैन करने या UPI PIN डालने की ज़रूरत नहीं होती।"),
        "unknown_number": ("अनजान नंबर पर बात करने को कहता है", "बातचीत निजी नंबर पर ले जाकर ठग आधिकारिक जाँच से बचते हैं।"),
    },
    "mr": {
        "unrealistic_returns": ("अवास्तव कमाईचे आश्वासन", "'रोज ₹50,000 कमवा' असे ऑफर बहुतेक खोटे असतात. खरी नोकरी किंवा गुंतवणूक असे पैसे देत नाही."),
        "asks_personal_info": ("वैयक्तिक किंवा पेमेंटची माहिती मागतो", "बँका आणि सरकारी कार्यालये कधीही मेसेज किंवा कॉलवर OTP, PIN, CVV किंवा पासवर्ड मागत नाहीत."),
        "urgency": ("घाईचा दबाव आणतो", "फसवणूक करणारे घाई करायला लावतात म्हणजे तुम्ही थांबून विचार करू नये किंवा कोणाला विचारू नये."),
        "suspicious_link": ("संशयास्पद लिंक आहे", "ही लिंक खरा पत्ता लपवते किंवा सुरक्षित नाही. ती उघडू नका."),
        "fake_brand_link": ("लिंक विश्वासू ब्रँड असल्याचे भासवते", "वेबसाइटचे नाव बँक किंवा सरकारी साइटसारखे दिसते पण ते अधिकृत नाही."),
        "install_app": ("अनोळखी ॲप इन्स्टॉल करायला सांगतो", "मेसेजमधून पाठवलेले ॲप तुमचे OTP वाचून पैसे चोरू शकतात. ॲप फक्त Play Store किंवा App Store वरून घ्या."),
        "advance_fee": ("कर्ज किंवा बक्षिसापूर्वी पैसे मागतो", "खरे कर्ज देणारे किंवा बक्षीस आधी फी मागत नाहीत."),
        "account_threat": ("खाते बंद करण्याची धमकी देतो", "बँका अनोळखी मेसेजवरून खाते बंद करत नाहीत. थेट बँक शाखेत किंवा अधिकृत ॲपवर तपासा."),
        "fake_prize": ("तुम्ही भाग न घेतलेले बक्षीस", "ज्या लॉटरी किंवा ड्रॉमध्ये तुम्ही भाग घेतला नाही ते तुम्ही जिंकू शकत नाही."),
        "impersonation": ("सरकारी कार्यालय किंवा बँक असल्याचे भासवतो", "सरकारी कार्यालये कॉल किंवा चॅटवर अटकेची धमकी देत नाहीत किंवा पैसे मागत नाहीत. 'डिजिटल अरेस्ट' खरे नसते."),
        "fake_job": ("खोटी नोकरी/टास्क फसवणूक", "लाइक्स किंवा छोट्या कामांसाठी पैसे देणे हा सापळा आहे. नंतर मोठ्या कमाईसाठी 'गुंतवणूक' मागितली जाते."),
        "remote_access": ("तुमच्या फोनचा रिमोट ॲक्सेस मागतो", "स्क्रीन-शेअरिंग ॲपमुळे अनोळखी लोक तुमचा फोन आणि बँक ॲप पाहू व वापरू शकतात."),
        "investment_tips": ("नोंदणी नसलेल्या गुंतवणूक टिप्स", "खात्रीशीर नफ्याचे आश्वासन देणारे टिप ग्रुप बहुतेक SEBI-नोंदणीकृत नसतात आणि पैसे घेऊन गायब होतात."),
        "upi_trick": ("UPI ने पैसे पाठवायला लावण्याची युक्ती", "पैसे मिळवण्यासाठी कधीही QR कोड स्कॅन करण्याची किंवा UPI PIN टाकण्याची गरज नसते."),
        "unknown_number": ("अनोळखी नंबरवर संपर्क करायला सांगतो", "गप्पा खासगी नंबरवर नेऊन फसवणूक करणारे अधिकृत तपासणी टाळतात."),
    },
    "ta": {
        "unrealistic_returns": ("நம்ப முடியாத வருமான வாக்குறுதி", "'தினமும் ₹50,000 சம்பாதியுங்கள்' போன்றவை பெரும்பாலும் போலி. உண்மையான வேலைகளும் முதலீடுகளும் இப்படிப் பணம் தருவதில்லை."),
        "asks_personal_info": ("தனிப்பட்ட அல்லது பணத் தகவலைக் கேட்கிறது", "வங்கிகளும் அரசு அலுவலகங்களும் செய்தி அல்லது அழைப்பில் OTP, PIN, CVV, கடவுச்சொல்லைக் கேட்பதில்லை."),
        "urgency": ("அவசரப்படுத்தி அழுத்தம் தருகிறது", "நீங்கள் நின்று யோசிக்காமலும் யாரிடமும் கேட்காமலும் இருக்க மோசடியாளர்கள் அவசரப்படுத்துவார்கள்."),
        "suspicious_link": ("சந்தேகமான இணைப்பு உள்ளது", "இந்த இணைப்பு உண்மையான முகவரியை மறைக்கிறது அல்லது பாதுகாப்பற்றது. அதைத் திறக்காதீர்கள்."),
        "fake_brand_link": ("நம்பகமான பிராண்ட் போல் நடிக்கும் இணைப்பு", "இணையதளப் பெயர் வங்கி அல்லது அரசுத் தளம் போல் தெரிகிறது, ஆனால் அது அதிகாரப்பூர்வமானது அல்ல."),
        "install_app": ("தெரியாத செயலியை நிறுவச் சொல்கிறது", "செய்திகளில் அனுப்பப்படும் செயலிகள் உங்கள் OTP-ஐப் படித்துப் பணத்தைத் திருடலாம். Play Store அல்லது App Store-இலிருந்து மட்டும் நிறுவுங்கள்."),
        "advance_fee": ("கடன் அல்லது பரிசுக்கு முன் பணம் கேட்கிறது", "உண்மையான கடன் வழங்குநர்களும் பரிசுகளும் முதலில் கட்டணம் கேட்பதில்லை."),
        "account_threat": ("கணக்கை முடக்குவதாக மிரட்டுகிறது", "வங்கிகள் தெரியாத செய்திகள் மூலம் கணக்கை முடக்குவதில்லை. உங்கள் வங்கிக் கிளை அல்லது அதிகாரப்பூர்வ செயலியில் நேரடியாகச் சரிபாருங்கள்."),
        "fake_prize": ("நீங்கள் பங்கேற்காத பரிசு வென்றதாகச் சொல்கிறது", "நீங்கள் சேராத லாட்டரி அல்லது குலுக்கலில் வெல்ல முடியாது."),
        "impersonation": ("அரசு அலுவலகம் அல்லது வங்கி போல் நடிக்கிறது", "அரசு அலுவலகங்கள் அழைப்பு அல்லது அரட்டையில் கைது மிரட்டல் விடுப்பதில்லை, பணம் கேட்பதில்லை. 'டிஜிட்டல் கைது' உண்மையல்ல."),
        "fake_job": ("போலி வேலை/பணி மோசடி", "லைக்குகள் அல்லது சிறு பணிகளுக்குப் பணம் தருவது ஒரு வலை. பின்னர் பெரிய தொகைக்காக 'முதலீடு' கேட்பார்கள்."),
        "remote_access": ("உங்கள் போனின் தொலை அணுகலைக் கேட்கிறது", "திரைப் பகிர்வு செயலிகள் மூலம் அந்நியர்கள் உங்கள் போனையும் வங்கிச் செயலியையும் பார்த்து இயக்கலாம்."),
        "investment_tips": ("பதிவு செய்யப்படாத முதலீட்டு ஆலோசனை", "உறுதியான லாபம் சொல்லும் ஆலோசனைக் குழுக்கள் பெரும்பாலும் SEBI-பதிவு பெறாதவை, பணத்துடன் மறைந்துவிடும்."),
        "upi_trick": ("UPI மூலம் பணம் அனுப்ப வைக்கும் தந்திரம்", "பணம் பெற QR குறியீட்டை ஸ்கேன் செய்யவோ UPI PIN உள்ளிடவோ தேவையில்லை."),
        "unknown_number": ("தெரியாத எண்ணைத் தொடர்பு கொள்ளச் சொல்கிறது", "உரையாடலைத் தனிப்பட்ட எண்ணுக்கு மாற்றுவதன் மூலம் மோசடியாளர்கள் அதிகாரப்பூர்வ சோதனைகளைத் தவிர்க்கிறார்கள்."),
    },
}

T = {
    "en": {"fraud": {
        "title": "Fraud Shield", "subtitle": "Detect. Analyze. Protect.", "history": "History",
        "intro": "Forward any message, SMS or screenshot. I'll check it for scam signs.",
        "pasteLabel": "Paste the message", "pastePlaceholder": "Paste the SMS or WhatsApp message here…",
        "tooShort": "Paste a bit more of the message (at least 10 characters).", "tooLong": "That's too long. Paste up to 5000 characters.",
        "from": "From:", "source": {"whatsapp": "WhatsApp", "sms": "SMS", "other": "Other"},
        "check": "Check this message", "uploadScreenshot": "Upload a screenshot",
        "imageTooBig": "That image is over 5 MB. Try a smaller screenshot.",
        "ocrUnavailable": "Reading screenshots isn't available right now. Please paste the message text instead.",
        "checking": "Checking the message for scam signs…", "readingImage": "Reading the screenshot and checking it…",
        "recent": "Recent checks", "resultTitle": "Scam check", "riskLevel": "RISK LEVEL", "redFlags": "Red flags detected",
        "whatToDo": "What you should do", "othersReported": "{{count}} other people reported a message like this.",
        "report": "Report this scam", "reported": "Thanks — you reported this. It helps protect others.",
        "call1930": "Call 1930", "youChecked": "You checked (from {{source}}):", "checkAnother": "Check another message",
        "deleteTitle": "Delete this check?", "deleteMessage": "It will be removed from your history. Reports you made stay.",
        "kept": "Checks are kept for 180 days.", "historyEmpty": "No checks yet. Paste a message you're unsure about.",
    }},
    "hi": {"fraud": {
        "title": "फ़्रॉड शील्ड", "subtitle": "पहचानें। जाँचें। बचें।", "history": "इतिहास",
        "intro": "कोई भी मैसेज, SMS या स्क्रीनशॉट भेजें। मैं उसमें धोखाधड़ी के संकेत जाँचूँगा।",
        "pasteLabel": "मैसेज पेस्ट करें", "pastePlaceholder": "SMS या WhatsApp मैसेज यहाँ पेस्ट करें…",
        "tooShort": "मैसेज थोड़ा और पेस्ट करें (कम से कम 10 अक्षर)।", "tooLong": "यह बहुत लंबा है। 5000 अक्षर तक पेस्ट करें।",
        "from": "कहाँ से:", "source": {"whatsapp": "WhatsApp", "sms": "SMS", "other": "अन्य"},
        "check": "यह मैसेज जाँचें", "uploadScreenshot": "स्क्रीनशॉट अपलोड करें",
        "imageTooBig": "यह तस्वीर 5 MB से बड़ी है। छोटा स्क्रीनशॉट आज़माएँ।",
        "ocrUnavailable": "अभी स्क्रीनशॉट पढ़ना उपलब्ध नहीं है। कृपया मैसेज का टेक्स्ट पेस्ट करें।",
        "checking": "मैसेज में धोखाधड़ी के संकेत जाँच रहा हूँ…", "readingImage": "स्क्रीनशॉट पढ़कर जाँच रहा हूँ…",
        "recent": "हाल की जाँचें", "resultTitle": "धोखाधड़ी जाँच", "riskLevel": "जोखिम स्तर", "redFlags": "ख़तरे के संकेत",
        "whatToDo": "आपको क्या करना चाहिए", "othersReported": "{{count}} और लोगों ने ऐसे मैसेज की शिकायत की है।",
        "report": "इस ठगी की शिकायत करें", "reported": "धन्यवाद — आपने शिकायत कर दी। इससे दूसरों को बचाने में मदद मिलती है।",
        "call1930": "1930 पर कॉल करें", "youChecked": "आपने जाँचा ({{source}} से):", "checkAnother": "दूसरा मैसेज जाँचें",
        "deleteTitle": "यह जाँच हटाएँ?", "deleteMessage": "यह आपके इतिहास से हट जाएगी। आपकी की गई शिकायतें रहेंगी।",
        "kept": "जाँचें 180 दिन तक रखी जाती हैं।", "historyEmpty": "अभी कोई जाँच नहीं। शक वाला मैसेज पेस्ट करें।",
    }},
    "mr": {"fraud": {
        "title": "फ्रॉड शील्ड", "subtitle": "ओळखा. तपासा. वाचा.", "history": "इतिहास",
        "intro": "कोणताही मेसेज, SMS किंवा स्क्रीनशॉट पाठवा. मी त्यातील फसवणुकीची चिन्हे तपासेन.",
        "pasteLabel": "मेसेज पेस्ट करा", "pastePlaceholder": "SMS किंवा WhatsApp मेसेज इथे पेस्ट करा…",
        "tooShort": "मेसेज थोडा जास्त पेस्ट करा (किमान 10 अक्षरे).", "tooLong": "हे खूप लांब आहे. 5000 अक्षरांपर्यंत पेस्ट करा.",
        "from": "कुठून:", "source": {"whatsapp": "WhatsApp", "sms": "SMS", "other": "इतर"},
        "check": "हा मेसेज तपासा", "uploadScreenshot": "स्क्रीनशॉट अपलोड करा",
        "imageTooBig": "हे चित्र 5 MB पेक्षा मोठे आहे. लहान स्क्रीनशॉट वापरा.",
        "ocrUnavailable": "आत्ता स्क्रीनशॉट वाचता येत नाही. कृपया मेसेजचा मजकूर पेस्ट करा.",
        "checking": "मेसेजमधील फसवणुकीची चिन्हे तपासत आहे…", "readingImage": "स्क्रीनशॉट वाचून तपासत आहे…",
        "recent": "अलीकडील तपासण्या", "resultTitle": "फसवणूक तपासणी", "riskLevel": "जोखीम पातळी", "redFlags": "धोक्याची चिन्हे",
        "whatToDo": "तुम्ही काय करावे", "othersReported": "आणखी {{count}} लोकांनी अशा मेसेजची तक्रार केली आहे.",
        "report": "या फसवणुकीची तक्रार करा", "reported": "धन्यवाद — तुम्ही तक्रार केली. यामुळे इतरांचे रक्षण होते.",
        "call1930": "1930 वर कॉल करा", "youChecked": "तुम्ही तपासले ({{source}} वरून):", "checkAnother": "दुसरा मेसेज तपासा",
        "deleteTitle": "ही तपासणी काढायची?", "deleteMessage": "ती तुमच्या इतिहासातून काढली जाईल. तुम्ही केलेल्या तक्रारी राहतील.",
        "kept": "तपासण्या 180 दिवस ठेवल्या जातात.", "historyEmpty": "अजून तपासणी नाही. शंका असलेला मेसेज पेस्ट करा.",
    }},
    "ta": {"fraud": {
        "title": "மோசடிக் கவசம்", "subtitle": "கண்டறி. ஆராய். காப்பாற்று.", "history": "வரலாறு",
        "intro": "எந்தச் செய்தி, SMS அல்லது திரைப்பிடிப்பையும் அனுப்புங்கள். மோசடி அறிகுறிகளைச் சரிபார்க்கிறேன்.",
        "pasteLabel": "செய்தியை ஒட்டவும்", "pastePlaceholder": "SMS அல்லது WhatsApp செய்தியை இங்கே ஒட்டவும்…",
        "tooShort": "செய்தியை இன்னும் கொஞ்சம் ஒட்டவும் (குறைந்தது 10 எழுத்துகள்).", "tooLong": "இது மிக நீளம். 5000 எழுத்துகள் வரை ஒட்டவும்.",
        "from": "எங்கிருந்து:", "source": {"whatsapp": "WhatsApp", "sms": "SMS", "other": "மற்றவை"},
        "check": "இந்தச் செய்தியைச் சரிபார்", "uploadScreenshot": "திரைப்பிடிப்பைப் பதிவேற்று",
        "imageTooBig": "இந்தப் படம் 5 MB-ஐ விடப் பெரியது. சிறிய திரைப்பிடிப்பை முயலுங்கள்.",
        "ocrUnavailable": "இப்போது திரைப்பிடிப்புகளைப் படிக்க முடியாது. செய்தியின் உரையை ஒட்டவும்.",
        "checking": "செய்தியில் மோசடி அறிகுறிகளைச் சரிபார்க்கிறேன்…", "readingImage": "திரைப்பிடிப்பைப் படித்துச் சரிபார்க்கிறேன்…",
        "recent": "சமீபத்திய சோதனைகள்", "resultTitle": "மோசடிச் சோதனை", "riskLevel": "அபாய நிலை", "redFlags": "கண்டறியப்பட்ட எச்சரிக்கைகள்",
        "whatToDo": "நீங்கள் செய்ய வேண்டியது", "othersReported": "மேலும் {{count}} பேர் இதுபோன்ற செய்தியைப் புகாரளித்துள்ளனர்.",
        "report": "இந்த மோசடியைப் புகாரளி", "reported": "நன்றி — புகாரளித்தீர்கள். இது மற்றவர்களைக் காக்க உதவும்.",
        "call1930": "1930-ஐ அழை", "youChecked": "நீங்கள் சரிபார்த்தது ({{source}}-இலிருந்து):", "checkAnother": "வேறு செய்தியைச் சரிபார்",
        "deleteTitle": "இந்தச் சோதனையை நீக்கவா?", "deleteMessage": "இது உங்கள் வரலாற்றிலிருந்து நீக்கப்படும். நீங்கள் செய்த புகார்கள் இருக்கும்.",
        "kept": "சோதனைகள் 180 நாட்கள் வைக்கப்படும்.", "historyEmpty": "இன்னும் சோதனைகள் இல்லை. சந்தேகமான செய்தியை ஒட்டவும்.",
    }},
}

for lang, reasons in REASONS.items():
    T[lang]["fraudReason"] = {k: {"title": a, "text": b} for k, (a, b) in reasons.items()}


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
