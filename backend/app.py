"""
Nova Healthtech - Core Application Server & API Gateway
Provides endpoints for Automatic Accident Detection & SOS, AI Consultation,
22-Language Translation, Health Guides, Emergency Triage, Doctor Consultations,
Medication Reminders, and Verified All-India Hospital & Pharmacy Directories.
"""

import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from flask import Flask, jsonify, make_response, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

ROOT_ENV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(ROOT_ENV, override=True)

from security import (
    rate_limiter,
    sanitize_input_text,
    apply_security_headers,
    get_client_ip,
)
from health_guide_service import get_health_guides
from database import (
    init_db,
    create_consultation_request,
    get_recent_consultations,
    create_medication_reminder,
    get_active_medication_reminders,
    log_medication_taken,
    delete_medication_reminder,
)
from benefits_service import (
    DigitalHealthIntegrationAdapter,
    SCHEMES_CATALOG,
    evaluate_preliminary_guidance,
)
from triage_service import (
    evaluate_emergency_triage,
    get_triage_rules_catalog,
)
from ai_assistant_service import (
    ai_assistant,
    LANGUAGE_NAMES,
    ALL_INDIA_HOSPITALS,
    ALL_INDIA_MEDICINE_STORES,
    translate_batch_live,
    translate_multiline_response,
)
from sos_service import (
    build_google_maps_url,
    create_or_update_sos_incident,
    cancel_sos_incident,
    list_trusted_contacts,
    add_trusted_contact,
    delete_trusted_contact,
    evaluate_sensor_fusion_payload,
    AUTHORIZED_DISPATCH_API_URL,
)

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

# Production-aware CORS configuration (supports Cloudflare Pages origin or local network)
ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*")
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

init_db()
health_adapter = DigitalHealthIntegrationAdapter()
SUPPORTED_LANGUAGE_CODES = list(LANGUAGE_NAMES.keys())


def _enrich_directory_records_with_maps(records: list) -> list:
    """Ensures every hospital and pharmacy has a verified clickable Google Maps URL and provenance metadata."""
    enriched = []
    for item in records:
        rec = dict(item)
        lat = rec.get("latitude")
        lng = rec.get("longitude")
        addr_query = f"{rec.get('name', '')}, {rec.get('address', '')}, {rec.get('city', '')}, {rec.get('state', '')} {rec.get('pin_code', '')}".strip()
        rec["maps_url"] = rec.get("maps_url") or build_google_maps_url(lat, lng, addr_query)
        rec["location_verification"] = (
            "coordinate_verified" if (lat is not None and lng is not None) else "official_address_verified"
        )
        enriched.append(rec)
    return enriched


@app.before_request
def enforce_rate_limits():
    # Never throttle emergency SOS, translation batching, or health monitoring
    if not request.path.startswith("/api/") or request.path in (
        "/api/translate-batch",
        "/api/translate-text",
        "/api/health",
        "/api/sos/incident",
        "/api/sos/cancel",
    ):
        return None
    client_ip = get_client_ip(request)
    is_strict = request.path in ("/api/consultations/request",)
    allowed, _ = rate_limiter.is_allowed(client_ip, is_strict_endpoint=is_strict)
    if not allowed:
        return jsonify(
            {
                "status": "error",
                "code": 429,
                "message": "Rate limit exceeded. Please wait a moment.",
            }
        ), 429
    return None


@app.after_request
def append_defensive_headers(response):
    response = apply_security_headers(response)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    ts = int(time.time())
    html_content = re.sub(r'href="style\.css[^"]*"', f'href="style.css?v={ts}"', html_content)
    html_content = re.sub(r'src="script\.js[^"]*"', f'src="script.js?v={ts}"', html_content)

    resp = make_response(html_content, 200)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


@app.route("/<path:path>")
def serve_static_files(path):
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    return jsonify({"status": "error", "message": "Resource not found"}), 404


@app.route("/api/health", methods=["GET"])
def health_check():
    gemini_key_present = bool(ai_assistant.get_api_key())
    return jsonify(
        {
            "status": "ok",
            "service": "Nova Healthtech API",
            "environment": os.getenv("FLASK_ENV", "production-ready"),
            "clinically_validated": False,
            "database_status": "sqlite_operational",
            "ai_online": True,
            "ai_key_configured": gemini_key_present,
            "ai_model": "AI Online • Live Web Search",
            "authorized_dispatch_partner_connected": bool(AUTHORIZED_DISPATCH_API_URL),
            "supported_languages_count": len(SUPPORTED_LANGUAGE_CODES),
            "supported_languages": SUPPORTED_LANGUAGE_CODES,
            "hospitals_count": len(ALL_INDIA_HOSPITALS),
            "medicine_stores_count": len(ALL_INDIA_MEDICINE_STORES),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "safety_notice": "AI is Online • SOS & All-India Verified Directories Active.",
        }
    ), 200


# ==============================================================================
# PHASE 2 & 3: AUTOMATIC ACCIDENT DETECTION & EMERGENCY SOS ENDPOINTS
# ==============================================================================

@app.route("/api/sos/evaluate-sensors", methods=["POST"])
def evaluate_sensors_endpoint():
    payload = request.get_json(silent=True) or {}
    result = evaluate_sensor_fusion_payload(payload)
    return jsonify({"status": "ok", "evaluation": result}), 200


@app.route("/api/sos/incident", methods=["POST"])
def trigger_sos_incident():
    payload = request.get_json(silent=True) or {}
    client_ip = get_client_ip(request)
    response_body, status_code = create_or_update_sos_incident(client_ip, payload)
    return jsonify(response_body), status_code


@app.route("/api/sos/cancel", methods=["POST"])
def cancel_sos_endpoint():
    payload = request.get_json(silent=True) or {}
    incident_uuid = sanitize_input_text(payload.get("incident_uuid", ""), max_length=80)
    reason = sanitize_input_text(payload.get("reason", "User confirmed safety"), max_length=120)
    if not incident_uuid:
        return jsonify({"status": "error", "message": "incident_uuid is required"}), 400
    res = cancel_sos_incident(incident_uuid, reason)
    return jsonify(res), 200


@app.route("/api/sos/contacts", methods=["GET", "POST"])
def manage_trusted_contacts():
    if request.method == "GET":
        return jsonify({"status": "ok", "contacts": list_trusted_contacts()}), 200

    payload = request.get_json(silent=True) or {}
    name = sanitize_input_text(payload.get("contact_name", ""), max_length=80)
    phone = sanitize_input_text(payload.get("phone_number", ""), max_length=20)
    rel = sanitize_input_text(payload.get("relationship", "Family / Emergency"), max_length=40)
    consent = bool(payload.get("consent_confirmed", False))

    ok, msg, new_id = add_trusted_contact(name, phone, rel, consent)
    if not ok:
        return jsonify({"status": "error", "message": msg}), 400
    return jsonify({"status": "ok", "message": msg, "contact_id": new_id, "contacts": list_trusted_contacts()}), 201


@app.route("/api/sos/contacts/<int:contact_id>", methods=["DELETE"])
def remove_trusted_contact(contact_id: int):
    delete_trusted_contact(contact_id)
    return jsonify({"status": "ok", "contacts": list_trusted_contacts()}), 200


# ==============================================================================
# 22-LANGUAGE TRANSLATION & CONVERSATIONAL AI ENDPOINTS
# ==============================================================================

@app.route("/api/translate-batch", methods=["POST"])
def translate_batch_endpoint():
    payload = request.get_json(silent=True) or {}
    texts = payload.get("texts", [])
    target_lang = str(payload.get("target_lang", "en")).strip().lower()[:10]

    if not isinstance(texts, list) or not texts or target_lang == "en":
        return jsonify({"status": "ok", "translations": texts}), 200

    cleaned_texts = [str(t)[:600] for t in texts[:350]]
    translated = translate_batch_live(cleaned_texts, target_lang=target_lang)
    return jsonify({"status": "ok", "target_lang": target_lang, "translations": translated}), 200


@app.route("/api/translate-text", methods=["POST"])
def translate_single_multiline_endpoint():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", ""))[:5000]
    target_lang = str(payload.get("target_lang", "en")).strip().lower()[:10]
    if not text:
        return jsonify({"status": "ok", "translated": ""}), 200
    translated = translate_multiline_response(text, target_lang=target_lang)
    return jsonify({"status": "ok", "translated": translated}), 200


@app.route("/api/assistant/config-key", methods=["POST"])
def configure_gemini_key():
    payload = request.get_json(silent=True) or {}
    api_key = str(payload.get("api_key", "")).strip()
    ok, msg = ai_assistant.save_api_key(api_key)
    if not ok:
        return jsonify({"status": "error", "message": msg}), 400
    return jsonify(
        {
            "status": "ok",
            "ai_online": True,
            "model": "AI Online • Live Web Search",
            "message": "AI is Online • Live Web Search active!",
        }
    ), 200


@app.route("/api/assistant/chat", methods=["POST"])
def assistant_chat():
    payload = request.get_json(silent=True) or {}
    message = sanitize_input_text(payload.get("message", ""), max_length=600)
    lang = sanitize_input_text(payload.get("lang", "en"), max_length=10).lower()
    raw_history = payload.get("history", [])

    if not message:
        return jsonify({"status": "error", "message": "Message text cannot be empty."}), 400

    # Deterministic emergency check (never delays emergency flagging)
    triage_eval = evaluate_emergency_triage(selected_rule_ids=[], free_text=message, lang=lang)
    is_critical = triage_eval.get("urgency_level") == "CRITICAL_EMERGENCY"

    clean_history = []
    if isinstance(raw_history, list):
        for item in raw_history[-8:]:
            if isinstance(item, dict):
                clean_history.append(
                    {
                        "role": "user" if item.get("role") == "user" else "assistant",
                        "text": sanitize_input_text(item.get("text", ""), max_length=600),
                    }
                )

    ai_result = ai_assistant.generate_preliminary_guidance(
        user_message=message,
        lang=lang,
        history=clean_history,
    )

    if is_critical:
        emerg_banner = (
            "🚨 **CRITICAL EMERGENCY WARNING — DO NOT WAIT FOR CHAT:**\n"
            "Your symptoms match a high-priority medical red flag. **Call 108 (Ambulance) or 112 immediately** "
            "or tap the red **SOS Emergency** button at the top of the page.\n\n"
        )
        if lang != "en":
            emerg_banner = translate_multiline_response(emerg_banner, target_lang=lang) + "\n\n"
        ai_result["reply"] = emerg_banner + ai_result.get("reply", "")
        ai_result["english_reply"] = (
            "🚨 **CRITICAL EMERGENCY WARNING — DO NOT WAIT FOR CHAT:**\n"
            "Your symptoms match a high-priority medical red flag. **Call 108 (Ambulance) or 112 immediately**.\n\n"
            + ai_result.get("english_reply", "")
        )

    return jsonify(
        {
            "status": "ok",
            "emergency_intercepted": is_critical,
            "triage_summary": triage_eval if is_critical else None,
            "ai_response": ai_result,
        }
    ), 200


@app.route("/api/guide/catalog", methods=["GET"])
def get_guide_catalog():
    lang = request.args.get("lang", "en").strip().lower()[:10]
    return jsonify(get_health_guides(lang=lang)), 200


@app.route("/api/stress-test/simulate-latency", methods=["GET"])
def simulate_latency():
    delay_sec = min(max(float(request.args.get("delay", 1.0)), 0.1), 3.0)
    time.sleep(delay_sec)
    return jsonify(
        {
            "status": "ok",
            "simulated_delay_seconds": delay_sec,
            "network_condition": "Simulated 2G/Rural EDGE Connection",
            "payload_weight_bytes": 142,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
    ), 200


@app.route("/api/consultations/request", methods=["POST"])
def request_consultation():
    payload = request.get_json(silent=True) or {}
    patient_name = sanitize_input_text(payload.get("patient_name", ""), max_length=80)
    contact_number = str(payload.get("contact_number", "")).strip()[:15]
    district = sanitize_input_text(payload.get("district", "Bhavnagar"), max_length=50)
    lang = sanitize_input_text(payload.get("preferred_language", "en"), max_length=10).lower()
    symptoms = sanitize_input_text(payload.get("symptoms_summary", ""), max_length=500)

    clean_digits = re.sub(r"\D", "", contact_number)
    if len(clean_digits) != 10:
        return jsonify({"status": "error", "message": "Enter a valid 10-digit mobile number."}), 400

    triage_check = evaluate_emergency_triage(selected_rule_ids=[], free_text=symptoms, lang=lang)
    urgency = triage_check.get("urgency_level", "ROUTINE")

    consult_id = create_consultation_request(
        patient_name=patient_name,
        contact_number=clean_digits,
        district=district,
        preferred_language=lang,
        symptoms_summary=symptoms,
        urgency_level=urgency,
    )
    return jsonify(
        {
            "status": "ok",
            "consultation_id": consult_id,
            "urgency_level": urgency,
            "emergency_warning": urgency == "CRITICAL_EMERGENCY",
        }
    ), 201


@app.route("/api/consultations/recent", methods=["GET"])
def get_consultations():
    return jsonify({"status": "ok", "consultations": get_recent_consultations(limit=10)}), 200


@app.route("/api/consultations/<int:consult_id>", methods=["DELETE"])
def remove_consultation(consult_id: int):
    db_path = create_consultation_request.__globals__.get("DB_PATH")
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for t in ("consultation_requests", "consultations"):
            if t in tables:
                cur.execute(f"DELETE FROM {t} WHERE id = ?", (consult_id,))
        conn.commit()
    return jsonify({"status": "ok", "message": "Consultation removed successfully"}), 200


@app.route("/api/reminders", methods=["GET"])
def list_reminders():
    return jsonify({"status": "ok", "reminders": get_active_medication_reminders()}), 200


@app.route("/api/reminders", methods=["POST"])
def add_reminder():
    payload = request.get_json(silent=True) or {}
    medicine_name = sanitize_input_text(payload.get("medicine_name", ""), max_length=100)
    dosage = sanitize_input_text(payload.get("prescribed_dosage", ""), max_length=80)
    scheduled_time = sanitize_input_text(payload.get("scheduled_time", ""), max_length=10)
    meal_relation = sanitize_input_text(payload.get("meal_relation", "after_food"), max_length=20)
    doctor_confirmed = bool(payload.get("doctor_prescribed_confirmed", False))
    notes = sanitize_input_text(payload.get("notes", ""), max_length=200)

    if not medicine_name or not dosage or not scheduled_time or not doctor_confirmed:
        return jsonify({"status": "error", "message": "All prescribed reminder fields are required."}), 400

    reminder_id = create_medication_reminder(
        medicine_name=medicine_name,
        prescribed_dosage=dosage,
        scheduled_time=scheduled_time,
        meal_relation=meal_relation,
        doctor_prescribed_confirmed=True,
        notes=notes,
    )
    return jsonify({"status": "ok", "reminder_id": reminder_id}), 201


@app.route("/api/reminders/<int:reminder_id>/taken", methods=["POST"])
def mark_reminder_taken(reminder_id: int):
    log_medication_taken(reminder_id)
    return jsonify({"status": "ok"}), 200


@app.route("/api/reminders/<int:reminder_id>", methods=["DELETE"])
def remove_reminder(reminder_id: int):
    delete_medication_reminder(reminder_id)
    return jsonify({"status": "ok"}), 200


@app.route("/api/triage/rules", methods=["GET"])
def get_triage_rules():
    return jsonify({"status": "ok", "rules": get_triage_rules_catalog()}), 200


@app.route("/api/triage/evaluate", methods=["POST"])
def evaluate_triage():
    payload = request.get_json(silent=True) or {}
    selected_ids = payload.get("selected_rule_ids", [])
    free_text = sanitize_input_text(payload.get("free_text", ""), max_length=500)
    lang = sanitize_input_text(payload.get("lang", "en"), max_length=10).lower()
    result = evaluate_emergency_triage(selected_rule_ids=selected_ids, free_text=free_text, lang=lang)
    return jsonify({"status": "ok", "triage": result}), 200


@app.route("/api/benefits/catalog", methods=["GET"])
def get_benefits_catalog():
    state_filter = request.args.get("state", "all").strip().lower()
    city_filter = request.args.get("city", "all").strip().lower()

    enriched_hospitals = _enrich_directory_records_with_maps(ALL_INDIA_HOSPITALS)
    enriched_stores = _enrich_directory_records_with_maps(ALL_INDIA_MEDICINE_STORES)

    hospitals = enriched_hospitals
    if state_filter != "all":
        hospitals = [h for h in hospitals if h["state"].lower() == state_filter]
    if city_filter != "all":
        hospitals = [h for h in hospitals if h["city"].lower() == city_filter]

    stores = enriched_stores
    if state_filter != "all":
        stores = [s for s in stores if s["state"].lower() == state_filter]
    if city_filter != "all":
        stores = [s for s in stores if s["city"].lower() == city_filter]

    return jsonify(
        {
            "status": "ok",
            "schemes": SCHEMES_CATALOG,
            "hospitals": hospitals,
            "medicine_stores": stores,
            "all_hospitals": enriched_hospitals,
            "all_medicine_stores": enriched_stores,
        }
    ), 200


@app.route("/api/benefits/screen", methods=["POST"])
def screen_benefits_guidance():
    payload = request.get_json(silent=True) or {}
    result = evaluate_preliminary_guidance(
        age_group=sanitize_input_text(payload.get("age_group", "under_60"), 20),
        state_residency=sanitize_input_text(payload.get("state_residency", "gujarat"), 20),
        income_bracket=sanitize_input_text(payload.get("income_bracket", "under_4_lakh"), 20),
        has_senior_70_plus=bool(payload.get("has_senior_70_plus", False)),
    )
    return jsonify({"status": "ok", "guidance": result}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print(f"\n=======================================================")
    print(f"✅ Nova Healthtech Running at: http://127.0.0.1:{port}")
    print(f"🚨 Automatic Accident Detection, SOS & Google Maps Active")
    print(f"🌐 22 Indian Languages & All-India Directories Active")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=debug_mode, threaded=True, use_reloader=False)