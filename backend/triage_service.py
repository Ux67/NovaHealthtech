"""
Nova Healthtech - Deterministic Emergency Symptom Red-Flag Service
Rule-based, zero-AI emergency screening in English (en), Gujarati (gu), and Hindi (hi).
Designed as the mandatory safety gate before any AI assistant interaction.
"""

from typing import Dict, Any, List


# Verified Deterministic Red-Flag Categories (Urban & Rural India Priorities)
RED_FLAG_RULES: List[Dict[str, Any]] = [
    {
        "id": "chest_pain_cardiac",
        "keywords": [
            "chest pain", "chest tightness", "heart attack", "left arm pain", "chest pressure",
            "છાતીમાં દુખાવો", "છાતીમાં ભારેપણું", "હાર્ટ એટેક", "ગભરામણ અને પરસેવો",
            "सीने में दर्द", "छाती में दर्द", "दिल का दौरा", "सीने में जकड़न",
        ],
        "i18n": {
            "en": {
                "label": "Chest pain, pressure, or tightness spreading to arm/jaw/back",
                "action": "Call 108 Ambulance immediately. Have the person sit or rest quietly; loosen tight clothing. Do not let them walk or drive themselves.",
            },
            "gu": {
                "label": "છાતીમાં તીવ્ર દુખાવો, ભારેપણું અથવા હાથ/જડબામાં ફેલાતો દુખાવો",
                "action": "તાત્કાલિક 108 એમ્બ્યુલન્સને કોલ કરો. દર્દીને શાંતિથી બેસાડો, ચુસ્ત કપડાં ઢીલા કરો અને તેમને ચાલવા દેશો નહીં.",
            },
            "hi": {
                "label": "सीने में तेज दर्द, भारीपन या हाथ/जबड़े में फैलता दर्द",
                "action": "तुरंत 108 एम्बुलेंस को कॉल करें। रोगी को आराम से बैठाएं, तंग कपड़े ढीले करें और उन्हें स्वयं चलने न दें।",
            },
        },
    },
    {
        "id": "breathing_difficulty",
        "keywords": [
            "cannot breathe", "shortness of breath", "difficulty breathing", "gasping", "choking", "blue lips",
            "શ્વાસ લેવામાં તકલીફ", "શ્વાસ રૂંધાવો", "હાંફ ચડવી", "હોઠ ભૂરા પડવા",
            "सांस लेने में कठिनाई", "सांस फूलना", "दम घुटना", "सांस नहीं आ रही",
        ],
        "i18n": {
            "en": {
                "label": "Severe difficulty breathing, gasping for air, or bluish lips/face",
                "action": "Call 108 immediately. Keep the person sitting upright (do not force them to lie flat) and ensure fresh air circulation.",
            },
            "gu": {
                "label": "શ્વાસ લેવામાં ગંભીર તકલીફ, શ્વાસ રૂંધાવો અથવા હોઠ ભૂરા પડવા",
                "action": "તાત્કાલિક 108 પર કોલ કરો. દર્દીને ટટ્ટાર બેસાડી રાખો (સીધા સુવડાવશો નહીં) અને ખુલ્લી હવા મળે તેનું ધ્યાન રાખો.",
            },
            "hi": {
                "label": "सांस लेने में गंभीर कठिनाई, दम घुटना या होंठ नीले पड़ना",
                "action": "तुरंत 108 पर कॉल करें। व्यक्ति को सीधा बैठाकर रखें (चित न लिटाएं) और खुली हवा आने दें।",
            },
        },
    },
    {
        "id": "stroke_neurological",
        "keywords": [
            "stroke", "face drooping", "slurred speech", "paralysis", "one side weak", "numbness on one side",
            "લકવો", "મોઢું વાંકું થઈ જવું", "બોલવામાં તૂટક અવાજ", "એક બાજુ હાથ પગ કામ ન કરવા",
            "लकवा", "चेहरा टेढ़ा होना", "बोलने में लड़खड़ाहट", "शरीर का एक हिस्सा सुन्न होना",
        ],
        "i18n": {
            "en": {
                "label": "Sudden face drooping, arm/leg weakness on one side, or slurred speech",
                "action": "Call 108 immediately and note the exact time symptoms started. Do NOT give food, water, or oral medicine (high choking risk).",
            },
            "gu": {
                "label": "અચાનક મોઢું વાંકું થવું, શરીરની એક બાજુ નબળાઈ (લકવાની અસર) કે બોલવામાં તકલીફ",
                "action": "તાત્કાલિક 108 બોલાવો અને લક્ષણો શરૂ થયાનો સમય નોંધો. દર્દીને મોઢેથી પાણી, ખોરાક કે દવા આપશો નહીં.",
            },
            "hi": {
                "label": "अचानक चेहरा टेढ़ा होना, एक तरफ हाथ-पैर में कमजोरी या बोलने में कठिनाई",
                "action": "तुरंत 108 बुलाएं और लक्षण शुरू होने का समय नोट करें। रोगी को मुंह से पानी या भोजन बिल्कुल न दें।",
            },
        },
    },
    {
        "id": "unconscious_seizure",
        "keywords": [
            "unconscious", "fainted", "not waking up", "seizure", "fits", "convulsions",
            "બેભાન", "ભાન ગુમાવવું", "આંચકી", "ખેંચ આવવી",
            "बेहोश", "होश न आना", "दौरा पड़ना", "मिर्गी का दौरा",
        ],
        "i18n": {
            "en": {
                "label": "Unconsciousness, inability to wake up, or active seizure / fits",
                "action": "Call 108. Gently turn the person onto their side (recovery position) to keep the airway clear. Never put spoons, fingers, or water in their mouth.",
            },
            "gu": {
                "label": "બેભાન અવસ્થા, ભાનમાં ન આવવું અથવા ખેંચ / આંચકી આવવી",
                "action": "108 પર કોલ કરો. દર્દીને એક પડખે સુવડાવો જેથી શ્વાસનળી ખુલ્લી રહે. મોઢામાં ચમચી, આંગળી કે પાણી ક્યારેય નાખશો નહીં.",
            },
            "hi": {
                "label": "बेहोशी, होश में न आना या तेज दौरे / ऐंठन आना",
                "action": "108 पर कॉल करें। व्यक्ति को एक करवट लिटाएं ताकि सांस की नली खुली रहे। मुंह में चम्मच, उंगली या पानी कभी न डालें।",
            },
        },
    },
    {
        "id": "severe_bleeding_trauma",
        "keywords": [
            "severe bleeding", "heavy bleeding", "head injury", "road accident", "deep wound", "vomiting blood",
            "વધારે લોહી નીકળવું", "ગંભીર ઈજા", "માથામાં ઈજા", "અકસ્માત", "લોહીની ઉલટી",
            "तेज रक्तस्राव", "बहुत खून बहना", "सिर में गंभीर चोट", "सड़क दुर्घटना", "खून की उल्टी",
        ],
        "i18n": {
            "en": {
                "label": "Uncontrolled bleeding, major accident/head injury, or vomiting blood",
                "action": "Call 108/112. Apply firm, steady pressure to external bleeding with a clean cloth. Do not move the neck/spine if a head or back injury is suspected.",
            },
            "gu": {
                "label": "અનિયંત્રિત રક્તસ્રાવ (લોહી વહેવું), ગંભીર અકસ્માત/માથાની ઈજા અથવા લોહીની ઉલટી",
                "action": "108/112 પર કોલ કરો. સ્વચ્છ કપડાથી ઘા પર સીધું દબાણ આપો. માથા કે કરોડરજ્જુની ઈજા હોય તો દર્દીની ગરદન હલાવશો નહીં.",
            },
            "hi": {
                "label": "अनियंत्रित रक्तस्राव, गंभीर दुर्घटना/सिर की चोट या खून की उल्टी",
                "action": "108/112 पर कॉल करें। साफ कपड़े से घाव पर सीधा दबाव बनाएं। सिर या रीढ़ की चोट की आशंका हो तो गर्दन न हिलाएं।",
            },
        },
    },
    {
        "id": "snakebite_poisoning",
        "keywords": [
            "snake bite", "snakebite", "scorpion sting", "poison", "pesticide", "overdose",
            "સાપ કરડવો", "સર્પદંશ", "વીંછી કરડવો", "ઝેર", "ઝેરી દવા",
            "सांप का काटना", "सर्पदंश", "बिच्छू का डंक", "जहर", "कीटनाशक पी लेना",
        ],
        "i18n": {
            "en": {
                "label": "Snakebite, severe scorpion sting, or suspected poisoning / chemical ingestion",
                "action": "Call 108 immediately to reach a government hospital with anti-venom. Keep the person calm and the bitten limb still. Do NOT cut the wound, suck venom, apply tight tourniquets, or use herbal/faith remedies.",
            },
            "gu": {
                "label": "સર્પદંશ (સાપ કરડવો), ગંભીર વીંછીનો ડંખ અથવા ઝેરી પદાર્થની અસર",
                "action": "એન્ટી-વેનમ ધરાવતી સરકારી હોસ્પિટલ પહોંચવા તાત્કાલિક 108 બોલાવો. દર્દીને શાંત રાખો. ઘા પર કાપો મૂકવો નહીં, દોરીથી કચકચાવીને બાંધવું નહીં અને ભુવા/ઝાડ-ફૂંકમાં સમય બગાડવો નહીં.",
            },
            "hi": {
                "label": "सांप का काटना (सर्पदंश), बिच्छू का डंक या जहर/कीटनाशक का सेवन",
                "action": "एंटी-वेनम वाले सरकारी अस्पताल पहुंचने के लिए तुरंत 108 बुलाएं। रोगी को शांत और स्थिर रखें। घाव को काटें नहीं, कसकर रस्सी न बांधें और झाड़-फूंक में समय न गंवाएं।",
            },
        },
    },
    {
        "id": "pregnancy_maternal_emergency",
        "keywords": [
            "pregnancy bleeding", "severe labor pain", "water broke early", "blurred vision in pregnancy",
            "ગર્ભાવસ્થામાં રક્તસ્રાવ", "પ્રસૂતિની ગંભીર પીડા", "ગર્ભાવસ્થામાં ખેંચ",
            "गर्भावस्था में रक्तस्राव", "गर्भावस्था में तेज दर्द", "प्रसव पीड़ा",
        ],
        "i18n": {
            "en": {
                "label": "Pregnancy emergency (vaginal bleeding, severe headache/blurred vision, or convulsions)",
                "action": "Call 108 immediately for free maternal ambulance transport to the nearest Civil / FRU Hospital.",
            },
            "gu": {
                "label": "ગર્ભાવસ્થા દરમિયાન રક્તસ્રાવ, તીવ્ર માથાનો દુખાવો/ઝાંખું દેખાવું અથવા ખેંચ આવવી",
                "action": "નજીકની સિવિલ કે સરકારી હોસ્પિટલમાં તાત્કાલિક પહોંચવા માટે 108 એમ્બ્યુલન્સને કોલ કરો.",
            },
            "hi": {
                "label": "गर्भावस्था में रक्तस्राव, तेज सिरदर्द/धुंधला दिखना या दौरे आना",
                "action": "नजदीकी सिविल या सरकारी अस्पताल तुरंत पहुंचने के लिए 108 एम्बुलेंस को कॉल करें।",
            },
        },
    },
]


def get_triage_rules_catalog() -> List[Dict[str, Any]]:
    """Returns the structured red-flag rules for client-side rendering and offline caching."""
    return RED_FLAG_RULES


def evaluate_emergency_triage(
    selected_rule_ids: List[str],
    free_text: str,
    lang: str = "en",
) -> Dict[str, Any]:
    """
    Preliminary emergency keyword screening only.
    A missing keyword match does NOT mean the person is safe.
    """

    lang_code = lang if lang in ("en", "gu", "hi") else "en"
    text = (free_text or "").strip().lower()
    selected = set(selected_rule_ids or [])

    matched_rules = []

    for rule in RED_FLAG_RULES:
        # Explicitly selected red flags always trigger the safety gate.
        checked = rule["id"] in selected

        # Retain the existing multilingual keyword catalogue.
        keyword_match = any(
            keyword.lower() in text
            for keyword in rule["keywords"]
        )

        if checked or keyword_match:
            localized = rule["i18n"].get(
                lang_code, rule["i18n"]["en"]
            )
            matched_rules.append({
                "id": rule["id"],
                "symptom": localized["label"],
                "immediate_action": localized["action"],
            })

    emergency_numbers = {
        "ambulance": "108",
        "national_emergency": "112",
    }

    if matched_rules:
        translations = {
            "en": (
                "A listed emergency warning sign was detected. "
                "Seek emergency medical help now. Call 108 or 112."
            ),
            "hi": (
                "आपातकालीन खतरे का संकेत मिला है। तुरंत चिकित्सा "
                "सहायता लें। 108 या 112 पर कॉल करें।"
            ),
            "gu": (
                "ઇમરજન્સીનું જોખમી લક્ષણ જણાયું છે. તાત્કાલિક "
                "તબીબી મદદ લો. 108 અથવા 112 પર કોલ કરો."
            ),
        }

        headlines = {
            "en": "Emergency Warning Sign Detected",
            "hi": "आपातकालीन खतरे का संकेत मिला",
            "gu": "ઇમરજન્સીનું જોખમી લક્ષણ જણાયું",
        }

        return {
            "urgency_level": "CRITICAL_EMERGENCY",
            "block_ai_assistant": True,
            "emergency_numbers": emergency_numbers,
            "headline": headlines[lang_code],
            "summary": translations[lang_code],
            "matched_red_flags": matched_rules,
            "clinical_disclaimer": (
                "Automated keyword screening only; not a diagnosis."
            ),
        }

    if not text:
        return {
            "urgency_level": "PRELIMINARY_NON_EMERGENCY",
            "block_ai_assistant": False,
            "emergency_numbers": emergency_numbers,
            "headline": {
                "en": "Describe Your Symptoms",
                "hi": "अपने लक्षण बताएं",
                "gu": "તમારાં લક્ષણો જણાવો",
            }[lang_code],
            "summary": {
                "en": "Describe your symptoms to begin preliminary guidance.",
                "hi": "प्रारंभिक मार्गदर्शन के लिए अपने लक्षण बताएं।",
                "gu": "પ્રારંભિક માર્ગદર્શન માટે તમારાં લક્ષણો જણાવો.",
            }[lang_code],
            "matched_red_flags": [],
            "clinical_disclaimer": (
                "This screening cannot diagnose or rule out illness."
            ),
        }

    # No listed emergency keyword matched.
    # This is NOT the same as confirming that the symptoms are harmless.
    return {
        "urgency_level": "PRELIMINARY_NON_EMERGENCY",
        "block_ai_assistant": False,
        "emergency_numbers": emergency_numbers,
        "headline": {
            "en": "Continue to Symptom Assessment",
            "hi": "लक्षणों का आकलन जारी रखें",
            "gu": "લક્ષણોનું મૂલ્યાંકન ચાલુ રાખો",
        }[lang_code],
        "summary": {
            "en": (
                "No listed emergency keyword was detected. "
                "This does not rule out a serious condition. "
                "Continue to the symptom assessment."
            ),
            "hi": (
                "सूची में कोई आपातकालीन शब्द नहीं मिला। इससे "
                "गंभीर बीमारी की संभावना समाप्त नहीं होती। "
                "लक्षणों का आकलन जारी रखें।"
            ),
            "gu": (
                "યાદીમાં કોઈ ઇમરજન્સી કીવર્ડ મળ્યો નથી. તેથી "
                "ગંભીર બીમારીની શક્યતા નકારી શકાતી નથી. "
                "લક્ષણોનું મૂલ્યાંકન ચાલુ રાખો."
            ),
        }[lang_code],
        "matched_red_flags": [],
        "clinical_disclaimer": (
            "Keyword screening only. Not a diagnosis or a "
            "reliable method of ruling out emergencies."
        ),
    }