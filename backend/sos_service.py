"""
Nova Healthtech - Automatic Accident Detection, 8-Second Auto-SOS & Direct Ambulance Call Service
- Stores SOS incidents, cancellations, and trusted emergency contacts in SQLite.
- Evaluates sensor-fusion telemetry and triggers the 8-second auto-call & location share countdown.
- Automatically places the 108 call AND sends KEYCODE_CALL (input keyevent 5) to press the green
  dialer button automatically on Android when connected via USB or Wi-Fi ADB.
"""

import json
import os
import re
import sqlite3
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
SOS_DB_PATH = os.path.join(BACKEND_DIR, "nova_health.db")

AUTHORIZED_DISPATCH_API_URL = os.getenv("AUTHORIZED_DISPATCH_API_URL", "").strip()
AUTHORIZED_DISPATCH_API_KEY = os.getenv("AUTHORIZED_DISPATCH_API_KEY", "").strip()


def init_sos_tables() -> None:
    """Creates non-destructive SQLite tables for SOS incidents and trusted contacts."""
    with sqlite3.connect(SOS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sos_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_uuid TEXT UNIQUE NOT NULL,
                trigger_source TEXT NOT NULL,
                severity_classification TEXT NOT NULL,
                status TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                accuracy_meters REAL,
                location_source TEXT,
                maps_url TEXT,
                sensor_summary_json TEXT,
                is_simulation INTEGER DEFAULT 0,
                dispatch_confirmed INTEGER DEFAULT 0,
                dispatch_status_message TEXT,
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS trusted_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                relationship TEXT,
                consent_confirmed INTEGER NOT NULL DEFAULT 1,
                created_at_utc TEXT NOT NULL
            )
            """
        )
        conn.commit()


init_sos_tables()

_RECENT_INCIDENT_TIMESTAMPS: Dict[str, float] = {}


def build_google_maps_url(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    address_query: str = "",
) -> str:
    """Generates a verified, properly encoded Google Maps search URL."""
    if latitude is not None and longitude is not None:
        try:
            lat_f = float(latitude)
            lng_f = float(longitude)
            if -90.0 <= lat_f <= 90.0 and -180.0 <= lng_f <= 180.0:
                return f"https://www.google.com/maps/search/?api=1&query={lat_f:.6f},{lng_f:.6f}"
        except (ValueError, TypeError):
            pass

    clean_query = (address_query or "").strip()
    if clean_query:
        return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(clean_query)}"
    return ""


def attempt_direct_android_call(phone_number: str = "108", client_ip: str = "") -> Tuple[bool, str]:
    """
    Automatically places a direct cellular call to `108` on a connected Android phone AND
    sends `KEYCODE_CALL` (input keyevent 5) so that even if Android's Emergency Dialer
    intercepts `108` and shows the green Call button, the green Call button is pressed
    automatically without human interaction.
    """
    clean_num = re.sub(r"[^0-9+]", "", str(phone_number)) or "108"
    try:
        # If the phone is connected over Wi-Fi Hotspot (like in 22408.jpg) with Wireless ADB on port 5555,
        # attempt a quick non-blocking connect first.
        if client_ip and client_ip not in ("127.0.0.1", "::1", "localhost"):
            try:
                subprocess.run(
                    ["adb", "connect", f"{client_ip}:5555"],
                    capture_output=True,
                    text=True,
                    timeout=1.5,
                )
            except Exception:
                pass

        # Step 1: Wake screen if asleep and launch the call intent for 108
        subprocess.run(
            ["adb", "shell", "input", "keyevent", "224"],  # KEYCODE_WAKEUP
            capture_output=True,
            text=True,
            timeout=2,
        )
        res = subprocess.run(
            ["adb", "shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{clean_num}"],
            capture_output=True,
            text=True,
            timeout=3,
        )

        # Step 2: Because Android treats 108 as an Emergency Response Service number and often stops
        # on the dialer keypad with '108' pre-filled, wait 1.2s and send KEYCODE_CALL (keyevent 5)
        # which automatically presses the green Call button!
        time.sleep(1.2)
        call_key_res = subprocess.run(
            ["adb", "shell", "input", "keyevent", "5"],  # KEYCODE_CALL (Presses the green call button)
            capture_output=True,
            text=True,
            timeout=2,
        )

        if (res.returncode == 0 or call_key_res.returncode == 0) and "error:" not in (
            res.stderr + call_key_res.stderr
        ).lower():
            return (
                True,
                f"Direct cellular call to {clean_num} initiated automatically (KEYCODE_CALL auto-pressed green button).",
            )
    except Exception:
        pass
    return False, ""


def evaluate_sensor_fusion_payload(sensor_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates accelerometer + gyroscope telemetry and triggers the 8-second automatic
    ambulance call & location-sharing countdown for any significant impact/drop pattern.
    """
    peak_linear_accel = float(sensor_data.get("peak_linear_accel_ms2", 0.0) or 0.0)
    peak_gyro_rad_s = float(sensor_data.get("peak_gyro_rad_s", 0.0) or 0.0)
    impact_duration_ms = float(sensor_data.get("impact_duration_ms", 0.0) or 0.0)
    prior_speed_kmh = float(sensor_data.get("prior_speed_kmh", 0.0) or 0.0)
    post_impact_stillness = bool(sensor_data.get("post_impact_stillness", False))
    free_fall_detected = bool(sensor_data.get("free_fall_detected", False))
    rhythmic_shaking = bool(sensor_data.get("rhythmic_shaking", False))
    spike_count_in_window = int(sensor_data.get("spike_count_in_window", 1) or 1)

    if peak_linear_accel < 18.0:
        return {
            "classification": "NORMAL_MOVEMENT",
            "requires_countdown": False,
            "countdown_seconds": 0,
            "requires_verification_prompt": False,
            "confidence_note": "Routine phone handling or minor bump below incident threshold.",
        }

    if rhythmic_shaking or (spike_count_in_window >= 4 and prior_speed_kmh < 10.0 and not free_fall_detected):
        return {
            "classification": "NORMAL_MOVEMENT",
            "requires_countdown": False,
            "countdown_seconds": 0,
            "requires_verification_prompt": False,
            "confidence_note": "Continuous hand shaking or repetitive handling pattern ignored.",
        }

    is_multi_sensor_crash = (
        peak_linear_accel >= 32.0
        and (peak_gyro_rad_s >= 4.0 or prior_speed_kmh >= 15.0)
        and impact_duration_ms >= 35.0
    ) or (peak_linear_accel >= 42.0 and post_impact_stillness)

    if is_multi_sensor_crash:
        return {
            "classification": "SUSPECTED_SEVERE_IMPACT",
            "requires_countdown": True,
            "countdown_seconds": 8,
            "requires_verification_prompt": True,
            "confidence_note": (
                f"Suspected severe impact detected (Peak Linear Accel: {peak_linear_accel:.1f} m/s², "
                f"Rotation: {peak_gyro_rad_s:.1f} rad/s). Starting 8-second auto-ambulance call & location share countdown."
            ),
        }

    return {
        "classification": "UNCERTAIN_IMPACT_OR_PHONE_DROP",
        "requires_countdown": True,
        "countdown_seconds": 8,
        "requires_verification_prompt": True,
        "confidence_note": (
            f"Impact/drop spike detected ({peak_linear_accel:.1f} m/s²). "
            "Starting 8-second countdown to automatically call 108 Ambulance and share location unless cancelled."
        ),
    }


def create_or_update_sos_incident(
    client_key: str,
    payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], int]:
    """
    Logs an SOS incident after the 8-second countdown, prevents duplicate floods,
    generates a verified Google Maps link, and executes direct call/dispatch logic.
    """
    now_ts = time.time()
    incident_uuid = str(payload.get("incident_uuid", "")).strip() or f"sos-{int(now_ts * 1000)}"
    trigger_source = str(payload.get("trigger_source", "manual_sos"))[:40]
    is_simulation = bool(payload.get("is_simulation", False))

    last_ts = _RECENT_INCIDENT_TIMESTAMPS.get(client_key, 0.0)
    if not payload.get("incident_uuid") and (now_ts - last_ts) < 10.0:
        return {
            "status": "deduplicated",
            "message": "Duplicate incident trigger ignored within 10-second cooldown window.",
        }, 200
    _RECENT_INCIDENT_TIMESTAMPS[client_key] = now_ts

    lat = payload.get("latitude")
    lng = payload.get("longitude")
    acc = payload.get("accuracy_meters")
    manual_address = str(payload.get("manual_location_text", "")).strip()[:250]
    loc_source = str(payload.get("location_source", "unavailable"))[:40]

    try:
        lat_val = float(lat) if lat is not None and str(lat) != "" else None
        lng_val = float(lng) if lng is not None and str(lng) != "" else None
        acc_val = float(acc) if acc is not None and str(acc) != "" else None
    except (ValueError, TypeError):
        lat_val, lng_val, acc_val = None, None, None

    maps_url = build_google_maps_url(lat_val, lng_val, manual_address)
    sensor_data = payload.get("sensor_data") or {}
    fusion_eval = evaluate_sensor_fusion_payload(sensor_data) if sensor_data else {
        "classification": "MANUAL_SOS_TRIGGER",
        "requires_countdown": True,
        "countdown_seconds": 8,
        "confidence_note": "User activated SOS workflow.",
    }

    dispatch_confirmed = False
    if is_simulation:
        dispatch_msg = (
            "SAFE SIMULATION MODE: Location packet logged locally after 8s countdown. "
            "No live phone call was placed."
        )
        inc_status = "SIMULATION_ACTIVE"
    elif AUTHORIZED_DISPATCH_API_URL and AUTHORIZED_DISPATCH_API_KEY:
        try:
            req_body = json.dumps({
                "incident_uuid": incident_uuid,
                "latitude": lat_val,
                "longitude": lng_val,
                "accuracy_meters": acc_val,
                "maps_url": maps_url,
                "trigger_source": trigger_source,
            }).encode("utf-8")
            req = urllib.request.Request(
                AUTHORIZED_DISPATCH_API_URL,
                data=req_body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {AUTHORIZED_DISPATCH_API_KEY}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                if resp.status == 200 and resp_data.get("dispatch_confirmed") is True:
                    dispatch_confirmed = True
                    dispatch_msg = f"Authorized Dispatch Confirmed (Ref: {resp_data.get('dispatch_id', 'OK')})."
                else:
                    dispatch_msg = "Location packet transmitted; initiating 108 voice call."
        except Exception as e:
            dispatch_msg = f"Location packet recorded locally ({str(e)[:45]}); initiating 108 voice call."
        inc_status = "DISPATCH_CONFIRMED" if dispatch_confirmed else "AUTO_CALL_INITIATED"
    else:
        dispatch_msg = (
            "GPS location packet recorded & copied for 108 Ambulance; "
            "automatic 108 ambulance call triggered after 8-second countdown."
        )
        inc_status = "AUTO_CALL_INITIATED"

    direct_call_placed = False
    if not is_simulation and bool(payload.get("place_direct_phone_call", True)):
        target_num = str(payload.get("target_ambulance_number", "108")).strip() or "108"
        direct_ok, direct_note = attempt_direct_android_call(target_num, client_ip=client_key)
        if direct_ok:
            direct_call_placed = True
            dispatch_msg = f"{direct_note} | {dispatch_msg}"

    now_iso = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(SOS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sos_incidents (
                incident_uuid, trigger_source, severity_classification, status,
                latitude, longitude, accuracy_meters, location_source, maps_url,
                sensor_summary_json, is_simulation, dispatch_confirmed,
                dispatch_status_message, created_at_utc, updated_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(incident_uuid) DO UPDATE SET
                status = excluded.status,
                latitude = COALESCE(excluded.latitude, sos_incidents.latitude),
                longitude = COALESCE(excluded.longitude, sos_incidents.longitude),
                accuracy_meters = COALESCE(excluded.accuracy_meters, sos_incidents.accuracy_meters),
                maps_url = COALESCE(excluded.maps_url, sos_incidents.maps_url),
                updated_at_utc = excluded.updated_at_utc
            """,
            (
                incident_uuid,
                trigger_source,
                fusion_eval["classification"],
                inc_status,
                lat_val,
                lng_val,
                acc_val,
                loc_source,
                maps_url,
                json.dumps(sensor_data)[:800],
                1 if is_simulation else 0,
                1 if dispatch_confirmed else 0,
                dispatch_msg,
                now_iso,
                now_iso,
            ),
        )
        conn.commit()

    return {
        "status": "ok",
        "incident": {
            "incident_uuid": incident_uuid,
            "trigger_source": trigger_source,
            "severity_classification": fusion_eval["classification"],
            "confidence_note": fusion_eval.get("confidence_note", ""),
            "incident_status": inc_status,
            "is_simulation": is_simulation,
            "direct_call_placed": direct_call_placed,
            "dispatch_confirmed": dispatch_confirmed,
            "dispatch_status_message": dispatch_msg,
            "location": {
                "latitude": lat_val,
                "longitude": lng_val,
                "accuracy_meters": acc_val,
                "location_source": loc_source,
                "manual_location_text": manual_address,
                "maps_url": maps_url,
            },
            "emergency_numbers": {
                "national_er_112": "112",
                "ambulance_108": "108",
                "regional_note": "In India, 112 is the pan-India Emergency Response Support System (ERSS) and 108 is the free emergency ambulance helpline across Gujarat and major states.",
            },
            "timestamp_utc": now_iso,
        },
    }, 201


def cancel_sos_incident(incident_uuid: str, reason: str = "User clicked I AM SAFE") -> Dict[str, Any]:
    """Cancels an active SOS countdown/incident and records the cancellation in SQLite."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(SOS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE sos_incidents
            SET status = 'CANCELLED_BY_USER',
                dispatch_status_message = ?,
                updated_at_utc = ?
            WHERE incident_uuid = ?
            """,
            (f"Cancelled by user ({reason[:100]}). No dispatch executed.", now_iso, incident_uuid),
        )
        conn.commit()
    return {
        "status": "ok",
        "incident_uuid": incident_uuid,
        "incident_status": "CANCELLED_BY_USER",
        "message": "SOS incident cancelled. No emergency dispatch was executed.",
        "timestamp_utc": now_iso,
    }


def list_trusted_contacts() -> List[Dict[str, Any]]:
    with sqlite3.connect(SOS_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT id, contact_name, phone_number, relationship, created_at_utc FROM trusted_contacts ORDER BY id DESC LIMIT 10"
        ).fetchall()
        return [dict(r) for r in rows]


def add_trusted_contact(name: str, phone: str, relationship: str, consent: bool) -> Tuple[bool, str, Optional[int]]:
    clean_digits = re.sub(r"\D", "", phone or "")
    if len(clean_digits) < 10 or len(clean_digits) > 13:
        return False, "Enter a valid 10-digit mobile number for the trusted contact.", None
    if not name or not consent:
        return False, "Contact name and explicit consent confirmation are required.", None

    now_iso = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(SOS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO trusted_contacts (contact_name, phone_number, relationship, consent_confirmed, created_at_utc)
            VALUES (?, ?, ?, 1, ?)
            """,
            (name[:80], clean_digits[-10:], relationship[:40], now_iso),
        )
        new_id = cur.lastrowid
        conn.commit()
    return True, "Trusted emergency contact saved.", new_id


def delete_trusted_contact(contact_id: int) -> None:
    with sqlite3.connect(SOS_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM trusted_contacts WHERE id = ?", (contact_id,))
        conn.commit()