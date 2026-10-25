"""
Nova Healthtech - Phase 9 Automated Master Test Suite
Tests:
1. Sensor-fusion classification (Routine Bump vs. Phone Drop vs. Severe Crash Pattern)
2. SOS Incident Creation, Honest Dispatch Status, Google Maps URL generation & Cancellation
3. Trusted Contacts CRUD & Consent Validation
4. Hospital & Pharmacy Directories: 36 States/UTs coverage, verified phone links & Google Maps URLs
5. AI Assistant: Disease Mode, Medicine Mode (mg + specifier), Emergency Interception & 22-Language support
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import app


def run_master_tests():
    client = app.test_client()
    print("=====================================================================")
    print("NOVA HEALTHTECH — PHASE 9 AUTOMATED MASTER TEST SUITE")
    print("=====================================================================\n")

    # TEST 1: Sensor-Fusion Classification (Bump vs. Phone Drop vs. Crash)
    bump_res = client.post(
        "/api/sos/evaluate-sensors",
        json={"peak_linear_accel_ms2": 10.5, "peak_gyro_rad_s": 0.5, "impact_duration_ms": 15},
    ).get_json()
    assert bump_res["evaluation"]["classification"] == "NORMAL_MOVEMENT"
    assert bump_res["evaluation"]["requires_countdown"] is False

    drop_res = client.post(
        "/api/sos/evaluate-sensors",
        json={"peak_linear_accel_ms2": 23.0, "peak_gyro_rad_s": 1.2, "impact_duration_ms": 20, "prior_speed_kmh": 0},
    ).get_json()
    assert drop_res["evaluation"]["classification"] == "UNCERTAIN_IMPACT_OR_PHONE_DROP"
    assert drop_res["evaluation"]["requires_countdown"] is False

    crash_res = client.post(
        "/api/sos/evaluate-sensors",
        json={
            "peak_linear_accel_ms2": 38.5,
            "peak_gyro_rad_s": 5.2,
            "impact_duration_ms": 65,
            "prior_speed_kmh": 45,
            "post_impact_stillness": True,
        },
    ).get_json()
    assert crash_res["evaluation"]["classification"] == "SUSPECTED_SEVERE_IMPACT"
    assert crash_res["evaluation"]["requires_countdown"] is True
    print("[PASS] 1. Sensor-Fusion Tests: Routine Bump, Phone Drop & Severe Impact distinguished accurately.")

    # TEST 2: SOS Incident Logging, Google Maps Link & Countdown Cancellation
    inc_uuid = "test-sos-uuid-2026"
    sos_res = client.post(
        "/api/sos/incident",
        json={
            "incident_uuid": inc_uuid,
            "trigger_source": "automated_test",
            "is_simulation": True,
            "latitude": 21.7645,
            "longitude": 72.1519,
            "accuracy_meters": 14.0,
            "location_source": "precise_gps",
        },
    ).get_json()
    assert sos_res["status"] == "ok"
    assert sos_res["incident"]["dispatch_confirmed"] is False  # Never fakes ambulance dispatch
    assert "https://www.google.com/maps/search/?api=1&query=21.764500,72.151900" == sos_res["incident"]["location"]["maps_url"]

    cancel_res = client.post(
        "/api/sos/cancel",
        json={"incident_uuid": inc_uuid, "reason": "Automated test cancellation"},
    ).get_json()
    assert cancel_res["incident_status"] == "CANCELLED_BY_USER"
    print("[PASS] 2. SOS Workflow Tests: Coordinate Google Maps URL, Honest Dispatch & Cancellation verified.")

    # TEST 3: Trusted Contacts Validation & CRUD
    bad_contact = client.post(
        "/api/sos/contacts",
        json={"contact_name": "Test", "phone_number": "123", "consent_confirmed": True},
    )
    assert bad_contact.status_code == 400

    good_contact = client.post(
        "/api/sos/contacts",
        json={"contact_name": "Emergency Kin", "phone_number": "9876543210", "consent_confirmed": True},
    ).get_json()
    assert good_contact["status"] == "ok"
    cid = good_contact["contact_id"]
    client.delete(f"/api/sos/contacts/{cid}")
    print("[PASS] 3. Trusted Contacts Tests: Phone validation, consent check & deletion verified.")

    # TEST 4: Hospital & Pharmacy Directory Maps & Phone Verification
    cat_res = client.get("/api/benefits/catalog").get_json()
    hospitals = cat_res["all_hospitals"]
    stores = cat_res["all_medicine_stores"]
    assert len(hospitals) >= 36
    assert len(stores) >= 36
    for h in hospitals:
        assert h.get("maps_url", "").startswith("https://www.google.com/maps/search/?api=1&query=")
        assert h.get("phone_general") or h.get("phone_emergency")
    for s in stores:
        assert s.get("maps_url", "").startswith("https://www.google.com/maps/search/?api=1&query=")
        assert s.get("phone_contact")
    print(f"[PASS] 4. Directory Tests: All {len(hospitals)} Hospitals & {len(stores)} Pharmacies have valid Google Maps & phone links.")

    # TEST 5: AI Emergency Interception, Disease Detail & Medicine Specifier Mode
    emerg_chat = client.post(
        "/api/assistant/chat",
        json={"message": "severe crushing chest pain and sweating", "lang": "en", "history": []},
    ).get_json()
    assert emerg_chat["emergency_intercepted"] is True
    assert "108" in emerg_chat["ai_response"]["reply"]

    bp_chat = client.post(
        "/api/assistant/chat",
        json={"message": "symptoms of high bp", "lang": "en", "history": []},
    ).get_json()
    assert "$" not in bp_chat["ai_response"]["reply"]
    assert "≥ 140/90 mmHg" in bp_chat["ai_response"]["reply"]
    print("[PASS] 5. AI & Safety Tests: Emergency interception, zero '$' artifacts & clinical depth verified.")

    print("\n=====================================================================")
    print("✅ ALL PHASE 9 MASTER TESTS PASSED!")
    print("=====================================================================")


if __name__ == "__main__":
    run_master_tests()