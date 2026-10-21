"""
Nova Healthtech - Offline Essential Health Guide Service
Evidence-based, non-prescriptive preliminary first-aid and home-care protocols.
Provides full offline-capable translations for English, Gujarati, and Hindi.
"""

from typing import Dict, Any, List

HEALTH_GUIDE_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "ors_dehydration",
        "category": "hydration_gastro",
        "emergency_warning": False,
        "i18n": {
            "en": {
                "title": "Severe Dehydration & Home ORS Preparation",
                "summary": "Step-by-step guidance for replacing vital body fluids lost to diarrhea, vomiting, or extreme heat.",
                "key_steps": [
                    "Wash hands thoroughly with soap and clean water before preparing fluids.",
                    "Clean Water Base: Measure exactly 1 Liter of safe drinking water (boiled and cooled if possible).",
                    "Home Solution Ratio: Stir in 6 level teaspoons of clean sugar and 1/2 level teaspoon of salt until completely dissolved.",
                    "If using standard WHO-ORS packets: Mix the entire packet into exactly 1 Liter of clean water (do not dilute in milk, juice, or less water).",
                    "Administration: Give small, frequent sips using a clean spoon or cup. Do not rush.",
                ],
                "warning": "If the person cannot drink, becomes unusually drowsy, or passes blood in stool, visit the nearest PHC or call 108 immediately.",
            },
            "gu": {
                "title": "ગંભીર ડિહાઇડ્રેશન અને ઘરે ORS (જીવનરક્ષક દ્રાવણ) બનાવવાની રીત",
                "summary": "ઝાડા, ઉલટી અથવા અતિશય ગરમીમાં શરીરમાં ઘટી ગયેલા ક્ષાર અને પાણીની તાત્કાલિક પૂર્તિ માટેનું માર્ગદર્શન.",
                "key_steps": [
                    "દ્રાવણ બનાવતા પહેલા હાથ સાબુ અને સ્વચ્છ પાણીથી બરાબર ધોવા.",
                    "પીવાનું પાણી: ૧ લીટર સ્વચ્છ, ઉકાળીને ઠંડુ કરેલું પાણી લો.",
                    "ઘરેલું પ્રમાણ: ૧ લીટર પાણીમાં ૬ નાની ચમચી ખાંડ અને અડધી નાની ચમચી મીઠું ઉમેરી ઓગાળી લો.",
                    "જો સરકારી ORS પેકેટ હોય: આખું પેકેટ બરાબર ૧ લીટર પાણીમાં જ ઓગાળવું (દૂધ કે રસમાં ભેળવવું નહીં).",
                    "આપવાની રીત: દર્દીને ચમચી અથવા નાની વાટકી વડે ધીમે ધીમે થોડા થોડા સમયે પીવડાવવું.",
                ],
                "warning": "જો દર્દી પાણી પી ન શકે, આંખો ઊંડી ઊતરી જાય કે બેભાન જેવો જણાય, તો તરત જ નજીકના સરકારી દવાખાને (PHC) લઈ જાઓ.",
            },
            "hi": {
                "title": "गंभीर निर्जलीकरण (Dehydration) और ओआरएस (ORS) बनाने की विधि",
                "summary": "दस्त, उल्टी या अत्यधिक गर्मी में शरीर में पानी और आवश्यक लवणों की कमी को सुरक्षित रूप से पूरा करने का तरीका।",
                "key_steps": [
                    "घोल तैयार करने से पहले अपने हाथों को साबुन और साफ पानी से अच्छी तरह धोएं।",
                    "स्वच्छ पानी: १ लीटर पीने योग्य (उबला हुआ और ठंडा किया गया) पानी लें।",
                    "घरेलू अनुपात: १ लीटर पानी में ६ छोटी चम्मच चीनी और आधा छोटा चम्मच नमक डालकर पूरी तरह घोलें।",
                    "यदि सरकारी ORS पैकेट उपलब्ध हो: पूरे पैकेट को ठीक १ लीटर साफ पानी में ही मिलाएं।",
                    "देने की विधि: रोगी को चम्मच या कप से थोड़े-थोड़े अंतराल पर धीरे-धीरे घूंट-घूंट करके पिलाएं।",
                ],
                "warning": "यदि रोगी कुछ भी पी न सके, अत्यधिक सुस्त हो जाए या मल में खून आए, तो तुरंत नजदीकी स्वास्थ्य केंद्र ले जाएं या 108 पर कॉल करें।",
            },
        },
    },
    {
        "id": "heatstroke_exhaustion",
        "category": "environmental",
        "emergency_warning": True,
        "i18n": {
            "en": {
                "title": "Heat Exhaustion & Sunstroke (Summer Care)",
                "summary": "Critical first-aid cooling protocol during severe summer heatwaves in Gujarat and central India.",
                "key_steps": [
                    "Immediate Relocation: Move the affected person to a cool, shaded area or an air-conditioned room immediately.",
                    "Airflow & Clothing: Loosen or remove tight outer clothing; turn on fans or fan them vigorously.",
                    "Active Cooling: Sponge their skin with cool (not freezing) water, focusing on neck, armpits, and groin where major blood vessels pass.",
                    "Oral Hydration: If the person is conscious and able to swallow, offer sips of cool water or ORS. Never force liquids into an unconscious person.",
                ],
                "warning": "If body temperature exceeds 104°F (40°C), skin is hot and dry without sweat, or mental confusion occurs, this is life-threatening Sunstroke. Dial 108 immediately.",
            },
            "gu": {
                "title": "લૂ લાગવી (હીટસ્ટ્રોક) અને અતિશય ગરમીમાં પ્રાથમિક સારવાર",
                "summary": "ગુજરાતના ઉનાળામાં સખત ગરમી અને લૂ સામે દર્દીનું શરીર ઠંડુ રાખવા માટેના તાત્કાલિક પગલાં.",
                "key_steps": [
                    "તરત જ છાંયડામાં લઈ જાઓ: દર્દીને તાત્કાલિક તડકામાંથી હટાવી ઠંડી જગ્યા કે પંખા નીચે સુવડાવો.",
                    "કપડાં ઢીલા કરો: ચુસ્ત કપડાં ઢીલા કરો જેથી શરીરની ગરમી બહાર નીકળી શકે.",
                    "શરીર ઠંડુ કરો: સામાન્ય ઠંડા પાણીમાં કપડું પલાળી ગળા, બગલ અને પગના સાંધા પર પોતાં મૂકો (બરફનું પાણી વાપરવું નહીં).",
                    "પાણી આપવું: જો દર્દી ભાનમાં હોય તો જ ધીમે ધીમે પાણી, છાશ કે ORS પીવડાવો.",
                ],
                "warning": "જો દર્દી ખૂબ ગરમ હોય, પરસેવો બંધ થઈ ગયો હોય અથવા બેભાન થાય, તો આ ગંભીર લૂ (Sunstroke) છે. તાત્કાલિક 108 બોલાવો.",
            },
            "hi": {
                "title": "लू लगना (Heatstroke) और अत्यधिक गर्मी में प्राथमिक उपचार",
                "summary": "गर्मी के मौसम में लू और तेज बुखार जैसी स्थिति में शरीर का तापमान सुरक्षित रूप से घटाने के निर्देश।",
                "key_steps": [
                    "छाया में ले जाएं: प्रभावित व्यक्ति को तुरंत धूप से हटाकर ठंडे और हवादार स्थान पर लिटाएं।",
                    "कपड़े ढीले करें: तंग कपड़े खोलें और पंखा चलाकर ताजी हवा आने दें।",
                    "शरीर को ठंडा करें: सामान्य ठंडे पानी की पट्टियां गर्दन, बगल और माथे पर रखें।",
                    "तरल पदार्थ: यदि व्यक्ति पूरी तरह होश में है, तो उसे धीरे-धीरे ठंडा पानी, छाछ या ओआरएस पिलाएं।",
                ],
                "warning": "यदि शरीर का तापमान बहुत तेज हो, पसीना आना बंद हो जाए या भ्रम/बेहोशी हो, तो तुरंत 108 एम्बुलेंस को कॉल करें।",
            },
        },
    },
    {
        "id": "burns_first_aid",
        "category": "trauma",
        "emergency_warning": False,
        "i18n": {
            "en": {
                "title": "First Aid for Thermal & Kitchen Burns",
                "summary": "Safe wound management for minor scalds and burns to prevent infection and tissue damage.",
                "key_steps": [
                    "Cool Running Water: Gently run cool tap water over the burn for 10 to 20 minutes. Do not use freezing ice.",
                    "Remove Constricting Items: Gently take off rings, bangles, or watches before swelling begins.",
                    "Do NOT Apply Home Pastes: Never apply toothpaste, turmeric, butter, oil, or cow dung—these trap heat and cause serious bacterial infections.",
                    "Protect the Blister: Do not burst or pop blisters. Cover loosely with a clean, sterile cloth or dry gauze.",
                ],
                "warning": "Seek emergency medical care at a hospital if burns cover the face, hands, joints, or groin, or if the burn was caused by chemicals or electricity.",
            },
            "gu": {
                "title": "દાઝી જવા પર (બર્ન ઇજા) પ્રાથમિક ઉપચાર",
                "summary": "રસોડામાં કે ગરમ પાણી/તેલથી દાઝી જવા પર ચેપ અટકાવવા અને ત્વચાના રક્ષણ માટેની સાચી પદ્ધતિ.",
                "key_steps": [
                    "સામાન્ય વહેતું પાણી: દાઝેલા ભાગ પર તાત્કાલિક ૧૦ થી ૨૦ મિનિટ સુધી નળનું સામાન્ય પાણી વહેવા દો (બરફ મૂકવો નહીં).",
                    "દાગીના ઉતારવા: સોજો આવે તે પહેલાં વીંટી, બંગડી કે ઘડિયાળ સાવચેતીપૂર્વક ઉતારી લો.",
                    "ઘરેલું લેપ ક્યારેય ન લગાવો: દાઝેલા ભાગ પર ટૂથપેસ્ટ, હળદર, તેલ કે ઘી ક્યારેય ચોપડવું નહીં; આનાથી ગંભીર ઇન્ફેક્શન થાય છે.",
                    "ફોલ્લા ફોડવા નહીં: ચામડી પર પડેલા ફોલ્લા ક્યારેય ફોડવા નહીં. તેના પર સ્વચ્છ સુતરાઉ કપડું ઢાંકો.",
                ],
                "warning": "જો મોઢું, હાથ કે ગુપ્તાંગ પર દાઝ્યું હોય અથવા કેમિકલ/કરંટથી દાઝ્યા હોવ, તો તરત જ સિવિલ હોસ્પિટલ પહોંચો.",
            },
            "hi": {
                "title": "जलने पर (Burns) सही प्राथमिक उपचार",
                "summary": "आग, गर्म पानी या तेल से जलने पर संक्रमण रोकने और घाव की सुरक्षा के सुरक्षित नियम।",
                "key_steps": [
                    "बहता सामान्य पानी: जले हुए स्थान पर तुरंत १० से २० मिनट तक नल का सामान्य पानी डालें (बर्फ न लगाएं)।",
                    "गहने हटाएं: सूजन आने से पहले अंगूठी, कड़े या घड़ी को सावधानी से निकाल लें।",
                    "घरेलू चीजें न लगाएं: घाव पर टूथपेस्ट, हल्दी, तेल या घी कभी न लगाएं; इससे गंभीर बैक्टीरिया संक्रमण हो सकता है।",
                    "छाले न फोड़ें: त्वचा पर बने छालों को बिल्कुल न फोड़ें। घाव को साफ, सूखे कपड़े से ढीला ढकें।",
                ],
                "warning": "यदि चेहरा, हाथ या बड़ा हिस्सा जला हो, या करंट/रसायन से चोट लगी हो, तो तुरंत अस्पताल जाएं।",
            },
        },
    },
    {
        "id": "snakebite_first_aid",
        "category": "toxicology",
        "emergency_warning": True,
        "i18n": {
            "en": {
                "title": "Snakebite & Poisonous Stings (Life-Saving Protocols)",
                "summary": "Vital dos and don'ts for rural communities to ensure anti-venom reaches the victim in time.",
                "key_steps": [
                    "Keep Calm & Still: Immobilize the victim. Anxiety and physical movement speed up venom distribution through the lymphatic system.",
                    "Splint the Limb: Keep the bitten arm or leg straight and below heart level, exactly like a fractured limb.",
                    "Remove Jewelry: Remove rings, anklets, and tight shoes before swelling begins.",
                    "Transport Immediately: Dial 108 to transport the victim to the nearest Civil or Sub-District Hospital with Anti-Snake Venom (ASV).",
                ],
                "warning": "STRICT PROHIBITION: Never cut the bite marks, never suck venom, never apply tight rope tourniquets, and never waste time on faith healing or village sorcery.",
            },
            "gu": {
                "title": "સર્પદંશ (સાપ કરડવો) - જીવનરક્ષક સાવચેતી અને નિયમો",
                "summary": "ગ્રામીણ વિસ્તારોમાં સાપ કરડવાના કિસ્સામાં એન્ટી-વેનમ સારવાર સમયસર મેળવવા માટે શું કરવું અને શું ન કરવું.",
                "key_steps": [
                    "દર્દીને શાંત અને સ્થિર રાખો: દર્દીને બિલકુલ હલનચલન કરવા દેશો નહીં. દોડાદોડ કરવાથી ઝેર શરીરમાં ઝડપથી ફેલાય છે.",
                    "અંગ સ્થિર કરો: કરડેલા હાથ કે પગને હાડકું ભાંગ્યું હોય તેમ લાકડી કે પાટિયાનો ટેકો આપી હૃદયના સ્તરથી નીચે સ્થિર રાખો.",
                    "દાગીના કાઢી લો: સોજો ચડે તે પહેલાં કડલાં, ઝાંઝરી કે વીંટી ઉતારી લો.",
                    "તાત્કાલિક હોસ્પિટલ પહોંચો: એન્ટી-સ્નેક વેનમ (ASV) ઇન્જેક્શન ધરાવતી નજીકની સરકારી સિવિલ હોસ્પિટલ જવા માટે 108 બોલાવો.",
                ],
                "warning": "સખત મનાઈ: ઘા પર કાપો મૂકવો નહીં, મોંથી ઝેર ચૂસવું નહીં, દોરીથી કચકચાવીને બાંધવું નહીં અને ભુવા કે ઝાડ-ફૂંકમાં કિંમતી સમય બગાડવો નહીં.",
            },
            "hi": {
                "title": "सर्पदंश (सांप का काटना) - जीवन रक्षक नियम",
                "summary": "ग्रामीण क्षेत्रों में सर्पदंश की स्थिति में समय पर एंटी-वेनम उपचार प्राप्त करने के लिए महत्वपूर्ण निर्देश।",
                "key_steps": [
                    "रोगी को शांत और स्थिर रखें: घबराहट और चलने-फिरने से जहर पूरे शरीर में तेजी से फैलता है। रोगी को बिल्कुल स्थिर रखें।",
                    "अंग को सहारा दें: काटे गए हाथ या पैर को दिल के स्तर से नीचे रखें और लकड़ी की खपच्ची से स्थिर करें।",
                    "गहने तुरंत उतारें: सूजन आने से पहले अंगूठी, पायल और तंग जूते निकाल लें।",
                    "तुरंत अस्पताल ले जाएं: एंटी-स्नेक वेनम (ASV) इंजेक्शन वाले नजदीकी सरकारी अस्पताल पहुंचने के लिए तुरंत 108 बुलाएं।",
                ],
                "warning": "सख्त चेतावनी: घाव पर चीरा न लगाएं, मुंह से जहर न चूसें, रस्सी से बहुत कसकर न बांधें और झाड़-फूंक में समय बिल्कुल न गंवाएं।",
            },
        },
    },
]


def get_health_guides(lang: str = "en") -> Dict[str, Any]:
    """Returns curated health guide entries localized to the specified language."""
    target_lang = lang if lang in ("en", "gu", "hi") else "en"
    result = []

    for item in HEALTH_GUIDE_CATALOG:
        loc = item["i18n"].get(target_lang, item["i18n"]["en"])
        result.append(
            {
                "id": item["id"],
                "category": item["category"],
                "emergency_warning": item["emergency_warning"],
                "title": loc["title"],
                "summary": loc["summary"],
                "key_steps": loc["key_steps"],
                "warning": loc["warning"],
            }
        )

    return {
        "status": "ok",
        "language": target_lang,
        "count": len(result),
        "guides": result,
    }