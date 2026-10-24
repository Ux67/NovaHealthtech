import os
import re
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

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

CORS(app, resources={r"/api/*": {"origins": "*"}})

init_db()
health_adapter = DigitalHealthIntegrationAdapter()
SUPPORTED_LANGUAGE_CODES = list(LANGUAGE_NAMES.keys())


@app.before_request
def enforce_rate_limits():
    if not request.path.startswith("/api/"):
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
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/sw.js")
def serve_service_worker():
    response = make_response(
        send_from_directory(FRONTEND_DIR, "sw.js", mimetype="application/javascript")
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


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
            "environment": "demonstration-prototype",
            "clinically_validated": False,
            "database_status": "sqlite_operational",
            "ai_online": True,
            "ai_key_configured": gemini_key_present,
            "ai_model": "AI Online • Live Web Search",
            "supported_languages_count": len(SUPPORTED_LANGUAGE_CODES),
            "supported_languages": SUPPORTED_LANGUAGE_CODES,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "safety_notice": "AI is Online • All-India Hospitals & Medicine Stores Active.",
        }
    ), 200


@app.route("/api/translate-batch", methods=["POST"])
def translate_batch_endpoint():
    payload = request.get_json(silent=True) or {}
    texts = payload.get("texts", [])
    target_lang = str(payload.get("target_lang", "en")).strip().lower()[:10]

    if not isinstance(texts, list) or not texts or target_lang == "en":
        return jsonify({"status": "ok", "translations": texts}), 200

    cleaned_texts = [str(t)[:600] for t in texts[:150]]
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
    return jsonify(
        {
            "status": "ok",
            "emergency_intercepted": False,
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
    """Returns All-India Participating Hospitals and All-India Medicine Stores."""
    state_filter = request.args.get("state", "all").strip().lower()
    city_filter = request.args.get("city", "all").strip().lower()

    hospitals = ALL_INDIA_HOSPITALS
    if state_filter != "all":
        hospitals = [h for h in hospitals if h["state"].lower() == state_filter]
    if city_filter != "all":
        hospitals = [h for h in hospitals if h["city"].lower() == city_filter]

    stores = ALL_INDIA_MEDICINE_STORES
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
            "all_hospitals": ALL_INDIA_HOSPITALS,
            "all_medicine_stores": ALL_INDIA_MEDICINE_STORES,
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
    app.run(host="0.0.0.0", port=port, debug=True)