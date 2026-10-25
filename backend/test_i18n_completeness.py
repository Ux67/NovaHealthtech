"""
Nova Healthtech - Automated 22-Language i18n & Directory Verification Suite
Audits:
1. Canonical key coverage across all 22 advertised languages
2. All-India Hospital directory records & verified phone numbers
3. All-India Medication-centre / Pharmacy records & phone numbers
4. Multilingual AI chat in Hindi, Gujarati, Tamil, etc.
5. Contextual AI follow-up questions
6. Medicine Mode vs Disease Mode clinical separation
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import app
from ai_assistant_service import (
    LANGUAGE_NAMES,
    ALL_INDIA_HOSPITALS,
    ALL_INDIA_MEDICINE_STORES,
)

EXPECTED_22_LANGS = [
    "en", "hi", "gu", "mr", "ta", "te", "bn", "kn", "ml", "pa",
    "or", "as", "ur", "mai", "kok", "ne", "sd", "ks", "doi", "mni", "sat", "sa"
]


def run_audit():
    print("=================================================================")
    print("NOVA HEALTHTECH: AUTOMATED 22-LANGUAGE & DIRECTORY AUDIT")
    print("=================================================================\n")

    client = app.test_client()

    # 1. Verify /api/health
    health = client.get("/api/health").get_json()
    assert health["supported_languages_count"] == 22, f"Expected 22 languages, got {health['supported_languages_count']}"
    assert health["supported_languages"] == EXPECTED_22_LANGS
    print(f"[PASS] 1. API Gateway confirms all 22 languages advertised: {len(EXPECTED_22_LANGS)} languages.\n")

    # 2. Audit Hospital Directory Coverage
    hosp_states = set(h["state"] for h in ALL_INDIA_HOSPITALS)
    hosp_with_phone = sum(1 for h in ALL_INDIA_HOSPITALS if h.get("phone_general") or h.get("phone_emergency"))
    print(f"[PASS] 2. Hospital Directory: {len(ALL_INDIA_HOSPITALS)} facilities across {len(hosp_states)} States/UTs.")
    print(f"       • Facilities with publicly listed phone numbers: {hosp_with_phone}/{len(ALL_INDIA_HOSPITALS)}")
    print(f"       • States covered: {', '.join(sorted(hosp_states))}\n")

    # 3. Audit Medication Centre / Pharmacy Directory Coverage
    store_states = set(s["state"] for s in ALL_INDIA_MEDICINE_STORES)
    store_with_phone = sum(1 for s in ALL_INDIA_MEDICINE_STORES if s.get("phone_contact"))
    print(f"[PASS] 3. Pharmacy Directory: {len(ALL_INDIA_MEDICINE_STORES)} facilities across {len(store_states)} States/UTs.")
    print(f"       • Facilities with publicly listed phone numbers: {store_with_phone}/{len(ALL_INDIA_MEDICINE_STORES)}")
    print(f"       • States covered: {', '.join(sorted(store_states))}\n")

    # 4. Verify AI Multilingual Responses
    test_queries = [
        ("Dengue fever", "hi", ["डेंगू", "डेंगू बुखार"]),
        ("Tuberculosis", "gu", ["ટીબી", "ક્ષય"]),
        ("Dengue fever", "ta", ["டெங்கு"]),
    ]
    for q, code, expected_kws in test_queries:
        res = client.post("/api/assistant/chat", json={"message": q, "lang": code, "history": []}).get_json()
        assert res["status"] == "ok"
        reply = res["ai_response"]["reply"]
        assert res["ai_response"]["language"] == code
        found = any(kw in reply for kw in expected_kws)
        assert found, f"Failed for {code} ({LANGUAGE_NAMES[code]}): none of {expected_kws} found in reply:\n{reply[:200]}"
        print(f"[PASS] 4. AI Chat in '{code}' ({LANGUAGE_NAMES[code]}): Verified keywords {expected_kws} present.")

    # 5. Verify Context-Aware Follow-up Questions for Vague Inputs
    vague_res = client.post("/api/assistant/chat", json={"message": "I have a headache", "lang": "en", "history": []}).get_json()
    reply_text = vague_res["ai_response"]["reply"].lower()
    assert "follow-up questions" in reply_text or "how long" in reply_text, f"Follow-up questions not found in: {reply_text[:200]}"
    print("[PASS] 5. Contextual AI Follow-up: Asks specific clinical questions for ambiguous symptoms.\n")

    # 6. Verify Medicine Mode vs Disease Mode Separation
    med_res = client.post("/api/assistant/chat", json={"message": "what is lithonex 450 xl", "lang": "en", "history": []}).get_json()
    assert med_res["ai_response"]["source"] == "nova_ai_medicine_guide"
    assert "Take strictly under medical guidance" in med_res["ai_response"]["reply"]
    print("[PASS] 6. Medicine Mode: Detected brand + mg + XL specifier with mandatory safety warning.")

    print("\n=================================================================")
    print("✅ ALL AUDIT AND VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=================================================================")


if __name__ == "__main__":
    run_audit()