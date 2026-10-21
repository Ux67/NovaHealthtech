"""
Nova Healthtech - Cautious AI Health Assistant Service
Connects to Google Gemini Pro with strict non-diagnostic system constraints.
Includes structured fallback when GEMINI_API_KEY is not configured.
"""

import os
from typing import Dict, Any
from google import genai

# Strict System Prompt enforcing non-diagnostic, non-prescriptive safety boundaries
CAUTIOUS_SYSTEM_PROMPT = """
You are the Cautious AI Health Assistant for Nova Healthtech, an accessible preliminary health guidance platform for Indian communities (especially Gujarat and rural areas).

ABSOLUTE SAFETY RULES:
1. NEVER PROVIDE A MEDICAL DIAGNOSIS. Never say "You have [Disease]" or "This is [Condition]". Always frame observations as general educational possibilities that must be evaluated by a qualified doctor.
2. NEVER PRESCRIBE MEDICATIONS OR MODIFY DOSAGES. Do not suggest specific antibiotic regimens, steroids, or prescription drugs. You may only suggest general comfort care (e.g., drinking clean boiled water, resting).
3. EMPHASIZE THE DOCTOR PATHWAY: Conclude by encouraging the user to consult a registered medical practitioner (MBBS/MD) or visit an Ayushman Bharat Health and Wellness Centre / Primary Health Centre (PHC).
4. PREPARATION FOCUS: Provide 2 to 3 clarifying questions the patient can write down to ask their doctor during a physical exam.
5. ZERO-PII RULE: Never ask the user for their Aadhaar number, phone number, address, or OTP.
6. LANGUAGE FIDELITY: You must respond strictly and fluently in the requested language ({lang_name}). Use simple, empathetic, culturally respectful phrasing suited for Indian families.

RESPONSE STRUCTURE (Keep concise and easy to read on mobile):
- Compassionate Acknowledgement (1 sentence).
- Preliminary Health Considerations (2-3 general possibilities to discuss with a physician).
- Practical Questions for Your Doctor (2-3 bullet points).
- Safe Supportive Care (simple rest/hydration measures; no prescription drugs).
- Safety Alert: "If symptoms worsen, high fever persists, or severe pain develops, visit a hospital immediately or call 108."
"""

LANGUAGE_NAMES = {
    "en": "English",
    "gu": "Gujarati (ગુજરાતી)",
    "hi": "Hindi (हिन्दी)",
}


class AIAssistantService:
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.is_configured = bool(self.api_key)

        if self.is_configured:
            self.client = genai.Client(api_key=self.api_key)

    def generate_preliminary_guidance(self, user_message: str, lang: str = "en") -> Dict[str, Any]:
        """
        Generates cautious guidance using Gemini Pro or a safe offline-resilient local fallback.
        """
        lang_code = lang if lang in LANGUAGE_NAMES else "en"
        lang_name = LANGUAGE_NAMES[lang_code]

        # Fallback if developer has not yet set their GEMINI_API_KEY in .env
        if not self.is_configured:
            return self._build_unconfigured_response(user_message, lang_code)

        system_instruction = CAUTIOUS_SYSTEM_PROMPT.format(lang_name=lang_name)

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
                generation_config={
                    "temperature": 0.25,  # Low temperature for factual, cautious, non-speculative responses
                    "top_p": 0.85,
                    "max_output_tokens": 550,
                },
            )

            prompt = (
                f"The user wrote in {lang_name}: '{user_message}'.\n"
                f"Provide cautious preliminary guidance strictly in {lang_name} following your system instructions."
            )

            response = model.generate_content(prompt)
            reply_text = response.text if response and response.text else ""

            if not reply_text:
                return self._build_safe_fallback(lang_code)

            return {
                "source": "gemini_cautious_assistant",
                "model": self.model_name,
                "reply": reply_text.strip(),
                "safety_disclaimer": (
                    "AI-generated preliminary wellness information. "
                    "Not a medical diagnosis or treatment plan. Always consult a qualified doctor."
                ),
            }

        except Exception as e:
            # Graceful error handling (e.g. quota limits, network drops)
            return self._build_safe_fallback(lang_code, error_detail=str(e))

    def _build_unconfigured_response(self, user_message: str, lang_code: str) -> Dict[str, Any]:
        """Safe placeholder response when GEMINI_API_KEY is not yet populated in .env."""
        responses = {
            "en": (
                "Nova AI Assistant Preview: I have received your question regarding: "
                f"'{user_message}'.\n\n"
                "• Preliminary Note: General symptoms like these can stem from multiple everyday or seasonal causes that require a physical exam.\n"
                "• Questions for Your Doctor: 'How long should these symptoms be monitored before testing?' and 'Are there specific foods or activities to avoid?'\n"
                "• Supportive Care: Rest in a well-ventilated room, stay well-hydrated with safe water, and do not self-medicate with unprescribed pharmaceuticals.\n\n"
                "(Note for Developer: Add your GEMINI_API_KEY to your backend .env file to enable live Gemini Pro generation.)"
            ),
            "gu": (
                f"નોવા AI આસિસ્ટન્ટ પ્રિવ્યૂ: તમારા પ્રશ્નની નોંધ લીધી છે: '{user_message}'.\n\n"
                "• પ્રાથમિક માર્ગદર્શન: આવા લક્ષણો સામાન્ય ઋતુગત ફેરફારો અથવા આરામની જરૂરિયાત દર્શાવે છે, જેની તપાસ ડૉક્ટર પાસે કરાવવી જરૂરી છે.\n"
                "• ડૉક્ટરને પૂછવાના પ્રશ્નો: 'આ લક્ષણો માટે કોઈ ચોક્કસ ટેસ્ટ કરાવવાની જરૂર છે?' અને 'ખોરાકમાં શું પરેજી રાખવી?'\n"
                "• સામાન્ય આરામ: પૂરતો આરામ લો, સ્વચ્છ ઉકાળેલું પાણી પીવો અને ડૉક્ટરની સલાહ વગર જાતે દવા લેશો નહીં.\n\n"
                "(ડેવલપર નોંધ: લાઈવ AI માટે .env ફાઇલમાં GEMINI_API_KEY ઉમેરો.)"
            ),
            "hi": (
                f"नोवा AI सहायक पूर्वावलोकन: आपके प्रश्न का संज्ञान लिया गया: '{user_message}'.\n\n"
                "• प्रारंभिक मार्गदर्शन: इस प्रकार के लक्षण कई सामान्य या मौसमी कारणों से हो सकते हैं, जिनकी सटीक पुष्टि डॉक्टर की जांच से ही संभव है।\n"
                "• डॉक्टर से पूछने योग्य प्रश्न: 'क्या इसके लिए किसी जांच की आवश्यकता है?' और 'किन गतिविधियों या आहार से बचना चाहिए?'\n"
                "• सामान्य देखरेख: पर्याप्त आराम करें, साफ व सुरक्षित पानी पिएं और बिना डॉक्टर के पर्चे के कोई दवा न लें।\n\n"
                "(डेवलपर नोट: लाइव AI के लिए .env फ़ाइल में GEMINI_API_KEY दर्ज करें।)"
            ),
        }
        return {
            "source": "local_preview_mode",
            "model": "preview_engine",
            "reply": responses.get(lang_code, responses["en"]),
            "safety_disclaimer": "Local preview mode active. Not clinically validated.",
        }

    def _build_safe_fallback(self, lang_code: str, error_detail: str = "") -> Dict[str, Any]:
        """Safe fallback if the remote AI API encounters network interruptions."""
        fallbacks = {
            "en": (
                "We could not reach the AI service at this moment. If you are experiencing "
                "troubling symptoms, please consult a nearby doctor or visit an Ayushman Bharat PHC. "
                "If you feel severe pain or difficulty breathing, dial 108 immediately."
            ),
            "gu": (
                "આ ક્ષણે AI સર્વિસ સાથે સંપર્ક થઈ શક્યો નથી. જો તમને અસ્વસ્થતા જણાય તો નજીકના સરકારી "
                "પ્રાથમિક આરોગ્ય કેન્દ્ર (PHC) અથવા ડૉક્ટરનો સંપર્ક કરો. જો ગંભીર તકલીફ હોય તો તાત્કાલિક 108 પર કોલ કરો."
            ),
            "hi": (
                "इस समय AI सेवा से संपर्क नहीं हो पा रहा है। यदि आप अस्वस्थ महसूस कर रहे हैं, तो कृपया नजदीकी "
                "स्वास्थ्य केंद्र या डॉक्टर से मिलें। किसी भी गंभीर आपात स्थिति में तुरंत 108 पर कॉल करें।"
            ),
        }
        return {
            "source": "service_fallback",
            "model": "safe_circuit_breaker",
            "reply": fallbacks.get(lang_code, fallbacks["en"]),
            "safety_disclaimer": "Emergency numbers (108 / 112) remain functional.",
        }


# Singleton service instance
ai_assistant = AIAssistantService()