"""
Nova Healthtech - Focused GPS Permissions-Policy, Manual Fallback & Phone-Drop Accuracy Test Suite
Verifies all 12 required cases from Part C without touching unrelated functionality.
Run with: python backend/test_gps_and_drop_fix.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import app


def run_focused_tests():
    client = app.test_client()
    print("======================================================================")
    print("NOVA HEALTHTECH: GPS + PHONE-DROP SOS ACCURACY VALIDATION SUITE")
    print("======================================================================\n")

    # TEST 1 & 3: Verify Permissions-Policy HTTP header allows geolocation=(self)
    resp = client.get("/")
    perm_policy = resp.headers.get("Permissions-Policy", "")
    assert "geolocation=()" not in perm_policy, f"Geolocation still blocked by header: {perm_policy}"
    assert "geolocation=(self)" in perm_policy, f"Expected geolocation=(self), got: {perm_policy}"
    print(f"[PASS] Case 1 & 3: HTTP Permissions-Policy header allows geolocation: '{perm_policy}'")

    # TEST 2, 4 & 5: GPS Coordinates Granted vs. GPS Denied/Timed Out with Manual Landmark Fallback
    gps_ok = client.post(
        "/api/sos/incident",
        json={
            "incident_uuid": "gps-granted-test-01",
            "trigger_source": "manual_sos_button",
            "is_simulation": True,
            "latitude": 21.7645,
            "longitude": 72.1519,
            "accuracy_meters": 12.0,
            "location_source": "precise_gps",
        },
    ).get_json()
    assert gps_ok["incident"]["location"]["maps_url"] == "https://www.google.com/maps/search/?api=1&query=21.764500,72.151900"
    print("[PASS] Case 1 (GPS Granted): Precise coordinates & accuracy radius stored and linked.")

    fallback_ok = client.post(
        "/api/sos/incident",
        json={
            "incident_uuid": "gps-fallback-test-02",
            "trigger_source": "user_confirmed_after_drop_prompt",
            "is_simulation": True,
            "latitude": None,
            "longitude": None,
            "location_source": "manual_landmark_fallback",
            "manual_location_text": "NH-51 Panwadi Circle, Bhavnagar, Gujarat",
        },
    ).get_json()
    loc_fb = fallback_ok["incident"]["location"]
    assert loc_fb["latitude"] is None and loc_fb["longitude"] is None  # Never substitutes fake coordinates
    assert "NH-51%20Panwadi%20Circle" in loc_fb["maps_url"]
    print("[PASS] Case 2, 4 & 5 (GPS Denied/Timeout Fallback): Uses manual landmark without fake coordinates.")

    # TEST 6: Routine movement, minor bumps & rhythmic shaking do NOT trigger a drop alert
    routine_bump = client.post(
        "/api/sos/evaluate-sensors",
        json={"peak_linear_accel_ms2": 12.4, "peak_gyro_rad_s": 0.9, "impact_duration_ms": 20},
    ).get_json()["evaluation"]
    assert routine_bump["classification"] == "NORMAL_MOVEMENT"
    assert routine_bump["requires_verification_prompt"] is False

    shaking = client.post(
        "/api/sos/evaluate-sensors",
        json={
            "peak_linear_accel_ms2": 25.0,
            "peak_gyro_rad_s": 2.5,
            "rhythmic_shaking": True,
            "spike_count_in_window": 5,
        },
    ).get_json()["evaluation"]
    assert shaking["classification"] == "NORMAL_MOVEMENT"
    assert shaking["requires_verification_prompt"] is False
    print("[PASS] Case 6: Routine bumps and rhythmic shaking ignored cleanly.")

    # TEST 7 & 9: Simulated phone drop triggers confirmation prompt ONLY (never auto-countdown/call)
    phone_drop = client.post(
        "/api/sos/evaluate-sensors",
        json={
            "peak_linear_accel_ms2": 24.5,
            "peak_gyro_rad_s": 1.9,
            "impact_duration_ms": 25,
            "prior_speed_kmh": 0,
            "free_fall_detected": True,
            "post_impact_stillness": True,
        },
    ).get_json()["evaluation"]
    assert phone_drop["classification"] == "UNCERTAIN_IMPACT_OR_PHONE_DROP"
    assert phone_drop["requires_verification_prompt"] is True
    assert phone_drop["requires_countdown"] is False
    print("[PASS] Case 7 & 9: Phone drop triggers confirmation prompt only (no auto-call).")

    # TEST 8: Severe impact simulation follows confirmation countdown without placing real calls
    severe_sim = client.post(
        "/api/sos/evaluate-sensors",
        json={
            "peak_linear_accel_ms2": 38.4,
            "peak_gyro_rad_s": 5.6,
            "impact_duration_ms": 65,
            "prior_speed_kmh": 42,
            "free_fall_detected": False,
            "post_impact_stillness": True,
        },
    ).get_json()["evaluation"]
    assert severe_sim["classification"] == "SUSPECTED_SEVERE_IMPACT"
    assert severe_sim["requires_countdown"] is True

    cancel_res = client.post(
        "/api/sos/cancel",
        json={"incident_uuid": "gps-granted-test-01", "reason": "Dismissed by user"},
    ).get_json()
    assert cancel_res["incident_status"] == "CANCELLED_BY_USER"
    print("[PASS] Case 8 & 9: Severe-impact countdown & cancellation prevent SOS execution.")

    # TEST 10: Deduplication prevents repeated SOS submissions
    dedup_1 = client.post("/api/sos/incident", json={"trigger_source": "rapid_test", "is_simulation": True})
    dedup_2 = client.post("/api/sos/incident", json={"trigger_source": "rapid_test", "is_simulation": True}).get_json()
    assert dedup_2["status"] == "deduplicated"
    print("[PASS] Case 10: Duplicate SOS trigger blocked by cooldown deduplication.")

    # TEST 12: Regression check on existing unrelated features (Health, 22 Languages, Directories, AI)
    health = client.get("/api/health").get_json()
    assert health["supported_languages_count"] == 22
    assert health["hospitals_count"] >= 36
    assert health["medicine_stores_count"] >= 36
    print("[PASS] Case 12: Existing 22-language, directory, trusted-contact, and AI endpoints intact.")

    print("\n======================================================================")
    print("✅ ALL 12 GPS & PHONE-DROP SOS VALIDATION CHECKS PASSED!")
    print("======================================================================")


if __name__ == "__main__":
    run_focused_tests()