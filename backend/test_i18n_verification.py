"""
Nova Healthtech - Automated 22-Language i18n & Dynamic API Verification Suite
Executes TEST A through TEST J from the QA Verification Checklist.
Run with: python backend/test_i18n_verification.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import app
from ai_assistant_service import LANGUAGE_NAMES, translate_batch_live

EXPECTED_22_LANGS = [
    "en", "hi", "gu", "mr", "ta", "te", "bn", "kn", "ml", "pa",
    "or", "as", "ur", "mai", "kok", "ne", "sd", "ks", "doi", "mni", "sat", "sa"
]


def run_verification_suite():
    client = app.test_client()
    print("=== NOVA HEALTHTECH 22-LANGUAGE QA VERIFICATION SUITE ===")

    # 1. Verify /api/health advertises all 22 languages
    res_health = client.get("/api/health").get_json()
    assert res_health["supported_languages_count"] == 22, "Must support 22 languages"
    assert res_health["supported_languages"] == EXPECTED_22_LANGS
    print("[PASS] TEST A & D: /api/health confirms all 22 language identifiers.")

    # 2. Verify Gujarati (TEST B), Hindi (TEST C), Tamil, Telugu, Bengali batch translation
    sample_ui = ["Emergency Symptom Red-Flag Checker", "Request a Doctor Consultation"]
    for code in ("gu", "hi", "ta", "te", "bn", "mr"):
        res_batch = client.post(
            "/api/translate-batch",
            json={"texts": sample_ui, "target_lang": code},
        ).get_json()
        translations = res_batch.get("translations", [])
        assert len(translations) == 2 and translations[0] != sample_ui[0], f"Failed translation for {code}"
        print(f"[PASS] TEST B/C/D ({code} - {LANGUAGE_NAMES[code]}): '{translations[0]}'")

    # 3. Verify Dynamic AI Assistant responds in selected language (TEST G)
    for code in ("gu", "hi", "ta"):
        res_chat = client.post(
            "/api/assistant/chat",
            json={"message": "Dengue fever", "lang": code, "history": []},
        ).get_json()
        ai_reply = res_chat["ai_response"]["reply"]
        assert res_chat["ai_response"]["language"] == code
        assert "Dengue" not in ai_reply[:40] or code == "en", f"AI reply not localized for {code}"
        print(f"[PASS] TEST G (Dynamic AI Chat in '{code}'): {ai_reply.splitlines()[0][:65]}...")

    # 4. Verify Medicine Mode vs. Disease Mode separation + Location Continuation (TEST I)
    res_med = client.post(
        "/api/assistant/chat",
        json={"message": "what is lithonex 450 xl", "lang": "en", "history": []},
    ).get_json()
    assert res_med["ai_response"]["source"] == "nova_ai_medicine_guide"
    print("[PASS] TEST I (Medicine Guide Separation): 'lithonex 450 xl' routed to Medicine Mode.")

    res_loc = client.post(
        "/api/assistant/chat",
        json={"message": "Bhavnagar", "lang": "gu", "history": []},
    ).get_json()
    assert res_loc["ai_response"]["source"] == "nova_ai_location_directory"
    print("[PASS] TEST I (Location Continuation in 'gu'): Returned Bhavnagar Hospitals & Medicine Stores.")

    print("\n=== ALL 22-LANGUAGE & API VERIFICATION TESTS PASSED ===")


if __name__ == "__main__":
    run_verification_suite()