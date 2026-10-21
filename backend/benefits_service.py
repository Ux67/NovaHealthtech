"""
Nova Healthtech - Indian Digital Health & Government Benefits Service
Provides verified scheme information, non-PII preliminary orientation,
official portal directory, and future-ready adapter interfaces for ABDM/PM-JAY.
"""

from typing import Dict, Any, List


class DigitalHealthIntegrationAdapter:
    """
    Future-ready interface for authorized government/insurer integrations (ABDM / NHA PM-JAY).
    In this demonstration prototype, live external government API calls are disabled
    until institutional sandbox credentials and WASA security certification are obtained.
    """

    def __init__(self) -> None:
        self.integration_mode = "local_verified_catalog_only"
        self.abdm_sandbox_connected = False
        self.pmjay_bis_connected = False

    def get_integration_status(self) -> Dict[str, Any]:
        return {
            "mode": self.integration_mode,
            "abdm_m1_m2_m3_enabled": self.abdm_sandbox_connected,
            "pmjay_bis_enabled": self.pmjay_bis_connected,
            "privacy_policy": (
                "Zero-PII architecture active. Government ID numbers, OTPs, "
                "and card scans are never collected or stored by this prototype."
            ),
        }


# Verified catalog of National & Gujarat Health Schemes (with EN, GU, HI translations)
SCHEMES_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "pmjay_ma_gujarat",
        "badge": "Gujarat + National",
        "helpline": "14555 / 1800-233-1022",
        "official_portal_label": "beneficiary.nha.gov.in",
        "official_portal_url": "https://beneficiary.nha.gov.in/",
        "state_portal_label": "ma.gujarat.gov.in",
        "state_portal_url": "https://ma.gujarat.gov.in/",
        "i18n": {
            "en": {
                "title": "Ayushman Bharat PM-JAY & Mukhyamantri Amrutam (PMJAY-MA Gujarat)",
                "coverage": "Up to ₹10 Lakh / family / year in Gujarat (₹5 Lakh national base cover)",
                "summary": (
                    "Integrated cashless secondary and tertiary hospitalization scheme for eligible "
                    "families in Gujarat under SECC criteria, BPL, or MA Vatsalya income rules."
                ),
                "eligibility_notes": (
                    "Covers households listed under PM-JAY SECC data, BPL families, and Gujarat "
                    "MA Vatsalya families (typically annual family income up to ₹4 Lakh, or up to "
                    "₹6 Lakh for families with senior citizens, plus designated frontline workers)."
                ),
                "documents_to_carry": [
                    "Government Identity Proof (brought directly to official kiosk/hospital; never enter on Nova)",
                    "Ration Card / Family Proof of Residence in Gujarat",
                    "Valid Income Certificate (from Mamlatdar/TDO/Collector for MA Vatsalya) or BPL proof",
                ],
                "action_guidance": (
                    "Check official beneficiary status on beneficiary.nha.gov.in or visit a Civic Centre, "
                    "Taluka kiosk, or an empanelled hospital's Arogya Mitra / Ayushman Mitra desk."
                ),
            },
            "gu": {
                "title": "આયુષ્માન ભારત PM-JAY અને મુખ્યમંત્રી અમૃતમ (PMJAY-MA ગુજરાત)",
                "coverage": "ગુજરાતમાં પરિવાર દીઠ વાર્ષિક ₹10 લાખ સુધીની કેશલેસ સારવાર (રાષ્ટ્રીય ધોરણે ₹5 લાખ)",
                "summary": (
                    "ગુજરાતના પાત્રતા ધરાવતા પરિવારો માટે સરકારી અને માન્ય ખાનગી હોસ્પિટલોમાં ગંભીર બીમારીઓ "
                    "અને ઓપરેશન માટે કેશલેસ હોસ્પિટલ સારવાર."
                ),
                "eligibility_notes": (
                    "PM-JAY યાદીમાં સમાવિષ્ટ પરિવારો, BPL કાર્ડ ધારકો, અને મા વાત્સલ્ય હેઠળ વાર્ષિક ₹4 લાખ "
                    "સુધીની આવક ધરાવતા પરિવારો (સિનિયર સિટીઝન ધરાવતા પરિવારો માટે ₹6 લાખ સુધીની મર્યાદા)."
                ),
                "documents_to_carry": [
                    "સરકારી ઓળખનો પુરાવો (ફક્ત સત્તાવાર સેન્ટર કે હોસ્પિટલ ખાતે બતાવવો; અહીં દાખલ કરવો નહીં)",
                    "રેશન કાર્ડ / રહેઠાણનો પુરાવો",
                    "મામલતદાર / TDO દ્વારા પ્રમાણિત આવકનો દાખલો (મા વાત્સલ્ય માટે)",
                ],
                "action_guidance": (
                    " સત્તાવાર વેબસાઇટ beneficiary.nha.gov.in પર પાત્રતા તપાસો અથવા નજીકની સરકારી હોસ્પિટલના "
                    "'આરોગ્ય મિત્ર' / 'આયુષ્માન મિત્ર' ડેસ્કનો સંપર્ક કરો."
                ),
            },
            "hi": {
                "title": "आयुष्मान भारत PM-JAY एवं मुख्यमंत्री अमृतम (PMJAY-MA गुजरात)",
                "coverage": "गुजरात में प्रति परिवार ₹10 लाख प्रति वर्ष तक कैशलेस उपचार (राष्ट्रीय स्तर पर ₹5 लाख)",
                "summary": (
                    "पात्र परिवारों के लिए सूचीबद्ध सरकारी और निजी अस्पतालों में गंभीर बीमारियों और सर्जरी "
                    "के लिए निःशुल्क कैशलेस भर्ती एवं उपचार।"
                ),
                "eligibility_notes": (
                    "PM-JAY सूची में शामिल परिवार, BPL परिवार, और गुजरात मा वात्सल्य के तहत ₹4 लाख तक की "
                    "वार्षिक आय वाले परिवार (वरिष्ठ नागरिकों वाले परिवारों के लिए ₹6 लाख तक) पात्र हो सकते हैं।"
                ),
                "documents_to_carry": [
                    "सरकारी पहचान पत्र (केवल आधिकारिक केंद्र या अस्पताल में दिखाएं; इस ऐप में दर्ज न करें)",
                    "राशन कार्ड / निवास प्रमाण पत्र",
                    "सक्षम अधिकारी (मामलातदार/TDO) द्वारा जारी आय प्रमाण पत्र",
                ],
                "action_guidance": (
                    "आधिकारिक पोर्टल beneficiary.nha.gov.in पर स्थिति जांचें या सूचीबद्ध अस्पताल के "
                    "'आरोग्य मित्र' / 'आयुष्मान मित्र' सहायता केंद्र पर जाएं।"
                ),
            },
        },
    },
    {
        "id": "ayushman_vay_vandana",
        "badge": "Senior Citizens 70+",
        "helpline": "14555",
        "official_portal_label": "beneficiary.nha.gov.in (Vay Vandana)",
        "official_portal_url": "https://beneficiary.nha.gov.in/",
        "state_portal_label": "Official Ayushman App Info",
        "state_portal_url": "https://pmjay.gov.in/",
        "i18n": {
            "en": {
                "title": "Ayushman Vay Vandana Card (Senior Citizens 70+)",
                "coverage": "Up to ₹5 Lakh / year (Universal for age 70+, no income limit)",
                "summary": (
                    "Dedicated cashless hospitalization cover for all Indian citizens aged 70 years and "
                    "above, regardless of household income or economic status."
                ),
                "eligibility_notes": (
                    "Every Indian citizen aged 70 years or older is eligible. There is NO income limit. "
                    "Pre-existing conditions are covered from Day 1. Seniors in existing PM-JAY families "
                    "receive an additional ₹5 Lakh top-up cover."
                ),
                "documents_to_carry": [
                    "Official Government Age & Identity Proof (verify only on official NHA portal/app)",
                    "Active Mobile Number for official NHA portal verification",
                ],
                "action_guidance": (
                    "Enrol directly through the official 'Ayushman App' or on beneficiary.nha.gov.in "
                    "using the dedicated Senior Citizen 70+ enrollment option, or visit an empanelled hospital."
                ),
            },
            "gu": {
                "title": "આયુષ્માન વય વંદના કાર્ડ (70+ વર્ષના વરિષ્ઠ નાગરિકો માટે)",
                "coverage": "વાર્ષિક ₹5 લાખ સુધીનું કેશલેસ કવર (આવકની કોઈ મર્યાદા નથી)",
                "summary": (
                    "70 વર્ષ કે તેથી વધુ ઉંમરના તમામ ભારતીય નાગરિકો માટે આવકના કોઈપણ નિયમ વિના મફત "
                    "હોસ્પિટલ સારવાર યોજના."
                ),
                "eligibility_notes": (
                    "70 વર્ષ કે તેથી વધુ ઉંમરના દરેક નાગરિક પાત્ર છે (ગરીબ, મધ્યમ વર્ગ કે સુખી પરિવાર). "
                    "પહેલાથી રહેલી બીમારીઓ પ્રથમ દિવસથી જ આવરી લેવાય છે."
                ),
                "documents_to_carry": [
                    "ઉંમર અને ઓળખનો માન્ય સરકારી પુરાવો (ફક્ત સત્તાવાર પોર્ટલ પર જ ચકાસણી કરવી)",
                    "મોબાઇલ નંબર (સત્તાવાર પોર્ટલ લોગિન માટે)",
                ],
                "action_guidance": (
                    "સત્તાવાર 'Ayushman App' અથવા beneficiary.nha.gov.in પર 70+ સિનિયર સિટીઝન વિભાગમાં "
                    "નોંધણી કરો અથવા નજીકના CSC / હોસ્પિટલ ડેસ્કની મુલાકાત લો."
                ),
            },
            "hi": {
                "title": "आयुष्मान वय वंदना कार्ड (70+ वर्ष के वरिष्ठ नागरिक)",
                "coverage": "₹5 लाख प्रति वर्ष तक कैशलेस कवर (आय की कोई सीमा नहीं)",
                "summary": (
                    "70 वर्ष या उससे अधिक आयु के सभी भारतीय नागरिकों के लिए बिना किसी आय सीमा के "
                    "निःशुल्क कैशलेस अस्पताल उपचार कवरेज।"
                ),
                "eligibility_notes": (
                    "70 वर्ष या अधिक आयु के सभी भारतीय नागरिक पात्र हैं—चाहे उनकी आय कुछ भी हो। "
                    "पुरानी बीमारियां पहले दिन से ही कवर होती हैं।"
                ),
                "documents_to_carry": [
                    "आयु और पहचान का आधिकारिक सरकारी प्रमाण (केवल आधिकारिक NHA पोर्टल पर उपयोग करें)",
                    "सक्रिय मोबाइल नंबर",
                ],
                "action_guidance": (
                    "आधिकारिक 'Ayushman App' या beneficiary.nha.gov.in के माध्यम से पंजीकरण करें, "
                    "अथवा नजदीकी CSC या सूचीबद्ध अस्पताल की सहायता लें।"
                ),
            },
        },
    },
    {
        "id": "abha_digital_health_id",
        "badge": "ABDM Digital Health",
        "helpline": "1800-11-4477 / 14477",
        "official_portal_label": "abha.abdm.gov.in",
        "official_portal_url": "https://abha.abdm.gov.in/",
        "state_portal_label": "abdm.gov.in",
        "state_portal_url": "https://abdm.gov.in/",
        "i18n": {
            "en": {
                "title": "ABHA (Ayushman Bharat Health Account)",
                "coverage": "14-Digit Voluntary Digital Health Identity & Consent-Based Health Locker",
                "summary": (
                    "Creates a unified digital health address (e.g., name@abdm) so you can link, view, "
                    "and share lab reports, prescriptions, and discharge summaries with doctors strictly "
                    "with your explicit consent."
                ),
                "eligibility_notes": (
                    "Voluntary and free for every resident in India. NOTE: An ABHA account is a digital "
                    "health record identity—it is NOT an insurance policy by itself, though it links "
                    "with PM-JAY and hospital records."
                ),
                "documents_to_carry": [
                    "Active Mobile Number or Driving Licence / Official ID (used only on abha.abdm.gov.in)",
                ],
                "action_guidance": (
                    "Create or manage your ABHA card exclusively at abha.abdm.gov.in or scan the ABDM "
                    "QR code at participating hospitals for fast OPD registration."
                ),
            },
            "gu": {
                "title": "ABHA (આયુષ્માન ભારત હેલ્થ એકાઉન્ટ)",
                "coverage": "14-અંકની ડિજિટલ હેલ્થ ઓળખ અને મેડિકલ રેકોર્ડ લોકર",
                "summary": (
                    "તમારા મેડિકલ રિપોર્ટ્સ, પ્રિસ્ક્રિપ્શન અને હોસ્પિટલની વિગતો ડિજિટલ રીતે સાચવવા અને તમારી "
                    "મંજૂરીથી ડોક્ટર સાથે શેર કરવા માટેનું સત્તાવાર ખાતું."
                ),
                "eligibility_notes": (
                    "ભારતના દરેક નાગરિક માટે સ્વૈચ્છિક અને મફત. નોંધ: ABHA કાર્ડ એ મેડિકલ રેકોર્ડ માટેની ઓળખ છે, "
                    "તે પોતે વીમા પોલિસી નથી (વીમા લાભ માટે PMJAY-MA કાર્ડ જરૂરી છે)."
                ),
                "documents_to_carry": [
                    "મોબાઇલ નંબર અથવા ડ્રાઇવિંગ લાયસન્સ / સરકારી ઓળખ (ફક્ત abha.abdm.gov.in પર વાપરવા માટે)",
                ],
                "action_guidance": (
                    "તમારું ABHA કાર્ડ બનાવવા માટે સત્તાવાર વેબસાઇટ abha.abdm.gov.in નો ઉપયોગ કરો."
                ),
            },
            "hi": {
                "title": "ABHA (आयुष्मान भारत हेल्थ अकाउंट)",
                "coverage": "14-अंकीय डिजिटल स्वास्थ्य पहचान और सहमति-आधारित रिकॉर्ड लॉकर",
                "summary": (
                    "अपनी जांच रिपोर्ट, डॉक्टर के पर्चे और डिस्चार्ज समरी को सुरक्षित रूप से डिजिटल रूप में "
                    "जोड़ने और अपनी सहमति से डॉक्टरों के साथ साझा करने की सुविधा।"
                ),
                "eligibility_notes": (
                    "सभी नागरिकों के लिए स्वैच्छिक और निःशुल्क। ध्यान दें: ABHA एक डिजिटल स्वास्थ्य पहचान है, "
                    "यह स्वयं बीमा कार्ड नहीं है।"
                ),
                "documents_to_carry": [
                    "मोबाइल नंबर या ड्राइविंग लाइसेंस / आधिकारिक पहचान (केवल abha.abdm.gov.in पर उपयोग हेतु)",
                ],
                "action_guidance": (
                    "केवल आधिकारिक पोर्टल abha.abdm.gov.in पर जाकर अपना ABHA खाता बनाएं या डाउनलोड करें।"
                ),
            },
        },
    },
]


# Curated Offline-Capable Directory of Major Public Empanelled Hospitals in Gujarat
# Users are directed to https://hem.nha.gov.in/search for the live nationwide list.
GUJARAT_HOSPITAL_DIRECTORY: List[Dict[str, str]] = [
    {
        "name": "Sir Takhtsinhji General Hospital (Civil Hospital)",
        "district": "Bhavnagar",
        "type": "Government Medical College & Civil Hospital",
        "schemes": "PMJAY-MA, Ayushman Vay Vandana, ABDM Enabled",
        "helpdesk": "Arogya Mitra Desk - Main OPD & Emergency Block, Jail Road, Bhavnagar",
        "emergency_phone": "108 / 14555",
    },
    {
        "name": "B.J. Medical College & Civil Hospital (Asarwa)",
        "district": "Ahmedabad",
        "type": "Government Tertiary Care & Super-Specialty Campus",
        "schemes": "PMJAY-MA, Ayushman Vay Vandana, U.N. Mehta Cardiology / GCRI Oncology",
        "helpdesk": "PMJAY-MA Helpdesk - Trauma & OPD Block, Asarwa, Ahmedabad",
        "emergency_phone": "108 / 14555",
    },
    {
        "name": "Sola Civil Hospital (GMERS Medical College Hospital)",
        "district": "Ahmedabad",
        "type": "Government GMERS Hospital",
        "schemes": "PMJAY-MA, Ayushman Vay Vandana, ABDM Scan & Share",
        "helpdesk": "Ground Floor Registration & Arogya Mitra Counter, S.G. Highway, Ahmedabad",
        "emergency_phone": "108 / 14555",
    },
    {
        "name": "Pandit Deendayal Upadhyay (PDU) Civil Hospital",
        "district": "Rajkot",
        "type": "Government Tertiary Teaching Hospital",
        "schemes": "PMJAY-MA, Ayushman Vay Vandana, ABDM Enabled",
        "helpdesk": "PMJAY-MA Counter, Hospital Chowk, Rajkot",
        "emergency_phone": "108 / 14555",
    },
    {
        "name": "Sir Sayajirao General (SSG) Hospital",
        "district": "Vadodara",
        "type": "Government Tertiary Teaching Hospital",
        "schemes": "PMJAY-MA, Ayushman Vay Vandana, ABDM Enabled",
        "helpdesk": "Arogya Mitra Helpdesk, Anandpura, Vadodara",
        "emergency_phone": "108 / 14555",
    },
    {
        "name": "New Civil Hospital (Majura Gate)",
        "district": "Surat",
        "type": "Government Tertiary Teaching Hospital",
        "schemes": "PMJAY-MA, Ayushman Vay Vandana, ABDM Enabled",
        "helpdesk": "PMJAY-MA Helpdesk, Majura Gate, Surat",
        "emergency_phone": "108 / 14555",
    },
]


def evaluate_preliminary_guidance(
    age_group: str,
    state_residency: str,
    income_bracket: str,
    has_senior_70_plus: bool,
) -> Dict[str, Any]:
    """
    Deterministic, Zero-PII preliminary orientation engine.
    Evaluates general household categories without collecting IDs, names, or financial records.
    """
    recommended_schemes: List[Dict[str, str]] = []

    # 1. Universal Senior Citizen 70+ Check (Ayushman Vay Vandana)
    if age_group == "70_plus" or has_senior_70_plus:
        recommended_schemes.append(
            {
                "scheme_id": "ayushman_vay_vandana",
                "title": "Ayushman Vay Vandana Card (Senior Citizens 70+)",
                "match_level": "High Preliminary Match (Age-Based Universal Cover)",
                "reason": (
                    "All Indian citizens aged 70 or older qualify for up to ₹5 Lakh/year "
                    "cashless hospitalization regardless of household income."
                ),
                "next_step": (
                    "Verify age on the official beneficiary.nha.gov.in portal or the official "
                    "Ayushman mobile app, or visit an empanelled hospital helpdesk."
                ),
            }
        )

    # 2. Gujarat PMJAY-MA & MA Vatsalya Check
    if state_residency == "gujarat":
        if income_bracket in ("bpl_secc", "under_4_lakh"):
            recommended_schemes.append(
                {
                    "scheme_id": "pmjay_ma_gujarat",
                    "title": "PMJAY-MA / Mukhyamantri Amrutam Vatsalya (Gujarat)",
                    "match_level": "Strong Preliminary Match (Income / Category Criteria)",
                    "reason": (
                        "Families in Gujarat under BPL/SECC criteria or with verified annual family "
                        "income up to ₹4 Lakh generally qualify for up to ₹10 Lakh/year family cover."
                    ),
                    "next_step": (
                        "Take your Ration Card and Mamlatdar/TDO Income Certificate to a Taluka kiosk, "
                        "Civic Centre, or hospital Arogya Mitra desk for official verification."
                    ),
                }
            )
        elif income_bracket == "4_to_6_lakh" and (age_group == "60_to_69" or age_group == "70_plus" or has_senior_70_plus):
            recommended_schemes.append(
                {
                    "scheme_id": "pmjay_ma_gujarat",
                    "title": "PMJAY-MA Vatsalya (Gujarat Senior Citizen Family Clause)",
                    "match_level": "Possible Preliminary Match (Verify Senior Family Income Clause)",
                    "reason": (
                        "Gujarat MA Vatsalya rules include provisions for families with senior citizens "
                        "having annual household income up to ₹6 Lakh."
                    ),
                    "next_step": (
                        "Confirm current income certificate rules at ma.gujarat.gov.in or your nearest "
                        "Government Hospital Arogya Mitra counter."
                    ),
                }
            )
    else:
        # Other Indian States
        if income_bracket == "bpl_secc":
            recommended_schemes.append(
                {
                    "scheme_id": "pmjay_ma_gujarat",
                    "title": "Ayushman Bharat PM-JAY (National Scheme)",
                    "match_level": "Preliminary Match (SECC / State NFSA Criteria)",
                    "reason": (
                        "Households listed in the SECC database or eligible state ration categories "
                        "qualify for ₹5 Lakh/year cashless hospitalization nationwide."
                    ),
                    "next_step": "Check your family listing at beneficiary.nha.gov.in or call 14555.",
                }
            )

    # 3. ABHA Digital Health Account (Universal for all Indian residents)
    recommended_schemes.append(
        {
            "scheme_id": "abha_digital_health_id",
            "title": "ABHA (Ayushman Bharat Health Account)",
            "match_level": "Eligible (Voluntary for All Residents)",
            "reason": (
                "Every citizen can create a free 14-digit ABHA digital health ID to organize lab "
                "reports and prescriptions safely with consent."
            ),
            "next_step": "Create voluntarily at abha.abdm.gov.in (Note: ABHA is a health ID, not insurance).",
        }
    )

    return {
        "disclaimer": (
            "IMPORTANT: This is general informational guidance only, NOT official government confirmation "
            "or hospital pre-authorization. Final eligibility is verified solely by NHA/State authorities "
            "or an authorized hospital's Ayushman Mitra / Arogya Mitra desk."
        ),
        "recommendations": recommended_schemes,
    }