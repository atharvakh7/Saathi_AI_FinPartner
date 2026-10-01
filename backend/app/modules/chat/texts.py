"""Fixed chat texts in en/hi/mr/ta: safety replies, confirmations and fallbacks are never left to
the LLM (spec §5.3 step 7 "fixed compassionate response", "polite redirect")."""

from datetime import date
from decimal import Decimal

T: dict[str, dict[str, str]] = {
    "distress": {
        "en": "I'm really sorry you're feeling this way. You are not alone, and talking to someone helps. "
              "Please call Tele-MANAS on 14416 (free, 24×7) to talk to a trained counsellor in your language. "
              "If you are in immediate danger, call 112. Money problems can be solved step by step, and I'm here "
              "to help with that whenever you're ready.",
        "hi": "मुझे बहुत दुख है कि आप ऐसा महसूस कर रहे हैं। आप अकेले नहीं हैं, किसी से बात करने से मदद मिलती है। "
              "कृपया Tele-MANAS को 14416 पर कॉल करें (मुफ़्त, 24 घंटे), वहाँ प्रशिक्षित सलाहकार आपकी भाषा में बात करेंगे। "
              "अगर आप तुरंत खतरे में हैं, तो 112 पर कॉल करें। पैसों की परेशानी धीरे-धीरे सुलझ सकती है, "
              "जब आप तैयार हों, मैं इसमें आपकी मदद करूँगा।",
        "mr": "तुम्हाला असं वाटतंय याचं मला खूप वाईट वाटतं. तुम्ही एकटे नाही आहात, कोणाशी तरी बोलल्याने मदत होते. "
              "कृपया Tele-MANAS ला 14416 वर कॉल करा (मोफत, 24 तास), तिथे प्रशिक्षित समुपदेशक तुमच्या भाषेत बोलतील. "
              "तुम्ही लगेच धोक्यात असाल तर 112 वर कॉल करा. पैशांच्या अडचणी हळूहळू सुटू शकतात, "
              "तुम्ही तयार असाल तेव्हा मी मदत करेन.",
        "ta": "நீங்கள் இப்படி உணர்வது எனக்கு மிகவும் வருத்தமாக இருக்கிறது. நீங்கள் தனியாக இல்லை, யாரிடமாவது பேசுவது உதவும். "
              "தயவுசெய்து Tele-MANAS-ஐ 14416 என்ற எண்ணில் அழைக்கவும் (இலவசம், 24 மணி நேரமும்), பயிற்சி பெற்ற ஆலோசகர்கள் "
              "உங்கள் மொழியில் பேசுவார்கள். உடனடி ஆபத்தில் இருந்தால் 112-ஐ அழைக்கவும். பணப் பிரச்சினைகளைப் படிப்படியாகத் "
              "தீர்க்கலாம், நீங்கள் தயாராக இருக்கும்போது நான் உதவுகிறேன்.",
    },
    "out_of_scope": {
        "en": "I can only help with money matters: saving, spending, loans, government schemes and staying safe from "
              "scams. What would you like to know about your money?",
        "hi": "मैं सिर्फ़ पैसों से जुड़ी बातों में मदद कर सकता हूँ: बचत, खर्च, कर्ज़, सरकारी योजनाएँ और धोखाधड़ी से बचाव। "
              "अपने पैसों के बारे में आप क्या जानना चाहेंगे?",
        "mr": "मी फक्त पैशांशी संबंधित गोष्टींमध्ये मदत करू शकतो: बचत, खर्च, कर्ज, सरकारी योजना आणि फसवणुकीपासून बचाव. "
              "तुमच्या पैशांबद्दल तुम्हाला काय जाणून घ्यायचं आहे?",
        "ta": "நான் பணம் தொடர்பான விஷயங்களில் மட்டுமே உதவ முடியும்: சேமிப்பு, செலவு, கடன், அரசுத் திட்டங்கள் மற்றும் "
              "மோசடியிலிருந்து பாதுகாப்பு. உங்கள் பணத்தைப் பற்றி என்ன தெரிந்துகொள்ள விரும்புகிறீர்கள்?",
    },
    "guardrail_fallback": {
        "en": "I can explain how saving and investing work, but I can't promise returns or pick investments for you. "
              "For investment decisions, please talk to a SEBI-registered investment adviser.",
        "hi": "मैं बचत और निवेश कैसे काम करते हैं, यह समझा सकता हूँ, लेकिन मैं मुनाफ़े का वादा नहीं कर सकता या आपके लिए "
              "निवेश नहीं चुन सकता। निवेश के फ़ैसलों के लिए कृपया SEBI-रजिस्टर्ड निवेश सलाहकार से बात करें।",
        "mr": "बचत आणि गुंतवणूक कशी काम करते हे मी समजावू शकतो, पण मी नफ्याचं वचन देऊ शकत नाही किंवा तुमच्यासाठी "
              "गुंतवणूक निवडू शकत नाही. गुंतवणुकीच्या निर्णयांसाठी कृपया SEBI-नोंदणीकृत गुंतवणूक सल्लागाराशी बोला.",
        "ta": "சேமிப்பும் முதலீடும் எப்படி வேலை செய்கின்றன என்று விளக்க முடியும், ஆனால் லாபத்தை உறுதியளிக்கவோ உங்களுக்காக "
              "முதலீட்டைத் தேர்ந்தெடுக்கவோ முடியாது. முதலீட்டு முடிவுகளுக்கு SEBI-பதிவு பெற்ற முதலீட்டு ஆலோசகரிடம் பேசவும்.",
    },
    "ask_amount_tx": {
        "en": "How much was it? For example: \"spent 200 on vegetables\" or \"sold onions for 5000\".",
        "hi": "कितने रुपये थे? जैसे: \"सब्ज़ी पर 200 खर्च किए\" या \"प्याज़ 5000 में बेचा\"।",
        "mr": "किती रुपये होते? उदा.: \"भाजीवर 200 खर्च केले\" किंवा \"कांदा 5000 ला विकला\".",
        "ta": "எவ்வளவு ரூபாய்? உதாரணம்: \"காய்கறிக்கு 200 செலவு\" அல்லது \"வெங்காயம் 5000-க்கு விற்றேன்\".",
    },
    "ask_amount_goal": {
        "en": "Nice goal! How much money do you need for it, and by when?",
        "hi": "अच्छा लक्ष्य है! इसके लिए कितने पैसे चाहिए, और कब तक?",
        "mr": "छान ध्येय आहे! यासाठी किती पैसे लागतील, आणि कधीपर्यंत?",
        "ta": "நல்ல இலக்கு! இதற்கு எவ்வளவு பணம் தேவை, எப்போதுக்குள்?",
    },
    "confirm_tx": {
        "en": "Add {what} for {category} on {date}?",
        "hi": "{date} को {category} के लिए {what} जोड़ दूँ?",
        "mr": "{date} रोजी {category}साठी {what} नोंदवू का?",
        "ta": "{date} அன்று {category}-க்கு {what} சேர்க்கட்டுமா?",
    },
    "confirm_goal": {
        "en": "Create a goal \"{title}\" of ₹{amount}{by}?",
        "hi": "₹{amount} का लक्ष्य \"{title}\" बना दूँ{by}?",
        "mr": "₹{amount} चं \"{title}\" हे ध्येय तयार करू का{by}?",
        "ta": "₹{amount} க்கு \"{title}\" இலக்கை உருவாக்கட்டுமா{by}?",
    },
    "goal_by": {"en": " by {date}", "hi": " ({date} तक)", "mr": " ({date} पर्यंत)", "ta": " ({date} க்குள்)"},
    "saved_tx": {
        "en": "Done! I added {what} for {category}.",
        "hi": "हो गया! {category}: {what} आपके रिकॉर्ड में सेव है।",
        "mr": "झालं! {category}: {what} तुमच्या नोंदीत जतन केलं.",
        "ta": "முடிந்தது! {category}: {what} உங்கள் பதிவில் சேர்க்கப்பட்டது.",
    },
    "saved_goal": {
        "en": "Done! Your goal \"{title}\" is ready. Add money to it whenever you can.",
        "hi": "हो गया! आपका लक्ष्य \"{title}\" बन गया। जब भी हो सके, इसमें पैसे जोड़ें।",
        "mr": "झालं! तुमचं \"{title}\" हे ध्येय तयार आहे. जमेल तेव्हा त्यात पैसे जोडा.",
        "ta": "முடிந்தது! உங்கள் \"{title}\" இலக்கு தயார். முடியும்போது இதில் பணம் சேர்க்கவும்.",
    },
    "cancelled": {
        "en": "Okay, I didn't save it.",
        "hi": "ठीक है, मैंने इसे सेव नहीं किया।",
        "mr": "ठीक आहे, मी हे जतन केलं नाही.",
        "ta": "சரி, நான் இதைச் சேமிக்கவில்லை.",
    },
    "save_failed": {
        "en": "Sorry, I couldn't save that. Please try again from the Money screen.",
        "hi": "माफ़ कीजिए, मैं इसे सेव नहीं कर पाया। कृपया मनी स्क्रीन से फिर कोशिश करें।",
        "mr": "माफ करा, मी हे जतन करू शकलो नाही. कृपया मनी स्क्रीनवरून पुन्हा प्रयत्न करा.",
        "ta": "மன்னிக்கவும், இதைச் சேமிக்க முடியவில்லை. பண திரையிலிருந்து மீண்டும் முயற்சிக்கவும்.",
    },
    "scam_need_text": {
        "en": "Please paste the full message or offer you received, and I'll check it for scam signs.",
        "hi": "कृपया वह पूरा मैसेज या ऑफ़र यहाँ पेस्ट करें, मैं उसमें धोखाधड़ी के संकेत जाँच दूँगा।",
        "mr": "कृपया आलेला पूर्ण मेसेज किंवा ऑफर इथे पेस्ट करा, मी त्यात फसवणुकीची चिन्हे तपासतो.",
        "ta": "நீங்கள் பெற்ற முழுச் செய்தியையோ சலுகையையோ இங்கே ஒட்டவும், மோசடி அறிகுறிகளைச் சரிபார்க்கிறேன்.",
    },
    # Amount + noun with the right gender agreement ("की आमदनी" but "का खर्च").
    "income": {"en": "income of ₹{amount}", "hi": "₹{amount} की आमदनी", "mr": "₹{amount} चे उत्पन्न",
               "ta": "₹{amount} வருமானம்"},
    "expense": {"en": "expense of ₹{amount}", "hi": "₹{amount} का खर्च", "mr": "₹{amount} चा खर्च",
                "ta": "₹{amount} செலவு"},
    "greeting_fallback": {
        "en": "Namaste {name}! How can I help with your money today?",
        "hi": "नमस्ते {name}! आज मैं आपके पैसों में कैसे मदद करूँ?",
        "mr": "नमस्कार {name}! आज मी तुमच्या पैशांबाबत कशी मदत करू?",
        "ta": "வணக்கம் {name}! இன்று உங்கள் பணத்தில் எப்படி உதவலாம்?",
    },
}

CHIPS: dict[str, dict[str, list[str]]] = {
    "yes_no": {"en": ["Yes", "No"], "hi": ["हाँ", "नहीं"], "mr": ["होय", "नाही"], "ta": ["ஆம்", "இல்லை"]},
    "after_scam": {
        "en": ["How do I report it?", "Check another message"],
        "hi": ["इसकी शिकायत कैसे करूँ?", "दूसरा मैसेज जाँचें"],
        "mr": ["तक्रार कशी करू?", "दुसरा मेसेज तपासा"],
        "ta": ["எப்படி புகார் செய்வது?", "வேறு செய்தியைச் சரிபார்"],
    },
    "starters": {
        "en": ["What is SIP?", "Is this message a scam?", "Which schemes can I get?"],
        "hi": ["SIP क्या है?", "क्या यह मैसेज धोखा है?", "मुझे कौन सी योजनाएँ मिल सकती हैं?"],
        "mr": ["SIP म्हणजे काय?", "हा मेसेज फसवणूक आहे का?", "मला कोणत्या योजना मिळू शकतात?"],
        "ta": ["SIP என்றால் என்ன?", "இந்தச் செய்தி மோசடியா?", "எனக்கு என்ன திட்டங்கள் கிடைக்கும்?"],
    },
    "greeting": {
        "en": ["Add today's expense", "Check my goals"],
        "hi": ["आज का खर्च जोड़ें", "मेरे लक्ष्य देखें"],
        "mr": ["आजचा खर्च जोडा", "माझी ध्येये पाहा"],
        "ta": ["இன்றைய செலவைச் சேர்", "என் இலக்குகளைப் பார்"],
    },
}

CATEGORY_NAMES: dict[str, dict[str, str]] = {
    "crop_sale": {"en": "crop sale", "hi": "फसल बिक्री", "mr": "पीक विक्री", "ta": "பயிர் விற்பனை"},
    "wages": {"en": "wages", "hi": "मज़दूरी", "mr": "मजुरी", "ta": "கூலி"},
    "salary": {"en": "salary", "hi": "वेतन", "mr": "पगार", "ta": "சம்பளம்"},
    "gig_payout": {"en": "gig payout", "hi": "गिग भुगतान", "mr": "गिग पेमेंट", "ta": "கிக் வருமானம்"},
    "allowance": {"en": "allowance", "hi": "भत्ता", "mr": "भत्ता", "ta": "படி"},
    "pension": {"en": "pension", "hi": "पेंशन", "mr": "पेन्शन", "ta": "ஓய்வூதியம்"},
    "business": {"en": "business", "hi": "व्यापार", "mr": "व्यवसाय", "ta": "வணிகம்"},
    "other_income": {"en": "other income", "hi": "अन्य आमदनी", "mr": "इतर उत्पन्न", "ta": "பிற வருமானம்"},
    "food": {"en": "food", "hi": "खाना", "mr": "अन्न", "ta": "உணவு"},
    "housing_rent": {"en": "rent", "hi": "किराया", "mr": "भाडे", "ta": "வாடகை"},
    "utilities": {"en": "bills", "hi": "बिल", "mr": "बिले", "ta": "கட்டணங்கள்"},
    "transport": {"en": "transport", "hi": "आना-जाना", "mr": "प्रवास", "ta": "போக்குவரத்து"},
    "health": {"en": "health", "hi": "स्वास्थ्य", "mr": "आरोग्य", "ta": "உடல்நலம்"},
    "education": {"en": "education", "hi": "पढ़ाई", "mr": "शिक्षण", "ta": "கல்வி"},
    "farm_inputs": {"en": "farm inputs", "hi": "खेती का सामान", "mr": "शेतीचे साहित्य", "ta": "விவசாயப் பொருட்கள்"},
    "debt_repayment": {"en": "loan repayment", "hi": "कर्ज़ चुकाना", "mr": "कर्जफेड", "ta": "கடன் திருப்பிச் செலுத்துதல்"},
    "insurance_premium": {"en": "insurance premium", "hi": "बीमा प्रीमियम", "mr": "विमा हप्ता", "ta": "காப்பீட்டுப் பிரீமியம்"},
    "subscriptions": {"en": "subscriptions", "hi": "सब्सक्रिप्शन", "mr": "सबस्क्रिप्शन", "ta": "சந்தாக்கள்"},
    "entertainment": {"en": "entertainment", "hi": "मनोरंजन", "mr": "मनोरंजन", "ta": "பொழுதுபோக்கு"},
    "other_expense": {"en": "other expense", "hi": "अन्य खर्च", "mr": "इतर खर्च", "ta": "பிற செலவு"},
}

# Spec §5.3: yes, haan, ha, हाँ, होय, ஆம் — plus common variants; and the matching no-set.
YES = {"yes", "y", "yeah", "yep", "ok", "okay", "sure", "haan", "han", "ha", "haa", "ho", "hoy", "hoi", "aam", "aamam",
       "हाँ", "हां", "हा", "जी", "जी हाँ", "होय", "हो", "ठीक", "ஆம்", "ஆமாம்", "சரி", "हाँ जी", "हां जी", "yes please"}
NO = {"no", "n", "nope", "nah", "cancel", "nahi", "nahin", "na", "nako", "illai", "venda",
      "नहीं", "नही", "ना", "नाही", "नको", "இல்லை", "வேண்டாம்", "no thanks"}


def t(key: str, language: str, **values) -> str:
    template = T[key].get(language) or T[key]["en"]
    return template.format(**values) if values else template


def chips(key: str, language: str) -> list[str]:
    return list(CHIPS[key].get(language) or CHIPS[key]["en"])


def category_name(category: str, language: str) -> str:
    names = CATEGORY_NAMES.get(category, {})
    return names.get(language) or names.get("en") or category.replace("_", " ")


def inr(amount: Decimal | float | int) -> str:
    """Indian digit grouping: 150000 -> '1,50,000'; paise shown only when present."""
    value = Decimal(str(amount)).quantize(Decimal("0.01"))
    whole, frac = divmod(value, 1)
    digits = str(int(whole))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join(groups + [tail])
    return digits if frac == 0 else f"{digits}.{int(frac * 100):02d}"


def day(d: date) -> str:
    return d.strftime("%d %b %Y").lstrip("0")


def normalized_answer(text: str) -> str:
    return " ".join(text.lower().strip(" .!?।,").split())
