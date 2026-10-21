import os
import re
import time
from datetime import datetime, timezone
from flask import Flask, jsonify, make_response, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

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
    GUJARAT_HOSPITAL_DIRECTORY,
    SCHEMES_CATALOG,
    evaluate_preliminary_guidance,
)
from triage_service import (
    evaluate_emergency_triage,
    get_triage_rules_catalog,
)
from ai_assistant_service import ai_assistant

load_dotenv()

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://127.0.0.1:5000",
                "http://localhost:5000",
                "http://127.0.0.1:5500",
                "http://localhost:5500",
            ]
        }
    },
)

init_db()
health_adapter = DigitalHealthIntegrationAdapter()


# =====================================================================
# SECURITY MIDDLEWARE & RATE LIMITING
# =====================================================================

@app.before_request
def enforce_rate_limits():
    """Applies sliding-window rate limits per client IP."""
    # Exclude static assets from rate-limiting
    if not request.path.startswith("/api/"):
        return None

    client_ip = get_client_ip(request)
    is_strict = request.path in ("/api/assistant/chat", "/api/consultations/request")

    allowed, remaining = rate_limiter.is_allowed(client_ip, is_strict_endpoint=is_strict)
    if not allowed:
        return jsonify(
            {
                "status": "error",
                "code": 429,
                "message": (
                    "Rate limit exceeded. To protect system availability for rural clinics, "
                    "please wait 60 seconds before submitting further requests."
                ),
                "retry_after_seconds": 60,
            }
        ), 429

    return None


@app.after_request
def append_defensive_headers(response):
    """Applies CSP, X-Frame-Options, and X-Content-Type-Options headers."""
    return apply_security_headers(response)


# =====================================================================
# CORE APPLICATION & STATIC ROUTES
# =====================================================================

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
    gemini_key_present = bool(os.getenv("GEMINI_API_KEY"))

    return jsonify(
        {
            "status": "ok",
            "service": "Nova Healthtech API",
            "environment": "demonstration-prototype",
            "clinically_validated": False,
            "security_hardening": {
                "rate_limiter": "active_sliding_window",
                "headers": "csp_frame_nosniff_enforced",
                "sanitization": "active_html_escape",
            },
            "offline_health_guide": "available_v1",
            "database_status": "sqlite_operational",
            "ai_key_configured": gemini_key_present,
            "ai_model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            "doctor_pathway_enabled": True,
            "supported_languages": ["en", "gu", "hi"],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "safety_notice": (
                "Demonstration prototype. Includes non-diagnostic preliminary AI guidance, "
                "deterministic emergency red-flag gates, and official scheme navigation."
            ),
        }
    ), 200


# =====================================================================
# MILESTONE 5: OFFLINE HEALTH GUIDE & NETWORK STRESS TEST ENDPOINTS
# =====================================================================

@app.route("/api/guide/catalog", methods=["GET"])
def get_guide_catalog():
    """Returns curated offline preliminary health and first-aid guides."""
    lang = request.args.get("lang", "en").strip().lower()
    return jsonify(get_health_guides(lang=lang)), 200


@app.route("/api/stress-test/simulate-latency", methods=["GET"])
def simulate_latency():
    """
    Simulates high-latency / slow 2G rural connection response.
    Delay clamped safely between 0.1s and 3.0s.
    """
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


# =====================================================================
# DOCTOR CONSULTATION & MEDICATION REMINDER ENDPOINTS
# =====================================================================

@app.route("/api/consultations/request", methods=["POST"])
def request_consultation():
    payload = request.get_json(silent=True) or {}

    patient_name = sanitize_input_text(payload.get("patient_name", ""), max_length=80)
    contact_number = str(payload.get("contact_number", "")).strip()[:15]
    district = sanitize_input_text(payload.get("district", "Bhavnagar"), max_length=50)
    lang = sanitize_input_text(payload.get("preferred_language", "en"), max_length=5)
    symptoms = sanitize_input_text(payload.get("symptoms_summary", ""), max_length=500)

    clean_digits = re.sub(r"\D", "", contact_number)
    if len(clean_digits) != 10:
        return jsonify(
            {
                "status": "error",
                "message": "Please enter a valid 10-digit Indian mobile number for doctor callback.",
            }
        ), 400

    if not patient_name or not symptoms:
        return jsonify(
            {"status": "error", "message": "Patient identifier and symptoms summary are required."}
        ), 400

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
            "message": (
                "Consultation request registered. A healthcare coordinator will review."
                if urgency != "CRITICAL_EMERGENCY"
                else "CRITICAL ALERT: Your symptoms suggest an emergency. Call 108 immediately."
            ),
        }
    ), 201


@app.route("/api/consultations/recent", methods=["GET"])
def get_consultations():
    consultations = get_recent_consultations(limit=10)
    return jsonify({"status": "ok", "consultations": consultations}), 200


@app.route("/api/reminders", methods=["GET"])
def list_reminders():
    reminders = get_active_medication_reminders()
    return jsonify({"status": "ok", "reminders": reminders}), 200


@app.route("/api/reminders", methods=["POST"])
def add_reminder():
    payload = request.get_json(silent=True) or {}

    medicine_name = sanitize_input_text(payload.get("medicine_name", ""), max_length=100)
    dosage = sanitize_input_text(payload.get("prescribed_dosage", ""), max_length=80)
    scheduled_time = sanitize_input_text(payload.get("scheduled_time", ""), max_length=10)
    meal_relation = sanitize_input_text(payload.get("meal_relation", "after_food"), max_length=20)
    doctor_confirmed = bool(payload.get("doctor_prescribed_confirmed", False))
    notes = sanitize_input_text(payload.get("notes", ""), max_length=200)

    if not medicine_name or not dosage or not scheduled_time:
        return jsonify(
            {"status": "error", "message": "Medicine name, dose, and time are required."}
        ), 400

    if not doctor_confirmed:
        return jsonify(
            {
                "status": "error",
                "message": "Confirmation required: Reminders must match your doctor's written prescription.",
            }
        ), 400

    try:
        reminder_id = create_medication_reminder(
            medicine_name=medicine_name,
            prescribed_dosage=dosage,
            scheduled_time=scheduled_time,
            meal_relation=meal_relation,
            doctor_prescribed_confirmed=True,
            notes=notes,
        )
        return jsonify(
            {
                "status": "ok",
                "reminder_id": reminder_id,
                "message": "Medication reminder schedule registered successfully.",
            }
        ), 201
    except ValueError as val_err:
        return jsonify({"status": "error", "message": str(val_err)}), 400


@app.route("/api/reminders/<int:reminder_id>/taken", methods=["POST"])
def mark_reminder_taken(reminder_id: int):
    success = log_medication_taken(reminder_id)
    if not success:
        return jsonify({"status": "error", "message": "Reminder not found"}), 404
    return jsonify({"status": "ok", "message": "Adherence logged successfully"}), 200


@app.route("/api/reminders/<int:reminder_id>", methods=["DELETE"])
def remove_reminder(reminder_id: int):
    success = delete_medication_reminder(reminder_id)
    if not success:
        return jsonify({"status": "error", "message": "Reminder not found"}), 404
    return jsonify({"status": "ok", "message": "Reminder removed successfully"}), 200


# =====================================================================
# AI ASSISTANT, TRIAGE, AND BENEFITS ENDPOINTS
# =====================================================================

@app.route("/api/assistant/chat", methods=["POST"])
def assistant_chat():
    payload = request.get_json(silent=True) or {}
    message = sanitize_input_text(payload.get("message", ""), max_length=600)
    lang = sanitize_input_text(payload.get("lang", "en"), max_length=5).lower()

    if not message:
        return jsonify({"status": "error", "message": "Message text cannot be empty."}), 400

    triage_result = evaluate_emergency_triage(selected_rule_ids=[], free_text=message, lang=lang)

    if triage_result.get("block_ai_assistant", False):
        return jsonify(
            {
                "status": "ok",
                "emergency_intercepted": True,
                "urgency_level": "CRITICAL_EMERGENCY",
                "triage": triage_result,
                "reply": None,
                "safety_message": (
                    "Pre-AI Safety Gate Interception: Life-threatening symptom detected. "
                    "Generative AI has been bypassed. Seek immediate emergency care."
                ),
            }
        ), 200

    ai_result = ai_assistant.generate_preliminary_guidance(user_message=message, lang=lang)
    return jsonify(
        {
            "status": "ok",
            "emergency_intercepted": False,
            "urgency_level": "PRELIMINARY_NON_EMERGENCY",
            "triage": triage_result,
            "ai_response": ai_result,
        }
    ), 200


@app.route("/api/triage/rules", methods=["GET"])
def get_triage_rules():
    return jsonify(
        {
            "status": "ok",
            "engine": "deterministic_rule_based_v1",
            "rules": get_triage_rules_catalog(),
        }
    ), 200


@app.route("/api/triage/evaluate", methods=["POST"])
def evaluate_triage():
    payload = request.get_json(silent=True) or {}
    selected_ids = payload.get("selected_rule_ids", [])
    if not isinstance(selected_ids, list):
        selected_ids = []
    free_text = sanitize_input_text(payload.get("free_text", ""), max_length=500)
    lang = sanitize_input_text(payload.get("lang", "en"), max_length=5).lower()

    result = evaluate_emergency_triage(
        selected_rule_ids=selected_ids, free_text=free_text, lang=lang
    )
    return jsonify({"status": "ok", "triage": result}), 200


@app.route("/api/benefits/catalog", methods=["GET"])
def get_benefits_catalog():
    district_filter = request.args.get("district", "").strip().lower()
    hospitals = GUJARAT_HOSPITAL_DIRECTORY
    if district_filter and district_filter != "all":
        hospitals = [
            h for h in GUJARAT_HOSPITAL_DIRECTORY if h["district"].lower() == district_filter
        ]

    return jsonify(
        {
            "status": "ok",
            "integration_status": health_adapter.get_integration_status(),
            "official_search_portals": {
                "pmjay_beneficiary_portal": "https://beneficiary.nha.gov.in/",
                "pmjay_hospital_search": "https://hem.nha.gov.in/search",
                "abha_portal": "https://abha.abdm.gov.in/",
                "gujarat_ma_portal": "https://ma.gujarat.gov.in/",
                "national_helpline": "14555",
            },
            "schemes": SCHEMES_CATALOG,
            "hospitals": hospitals,
        }
    ), 200


@app.route("/api/benefits/screen", methods=["POST"])
def screen_benefits_guidance():
    payload = request.get_json(silent=True) or {}
    age_group = sanitize_input_text(payload.get("age_group", "under_60"), max_length=20)
    state_residency = sanitize_input_text(payload.get("state_residency", "gujarat"), max_length=20)
    income_bracket = sanitize_input_text(payload.get("income_bracket", "under_4_lakh"), max_length=20)
    has_senior_70_plus = bool(payload.get("has_senior_70_plus", False))

    result = evaluate_preliminary_guidance(
        age_group=age_group,
        state_residency=state_residency,
        income_bracket=income_bracket,
        has_senior_70_plus=has_senior_70_plus,
    )
    return jsonify({"status": "ok", "guidance": result}), 200


@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({"status": "error", "code": 404, "message": "Resource not found."}), 404


@app.errorhandler(500)
def handle_internal_error(error):
    return jsonify(
        {
            "status": "error",
            "code": 500,
            "message": "Internal server error. In case of emergency, dial 108 or 112 immediately.",
        }
    ), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    print(f"Starting Nova Healthtech Server on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=debug_mode)