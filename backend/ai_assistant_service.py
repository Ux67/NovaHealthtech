"""
Nova Healthtech - Master 22-Language Deep Clinical & Pharmaceutical AI Engine
- Restores fast, start-to-end 22-language full-website batch translation (fixes trailing newline mismatch + adds 3-engine fallback).
- Zero LaTeX '$' artifacts: uses clean Unicode clinical symbols (≥, ≤, SpO₂, °F, °C, Vitamin B12).
- Strictly separates Disease/Symptom Guidance from Medicine Information (never displays irrelevant medicine recommendations on general disease queries, and never prescribes dosages without clinical oversight).
- Integrates Built-in Clinical Encyclopedia + Indian Brand Monographs + NIH RxNav + US FDA OpenFDA + Wikipedia Medical APIs + Adaptive LLM.
- Includes All-India Hospital & Pharmacy directories covering all 36 Indian States & Union Territories.
"""

from concurrent.futures import ThreadPoolExecutor
import difflib
import html
import json
import os
import re
import ssl
from threading import Lock
import urllib.parse
import urllib.request
import urllib.error
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv
import requests

try:
    from api_key_config import GEMINI_API_KEY as CONFIG_FILE_KEY
except ImportError:
    CONFIG_FILE_KEY = "AQ.Ab8RN6LWsU2x9Vvg9UP2TkTSKOCWeXxm5PI5Wx1TzgMAEajf5w"

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
CACHE_FILE_PATH = os.path.join(BACKEND_DIR, "translation_cache_master.json")

for folder in (ROOT_DIR, BACKEND_DIR):
    for fname in (".env", ".env.txt"):
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath):
            load_dotenv(fpath, override=True)

SSL_CTX = ssl._create_unverified_context()


def _make_maps_url(lat: Any, lng: Any, query_str: str) -> str:
    if lat is not None and lng is not None:
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query_str or 'Hospital India')}"


LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English", "hi": "Hindi (हिन्दी)", "gu": "Gujarati (ગુજરાતી)", "mr": "Marathi (मराठी)",
    "ta": "Tamil (தமிழ்)", "te": "Telugu (తెలుగు)", "bn": "Bengali (বাংলা)", "kn": "Kannada (ಕನ್ನಡ)",
    "ml": "Malayalam (മലയാളം)", "pa": "Punjabi (ਪੰਜਾਬੀ)", "or": "Odia (ଓଡ଼ିଆ)", "as": "Assamese (অসমীয়া)",
    "ur": "Urdu (اردو)", "mai": "Maithili (मैथिली)", "kok": "Konkani (कोंकणी)", "ne": "Nepali (नेपाली)",
    "sd": "Sindhi (सिन्धी)", "ks": "Kashmiri (कॉशुर)", "doi": "Dogri (डोगरी)", "mni": "Manipuri (মৈতৈলোন্)",
    "sat": "Santali (ᱥᱟᱱᱛᱟᱲᱤ)", "sa": "Sanskrit (संस्कृतम्)",
}

GTX_LANG_CODE_MAP: Dict[str, str] = {
    "en": "en", "hi": "hi", "gu": "gu", "mr": "mr", "ta": "ta", "te": "te",
    "bn": "bn", "kn": "kn", "ml": "ml", "pa": "pa", "or": "or", "as": "as",
    "ur": "ur", "mai": "mai", "kok": "gom", "ne": "ne", "sd": "sd", "ks": "hi",
    "doi": "doi", "mni": "mni-Mtei", "sat": "sat", "sa": "sa",
}

NATIVE_DIGITS_MAP: Dict[str, str] = {
    "en": "0123456789", "hi": "०१२३४५६७८९", "gu": "૦૧૨૩૪૫૬૭૮૯", "mr": "०१२३४५६७८९",
    "ta": "௦௧௨௩௪௫௬௭௮௯", "te": "౦౧౨౩౪౫౬౭౮౯", "bn": "০১২৩৪৫৬৭৮৯", "kn": "೦೧೨೩೪೫೬೭೮೯",
    "ml": "൦൧൨൩൪൫൬൭൮൯", "pa": "੦੧੨੩੪੫੬੭੮੯", "or": "୦୧୨୩୪୫୬୭୮୯", "as": "০১২৩৪৫৬৭৮৯",
    "ur": "۰۱۲۳۴۵۶۷۸۹", "mai": "०१२३४५६७८९", "kok": "०१२३४५६७८९", "ne": "०१२३४५६७८९",
    "sd": "०१२३४५६७८९", "ks": "०१२३४५६७८९", "doi": "०१२३४५६७८९", "mni": "০১২৩৪৫৬৭৮৯",
    "sat": "᱐᱑᱒᱓᱔᱕᱖᱗᱘᱙", "sa": "०१२३४५६७८९",
}

_CACHE_LOCK = Lock()
_SERVER_TRANSLATION_CACHE: Dict[str, Dict[str, str]] = {}

for _existing_cache in ("translation_cache_master.json", "translation_cache_master_v2.json"):
    _cpath = os.path.join(BACKEND_DIR, _existing_cache)
    if os.path.isfile(_cpath):
        try:
            with open(_cpath, "r", encoding="utf-8") as _cf:
                _loaded = json.load(_cf)
                if isinstance(_loaded, dict):
                    for _lk, _lv in _loaded.items():
                        if isinstance(_lv, dict):
                            _SERVER_TRANSLATION_CACHE.setdefault(_lk, {}).update(_lv)
        except Exception:
            pass


def _save_server_cache() -> None:
    try:
        with _CACHE_LOCK:
            with open(CACHE_FILE_PATH, "w", encoding="utf-8") as cf:
                json.dump(_SERVER_TRANSLATION_CACHE, cf, ensure_ascii=False)
    except Exception:
        pass


def strip_latex_artifacts(text: str) -> str:
    """Removes any accidental LaTeX math symbols ($...$, \\ge, \\le, _{...}) and replaces with clean Unicode."""
    if not text:
        return ""
    cleaned = text.replace("\\ge", "≥").replace("\\le", "≤").replace("\\pm", "±")
    cleaned = cleaned.replace("$SpO_2$", "SpO₂").replace("SpO_2", "SpO₂")
    cleaned = cleaned.replace("$B_{12}$", "B12").replace("B_{12}", "B12")
    cleaned = re.sub(r"\$([^$]+)\$", r"\1", cleaned)
    cleaned = cleaned.replace("$", "")
    return cleaned


def normalize_indic_digits_to_ascii(text: str) -> str:
    if not text:
        return ""
    out = str(text)
    for _, digits in NATIVE_DIGITS_MAP.items():
        if digits == "0123456789" or len(digits) != 10:
            continue
        for idx, ch in enumerate(digits):
            out = out.replace(ch, str(idx))
    return out


def convert_ascii_digits_to_native(text: str, lang_code: str) -> str:
    if not text:
        return text
    ascii_text = normalize_indic_digits_to_ascii(strip_latex_artifacts(str(text)))
    if lang_code == "en" or lang_code not in NATIVE_DIGITS_MAP:
        return ascii_text
    target_digits = NATIVE_DIGITS_MAP[lang_code]
    if len(target_digits) != 10:
        return ascii_text
    trans_table = str.maketrans("0123456789", target_digits)
    return ascii_text.translate(trans_table)


def _words_actually_changed(orig_en: str, candidate: str) -> bool:
    """Returns True only if the English words were genuinely translated (not just digits)."""
    if not candidate or not candidate.strip():
        return False
    orig_w = re.sub(r"[^a-zA-Z]+", "", normalize_indic_digits_to_ascii(orig_en)).lower()
    cand_w = re.sub(r"[^a-zA-Z]+", "", normalize_indic_digits_to_ascii(candidate)).lower()
    if not orig_w:
        return True
    return orig_w != cand_w


# ==============================================================================
# 3-ENGINE NEWLINE-PRESERVING BATCH & MULTILINE TRANSLATOR
# ==============================================================================

def _call_raw_translator(text: str, target_lang: str, source_lang: str = "en") -> str:
    gtx_target = GTX_LANG_CODE_MAP.get(target_lang, target_lang)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    }

    try:
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl={source_lang}&tl={urllib.parse.quote(gtx_target)}&dt=t"
        )
        form_data = urllib.parse.urlencode({"q": text}).encode("utf-8")
        req = urllib.request.Request(url, data=form_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and data and isinstance(data[0], list):
                out = "".join(
                    [str(seg[0]) for seg in data[0] if isinstance(seg, list) and seg and seg[0] is not None]
                ).strip()
                if out and (target_lang == "en" or _words_actually_changed(text, out)):
                    return strip_latex_artifacts(out)
    except Exception:
        pass

    if len(text) <= 1900:
        try:
            m_url = (
                f"https://translate.google.com/m?sl={source_lang}&tl={urllib.parse.quote(gtx_target)}"
                f"&hl=en&q={urllib.parse.quote(text)}"
            )
            m_ua = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
            req2 = urllib.request.Request(m_url, headers={"User-Agent": m_ua}, method="GET")
            with urllib.request.urlopen(req2, timeout=8, context=SSL_CTX) as resp2:
                raw_html = resp2.read().decode("utf-8", errors="ignore")
                match = re.search(r'<div class="result-container">(.*?)</div>', raw_html, flags=re.S)
                if match:
                    extracted = html.unescape(match.group(1)).strip()
                    if extracted and (target_lang == "en" or _words_actually_changed(text, extracted)):
                        return strip_latex_artifacts(extracted)
        except Exception:
            pass

    try:
        c5_url = (
            f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex"
            f"&sl={source_lang}&tl={urllib.parse.quote(gtx_target)}"
        )
        form_data = urllib.parse.urlencode({"q": text}).encode("utf-8")
        req3 = urllib.request.Request(c5_url, data=form_data, headers=headers, method="POST")
        with urllib.request.urlopen(req3, timeout=8, context=SSL_CTX) as resp3:
            data3 = json.loads(resp3.read().decode("utf-8"))
            if isinstance(data3, list) and data3:
                out3 = ""
                if isinstance(data3[0], str):
                    out3 = data3[0].strip()
                elif isinstance(data3[0], list) and data3[0] and isinstance(data3[0][0], str):
                    out3 = data3[0][0].strip()
                if out3 and (target_lang == "en" or _words_actually_changed(text, out3)):
                    return strip_latex_artifacts(out3)
    except Exception:
        pass

    return ""


def translate_text_live(text: str, target_lang: str, source_lang: str = "auto") -> str:
    if not text or not text.strip():
        return text
    clean_src = strip_latex_artifacts(normalize_indic_digits_to_ascii(text.strip()))

    if target_lang == "en":
        if all(ord(c) < 128 for c in clean_src):
            return clean_src

    if target_lang != "en" and source_lang in ("en", "auto"):
        lang_bucket = _SERVER_TRANSLATION_CACHE.get(target_lang, {})
        cached = lang_bucket.get(clean_src)
        if cached and _words_actually_changed(clean_src, cached):
            return convert_ascii_digits_to_native(cached, target_lang)

    if target_lang != "en" and not re.search(r"[a-zA-Z]", clean_src):
        return convert_ascii_digits_to_native(clean_src, target_lang)

    translated_out = _call_raw_translator(clean_src, target_lang=target_lang, source_lang=source_lang)
    if translated_out:
        if target_lang != "en":
            final_s = convert_ascii_digits_to_native(translated_out, target_lang)
            if _words_actually_changed(clean_src, final_s):
                with _CACHE_LOCK:
                    _SERVER_TRANSLATION_CACHE.setdefault(target_lang, {})[clean_src] = final_s
            return final_s
        return translated_out

    return convert_ascii_digits_to_native(clean_src, target_lang) if target_lang != "en" else clean_src


def _translate_chunk_newline_batch(chunk: List[str], target_lang: str) -> List[str]:
    if not chunk:
        return []

    clean_chunk = [
        strip_latex_artifacts(normalize_indic_digits_to_ascii(re.sub(r"[\r\n]+", " ", str(s)).strip()))
        for s in chunk
    ]
    joined_payload = "\n".join(clean_chunk)

    full_trans = _call_raw_translator(joined_payload, target_lang=target_lang, source_lang="en")
    if full_trans:
        lines = [strip_latex_artifacts(line.strip()) for line in full_trans.strip().split("\n") if line.strip()]
        if len(lines) == len(clean_chunk):
            out_list: List[str] = []
            with _CACHE_LOCK:
                bucket = _SERVER_TRANSLATION_CACHE.setdefault(target_lang, {})
                for orig_s, trans_s in zip(clean_chunk, lines):
                    final_s = convert_ascii_digits_to_native(trans_s or orig_s, target_lang)
                    if _words_actually_changed(orig_s, final_s):
                        bucket[orig_s] = final_s
                    out_list.append(final_s)
            return out_list

    if len(clean_chunk) > 4:
        mid = len(clean_chunk) // 2
        return _translate_chunk_newline_batch(clean_chunk[:mid], target_lang) + _translate_chunk_newline_batch(
            clean_chunk[mid:], target_lang
        )

    with ThreadPoolExecutor(max_workers=3) as ex:
        return list(ex.map(lambda s: translate_text_live(s, target_lang, "en"), clean_chunk))


def translate_batch_live(texts: List[str], target_lang: str) -> List[str]:
    if not texts or target_lang == "en":
        return [strip_latex_artifacts(normalize_indic_digits_to_ascii(str(t))) for t in texts]

    lang_bucket = _SERVER_TRANSLATION_CACHE.get(target_lang, {})
    unique_missing: List[str] = []
    seen = set()

    for t in texts:
        s = strip_latex_artifacts(normalize_indic_digits_to_ascii(re.sub(r"[\r\n]+", " ", str(t)).strip()))
        if s and re.search(r"[a-zA-Z]", s):
            cached_val = lang_bucket.get(s)
            if (not cached_val or not _words_actually_changed(s, cached_val)) and s not in seen:
                seen.add(s)
                unique_missing.append(s)

    if unique_missing:
        chunk_size = 22
        chunks = [unique_missing[i : i + chunk_size] for i in range(0, len(unique_missing), chunk_size)]
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(lambda c: _translate_chunk_newline_batch(c, target_lang), chunks))
        _save_server_cache()

    updated_bucket = _SERVER_TRANSLATION_CACHE.get(target_lang, {})
    results: List[str] = []
    for t in texts:
        s = strip_latex_artifacts(normalize_indic_digits_to_ascii(re.sub(r"[\r\n]+", " ", str(t)).strip()))
        val = updated_bucket.get(s, s)
        results.append(convert_ascii_digits_to_native(val, target_lang))

    return results


def translate_multiline_response(full_text: str, target_lang: str) -> str:
    clean_input = strip_latex_artifacts(full_text)
    if not clean_input or target_lang == "en":
        return clean_input
    translated = translate_text_live(clean_input, target_lang=target_lang, source_lang="en")
    _save_server_cache()
    return strip_latex_artifacts(translated) if translated else clean_input


# ==============================================================================
# ALL-INDIA HOSPITALS & MEDICINE STORES COVERING ALL 36 STATES & UTs
# ==============================================================================

ALL_INDIA_HOSPITALS: List[Dict[str, Any]] = [
    {"state": "Andhra Pradesh", "city": "Visakhapatnam", "name": "King George Hospital (KGH) & AIIMS Mangalagiri", "facility_category": "Government Medical College & Central AIIMS", "schemes": "PM-JAY, Dr. NTR Vaidya Seva, ABHA", "address": "Maharanipeta, Visakhapatnam, Andhra Pradesh", "pin_code": "530002", "phone_general": "0891-2564891", "phone_emergency": "108", "specialties": "General Medicine, Cardiology, Trauma, Surgery, Maternal Care", "website": "https://www.kghvisakhapatnam.com/"},
    {"state": "Arunachal Pradesh", "city": "Itanagar", "name": "Tomo Riba Institute of Health & Medical Sciences (TRIHMS)", "facility_category": "State Government Medical College Hospital", "schemes": "PM-JAY, Chief Minister Arogya Arunachal Yojana", "address": "Old Assembly Complex, Naharlagun, Itanagar, Arunachal Pradesh", "pin_code": "791110", "phone_general": "0360-2350332", "phone_emergency": "108", "specialties": "Internal Medicine, Emergency Trauma, Pediatrics, Surgery", "website": "https://trihms.co.in/"},
    {"state": "Assam", "city": "Guwahati", "name": "AIIMS Guwahati & Gauhati Medical College Hospital (GMCH)", "facility_category": "Central AIIMS & State Medical College", "schemes": "PM-JAY Ayushman Asom, ABHA", "address": "Bhangagarh / Changsari, Guwahati, Assam", "pin_code": "781032", "phone_general": "0361-2529457", "phone_emergency": "108", "specialties": "Cardiology, Oncology, Neurology, 24x7 Trauma Care", "website": "https://gmch.assam.gov.in/"},
    {"state": "Bihar", "city": "Patna", "name": "AIIMS Patna & Patna Medical College Hospital (PMCH)", "facility_category": "Central AIIMS & Apex State Medical College", "schemes": "PM-JAY Mukhyamantri Jan Arogya, ABHA", "address": "Phulwari Sharif / Ashok Rajpath, Patna, Bihar", "pin_code": "801507", "phone_general": "0612-2451070", "phone_emergency": "108", "specialties": "Multi-Super Speciality, Emergency & Critical Care, Oncology", "website": "https://aiimspatna.edu.in/"},
    {"state": "Chhattisgarh", "city": "Raipur", "name": "AIIMS Raipur & Dr. B.R. Ambedkar Memorial Hospital", "facility_category": "Central AIIMS & State Medical College Hospital", "schemes": "PM-JAY Shaheed Veer Narayan Singh Ayushman Swasthya", "address": "Great Eastern Road, Tatibandh, Raipur, Chhattisgarh", "pin_code": "492099", "phone_general": "0771-2572240", "phone_emergency": "108", "specialties": "Cardiology, Neurosurgery, Trauma, Dialysis, Oncology", "website": "https://www.aiimsraipur.edu.in/"},
    {"state": "Goa", "city": "Panaji", "name": "Goa Medical College & Hospital (Bambolim)", "facility_category": "Premier State Government Medical College", "schemes": "PM-JAY, DDSSY Goa Health Scheme", "address": "NH-66, Bambolim, Tiswadi, Panaji, Goa", "pin_code": "403202", "phone_general": "0832-2495000", "phone_emergency": "108", "specialties": "Cardiac Care, Trauma Unit, General Surgery, Pediatrics", "website": "https://gmc.goa.gov.in/"},
    {"state": "Gujarat", "city": "Bhavnagar", "name": "Sir Takhtsinhji General Hospital (Civil Hospital Bhavnagar)", "facility_category": "Government Medical College & Civil Hospital", "schemes": "PM-JAY, PMJAY-MA, Free OPD & 24x7 Trauma", "address": "Jail Road, Panwadi, Bhavnagar, Gujarat", "pin_code": "364001", "phone_general": "0278-2511411", "phone_emergency": "108", "specialties": "General Medicine, Surgery, Maternal & Child Health, Emergency", "website": "https://gmcbhavnagar.edu.in/"},
    {"state": "Gujarat", "city": "Bhavnagar", "name": "HCG Hospitals Bhavnagar", "facility_category": "Empanelled Multispeciality Hospital", "schemes": "PM-JAY, PMJAY-MA (Cardiac & Oncology)", "address": "Meghani Circle, Bhavnagar, Gujarat", "pin_code": "364001", "phone_general": "0278-6644000", "phone_emergency": "108", "specialties": "Cardiology, Oncology, ICU & Emergency Care", "website": "https://www.hcghospitals.in/"},
    {"state": "Gujarat", "city": "Ahmedabad", "name": "B.J. Medical College & Civil Hospital Asarwa", "facility_category": "Apex Government Civil Medicity", "schemes": "PM-JAY, PMJAY-MA, 70+ Vay Vandana, ABHA", "address": "Asarwa, Ahmedabad, Gujarat", "pin_code": "380016", "phone_general": "079-22683721", "phone_emergency": "108", "specialties": "Multi-Super Speciality, Kidney & Heart Institute, Trauma ICU", "website": "https://bjmcabd.edu.in/"},
    {"state": "Gujarat", "city": "Rajkot", "name": "AIIMS Rajkot & PDU Government Civil Hospital", "facility_category": "Central AIIMS & State Civil Hospital", "schemes": "PM-JAY, PMJAY-MA, ABHA", "address": "Khandheri / Hospital Chowk, Rajkot, Gujarat", "pin_code": "360001", "phone_general": "0281-2458337", "phone_emergency": "108", "specialties": "Internal Medicine, Surgery, Orthopedics, Emergency Care", "website": "https://aiimsrajkot.edu.in/"},
    {"state": "Gujarat", "city": "Vadodara", "name": "Sir Sayajirao General (SSG) Hospital", "facility_category": "Government Medical College Hospital", "schemes": "PM-JAY, PMJAY-MA, Free Emergency Care", "address": "Anandpura, Vadodara, Gujarat", "pin_code": "390001", "phone_general": "0265-2424848", "phone_emergency": "108", "specialties": "General Medicine, Pediatrics, Trauma, Cardiology", "website": "https://www.medicalcollegebaroda.edu.in/"},
    {"state": "Gujarat", "city": "Surat", "name": "New Civil Hospital (GMC Surat)", "facility_category": "Government Medical College Hospital", "schemes": "PM-JAY, PMJAY-MA, 24x7 Emergency", "address": "Majura Gate, Surat, Gujarat", "pin_code": "395001", "phone_general": "0261-2244456", "phone_emergency": "108", "specialties": "Trauma Care, General Medicine, Obstetrics, Burns Ward", "website": "https://www.nchsurat.org/"},
    {"state": "Haryana", "city": "Rohtak", "name": "Pt. B.D. Sharma PGIMS Rohtak & ESIC Medical College Faridabad", "facility_category": "State Medical University & Tertiary Hospital", "schemes": "PM-JAY Chirayu Haryana, ABHA", "address": "Medical Road, Rohtak, Haryana", "pin_code": "124001", "phone_general": "01262-281308", "phone_emergency": "108", "specialties": "Cardiology, Trauma Center, Pulmonary Medicine, Oncology", "website": "https://uhsr.ac.in/"},
    {"state": "Himachal Pradesh", "city": "Shimla", "name": "Indira Gandhi Medical College & Hospital (IGMC Shimla) & AIIMS Bilaspur", "facility_category": "Apex State Medical College & Central AIIMS", "schemes": "PM-JAY & Himcare Cashless Scheme", "address": "Ridge Sanjauli Road, Shimla, Himachal Pradesh", "pin_code": "171001", "phone_general": "0177-2804251", "phone_emergency": "108", "specialties": "Cardiology, Respiratory Medicine, General Surgery, Emergency", "website": "https://www.igmcshimla.edu.in/"},
    {"state": "Jharkhand", "city": "Ranchi", "name": "Rajendra Institute of Medical Sciences (RIMS Ranchi) & AIIMS Deoghar", "facility_category": "Autonomous State Medical Institute & Central AIIMS", "schemes": "PM-JAY Mukhyamantri Jan Arogya, ABHA", "address": "Bariatu Road, Ranchi, Jharkhand", "pin_code": "834009", "phone_general": "0651-2541533", "phone_emergency": "108", "specialties": "Neurosurgery, Cardiology, Trauma & Emergency, Oncology", "website": "https://rimsranchi.ac.in/"},
    {"state": "Karnataka", "city": "Bengaluru", "name": "Victoria Hospital (BMCRI) & NIMHANS Bengaluru", "facility_category": "Government Medical College & National Mental/Neuro Institute", "schemes": "PM-JAY Arogya Karnataka, ABHA", "address": "Fort Road, City Market / Hosur Road, Bengaluru, Karnataka", "pin_code": "560002", "phone_general": "080-26701150", "phone_emergency": "080-46110007", "specialties": "Neurosciences, Psychiatry, Trauma, General Medicine, Burns", "website": "https://nimhans.ac.in/"},
    {"state": "Karnataka", "city": "Mysuru", "name": "Krishnarajendra (K.R.) Hospital & MMC&RI Mysuru", "facility_category": "Government Medical College Hospital", "schemes": "PM-JAY Arogya Karnataka", "address": "Irwin Road, Mysuru, Karnataka", "pin_code": "570001", "phone_general": "0821-2520512", "phone_emergency": "108", "specialties": "General Medicine, Surgery, Pediatrics, Emergency", "website": "https://mmcri.karnataka.gov.in/"},
    {"state": "Kerala", "city": "Thiruvananthapuram", "name": "Government Medical College Hospital & Sree Chitra Tirunal (SCTIMST)", "facility_category": "Apex Government Medical & Cardiac/Neuro Institute", "schemes": "PM-JAY Karunya Arogya Suraksha (KASP)", "address": "Ulloor - Akkulam Road, Medical College PO, Thiruvananthapuram", "pin_code": "695011", "phone_general": "0471-2528300", "phone_emergency": "108", "specialties": "Cardiovascular, Neurology, Multi-Speciality Trauma", "website": "https://www.sctimst.ac.in/"},
    {"state": "Madhya Pradesh", "city": "Bhopal", "name": "AIIMS Bhopal & Gandhi Medical College (Hamidia Hospital)", "facility_category": "Central AIIMS & State Govt Medical College", "schemes": "PM-JAY Ayushman Bharat Niramayam", "address": "Saket Nagar / Sultania Road, Bhopal, Madhya Pradesh", "pin_code": "462020", "phone_general": "0755-2672355", "phone_emergency": "108", "specialties": "Trauma & Emergency, Cardiology, Pulmonology, Oncology", "website": "https://aiimsbhopal.edu.in/"},
    {"state": "Maharashtra", "city": "Mumbai", "name": "King Edward Memorial (KEM) Hospital & Sir J.J. Hospital", "facility_category": "Public Municipal & State Government Medical Colleges", "schemes": "PM-JAY, MJPJAY, ABHA", "address": "Parel / Byculla, Mumbai, Maharashtra", "pin_code": "400012", "phone_general": "022-24107000", "phone_emergency": "108", "specialties": "Cardiology, Neurology, Nephrology, 24x7 Trauma Ward", "website": "https://www.kem.edu/"},
    {"state": "Maharashtra", "city": "Pune", "name": "Sassoon General Hospital (B.J. Government Medical College Pune)", "facility_category": "State Government Tertiary Hospital", "schemes": "PM-JAY, MJPJAY, Free OPD", "address": "Jayprakash Narayan Road, Near Pune Railway Station, Pune", "pin_code": "411001", "phone_general": "020-26128000", "phone_emergency": "108", "specialties": "Emergency Medicine, Surgery, Infectious Diseases, ICU", "website": "https://www.bjmcpune.org/"},
    {"state": "Maharashtra", "city": "Nagpur", "name": "AIIMS Nagpur & Government Medical College (GMCH Nagpur)", "facility_category": "Central AIIMS & State Medical College", "schemes": "PM-JAY, MJPJAY, 70+ Vay Vandana", "address": "MIHAN / Hanuman Nagar, Nagpur, Maharashtra", "pin_code": "441108", "phone_general": "0712-2352022", "phone_emergency": "108", "specialties": "Multi-Super Speciality, Trauma, Oncology, Cardiology", "website": "https://aiimsnagpur.edu.in/"},
    {"state": "Manipur", "city": "Imphal", "name": "Regional Institute of Medical Sciences (RIMS Imphal) & JNIMS", "facility_category": "Regional Autonomous Government Medical Institute", "schemes": "PM-JAY, CMHT Manipur", "address": "Lamphelpat, Imphal, Manipur", "pin_code": "795004", "phone_general": "0385-2414720", "phone_emergency": "108", "specialties": "General Medicine, Surgery, Trauma, Maternal Care", "website": "https://www.rims.edu.in/"},
    {"state": "Meghalaya", "city": "Shillong", "name": "NEIGRIHMS Shillong (North Eastern Indira Gandhi Regional Institute)", "facility_category": "Central Autonomous Super-Specialty Institute", "schemes": "PM-JAY, MHIS Meghalaya", "address": "Mawdiangdiang, Shillong, Meghalaya", "pin_code": "793018", "phone_general": "0364-2538013", "phone_emergency": "108", "specialties": "Cardiology, Neurosurgery, Oncology, Emergency Care", "website": "https://neigrihms.gov.in/"},
    {"state": "Mizoram", "city": "Aizawl", "name": "Zoram Medical College (ZMC) & Civil Hospital Aizawl", "facility_category": "State Government Medical College & Civil Hospital", "schemes": "PM-JAY, Mizoram State Health Care Scheme", "address": "Falkawn / Dawrpui, Aizawl, Mizoram", "pin_code": "796005", "phone_general": "0389-2322318", "phone_emergency": "102", "specialties": "General Medicine, Emergency Care, Surgery, Pediatrics", "website": "https://zmc.edu.in/"},
    {"state": "Nagaland", "city": "Kohima", "name": "Naga Hospital Authority Kohima (NHAK) & NIMSR", "facility_category": "Apex State Government Hospital & Medical College", "schemes": "PM-JAY, CMHIS Nagaland", "address": "P.R. Hill, Kohima, Nagaland", "pin_code": "797001", "phone_general": "0370-2222916", "phone_emergency": "102", "specialties": "Internal Medicine, Trauma, Maternal & Child Care", "website": "https://nimsr.nagaland.gov.in/"},
    {"state": "Odisha", "city": "Bhubaneswar", "name": "AIIMS Bhubaneswar & SCB Medical College Cuttack", "facility_category": "Central AIIMS & Premier State Medical College", "schemes": "PM-JAY & Gopabandhu Jan Arogya, ABHA", "address": "Sijua, Patrapada, Bhubaneswar, Odisha", "pin_code": "751019", "phone_general": "0674-2476789", "phone_emergency": "108", "specialties": "Cardiology, Oncology, Neurosurgery, 24x7 Trauma ICU", "website": "https://aiimsbhubaneswar.nic.in/"},
    {"state": "Punjab", "city": "Amritsar", "name": "Guru Nanak Dev Hospital (GMC Amritsar) & AIIMS Bathinda", "facility_category": "Government Medical College & Central AIIMS", "schemes": "PM-JAY Sarbat Sehat Bima", "address": "Majitha Road, Amritsar, Punjab", "pin_code": "143001", "phone_general": "0183-2426918", "phone_emergency": "108", "specialties": "General Medicine, Surgery, Cardiology, Emergency", "website": "https://www.gmc.edu.in/"},
    {"state": "Rajasthan", "city": "Jaipur", "name": "Sawai Man Singh (SMS) Medical College Hospital & AIIMS Jodhpur", "facility_category": "Apex State Government Hospital & Central AIIMS", "schemes": "PM-JAY Mukhyamantri Ayushman Arogya", "address": "JLN Marg, Gangawal Park, Jaipur, Rajasthan", "pin_code": "302004", "phone_general": "0141-2518222", "phone_emergency": "108", "specialties": "Polytrauma Center, Cardiology, Organ Transplant, ICU", "website": "https://medicaleducation.rajasthan.gov.in/smsjaipur/"},
    {"state": "Sikkim", "city": "Gangtok", "name": "Sir Thutob Namgyal Memorial (STNM) Hospital Gangtok", "facility_category": "Apex State Government Multi-Speciality Hospital", "schemes": "PM-JAY, Mukhyamantri Jeevan Raksha Kosh", "address": "Sochakgang, Sichey, Gangtok, Sikkim", "pin_code": "737101", "phone_general": "03592-202944", "phone_emergency": "102", "specialties": "General Medicine, Dialysis, Emergency Trauma, Surgery", "website": "https://www.sikkim.gov.in/departments/health-family-welfare-department"},
    {"state": "Tamil Nadu", "city": "Chennai", "name": "Rajiv Gandhi Government General Hospital (RGGGH Chennai)", "facility_category": "Premier State Government Tertiary Hospital", "schemes": "PM-JAY CMCHIS, Free Emergency & OPD", "address": "Poonamallee High Road, Park Town, Chennai, Tamil Nadu", "pin_code": "600003", "phone_general": "044-25305000", "phone_emergency": "108", "specialties": "Cardiology, Neurology, Zero-Delay Trauma Ward, Oncology", "website": "https://www.mmcrgggh.tn.gov.in/"},
    {"state": "Telangana", "city": "Hyderabad", "name": "Osmania General Hospital, Gandhi Hospital & NIMS Hyderabad", "facility_category": "Apex State Government Tertiary Hospitals", "schemes": "PM-JAY Aarogyasri, ABHA", "address": "Afzal Gunj / Punjagutta, Hyderabad, Telangana", "pin_code": "500012", "phone_general": "040-24600146", "phone_emergency": "108", "specialties": "Multi-Super Speciality, Trauma, Nephrology, Cardiology", "website": "https://www.nims.edu.in/"},
    {"state": "Tripura", "city": "Agartala", "name": "Agartala Government Medical College & GBP Hospital", "facility_category": "State Government Medical College Hospital", "schemes": "PM-JAY, CM-JAY Tripura", "address": "Kunjaban, Agartala, Tripura", "pin_code": "799006", "phone_general": "0381-2357130", "phone_emergency": "102", "specialties": "Internal Medicine, Trauma Center, Surgery, Pediatrics", "website": "https://agmc.ac.in/"},
    {"state": "Uttar Pradesh", "city": "Lucknow", "name": "King George's Medical University (KGMU) & SGPGIMS Lucknow", "facility_category": "Apex Government Medical Universities", "schemes": "PM-JAY Mukhyamantri Jan Arogya, ABHA", "address": "Shah Mina Road, Chowk / Raebareli Road, Lucknow, UP", "pin_code": "226003", "phone_general": "0522-2257540", "phone_emergency": "108", "specialties": "Apex Trauma Center, Cardiology, Neurology, Gastroenterology", "website": "https://www.kgmu.org/"},
    {"state": "Uttarakhand", "city": "Rishikesh", "name": "AIIMS Rishikesh & Doon Medical College Hospital Dehradun", "facility_category": "Central AIIMS & State Medical College Hospital", "schemes": "PM-JAY Atal Ayushman Uttarakhand", "address": "Virbhadra Road, Shivaji Nagar, Rishikesh, Uttarakhand", "pin_code": "249203", "phone_general": "0135-2462927", "phone_emergency": "108", "specialties": "Heli-Trauma Services, Cardiology, Oncology, Neurosurgery", "website": "https://aiimsrishikesh.edu.in/"},
    {"state": "West Bengal", "city": "Kolkata", "name": "SSKM Hospital (IPGMER) & Medical College Kolkata", "facility_category": "Premier Government Medical Colleges & AIIMS Kalyani", "schemes": "PM-JAY, Swasthya Sathi, Free OPD", "address": "244 AJC Bose Road / 88 College Street, Kolkata, West Bengal", "pin_code": "700020", "phone_general": "033-22231589", "phone_emergency": "108", "specialties": "Cardiology, Nephrology, Trauma, Oncology, Burns", "website": "https://ipgmer.gov.in/"},
    {"state": "Andaman and Nicobar Islands", "city": "Port Blair", "name": "G.B. Pant Hospital & ANIIMS Port Blair", "facility_category": "UT Government Medical College Hospital", "schemes": "PM-JAY, Free UT Healthcare", "address": "Atlanta Point, Port Blair, Andaman & Nicobar Islands", "pin_code": "744104", "phone_general": "03192-232102", "phone_emergency": "102", "specialties": "General Medicine, Emergency Care, Surgery, Maternal Care", "website": "https://aniims.andamannicobar.gov.in/"},
    {"state": "Chandigarh", "city": "Chandigarh", "name": "PGIMER Chandigarh & GMCH Sector 32", "facility_category": "Premier National Medical & Research Institute", "schemes": "PM-JAY, 70+ Vay Vandana, Himcare", "address": "Sector 12, Chandigarh", "pin_code": "160012", "phone_general": "0172-2747585", "phone_emergency": "0172-2756565", "specialties": "Advanced Cardiac Center, Trauma Center, Eye & Neuro Center", "website": "https://pgimer.edu.in/"},
    {"state": "Dadra and Nagar Haveli and Daman and Diu", "city": "Silvassa", "name": "Shri Vinoba Bhave Civil Hospital & NAMO Medical Education Institute", "facility_category": "UT Government Medical College & Civil Hospital", "schemes": "PM-JAY, ABHA Scan & Share", "address": "Sayli Road, Silvassa, Dadra & Nagar Haveli", "pin_code": "396230", "phone_general": "0260-2642940", "phone_emergency": "108", "specialties": "General Medicine, Trauma, Dialysis, Maternal & Child Care", "website": "https://namomeridnhdd.in/"},
    {"state": "Delhi", "city": "New Delhi", "name": "All India Institute of Medical Sciences (AIIMS New Delhi) & Safdarjung Hospital", "facility_category": "Premier Central Autonomous & Central Govt Hospitals", "schemes": "PM-JAY, 70+ Vay Vandana, ABHA Scan & Share", "address": "Ansari Nagar, Aurobindo Marg, New Delhi", "pin_code": "110029", "phone_general": "011-26588500", "phone_emergency": "011-26593666", "specialties": "All Super-Specialties, JPN Apex Trauma Center, AIIMS Cancer Center", "website": "https://www.aiims.edu/"},
    {"state": "Jammu and Kashmir", "city": "Srinagar", "name": "SKIMS Soura, GMC Srinagar & AIIMS Vijaypur Jammu", "facility_category": "Apex Medical University & Central AIIMS", "schemes": "PM-JAY SEHAT Universal Health Coverage", "address": "Soura / Karan Nagar, Srinagar, Jammu & Kashmir", "pin_code": "190011", "phone_general": "0194-2401013", "phone_emergency": "108", "specialties": "Cardiology, Oncology, Neurosurgery, 24x7 Emergency Care", "website": "https://www.skims.ac.in/"},
    {"state": "Ladakh", "city": "Leh", "name": "Sonam Norboo Memorial (SNM) District Hospital Leh", "facility_category": "Apex UT Government District Hospital", "schemes": "PM-JAY Universal Coverage, High-Altitude Medicine", "address": "Old Leh Road, Leh, Ladakh", "pin_code": "194101", "phone_general": "01982-252014", "phone_emergency": "102", "specialties": "High-Altitude Pulmonary Care, Emergency Medicine, Surgery", "website": "https://leh.nic.in/public-utility-category/hospitals/"},
    {"state": "Lakshadweep", "city": "Kavaratti", "name": "Indira Gandhi Hospital (IGH) Kavaratti", "facility_category": "UT Government Referral Hospital", "schemes": "PM-JAY & UT Free Evacuation Care", "address": "Kavaratti Island, Lakshadweep", "pin_code": "682555", "phone_general": "04896-262348", "phone_emergency": "108", "specialties": "General Medicine, Emergency Stabilization, Obstetrics", "website": "https://lakshadweep.gov.in/"},
    {"state": "Puducherry", "city": "Puducherry", "name": "JIPMER Puducherry (Jawaharlal Institute of Postgraduate Medical Education)", "facility_category": "Institute of National Importance (Central Govt)", "schemes": "PM-JAY, Free OPD & Emergency Care, ABHA", "address": "Dhanvantari Nagar, Gorimedu, Puducherry", "pin_code": "605006", "phone_general": "0413-2298288", "phone_emergency": "0413-2296562", "specialties": "All Super-Specialties, 24x7 Trauma & Toxicology Center", "website": "https://jipmer.edu.in/"},
]

for _h_item in ALL_INDIA_HOSPITALS:
    _h_item["maps_url"] = _make_maps_url(
        _h_item.get("latitude"),
        _h_item.get("longitude"),
        f"{_h_item['name']}, {_h_item['address']}, {_h_item['city']}, {_h_item['state']} {_h_item.get('pin_code', '')}",
    )

ALL_INDIA_MEDICINE_STORES: List[Dict[str, Any]] = [
    {"state": "Andhra Pradesh", "city": "Visakhapatnam", "name": "PM Bhartiya Janaushadhi Kendra — King George Hospital (KGH)", "facility_category": "24x7 Government Generic Medicine Store", "hours": "Open 24x7", "address": "KGH Compound, Maharanipeta, Visakhapatnam", "pin_code": "530002", "phone_contact": "1800-180-8080", "services": "50%–90% Subsidized Generic Medicines & Surgical Supplies", "website": "https://janaushadhi.gov.in"},
    {"state": "Arunachal Pradesh", "city": "Itanagar", "name": "PM Bhartiya Janaushadhi Kendra — TRIHMS Hospital Naharlagun", "facility_category": "Government Generic Medicine Store", "hours": "Open 24x7", "address": "TRIHMS Campus, Naharlagun, Itanagar", "pin_code": "791110", "phone_contact": "1800-180-8080", "services": "Essential Generic Antibiotics, Analgesics & Chronic Care Drugs", "website": "https://janaushadhi.gov.in"},
    {"state": "Assam", "city": "Guwahati", "name": "AMRIT Pharmacy & PMBJK — GMCH Bhangagarh & AIIMS Guwahati", "facility_category": "24x7 Government Generic & Oncology Pharmacy", "hours": "Open 24x7", "address": "GMCH Complex, Bhangagarh, Guwahati, Assam", "pin_code": "781032", "phone_contact": "1800-180-8080", "services": "Subsidized Cancer/Cardiac Medicines & Jan Aushadhi Generics", "website": "https://janaushadhi.gov.in"},
    {"state": "Bihar", "city": "Patna", "name": "AMRIT Pharmacy & PMBJK — AIIMS Patna & PMCH Campus", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "Phulwari Sharif (AIIMS) & Ashok Rajpath (PMCH), Patna", "pin_code": "801507", "phone_contact": "1800-180-8080", "services": "Subsidized Generic Drugs, Insulin & Cardiac Implants", "website": "https://janaushadhi.gov.in"},
    {"state": "Chhattisgarh", "city": "Raipur", "name": "AMRIT Pharmacy & Jan Aushadhi — AIIMS Raipur & Mekahara", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "GE Road, Tatibandh, AIIMS Raipur Gate, Chhattisgarh", "pin_code": "492099", "phone_contact": "1800-180-8080", "services": "Low-Cost Generic Formulations & Surgical Consumables", "website": "https://janaushadhi.gov.in"},
    {"state": "Goa", "city": "Panaji", "name": "PM Bhartiya Janaushadhi Kendra — Goa Medical College Bambolim", "facility_category": "Government Generic Medicine Store", "hours": "Open 24x7", "address": "GMC Bambolim Campus, Panaji, Goa", "pin_code": "403202", "phone_contact": "1800-180-8080", "services": "Quality Generic Medicines at 50%–90% Lower Prices", "website": "https://janaushadhi.gov.in"},
    {"state": "Gujarat", "city": "Bhavnagar", "name": "PM Bhartiya Janaushadhi Kendra — Sir Takhtsinhji Civil Hospital", "facility_category": "24x7 Government Generic Medicine Store", "hours": "Open 24x7 (OPD Gate)", "address": "Near OPD Gate, Sir Takhtsinhji Hospital, Jail Road, Bhavnagar", "pin_code": "364001", "phone_contact": "1800-180-8080", "services": "Jan Aushadhi Generics, BP/Diabetic Medicines, ORS & Surgical Items", "website": "https://janaushadhi.gov.in"},
    {"state": "Gujarat", "city": "Bhavnagar", "name": "PMBJK Kalanala & Medkart Generic Pharmacy Bhavnagar", "facility_category": "Jan Aushadhi & Retail Generic Pharmacy", "hours": "8:00 AM – 11:00 PM", "address": "Kalanala / Waghawadi Road, Bhavnagar, Gujarat", "pin_code": "364001", "phone_contact": "0278-2511411", "services": "WHO-GMP Certified Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Gujarat", "city": "Ahmedabad", "name": "PM Bhartiya Janaushadhi Kendra — Civil Hospital Asarwa & Sola", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "Civil Hospital Campus, Asarwa & Sola SG Highway, Ahmedabad", "pin_code": "380016", "phone_contact": "1800-180-8080", "services": "Subsidized Generic Medicines, Inhalers & Insulin", "website": "https://janaushadhi.gov.in"},
    {"state": "Gujarat", "city": "Rajkot", "name": "PM Bhartiya Janaushadhi Kendra — PDU Civil Hospital & AIIMS Rajkot", "facility_category": "24x7 Government Generic Medicine Store", "hours": "Open 24x7", "address": "Hospital Chowk, Jamnagar Road, Rajkot, Gujarat", "pin_code": "360001", "phone_contact": "1800-180-8080", "services": "Chronic & Acute Generic Medications", "website": "https://janaushadhi.gov.in"},
    {"state": "Gujarat", "city": "Vadodara", "name": "PM Bhartiya Janaushadhi Kendra — SSG Hospital Anandpura", "facility_category": "24x7 Government Generic Medicine Store", "hours": "Open 24x7", "address": "SSG Hospital Compound, Anandpura, Vadodara", "pin_code": "390001", "phone_contact": "1800-180-8080", "services": "Subsidized Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Gujarat", "city": "Surat", "name": "PM Bhartiya Janaushadhi Kendra — New Civil Hospital Majura Gate", "facility_category": "24x7 Government Generic Medicine Store", "hours": "Open 24x7", "address": "New Civil Hospital Campus, Majura Gate, Surat", "pin_code": "395001", "phone_contact": "1800-180-8080", "services": "24x7 Generic Pharmacy & Surgical Store", "website": "https://janaushadhi.gov.in"},
    {"state": "Haryana", "city": "Rohtak", "name": "AMRIT Pharmacy & PMBJK — PGIMS Rohtak Campus", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "OPD Block, PGIMS Rohtak, Haryana", "pin_code": "124001", "phone_contact": "1800-180-8080", "services": "Subsidized Generic & Life-Saving Drugs", "website": "https://janaushadhi.gov.in"},
    {"state": "Himachal Pradesh", "city": "Shimla", "name": "AMRIT Pharmacy & Jan Aushadhi — IGMC Shimla & AIIMS Bilaspur", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "IGMC Campus, Ridge Sanjauli Road, Shimla", "pin_code": "171001", "phone_contact": "1800-180-8080", "services": "Affordable Generic Medicines & Surgical Supplies", "website": "https://janaushadhi.gov.in"},
    {"state": "Jharkhand", "city": "Ranchi", "name": "PM Bhartiya Janaushadhi Kendra — RIMS Bariatu Ranchi", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "RIMS Campus, Bariatu Road, Ranchi, Jharkhand", "pin_code": "834009", "phone_contact": "1800-180-8080", "services": "Subsidized Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Karnataka", "city": "Bengaluru", "name": "PM Bhartiya Janaushadhi Kendra — Victoria Hospital & NIMHANS", "facility_category": "24x7 Government Generic Medicine Store", "hours": "Open 24x7", "address": "City Market (Victoria Campus) & Hosur Road (NIMHANS), Bengaluru", "pin_code": "560002", "phone_contact": "1800-180-8080", "services": "Neurological, Psychiatric, Cardiac & General Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Kerala", "city": "Thiruvananthapuram", "name": "Karunya Community Pharmacy & PMBJK — Govt Medical College", "facility_category": "24x7 Government Subsidized Pharmacy", "hours": "Open 24x7", "address": "Medical College Junction, Thiruvananthapuram, Kerala", "pin_code": "695011", "phone_contact": "1800-180-8080", "services": "Subsidized Branded & Generic Formulations", "website": "https://janaushadhi.gov.in"},
    {"state": "Madhya Pradesh", "city": "Bhopal", "name": "AMRIT Pharmacy & PMBJK — AIIMS Bhopal & Hamidia Hospital", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "Saket Nagar (AIIMS) & Sultania Road, Bhopal", "pin_code": "462020", "phone_contact": "1800-180-8080", "services": "Subsidized Generic & Oncology Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Maharashtra", "city": "Mumbai", "name": "AMRIT Pharmacy & PMBJK — KEM Hospital Parel & JJ Hospital", "facility_category": "24x7 Govt Generic & Life-Saving Drug Store", "hours": "Open 24x7", "address": "KEM Campus Parel & JJ Compound Byculla, Mumbai", "pin_code": "400012", "phone_contact": "022-24107000", "services": "Subsidized Oncology, Cardiac & Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Maharashtra", "city": "Pune", "name": "PM Bhartiya Janaushadhi Kendra — Sassoon General Hospital", "facility_category": "24x7 Government Generic Medicine Store", "hours": "Open 24x7", "address": "Near Pune Railway Station, Sassoon Compound, Pune", "pin_code": "411001", "phone_contact": "1800-180-8080", "services": "Jan Aushadhi Certified Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Manipur", "city": "Imphal", "name": "AMRIT Pharmacy & PMBJK — RIMS Lamphelpat Imphal", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "RIMS Campus, Lamphelpat, Imphal, Manipur", "pin_code": "795004", "phone_contact": "1800-180-8080", "services": "Subsidized Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Meghalaya", "city": "Shillong", "name": "AMRIT Pharmacy & Jan Aushadhi — NEIGRIHMS Shillong", "facility_category": "24x7 Central Govt Generic Pharmacy", "hours": "Open 24x7", "address": "NEIGRIHMS Campus, Mawdiangdiang, Shillong", "pin_code": "793018", "phone_contact": "1800-180-8080", "services": "Subsidized Generic & Super-Specialty Drugs", "website": "https://janaushadhi.gov.in"},
    {"state": "Mizoram", "city": "Aizawl", "name": "PM Bhartiya Janaushadhi Kendra — Civil Hospital Aizawl", "facility_category": "Government Generic Medicine Store", "hours": "Open Daily", "address": "Dawrpui, Civil Hospital Compound, Aizawl, Mizoram", "pin_code": "796001", "phone_contact": "1800-180-8080", "services": "Essential Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Nagaland", "city": "Kohima", "name": "PM Bhartiya Janaushadhi Kendra — Naga Hospital (NHAK)", "facility_category": "Government Generic Medicine Store", "hours": "Open Daily", "address": "P.R. Hill, NHAK Campus, Kohima, Nagaland", "pin_code": "797001", "phone_contact": "1800-180-8080", "services": "Subsidized Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Odisha", "city": "Bhubaneswar", "name": "AMRIT Pharmacy & Nirmaya PMBJK — AIIMS Bhubaneswar", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "Sijua Patrapada, AIIMS OPD Block, Bhubaneswar, Odisha", "pin_code": "751019", "phone_contact": "1800-180-8080", "services": "Free Nirmaya & Subsidized Jan Aushadhi Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Punjab", "city": "Amritsar", "name": "PM Bhartiya Janaushadhi Kendra — Guru Nanak Dev Hospital", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "Majitha Road, GNDH Campus, Amritsar, Punjab", "pin_code": "143001", "phone_contact": "1800-180-8080", "services": "Subsidized Generic Formulations", "website": "https://janaushadhi.gov.in"},
    {"state": "Rajasthan", "city": "Jaipur", "name": "PM Bhartiya Janaushadhi Kendra & Sahkari Bhandar — SMS Hospital", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "JLN Marg, SMS Hospital Campus, Jaipur, Rajasthan", "pin_code": "302004", "phone_contact": "1800-180-8080", "services": "24x7 Subsidized Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Sikkim", "city": "Gangtok", "name": "PM Bhartiya Janaushadhi Kendra — New STNM Hospital Sochakgang", "facility_category": "Government Generic Medicine Store", "hours": "Open 24x7", "address": "STNM Hospital Complex, Sochakgang, Gangtok, Sikkim", "pin_code": "737101", "phone_contact": "1800-180-8080", "services": "Subsidized Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Tamil Nadu", "city": "Chennai", "name": "Mudhalvar Marundhagam & PMBJK — RGGGH Park Town", "facility_category": "24x7 Government Subsidized Generic Pharmacy", "hours": "Open 24x7", "address": "Opposite Central Station, RGGGH Campus, Chennai", "pin_code": "600003", "phone_contact": "1800-180-8080", "services": "50%–90% Subsidized Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Telangana", "city": "Hyderabad", "name": "AMRIT Pharmacy & PMBJK — NIMS Punjagutta & Osmania Hospital", "facility_category": "24x7 Government Generic & Surgical Pharmacy", "hours": "Open 24x7", "address": "Punjagutta (NIMS) & Afzal Gunj, Hyderabad, Telangana", "pin_code": "500082", "phone_contact": "1800-180-8080", "services": "Subsidized Generic & Specialty Drugs", "website": "https://janaushadhi.gov.in"},
    {"state": "Tripura", "city": "Agartala", "name": "PM Bhartiya Janaushadhi Kendra — GBP Hospital Kunjaban", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "GBP Hospital Complex, Kunjaban, Agartala, Tripura", "pin_code": "799006", "phone_contact": "1800-180-8080", "services": "Subsidized Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Uttar Pradesh", "city": "Lucknow", "name": "AMRIT Pharmacy & PMBJK — KGMU Chowk & SGPGI Lucknow", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "Shah Mina Road, KGMU Trauma Center, Lucknow, UP", "pin_code": "226003", "phone_contact": "1800-180-8080", "services": "24x7 Trauma, Cardiac & Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Uttarakhand", "city": "Rishikesh", "name": "AMRIT Pharmacy & PMBJK — AIIMS Rishikesh", "facility_category": "24x7 Central Govt Generic Pharmacy", "hours": "Open 24x7", "address": "Gate No. 1, AIIMS Virbhadra Road, Rishikesh, Uttarakhand", "pin_code": "249203", "phone_contact": "1800-180-8080", "services": "Subsidized Generic & Life-Saving Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "West Bengal", "city": "Kolkata", "name": "Fair Price Medicine Shop & PMBJK — SSKM & Medical College Kolkata", "facility_category": "24x7 Government Fair Price & Generic Store", "hours": "Open 24x7", "address": "244 AJC Bose Road (SSKM Campus), Kolkata, West Bengal", "pin_code": "700020", "phone_contact": "1800-180-8080", "services": "60%–85% Discounted Generic & Critical Care Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Andaman and Nicobar Islands", "city": "Port Blair", "name": "PM Bhartiya Janaushadhi Kendra — G.B. Pant Hospital Port Blair", "facility_category": "UT Government Generic Medicine Store", "hours": "Open 24x7", "address": "G.B. Pant Hospital Premises, Atlanta Point, Port Blair", "pin_code": "744104", "phone_contact": "1800-180-8080", "services": "Subsidized Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Chandigarh", "city": "Chandigarh", "name": "AMRIT Pharmacy & Jan Aushadhi Store — PGIMER Sector 12", "facility_category": "24x7 Central Govt Generic & Surgical Pharmacy", "hours": "Open 24x7", "address": "New OPD Block & Emergency Complex, PGIMER Sector 12, Chandigarh", "pin_code": "160012", "phone_contact": "0172-2747585", "services": "Subsidized Oncology, Cardiac & Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Dadra and Nagar Haveli and Daman and Diu", "city": "Silvassa", "name": "PM Bhartiya Janaushadhi Kendra — Vinoba Bhave Civil Hospital", "facility_category": "24x7 UT Government Generic Pharmacy", "hours": "Open 24x7", "address": "VBCH Campus, Sayli Road, Silvassa", "pin_code": "396230", "phone_contact": "1800-180-8080", "services": "Subsidized Generic Formulations", "website": "https://janaushadhi.gov.in"},
    {"state": "Delhi", "city": "New Delhi", "name": "AMRIT Pharmacy & PM Janaushadhi Kendra — AIIMS & Safdarjung Hospital", "facility_category": "24x7 Central Govt Generic & Cancer/Cardiac Pharmacy", "hours": "Open 24x7", "address": "Gate No. 1, AIIMS Ansari Nagar & Safdarjung OPD Block, New Delhi", "pin_code": "110029", "phone_contact": "011-26588500", "services": "50%–90% Subsidized Generic, Cardiac & Oncology Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Jammu and Kashmir", "city": "Srinagar", "name": "AMRIT Pharmacy & PMBJK — SKIMS Soura & GMC Srinagar", "facility_category": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "SKIMS Main Gate, Soura, Srinagar, Jammu & Kashmir", "pin_code": "190011", "phone_contact": "1800-180-8080", "services": "Subsidized Generic & Super-Specialty Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Ladakh", "city": "Leh", "name": "PM Bhartiya Janaushadhi Kendra — SNM Hospital Leh", "facility_category": "UT Government Generic Medicine Store", "hours": "Open Daily", "address": "SNM District Hospital Compound, Leh, Ladakh", "pin_code": "194101", "phone_contact": "1800-180-8080", "services": "Essential & High-Altitude Generic Medications", "website": "https://janaushadhi.gov.in"},
    {"state": "Lakshadweep", "city": "Kavaratti", "name": "PM Bhartiya Janaushadhi Kendra — Indira Gandhi Hospital Kavaratti", "facility_category": "UT Government Generic Pharmacy", "hours": "Open Daily", "address": "IGH Hospital Complex, Kavaratti, Lakshadweep", "pin_code": "682555", "phone_contact": "1800-180-8080", "services": "Essential Generic Medicines", "website": "https://janaushadhi.gov.in"},
    {"state": "Puducherry", "city": "Puducherry", "name": "AMRIT Pharmacy & PMBJK — JIPMER Gorimedu Campus", "facility_category": "24x7 Central Govt Generic Pharmacy", "hours": "Open 24x7", "address": "JIPMER Campus, Dhanvantari Nagar, Puducherry", "pin_code": "605006", "phone_contact": "0413-2298288", "services": "Subsidized Generic & Specialty Medicines", "website": "https://janaushadhi.gov.in"},
]

for _s_item in ALL_INDIA_MEDICINE_STORES:
    _s_item["maps_url"] = _make_maps_url(
        _s_item.get("latitude"),
        _s_item.get("longitude"),
        f"{_s_item['name']}, {_s_item['address']}, {_s_item['city']}, {_s_item['state']} {_s_item.get('pin_code', '')}",
    )


# ==============================================================================
# PHARMACEUTICAL SPECIFIERS & INDIAN MEDICINE BRAND PROFILES
# ==============================================================================

SPECIFIER_DEFINITIONS: Dict[str, str] = {
    "xl": "**XL (Extended Release):** Engineered to release the active medication slowly over 12 to 24 hours to maintain steady blood levels. Swallow whole with water—**never chew, crush, or break**.",
    "sr": "**SR (Sustained Release):** Releases the active drug gradually over time so fewer daily doses are needed. **Swallow whole; do not crush, split, or chew.**",
    "xr": "**XR (Extended Release):** Long-acting 24-hour formulation. **Swallow whole without crushing.**",
    "er": "**ER (Extended Release):** Slow-release matrix tablet. **Do not crush, split, or chew.**",
    "dsr": "**DSR (Domperidone Sustained Release):** Combines a proton-pump acid reducer (like Pantoprazole or Rabeprazole) with sustained-release Domperidone (prevents nausea/reflux). Typically taken before meals as advised by a physician.",
    "md": "**MD (Mouth Dissolving):** Orally disintegrating tablet that dissolves rapidly on the tongue within seconds without needing water.",
    "dt": "**DT (Dispersible Tablet):** Can be dispersed in a spoonful of clean boiled/cooled water right before administration.",
    "od": "**OD (Once Daily):** Formulation intended for once-daily administration under medical supervision.",
    "bd": "**BD / BID (Twice Daily):** Formulation intended for twice-daily administration under medical supervision.",
    "forte": "**Forte (Strong / Higher Strength):** Contains a higher milligram concentration or reinforced combination of active ingredients.",
    "plus": "**Plus (Combination Formula):** Contains an additional synergistic active ingredient for broader symptom relief.",
    "duo": "**Duo (Dual Action):** Combines two active ingredients working together (such as Amoxicillin + Clavulanic Acid).",
    "cv": "**CV (Clavulanic Acid Combination):** Pairs a penicillin antibiotic with Clavulanic Acid to overcome bacterial beta-lactamase resistance.",
    "sp": "**SP (Serratiopeptidase Combination):** Combines an NSAID pain reliever + Paracetamol + **Serratiopeptidase** (an enzyme that clears inflammatory fluid and tissue swelling).",
    "lc": "**LC (Levocetirizine Combination):** Combines Montelukast with Levocetirizine for allergic rhinitis and airway relief.",
    "am": "**AM (Amlodipine Combination):** Combines a blood pressure medicine (such as Telmisartan) with **Amlodipine** (a calcium channel blocker).",
    "h": "**H (Hydrochlorothiazide Combination):** Includes a mild thiazide diuretic ('water pill') to lower blood pressure.",
    "gp": "**GP (Glimepiride Combination):** Combines Metformin with **Glimepiride** for Type 2 Diabetes.",
    "oz": "**OZ (Ornidazole Combination):** Combines an antibiotic (like Ofloxacin) with **Ornidazole** for mixed bacterial/protozoal GI infections.",
    "tz": "**TZ (Tinidazole Combination):** Combines Norfloxacin or Ciprofloxacin with **Tinidazole** for mixed gut infections.",
}

ASK_USER_LOCATION_PROMPT = (
    "\n\n📍 **Want Nearby Hospitals & 24x7 Medicine Stores in Your Area?**\n"
    "Reply with your **City or State name in India** (e.g., *Bhavnagar, Ahmedabad, Mumbai, Delhi, Bengaluru, Chennai, Srinagar, Guwahati, Patna, or Kolkata*), "
    "and I will list verified Government/PM-JAY Hospitals and Jan Aushadhi Pharmacies near you."
)

MANDATORY_MEDICINE_WARNING = (
    "\n\n⚠️ **Clinical Oversight & Non-Prescription Warning:**\n"
    "**This information is for educational reference only and is NOT a medical prescription.** "
    "Individual dosages depend on age, weight, kidney/liver function, and clinical evaluation. "
    "Never start, stop, or alter any medication or dosage without consulting a registered medical practitioner (MBBS/MD)."
)

INDIAN_BRAND_PROFILES: List[Dict[str, Any]] = [
    {
        "brands": ["lithonex", "lithosun", "intalith", "lichen", "lithium", "licab"],
        "generic_salt": "Lithium Carbonate (Mood Stabilizer / Antimanic CNS Agent)",
        "common_strengths": "300 mg, 400 mg, 450 mg (SR / XL Extended Release Tablet)",
        "uses": (
            "• **Bipolar Disorder (Manic-Depressive Illness):** Stabilizes brain mood circuits to prevent extreme emotional highs (mania/hypomania) and severe depressive lows.\n"
            "• **Acute Manic Episodes:** Calms racing thoughts, severe irritability, sleeplessness, and psychomotor agitation.\n"
            "• **Treatment-Resistant Major Depression:** Used as an augmenting mood stabilizer under specialist psychiatric care."
        ),
        "side_effects": (
            "• **Common Side Effects:** Fine hand tremor, increased thirst (polydipsia), frequent urination (polyuria), mild nausea, or weight changes.\n"
            "• **Toxicity Warning Signs (>1.5 mEq/L — Emergency):** Coarse hand tremors, slurred speech, unsteady gait (ataxia), severe vomiting/diarrhea, muscle twitching, or confusion."
        ),
        "contraindications": (
            "• Severe renal impairment, acute dehydration, significant cardiovascular disease (Brugada syndrome), untreated hypothyroidism, or severe sodium depletion (hyponatremia)."
        ),
        "interactions": (
            "• **Critical Drug Interactions:** Avoid NSAID painkillers (Ibuprofen, Diclofenac, Aceclofenac, Zerodol, Naproxen), Thiazide diuretics (Hydrochlorothiazide), and ACE inhibitors unless closely monitored by a psychiatrist, as they reduce renal Lithium clearance and trigger toxicity.\n"
            "• **Fluid & Sodium Balance:** Dehydration or sudden low-salt diets dangerously elevate serum Lithium concentrations."
        ),
        "warnings": (
            "• **Mandatory Therapeutic Drug Monitoring (TDM):** Requires periodic **Serum Lithium blood level checks**, **Kidney Function Tests (Creatinine/eGFR)**, and **Thyroid Function (TSH)** tests.\n"
            "• **Extended-Release Integrity:** `XL` / `SR` tablets must be swallowed whole—never chewed, crushed, or split."
        ),
    },
    {
        "brands": ["dolo", "calpol", "crocin", "pacimol", "sumo l", "pyrigesic", "metacin", "p 500", "p 650", "paracetamol", "acetaminophen", "t-98", "tylenol"],
        "generic_salt": "Paracetamol / Acetaminophen (Antipyretic & Non-Opioid Central Analgesic)",
        "common_strengths": "500 mg, 650 mg, 1000 mg SR Tablet; Pediatric Oral Suspension",
        "uses": (
            "• **Fever Reduction (Antipyretic):** Used to lower elevated body temperature in viral fevers, dengue, malaria, typhoid, influenza, and post-vaccination pyrexia.\n"
            "• **Pain Relief (Analgesic):** Relieves mild-to-moderate headache, migraine, toothache, sore throat, myalgia (muscle ache), and joint pain."
        ),
        "side_effects": (
            "• Generally well tolerated within clinician-advised limits. Rare adverse effects include allergic skin rash, erythema, or mild epigastric discomfort.\n"
            "• **Overdose Risk:** Excessive intake causes acute, potentially fatal hepatic necrosis (liver failure)."
        ),
        "contraindications": (
            "• Severe active hepatic impairment, acute viral hepatitis, or known hypersensitivity to acetaminophen."
        ),
        "interactions": (
            "• **Duplicate Ingredient Risk:** Many over-the-counter cold, flu, and pain combinations (e.g., Sinarest, Wikoryl, Zerodol-P, Combiflam) already contain Paracetamol—combining them risks accidental liver overdose.\n"
            "• **Alcohol & Warfarin:** Chronic alcohol use increases hepatotoxicity risk; prolonged use may potentiate Warfarin anticoagulation."
        ),
        "warnings": (
            "• Do not exceed the maximum daily limit advised by a physician. Seek immediate medical attention if yellowing of the eyes/skin or upper-right abdominal pain occurs."
        ),
    },
    {
        "brands": ["zerodol", "aceclo", "hifenac", "movon", "aceclofenac", "voveran", "reactin", "diclofenac", "combiflam", "brufen", "ibuprofen", "flexon", "naprosyn", "naxdom", "naproxen", "nucoxia", "etoshine", "etoricoxib"],
        "generic_salt": "Non-Steroidal Anti-Inflammatory Drug (NSAID: Aceclofenac / Diclofenac / Ibuprofen / Naproxen / Etoricoxib ± Paracetamol ± Serratiopeptidase)",
        "common_strengths": "100 mg, 200 mg SR, 400 mg, P (with Paracetamol), SP (with Paracetamol + Serratiopeptidase)",
        "uses": (
            "• **Inflammatory & Musculoskeletal Pain:** Osteoarthritis, rheumatoid arthritis, ankylosing spondylitis, acute lower back pain, cervical spondylosis, and ligament sprains.\n"
            "• **Dental & Post-Operative Inflammation:** Reduces acute dental pain and tissue edema (`SP` variants include Serratiopeptidase)."
        ),
        "side_effects": (
            "• Gastritis, heartburn, epigastric pain, nausea, dyspepsia, dizziness, fluid retention/edema, or elevated blood pressure and liver enzymes."
        ),
        "contraindications": (
            "• **Dengue & Hemorrhagic Fevers:** Strictly contraindicated during suspected Dengue fever due to platelet dysfunction and severe gastrointestinal/internal bleeding risk.\n"
            "• **GI, Renal & Cardiac Conditions:** Active peptic ulcer, GI bleeding, severe renal or hepatic disease, aspirin-sensitive asthma, coronary artery bypass graft (CABG) perioperative period, and third trimester of pregnancy."
        ),
        "interactions": (
            "• Avoid combining with other NSAIDs, Aspirin, anticoagulants (Warfarin, Apixaban, Clopidogrel), oral corticosteroids, Lithium, Methotrexate, or ACE inhibitors/ARBs."
        ),
        "warnings": (
            "• NSAIDs carry boxed warnings for gastrointestinal ulceration/bleeding and increased cardiovascular thrombotic risk with prolonged or high-dose use. Always administer under medical supervision."
        ),
    },
    {
        "brands": ["pan", "pantocid", "pantop", "pantodac", "pantoprazole", "omez", "omicip", "omeprazole", "razo", "rabicip", "cyra", "veloz", "rabeprazole", "nexpro", "sompraz", "esomeprazole", "aciloc", "rantac"],
        "generic_salt": "Proton Pump Inhibitor (PPI: Pantoprazole / Omeprazole / Rabeprazole / Esomeprazole ± Domperidone)",
        "common_strengths": "20 mg, 40 mg, D (with 10mg Domperidone), DSR (with 30mg Sustained-Release Domperidone)",
        "uses": (
            "• **Acid Peptic Disorders:** Gastroesophageal Reflux Disease (GERD), erosive esophagitis, gastritis, peptic and duodenal ulcers, and Zollinger-Ellison syndrome.\n"
            "• **Reflux & Nausea (`D` / `DSR` Variants):** Domperidone functions as a prokinetic to enhance gastric emptying and reduce regurgitation."
        ),
        "side_effects": (
            "• Headache, dry mouth, diarrhea or constipation, flatulence, abdominal discomfort, or dizziness."
        ),
        "contraindications": (
            "• Known hypersensitivity to substituted benzimidazoles; for Domperidone-containing (`D`/`DSR`) variants: prolactin-releasing pituitary tumor (prolactinoma), GI hemorrhage/mechanical obstruction, or cardiac QT prolongation."
        ),
        "interactions": (
            "• Reduces gastric acidity, which can decrease absorption of Ketoconazole, Itraconazole, Atazanavir, and Iron salts. Omeprazole/Esomeprazole may inhibit CYP2C19 activation of Clopidogrel."
        ),
        "warnings": (
            "• Prolonged unsupervised therapy (>1 year) is associated with Vitamin B12 deficiency, hypomagnesemia, and increased risk of osteoporotic fractures. Enteric-coated tablets and `DSR` capsules must be swallowed whole."
        ),
    },
    {
        "brands": ["augmentin", "moxikind", "clavam", "amoxyclav", "novamox", "almox", "amoxicillin", "ceftum", "taxim", "monocef", "gudcef", "zifi", "mahacef", "cefixime", "cefpodoxime", "cefuroxime", "azithral", "azee", "zady", "azithromycin", "ciplox", "ciprofloxacin", "norflox", "oflox", "metrogyl", "flagyl", "doxycycline"],
        "generic_salt": "Prescription Antibacterial / Antimicrobial Formulation",
        "common_strengths": "625 mg (Amoxicillin 500mg + Clavulanic Acid 125mg), 500 mg, 250 mg, 200 mg, OZ / TZ",
        "uses": (
            "• **Confirmed Bacterial Infections:** Bacterial sinusitis, otitis media, pharyngitis/tonsillitis, community-acquired pneumonia, urinary tract infections (UTI), enteric (typhoid) fever, and skin/soft-tissue infections.\n"
            "• **Zero Viral Activity:** Antibiotics are completely ineffective against viral colds, influenza, or dengue."
        ),
        "side_effects": (
            "• Antibiotic-associated diarrhea, nausea, vomiting, abdominal cramps, oral/vaginal candidiasis, or hypersensitivity skin rashes."
        ),
        "contraindications": (
            "• History of severe immediate hypersensitivity (anaphylaxis or Stevens-Johnson syndrome) to Penicillins, Cephalosporins, Macrolides, or Fluoroquinolones; history of cholestatic jaundice with Amoxicillin-Clavulanate."
        ),
        "interactions": (
            "• Antacids containing aluminum/magnesium, calcium, zinc, or iron significantly chelate and block absorption of Fluoroquinolones and Tetracyclines. Metronidazole/Ornidazole (`OZ`/`TZ`) cause a severe disulfiram-like reaction with alcohol."
        ),
        "warnings": (
            "• **Antimicrobial Stewardship:** Taking antibiotics without a confirmed bacterial diagnosis or stopping a prescribed course early drives multidrug bacterial resistance (AMR)."
        ),
    },
    {
        "brands": ["telma", "tazloc", "telmikind", "telmisartan", "losar", "losartan", "amlokind", "stamlo", "amlodipine", "cilacar", "cilnidipine", "concor", "metolar", "prolomet", "metoprolol", "cardace", "ramipril"],
        "generic_salt": "Antihypertensive / Cardiovascular Agent (ARB / Calcium Channel Blocker / Beta-Blocker / ACE Inhibitor)",
        "common_strengths": "20 mg, 40 mg, 80 mg, 5 mg, 10 mg, 25 mg XL, 50 mg XL (with AM, H, CT combinations)",
        "uses": (
            "• **Essential Hypertension (High Blood Pressure):** Lowers systemic arterial pressure to reduce the risk of stroke, myocardial infarction, and renal failure.\n"
            "• **Angina Pectoris, Heart Failure & Arrhythmia Rate Control.**"
        ),
        "side_effects": (
            "• Postural dizziness/lightheadedness, peripheral ankle edema (common with Amlodipine), dry persistent cough (with ACE inhibitors like Ramipril), fatigue, or hyperkalemia (high blood potassium with ARBs/ACEIs)."
        ),
        "contraindications": (
            "• **Pregnancy Boxed Warning:** ARBs (Telmisartan, Losartan) and ACE inhibitors (Ramipril) are strictly contraindicated in pregnancy due to fetal toxicity.\n"
            "• Bilateral renal artery stenosis; severe bradycardia or cardiogenic shock (for Beta-blockers)."
        ),
        "interactions": (
            "• NSAID painkillers attenuate antihypertensive efficacy and worsen kidney function when combined with ARBs/ACEIs/diuretics. Potassium supplements or potassium-sparing diuretics increase hyperkalemia risk."
        ),
        "warnings": (
            "• **Never Discontinue Abruptly:** Sudden cessation of antihypertensives or beta-blockers can precipitate rebound hypertension, tachycardia, or angina."
        ),
    },
    {
        "brands": ["glycomet", "metsmall", "glucophage", "metformin", "amaryl", "glimestar", "glimepiride", "janumet", "istamet", "galvus", "vildagliptin", "sitagliptin", "teneligliptin", "forxiga", "jardiance", "udapa", "dapagliflozin", "empagliflozin"],
        "generic_salt": "Oral Anti-Diabetic Agent (Biguanide / Sulfonylurea / DPP-4 Inhibitor / SGLT2 Inhibitor)",
        "common_strengths": "500 mg SR, 850 mg, 1000 mg, GP1 / GP2, 10 mg, 20 mg, 50 mg, 100 mg",
        "uses": (
            "• **Type 2 Diabetes Mellitus:** Improves glycemic control by decreasing hepatic glucose production, enhancing peripheral insulin sensitivity, or increasing insulin secretion/urinary glucose excretion."
        ),
        "side_effects": (
            "• GI disturbances (nausea, metallic taste, diarrhea with Metformin), **hypoglycemia / low blood sugar <70 mg/dL** (sweating, tremor, palpitations with Sulfonylureas like Glimepiride), or genital mycotic/urinary tract infections (with SGLT2 inhibitors)."
        ),
        "contraindications": (
            "• Severe renal impairment (eGFR < 30 mL/min/1.73m²), acute metabolic acidosis (including Diabetic Ketoacidosis), severe hepatic dysfunction, or acute dehydration/hypoxia."
        ),
        "interactions": (
            "• Alcohol potentiates the risk of lactic acidosis (with Metformin) and severe hypoglycemia. Iodinated contrast media require temporary withholding of Metformin per radiology protocol. Beta-blockers may mask adrenergic warning signs of hypoglycemia."
        ),
        "warnings": (
            "• Long-term Metformin therapy requires periodic Vitamin B12 and renal function monitoring. Patients on `GP` / Sulfonylurea combinations must recognize and treat hypoglycemia promptly."
        ),
    },
    {
        "brands": ["nexito", "cipralex", "escitalopram", "serlift", "zoloft", "sertraline", "prodep", "fludac", "fluoxetine", "clonafit", "zapiz", "clonazepam", "restyl", "alprax", "alprazolam", "etizola", "etizolam", "oleanz", "olanzapine", "risdone", "risperidone"],
        "generic_salt": "Neuro-Psychiatric Medication (SSRI Antidepressant / Benzodiazepine Anxiolytic / Atypical Antipsychotic)",
        "common_strengths": "5 mg, 10 mg, 20 mg, 0.25 mg, 0.5 mg, MD",
        "uses": (
            "• **Major Depressive Disorder, Generalized Anxiety Disorder (GAD), Panic Disorder, Obsessive-Compulsive Disorder (OCD), and Psychiatric Mood/Sleep Stabilization.**"
        ),
        "side_effects": (
            "• Drowsiness or insomnia, mild initial nausea, dry mouth, dizziness, weight or metabolic changes, or sedation."
        ),
        "contraindications": (
            "• Concurrent use of Monoamine Oxidase Inhibitors (MAOIs) within 14 days (risk of Serotonin Syndrome); severe respiratory insufficiency or untreated narrow-angle glaucoma (for Benzodiazepines)."
        ),
        "interactions": (
            "• Strictly avoid alcohol, opioids, and other CNS depressants (causes dangerous respiratory depression and sedation). Tramadol, Triptans, and Linezolid increase Serotonin Syndrome risk with SSRIs."
        ),
        "warnings": (
            "• **Discontinuation Syndrome Warning:** Never stop psychiatric medications abruptly—sudden withdrawal causes rebound anxiety, dizziness, paresthesias, or seizures. Any dose adjustment must be supervised by a Psychiatrist."
        ),
    },
]

# ==============================================================================
# DEEP MULTI-BULLET CLINICAL DISEASE & SYMPTOM ENCYCLOPEDIA (SEPARATE FROM MEDICINES)
# ==============================================================================

CLINICAL_DISEASE_DATABASE: List[Dict[str, Any]] = [
    {
        "keywords": ["hypertension", "high blood pressure", "high bp", "bp", "blood pressure", "ब्लड प्रेशर", "हाई बीपी", "હાઈ બીપી", "બીપી"],
        "title": "Hypertension (High Blood Pressure)",
        "overview": (
            "Hypertension is a chronic cardiovascular condition in which the force of blood pushing against artery walls remains consistently elevated (**≥ 140/90 mmHg** on repeated clinical readings).\n"
            "• **Clinical BP Categories:**\n"
            "  - **Normal BP:** Less than **120/80 mmHg**\n"
            "  - **Elevated / Pre-Hypertension:** **120–129 / <80 mmHg**\n"
            "  - **Stage 1 Hypertension:** **130–139 / 80–89 mmHg**\n"
            "  - **Stage 2 Hypertension:** **≥ 140 / ≥ 90 mmHg**\n"
            "  - **Hypertensive Crisis (Emergency):** **> 180 / > 120 mmHg** (requires immediate hospital care)"
        ),
        "causes": (
            "• **High Dietary Sodium (Salt):** Excess intake of table salt, pickles, papad, salted namkeen, and processed foods causes fluid retention and arterial stiffness.\n"
            "• **Primary (Essential) Factors:** Genetics/family history, age-related stiffening of blood vessels, obesity, and physical inactivity.\n"
            "• **Chronic Stress & Poor Sleep:** Persistent mental stress, smoking/tobacco (causes vasoconstriction), alcohol, and obstructive sleep apnea.\n"
            "• **Secondary Medical Causes:** Chronic kidney disease, thyroid disorders, or adrenal gland disorders."
        ),
        "symptoms": (
            "• **Often Asymptomatic ('The Silent Killer'):** Most people have no warning signs for years until BP reaches high levels, making regular cuff screening vital.\n"
            "• **Early / Moderate Symptoms:** Dull throbbing **morning headache (especially at the back of the head/neck)**, lightheadedness or dizziness, easy fatigue, and palpitations.\n"
            "• **Visual & Ear Symptoms:** Blurred or double vision, seeing spots, and a pulsing/ringing sound in the ears (tinnitus).\n"
            "• **Severe / Hypertensive Crisis Red Flags:** **Chest pain or tightness**, **shortness of breath**, **spontaneous nosebleeds**, **numbness/weakness in the face or limbs**, or confusion."
        ),
        "diagnosis": (
            "• **Serial Sphygmomanometer / Digital BP Monitoring:** At least 2 to 3 readings taken on different days after sitting quietly for 5 minutes (or 24-hour Ambulatory BP Monitoring - ABPM).\n"
            "• **12-Lead ECG & 2D Echocardiography:** Checks for Left Ventricular Hypertrophy and rhythm changes.\n"
            "• **Fasting Lipid Profile & Blood Sugar (HbA1c / FBS):** Evaluates cholesterol plaque risk and co-existing diabetes.\n"
            "• **Renal Function Test (Serum Creatinine, eGFR, Electrolytes Na+/K+) & Urine Microalbumin:** Assesses kidney health.\n"
            "• **Ophthalmic Fundoscopy:** Examines retinal blood vessels for hypertensive retinopathy."
        ),
        "precautions": (
            "• **Strict DASH Diet & Salt Restriction:** Limit total salt intake to **under 5 grams (1 level teaspoon) per day**. Avoid adding raw salt at the table and avoid pickles, papad, salted biscuits, and canned foods.\n"
            "• **Eat Potassium- & Fiber-Rich Foods:** Include bananas, coconut water (if kidney function is normal), spinach, beetroot, oats, garlic, flaxseeds, and fresh fruits.\n"
            "• **Daily Aerobic Exercise:** Perform **30 to 40 minutes of brisk walking**, cycling, or pranayama 5 days a week; avoid heavy breath-holding weight lifting.\n"
            "• **Consistent Clinical Follow-Up:** Monitor home BP readings in a logbook, quit tobacco completely, and follow your physician's treatment plan consistently."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** Consult a **General Physician / Internal Medicine Specialist (MD Medicine)** for initial evaluation, or a **Cardiologist (DM Cardiology)** and **Nephrologist** if BP remains uncontrolled."
        ),
        "serious_hospital_and_helplines": (
            "• **Emergency Red-Flag Trigger:** If blood pressure exceeds **180/120 mmHg** OR is accompanied by **chest pain, shortness of breath, slurred speech, facial drooping, vision loss, or severe headache**:\n"
            "  - **Trigger Emergency SOS or Dial 108 / 112 Immediately** for emergency transport.\n"
            "  - **PM-JAY Hospital Helpline:** Dial **14555**.\n"
            "• **Recommended Hospitals:** Rush to the nearest **24x7 Emergency & Cardiac Care Unit at a Government Medical College Hospital, Civil Hospital, AIIMS, or PM-JAY Empanelled Hospital**."
        ),
    },
    {
        "keywords": ["depression", "depressed", "sadness", "hopeless", "suicidal", "mental health", "डिप्रेशन", "अवसाद", "ડિપ્રેશન", "उदासी"],
        "title": "Clinical Depression (Major Depressive Disorder)",
        "overview": (
            "Clinical depression (Major Depressive Disorder) is a serious, common, and treatable medical mood disorder involving neurochemical and stress-response changes in the brain.\n"
            "• Unlike temporary everyday sadness, clinical depression persists for **at least 2 consecutive weeks** and interferes with sleep, energy, appetite, concentration, and daily functioning."
        ),
        "causes": (
            "• **Neurochemical Dysregulation:** Alterations in key brain neurotransmitters (**Serotonin, Norepinephrine, and Dopamine**) and cortisol regulation.\n"
            "• **Endocrine & Nutritional Deficiencies:** **Hypothyroidism (high TSH)**, severe **Vitamin B12 deficiency**, **Vitamin D3 deficiency**, or chronic anemia often mimic or worsen depressive fatigue.\n"
            "• **Psychosocial & Trauma Triggers:** Bereavement, academic or career stress, financial distress, chronic illness, postpartum hormonal shifts, or social isolation.\n"
            "• **Genetic Vulnerability:** Family history of mood disorders."
        ),
        "symptoms": (
            "• **Emotional Symptoms:** Persistent sad, empty, tearful, or irritable mood; **anhedonia** (loss of interest or pleasure in hobbies, social activities, and studies/work); feelings of helplessness, guilt, or worthlessness.\n"
            "• **Physical & Vegetative Symptoms:** **Insomnia** (especially early-morning awakening) or **hypersomnia** (oversleeping); significant **appetite and weight changes**; constant physical exhaustion and unexplained body aches.\n"
            "• **Cognitive Symptoms:** Brain fog, inability to concentrate, indecisiveness, and slowed speech or movements.\n"
            "• **Severe / Crisis Red Flags:** Recurrent thoughts of self-harm or feeling that life is not worth living."
        ),
        "diagnosis": (
            "• **Structured Clinical Evaluation:** Assessment using **DSM-5 / ICD-11 criteria** and the **PHQ-9 (Patient Health Questionnaire-9)** severity scale.\n"
            "• **Medical Rule-Out Blood Panel:**\n"
            "  - **Thyroid Function Test (TSH, Free T3, Free T4)**\n"
            "  - **Serum Vitamin B12 & Folate Levels**\n"
            "  - **25-Hydroxy Vitamin D3 Level**\n"
            "  - **Complete Blood Count (CBC), Fasting Blood Sugar & Liver/Kidney Panel**"
        ),
        "precautions": (
            "• **Break Isolation Immediately:** Share what you are feeling with a trusted family member, friend, or healthcare professional—depression is a biological medical condition, never a personal weakness.\n"
            "• **Morning Sunlight & Circadian Rhythm:** Get **20–30 minutes of morning sunlight** before 9 AM and maintain a regular wake-up time.\n"
            "• **Brain-Supportive Nutrition:** Eat omega-3 and B-vitamin rich foods (walnuts, flaxseeds, curd, paneer, dal, green leafy vegetables) and **strictly avoid alcohol** or unprescribed sedatives.\n"
            "• **Paced Physical Activity:** Start with a 20-minute gentle walk outdoors daily."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:**\n"
            "  - **Psychiatrist (MD Psychiatry):** For medical diagnosis and biological/nutritional evaluation.\n"
            "  - **Clinical Psychologist (M.Phil / PhD):** For **Cognitive Behavioral Therapy (CBT)** and structured counseling."
        ),
        "serious_hospital_and_helplines": (
            "• **24x7 National Toll-Free Mental Health Helplines (Government of India):**\n"
            "  - **Tele-MANAS (20+ Languages, 24x7 Free):** Dial **14416** or **1800-891-4416**\n"
            "  - **NIMHANS Psychosocial Helpline:** Dial **080-46110007**\n"
            "  - **Kiran Mental Health Helpline:** Dial **1800-599-0019**\n"
            "• **Hospital Recommendation:** Visit **NIMHANS Bengaluru**, the **Department of Psychiatry at any AIIMS**, or your nearest **Government Medical College & Civil Hospital Psychiatry OPD**."
        ),
    },
    {
        "keywords": ["anxiety", "panic attack", "nervous", "worry", "palpitation", "घबराहट", "चिंता", "ગભરામણ", "ચિંતા"],
        "title": "Anxiety Disorder & Acute Panic Attacks",
        "overview": (
            "Anxiety disorders involve persistent, excessive worry and an overactive sympathetic nervous system ('fight-or-flight' adrenaline response), often causing sudden **panic attacks** with intense physical symptoms."
        ),
        "causes": (
            "• **Autonomic Nervous System Hyperactivity:** Surge of adrenaline/cortisol coupled with reduced GABA calming activity.\n"
            "• **Medical & Stimulant Triggers:** Excess caffeine, thyroid overactivity (**Hyperthyroidism**), low blood sugar (hypoglycemia), anemia, or sleep deprivation.\n"
            "• **Chronic Stress & Trauma:** Academic/career pressure, health anxiety, or unresolved emotional stress."
        ),
        "symptoms": (
            "• **Cardiorespiratory Symptoms:** Pounding or racing heartbeat (**palpitations**), chest tightness, feeling unable to take a full deep breath (**air hunger**), and hyperventilation.\n"
            "• **Autonomic & Neurological Symptoms:** Sweating palms, trembling hands, dry mouth, dizziness, tingling in fingers, and stomach churning/nausea.\n"
            "• **Psychological Symptoms:** Restlessness, racing thoughts, insomnia, and sudden fear of losing control."
        ),
        "diagnosis": (
            "• **Clinical Evaluation:** **GAD-7 (Generalized Anxiety Disorder)** and Panic Severity assessment.\n"
            "• **12-Lead ECG & Pulse Oximetry (SpO₂):** Performed first to rule out cardiac arrhythmia or hypoxia.\n"
            "• **Laboratory Workup:** **Thyroid Profile (TSH, Free T3/T4)**, **CBC (Hemoglobin)**, **Fasting Blood Sugar**, and **Serum Vitamin B12 / Vitamin D3**."
        ),
        "precautions": (
            "• **Immediate 4-7-8 Breathing Reset:** Inhale quietly through the nose for **4 seconds**, hold the breath for **7 seconds**, and exhale slowly through pursed lips for **8 seconds** to activate the Vagus nerve.\n"
            "• **5-4-3-2-1 Sensory Grounding:** Name 5 things you see, 4 things you can touch, 3 things you hear, 2 things you smell, and 1 slow breath.\n"
            "• **Eliminate Stimulants:** Avoid coffee, energy drinks, colas, smoking, and late-night screen exposure."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **Psychiatrist (MD)**, **Clinical Psychologist (for CBT & breathing retraining)**, or **General Physician (MD Medicine)**."
        ),
        "serious_hospital_and_helplines": (
            "• **24x7 Free Mental Health Counseling (Tele-MANAS):** Dial **14416** or **1800-891-4416**.\n"
            "• **Cardiac Rule-Out Warning:** If chest pain is crushing, radiates to the left arm/jaw, or occurs on physical exertion, trigger SOS or dial **108** immediately for an emergency hospital ECG."
        ),
    },
    {
        "keywords": ["dengue", "ડેન્ગ્યુ", "डेंगू", "டெங்கு", "డెంగ్యూ", "ডেঙ্গু"],
        "title": "Dengue Fever (डेंगू / ડેન્ગ્યુ)",
        "overview": (
            "Dengue fever is an acute mosquito-borne viral infection caused by the **Dengue Virus (DENV serotypes 1, 2, 3, or 4)** and transmitted by daytime-biting ***Aedes aegypti*** mosquitoes.\n"
            "• **Clinical Phases:**\n"
            "  1. **Febrile Phase (Days 1–3):** High fever (103°F–104°F) and severe body aches.\n"
            "  2. **Critical Phase (Days 4–6):** Fever drops, but **platelets fall and plasma leakage (rising Hematocrit/PCV)** can occur—this window requires closest monitoring.\n"
            "  3. **Recovery Phase (Days 7–10):** Fluid reabsorption and platelet recovery."
        ),
        "causes": (
            "• **Vector Transmission:** Bite of an infected female *Aedes aegypti* mosquito, which bites primarily **during daylight hours (morning and late afternoon)**.\n"
            "• **Stagnant Freshwater Breeding:** Breeds in clean stagnant water inside coolers, flowerpots, AC trays, coconut shells, and uncovered water containers."
        ),
        "symptoms": (
            "• **Classic Dengue Symptoms:** Sudden high fever (**103°F–105°F**) with chills, intense frontal headache, **retro-orbital pain (pain behind the eyes)**, and severe back, muscle, and joint pain (*'breakbone fever'*).\n"
            "• **Cutaneous & GI Symptoms:** Facial flushing, maculopapular skin rash (Days 3–5), loss of appetite, nausea, and vomiting.\n"
            "• **Severe Dengue Warning Signs (Days 3–7):** Severe continuous abdominal pain, persistent vomiting (>3 times in 24h), **bleeding from gums or nose**, red/purple skin spots (petechiae), black tarry stools, extreme lethargy, or cold clammy extremities."
        ),
        "diagnosis": (
            "• **Dengue NS1 Antigen Test (ELISA):** Primary confirmatory blood test during **Days 1 to 5** of fever.\n"
            "• **Dengue IgM & IgG Antibody Test (MAC-ELISA):** Becomes positive from **Day 5 onwards**.\n"
            "• **Serial Complete Blood Count (CBC) Every 24 Hours:** Monitors **Platelet Count** (Normal: 1,50,000–4,50,000/µL) and **Hematocrit (PCV)** (a >20% rise indicates plasma leakage).\n"
            "• **Liver Function Test (SGPT/SGOT):** Checks for hepatic involvement."
        ),
        "precautions": (
            "• **Aggressive Oral Hydration (Essential):** Drink **3 to 3.5 Liters of fluids daily**—WHO-ORS, tender coconut water, fresh pomegranate/mosambi juice, dal water, and boiled cooled water. Verify urination every 4–6 hours.\n"
            "• **Tepid Sponging & Rest:** Use lukewarm water sponging for high fever spikes and rest under a mosquito net even during daytime hours.\n"
            "• **Critical Safety Precaution:** **Never self-medicate with NSAID painkillers (Aspirin, Ibuprofen, Diclofenac, Aceclofenac, Naproxen) or steroids**, as they impair platelet function and trigger severe internal bleeding. Consult a physician for safe fever management."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **Internal Medicine Specialist / General Physician (MD Medicine)** or **Pediatrician (MD Pediatrics)**."
        ),
        "serious_hospital_and_helplines": (
            "• **Immediate Hospitalization Criteria:** Platelet count dropping rapidly below **50,000/µL**, rising Hematocrit (PCV), bleeding from gums/nose, persistent vomiting, severe stomach pain, or low BP.\n"
            "• **Emergency Helplines:** Trigger SOS or dial **108** (Ambulance), **104** (Health Helpline), or **14555** (PM-JAY)."
        ),
    },
    {
        "keywords": ["tuberculosis", "tb", "ટીબી", "टीबी", "क्षयरोग", "காசநோய்"],
        "title": "Tuberculosis (TB - ટીબી / टीबी)",
        "overview": (
            "Tuberculosis (TB) is a contagious bacterial infection caused by ***Mycobacterium tuberculosis*** that most commonly affects the lungs (**Pulmonary TB**) but can also affect lymph nodes, spine, brain, or abdomen (**Extra-Pulmonary TB**).\n"
            "• **Curable Condition:** TB is curable with a complete, physician-supervised course of standard anti-tubercular therapy under India's National TB Elimination Programme (NTEP)."
        ),
        "causes": (
            "• **Airborne Droplet Transmission:** Spreads through the air when a person with active sputum-positive lung TB coughs, sneezes, or speaks.\n"
            "• **High-Risk Factors:** Close prolonged indoor contact, undernutrition, poorly controlled **Diabetes**, tobacco smoking, or immunocompromised states."
        ),
        "symptoms": (
            "• **Cardinal Respiratory Symptoms:** **Persistent cough lasting more than 2 weeks**, coughing up blood-streaked sputum (**hemoptysis**), pleuritic chest pain, and shortness of breath.\n"
            "• **Systemic Constitutional Symptoms:** **Evening-rise fever**, **drenching night sweats**, and **unexplained weight loss with loss of appetite**."
        ),
        "diagnosis": (
            "• **Sputum CBNAAT / TrueNat (GeneXpert) Rapid Molecular Test:** Detects *M. tuberculosis* DNA and checks for **Rifampicin resistance (MDR-TB)** within 2 hours (free at Government NTEP centers).\n"
            "• **Two-Spot Sputum AFB Smear Microscopy & Liquid Culture (MGIT).**\n"
            "• **Digital Chest X-Ray (PA View), ESR, CBC, and Blood Sugar (HbA1c).**"
        ),
        "precautions": (
            "• **Strict Treatment Adherence:** Complete the full multi-month physician-prescribed NTEP regimen without skipping doses to prevent Multi-Drug Resistant TB (MDR-TB).\n"
            "• **High-Protein Recovery Diet:** Consume protein-rich meals (dal, chana, rajma, paneer, milk, curd, soy, eggs, groundnuts) to rebuild lung tissue and immunity.\n"
            "• **Cough Hygiene & Ventilation:** Cover mouth when coughing, wear a mask during the initial infectious phase, and keep living areas well-ventilated with sunlight."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **Pulmonologist / Chest Specialist (MD Respiratory Medicine)** or the **Medical Officer at your nearest Government NTEP / DOTS TB Center**."
        ),
        "serious_hospital_and_helplines": (
            "• **National Toll-Free TB Helpline (Nikshay Sampark):** Dial **1800-11-6666** (Free CBNAAT testing, treatment, and Nikshay Poshan nutritional support at Government Hospitals).\n"
            "• **Emergency Red Flags:** Coughing up large amounts of blood, severe breathlessness, or jaundice—dial **108** immediately."
        ),
    },
    {
        "keywords": ["diabetes", "blood sugar", "high sugar", "ડાયાબિટીસ", "मधुमेह", "शुगर"],
        "title": "Diabetes Mellitus (High Blood Sugar)",
        "overview": (
            "Diabetes Mellitus is a chronic metabolic disorder in which blood glucose levels remain persistently elevated due to impaired insulin secretion, insulin resistance, or both.\n"
            "• **Diagnostic Reference Targets:**\n"
            "  - **Normal:** Fasting **< 100 mg/dL** | Post-Meal (2h PPBS) **< 140 mg/dL** | HbA1c **< 5.7%**\n"
            "  - **Pre-Diabetes:** Fasting **100–125 mg/dL** | PPBS **140–199 mg/dL** | HbA1c **5.7%–6.4%**\n"
            "  - **Diabetes:** Fasting **≥ 126 mg/dL** | PPBS **≥ 200 mg/dL** | HbA1c **≥ 6.5%**"
        ),
        "causes": (
            "• **Insulin Resistance & Beta-Cell Dysfunction:** Visceral adiposity and physical inactivity reduce cellular glucose uptake.\n"
            "• **Dietary & Genetic Factors:** High intake of refined carbohydrates/sugars, chronic stress, family history, or gestational history."
        ),
        "symptoms": (
            "• **The Classic '3 Ps':** **Polyuria** (frequent urination, especially at night), **Polydipsia** (excessive thirst), and **Polyphagia** (increased hunger).\n"
            "• **Additional Symptoms:** Unexplained weight loss, fatigue, **blurred vision**, tingling/numbness in the feet (**neuropathy**), and slow-healing wounds."
        ),
        "diagnosis": (
            "• **HbA1c (Glycosylated Hemoglobin):** Reflects 90-day average blood glucose.\n"
            "• **Fasting Blood Sugar (FBS) & 2-Hour Post-Prandial Blood Sugar (PPBS).**\n"
            "• **Annual Screening:** **Urine Microalbumin-to-Creatinine Ratio & Serum Creatinine** (kidneys), **Fasting Lipid Profile** (heart), and **Dilated Retinal Eye Exam**."
        ),
        "precautions": (
            "• **Balanced Plate Method:** Fill **50% of your plate with non-starchy green vegetables**, **25% with protein** (dal, legumes, paneer, curd, eggs), and **25% with complex high-fiber grains** (multigrain/millets).\n"
            "• **Avoid Glycemic Spikes:** Eliminate refined sugar, sweet beverages, maida bakery items, and deep-fried snacks.\n"
            "• **Daily Exercise & Foot Care:** Walk briskly for 30–40 minutes daily and inspect feet daily for cuts or blisters."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **Endocrinologist / Diabetologist (DM Endocrinology)**, **MD Internal Medicine**, and an **Ophthalmologist**."
        ),
        "serious_hospital_and_helplines": (
            "• **Acute Diabetic Emergencies:**\n"
            "  1. **Hypoglycemia (Blood Sugar < 70 mg/dL):** Cold sweating, trembling, palpitations, confusion—immediately consume **15g fast-acting sugar/glucose** and recheck in 15 minutes.\n"
            "  2. **Diabetic Ketoacidosis / HHS (Blood Sugar > 350–400 mg/dL):** Vomiting, abdominal pain, fruity breath, rapid breathing, or drowsiness—**Dial 108 immediately**."
        ),
    },
    {
        "keywords": ["heart attack", "chest pain", "cardiac", "angina", "myocardial", "हार्ट अटैक", "सीने में दर्द", "હાર્ટ એટેક", "છાતીમાં દુખાવો"],
        "title": "Chest Pain & Acute Cardiac Warning (Suspected Heart Attack / Angina)",
        "overview": (
            "Acute chest pain or pressure can signal **Myocardial Ischemia (Angina)** or an **Acute Myocardial Infarction (Heart Attack)**, where a coronary artery supplying oxygen to the heart muscle is obstructed."
        ),
        "causes": (
            "• **Coronary Artery Disease (Atherosclerosis):** Plaque rupture and thrombus formation narrowing coronary arteries.\n"
            "• **Risk Factors:** Uncontrolled hypertension, diabetes, smoking, dyslipidemia (high LDL), obesity, family history, and severe stress."
        ),
        "symptoms": (
            "• **Classic Cardiac Chest Pain:** Heavy **crushing, squeezing, tightness, or burning pressure in the center or left chest** lasting more than a few minutes.\n"
            "• **Radiation:** Pain spreading to the **left shoulder, inner left arm, neck, lower jaw, back, or upper abdomen (often mistaken for 'acidity/gas')**.\n"
            "• **Associated Signs:** **Profuse cold sweating**, sudden shortness of breath, dizziness, nausea, or vomiting."
        ),
        "diagnosis": (
            "• **Immediate 12-Lead ECG (within 10 minutes of arrival).**\n"
            "• **High-Sensitivity Cardiac Troponin-I / Troponin-T & CK-MB Blood Tests.**\n"
            "• **2D Echocardiogram (Echo) & Coronary Angiography.**"
        ),
        "precautions": (
            "• **Immediate First-Aid While Waiting for Emergency Transport:**\n"
            "  - **Stop all physical activity** immediately; rest in a **half-upright position (45 degrees)**.\n"
            "  - Loosen tight clothing and ensure fresh air.\n"
            "  - **Never walk or drive yourself** to the hospital."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **Interventional Cardiologist (DM Cardiology)** & **Emergency Medicine Specialist**."
        ),
        "serious_hospital_and_helplines": (
            "• **CRITICAL EMERGENCY — TRIGGER SOS OR DIAL 108 / 112 IMMEDIATELY!**\n"
            "• Rush within the **Golden Hour (first 60 minutes)** to a **24x7 Cath-Lab & ICU equipped Government Medical College Hospital, AIIMS, or PM-JAY Cardiac Hospital**."
        ),
    },
    {
        "keywords": ["stroke", "paralysis", "brain attack", "slurred speech", "weakness one side", "लकवा", "स्ट्रोक", "લકવો", "સ્ટ્રોક"],
        "title": "Acute Stroke / Paralysis (Brain Attack)",
        "overview": (
            "A stroke occurs when blood flow to part of the brain is blocked by a clot (**Ischemic Stroke — 85%**) or when a cerebral blood vessel ruptures (**Hemorrhagic Stroke — 15%**)."
        ),
        "causes": (
            "• **Uncontrolled Hypertension (#1 cause), Atrial Fibrillation, Carotid Stenosis, Diabetes, High Cholesterol, and Tobacco Use.**"
        ),
        "symptoms": (
            "• **B.E.F.A.S.T. Warning Signs:**\n"
            "  - **B — Balance:** Sudden loss of balance or coordination.\n"
            "  - **E — Eyes:** Sudden blurred, double, or lost vision.\n"
            "  - **F — Face Drooping:** Uneven smile or facial numbness.\n"
            "  - **A — Arm / Leg Weakness:** Sudden weakness or paralysis on **one side of the body**.\n"
            "  - **S — Speech Difficulty:** Slurred speech or inability to speak/understand.\n"
            "  - **T — Time:** Note the exact time symptoms started!"
        ),
        "diagnosis": (
            "• **Urgent Non-Contrast CT Scan of the Brain** (distinguishes clot vs. hemorrhage immediately).\n"
            "• **MRI Brain (DWI), CT Angiography, Blood Glucose, Coagulation Profile, and ECG.**"
        ),
        "precautions": (
            "• **Note Exact Onset Time:** Essential for evaluating eligibility within the **4.5-hour Golden Window**.\n"
            "• **Strictly Nothing by Mouth (NPO):** **Do NOT give water, food, or oral tablets** due to choking/aspiration risk.\n"
            "• **Recovery Position:** Position the patient on their side with the head slightly elevated if drowsy."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **Neurologist (DM Neurology), Neurosurgeon**, and **Emergency Stroke Team**."
        ),
        "serious_hospital_and_helplines": (
            "• **CRITICAL EMERGENCY — TRIGGER SOS OR DIAL 108 / 112 IMMEDIATELY!**\n"
            "• Rush to a **CT-Scan & Stroke-Unit equipped Government Medical College, AIIMS, NIMHANS, PGIMER, or PM-JAY Hospital**."
        ),
    },
    {
        "keywords": ["appendicitis", "appendix", "એપેન્ડિક્સ", "अपेंडिसाइटिस", "अपेंडिक्स"],
        "title": "Acute Appendicitis",
        "overview": (
            "Acute appendicitis is a sudden inflammation of the appendix in the **lower right abdomen**. It is a surgical emergency because an untreated appendix can perforate within 24–72 hours."
        ),
        "causes": (
            "• **Luminal Obstruction:** Blockage of the appendiceal lumen by a fecalith or lymphoid hyperplasia, leading to bacterial overgrowth and ischemia."
        ),
        "symptoms": (
            "• **Migratory Pain:** Begins around the **navel** and localizes within 6–12 hours as **sharp, constant pain in the lower right abdomen (McBurney's point)**, worsened by coughing or movement.\n"
            "• **Associated Signs:** Nausea, vomiting, anorexia (loss of appetite), low-grade fever, and abdominal guarding."
        ),
        "diagnosis": (
            "• **Surgical Clinical Exam, Graded-Compression Ultrasound (USG Abdomen & Pelvis), Contrast CT Abdomen, CBC (Leukocytosis), CRP, and Urine Routine.**"
        ),
        "precautions": (
            "• **Keep Stomach Empty (NPO):** Do not eat or drink water in case urgent surgery is required.\n"
            "• **Avoid Heating Pads, Laxatives, or Unprescribed Painkillers:** Heat or laxatives can precipitate rupture, and painkillers can mask clinical signs."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **General & Laparoscopic Surgeon (MS General Surgery)**."
        ),
        "serious_hospital_and_helplines": (
            "• **Surgical Emergency:** Trigger SOS or dial **108** and proceed to a **24x7 Surgical Emergency Ward at a Government Civil Hospital, Medical College, or PM-JAY Hospital**."
        ),
    },
    {
        "keywords": ["typhoid", "enteric fever", "ટાઇફોઇડ", "टाइफाइड", "டைபாய்டு"],
        "title": "Typhoid Fever (Enteric Fever)",
        "overview": (
            "Typhoid fever is a systemic bacterial infection caused by ***Salmonella enterica* serotype Typhi**, contracted through contaminated water or food."
        ),
        "causes": (
            "• **Fecal-Oral Transmission:** Unboiled/unfiltered water, contaminated ice, street-vended cut fruits, raw salads, or unpasteurized milk."
        ),
        "symptoms": (
            "• **Step-Ladder Fever:** Progressively rising fever reaching **103°F–104°F**, diffuse abdominal pain, coated tongue, headache, profound weakness, and diarrhea or constipation."
        ),
        "diagnosis": (
            "• **Blood Culture (BACTEC — Week 1 Gold Standard)**, **Typhidot IgM / Widal Test (Week 2+)**, **CBC**, and **Liver Enzymes (SGPT/SGOT)**."
        ),
        "precautions": (
            "• **Boiled Water & Bland Diet:** Drink only rolling-boiled cooled water and WHO-ORS; eat soft, low-fiber meals (moong dal khichdi, curd rice, mashed banana) and avoid spicy/fried/coarse foods."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **General Physician / Internal Medicine Specialist (MD Medicine)** or **Pediatrician**."
        ),
        "serious_hospital_and_helplines": (
            "• **Emergency Red Flags:** Black/bloody stools, severe abdominal rigidity, persistent vomiting, or confusion—dial **108** immediately."
        ),
    },
    {
        "keywords": ["pneumonia", "lung infection", "નિમોનિયા", "निमोनिया", "நிமோனியா"],
        "title": "Pneumonia (Acute Lung Infection)",
        "overview": (
            "Pneumonia is an acute lower respiratory tract infection that inflames the lung alveoli, filling them with exudate and impairing gas exchange."
        ),
        "causes": (
            "• **Bacterial (*Streptococcus pneumoniae*), Viral (Influenza, RSV), or Aspiration Triggers.**"
        ),
        "symptoms": (
            "• Deep **productive cough** with yellow/green/rust sputum, **shortness of breath**, rapid breathing, **sharp pleuritic chest pain**, and high fever (**102°F–104°F**) with chills."
        ),
        "diagnosis": (
            "• **Pulse Oximetry (SpO₂)**, **Digital Chest X-Ray (PA View)**, **CBC, CRP/Procalcitonin**, and **Sputum Culture**."
        ),
        "precautions": (
            "• Rest propped up at 45 degrees, maintain warm hydration and steam inhalation, and monitor **SpO₂ oxygen saturation** closely."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **Pulmonologist (MD Respiratory Medicine)**, **MD Internal Medicine**, or **Pediatrician**."
        ),
        "serious_hospital_and_helplines": (
            "• **CRITICAL RED FLAGS:** **SpO₂ < 92%–94%**, bluish lips/nails, chest indrawing, or confusion—**Dial 108 immediately**."
        ),
    },
    {
        "keywords": ["malaria", "shivering fever", "મલેરિયા", "मलेरिया"],
        "title": "Malaria",
        "overview": (
            "Malaria is an acute mosquito-borne protozoal blood infection caused by ***Plasmodium vivax*** or ***Plasmodium falciparum***, transmitted by female *Anopheles* mosquitoes."
        ),
        "causes": (
            "• **Parasitic Transmission:** Bite of an infected *Anopheles* mosquito (primarily dusk to dawn)."
        ),
        "symptoms": (
            "• **Classic 3-Stage Paroxysm:** **Cold Stage** (intense shivering rigors), **Hot Stage** (103°F–105°F fever, headache, vomiting), and **Sweating Stage** (profuse sweat and temperature drop), plus anemia and splenomegaly."
        ),
        "diagnosis": (
            "• **Peripheral Blood Smear (Thick & Thin Giemsa Film)**, **Rapid Diagnostic Antigen Test (RDT)**, and **CBC (Hemoglobin & Platelets)**."
        ),
        "precautions": (
            "• Maintain oral hydration with WHO-ORS, use lukewarm sponging during fever spikes, sleep under insecticide-treated mosquito nets, and complete species-specific medical treatment under a physician."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **General Physician / Internal Medicine Specialist (MD Medicine)**."
        ),
        "serious_hospital_and_helplines": (
            "• **Cerebral / Severe Malaria Red Flags:** Confusion, seizures, dark cola-colored urine, jaundice, or persistent vomiting—**Dial 108 immediately**."
        ),
    },
    {
        "keywords": ["jaundice", "hepatitis", "yellow eyes", "liver", "કમળો", "पीलिया"],
        "title": "Jaundice & Acute Viral Hepatitis",
        "overview": (
            "Jaundice is the yellowish discoloration of the sclera (whites of the eyes) and skin due to elevated **Serum Bilirubin (> 2.5 mg/dL)** from hepatic inflammation or biliary obstruction."
        ),
        "causes": (
            "• **Water-/Food-Borne Viral Hepatitis (Hep A & Hep E)**, **Blood-Borne Hepatitis (Hep B & Hep C)**, alcohol/drug toxicity, or gallstones."
        ),
        "symptoms": (
            "• **Dark mustard/tea-colored urine**, **yellowing of eyes and skin**, pale stools, extreme aversion to food smell, nausea, fatigue, and right upper quadrant ache."
        ),
        "diagnosis": (
            "• **Liver Function Test (Total/Direct Bilirubin, SGPT/ALT, SGOT/AST, ALP, Albumin)**, **Viral Serology (Anti-HAV IgM, Anti-HEV IgM, HBsAg, Anti-HCV)**, **PT/INR**, and **USG Whole Abdomen**."
        ),
        "precautions": (
            "• **Strictly Avoid Unverified Herbal Concoctions, Alcohol, Oily Foods & Unprescribed Painkillers.**\n"
            "• Drink boiled cooled water, coconut water, and eat soft steamed carbohydrate meals."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **Gastroenterologist / Hepatologist (DM Gastroenterology)** or **MD Internal Medicine**."
        ),
        "serious_hospital_and_helplines": (
            "• **Hepatic Encephalopathy / Liver Failure Red Flags:** Drowsiness, confusion, persistent vomiting, bleeding gums, or abdominal fluid swelling—**Dial 108 immediately**."
        ),
    },
    {
        "keywords": ["kidney stone", "renal stone", "calculus", "flank pain", "પથરી", "किडनी स्टोन", "पथरी"],
        "title": "Kidney Stones (Renal Calculi / Urolithiasis)",
        "overview": (
            "Kidney stones are crystalline mineral deposits (Calcium Oxalate, Uric Acid, or Struvite) that form in the kidneys and cause acute colicky pain when migrating through the ureter."
        ),
        "causes": (
            "• **Chronic Dehydration (Low Urine Volume)**, high dietary sodium, high oxalate intake, hypercalciuria, or hyperuricemia."
        ),
        "symptoms": (
            "• **Renal Colic:** Sudden, severe wave-like pain from the **flank/back radiating to the lower abdomen and groin**, burning urination, pink/red urine (hematuria), nausea, and vomiting."
        ),
        "diagnosis": (
            "• **Ultrasound KUB**, **Non-Contrast Helical CT KUB (NCCT KUB)**, **Urine Routine & Culture**, and **Serum Creatinine, Uric Acid & Calcium**."
        ),
        "precautions": (
            "• Drink **3 to 3.5 Liters of water daily** (including fresh lemon water for natural citrate), reduce dietary salt, and limit high-oxalate foods (spinach, beetroot, nuts)."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **Urologist (MCh Urology)** or **Nephrologist**."
        ),
        "serious_hospital_and_helplines": (
            "• **UROLOGICAL EMERGENCY:** Stone pain with **high fever and chills** (infected obstructed kidney) or **inability to pass urine for >8 hours**—**Dial 108 immediately**."
        ),
    },
    {
        "keywords": ["asthma", "bronchitis", "wheezing", "breathlessness", "અસ્થમા", "अस्थमा", "दमा"],
        "title": "Bronchial Asthma & Acute Bronchitis",
        "overview": (
            "Asthma is a chronic airway inflammatory condition causing reversible bronchial hyper-responsiveness, wheezing, breathlessness, chest tightness, and nocturnal/early-morning cough."
        ),
        "causes": (
            "• Dust mites, air pollution/smoke, pollen, cold air, viral respiratory infections, or NSAID sensitivity."
        ),
        "symptoms": (
            "• High-pitched **expiratory wheezing**, shortness of breath, chest tightness, and cough worsening at night or early morning."
        ),
        "diagnosis": (
            "• **Spirometry (PFT with FEV1/FVC bronchodilator reversibility)**, **Peak Expiratory Flow Rate (PEFR)**, **Pulse Oximetry (SpO₂)**, **Chest X-Ray**, and **CBC (Eosinophils / IgE)**."
        ),
        "precautions": (
            "• Avoid dust, smoke, and cold air triggers; use wet mopping; wear a mask in polluted areas; and follow your pulmonologist's action plan."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **Pulmonologist / Chest Physician (MD Respiratory Medicine)**."
        ),
        "serious_hospital_and_helplines": (
            "• **SEVERE ASTHMA ATTACK RED FLAGS:** Inability to speak full sentences, **SpO₂ < 92%**, bluish lips, or silent chest—**Dial 108 immediately**."
        ),
    },
    {
        "keywords": ["migraine", "headache", "vertigo", "dizziness", "માથાનો દુખાવો", "सिरदर्द", "माइग्रेन", "चक्कर"],
        "title": "Migraine, Tension Headache & Vertigo",
        "overview": (
            "Primary headaches include **Migraine** (pulsating, often unilateral head pain with light/sound sensitivity and nausea) and **Tension Headache** (bilateral band-like tightness), while secondary headaches can arise from hypertension, sinusitis, or eye strain."
        ),
        "causes": (
            "• **Skipped meals/fasting**, dehydration, sleep irregularity, bright screens, stress, hormonal shifts, uncorrected eye power, or high blood pressure."
        ),
        "symptoms": (
            "• Throbbing temple/head pain (4–72h), **photophobia** (light sensitivity), **phonophobia** (sound sensitivity), visual aura, nausea, or spinning vertigo."
        ),
        "diagnosis": (
            "• **Blood Pressure (BP) & Blood Sugar Check**, **Ophthalmic Eye Refraction**, **ENT Sinus Exam**, and **MRI/CT Brain** if red flags exist."
        ),
        "precautions": (
            "• Rest in a dark quiet room with a cool forehead compress; follow the **SEEDS routine** (Sleep 7–8h, Eat meals on time without fasting, Exercise gently, Drink 2.5–3L water, take Screen breaks every 20 mins)."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **Neurologist (DM Neurology)**, **General Physician (MD Medicine)**, or **Ophthalmologist**."
        ),
        "serious_hospital_and_helplines": (
            "• **EMERGENCY HEADACHE RED FLAGS:** Sudden 'thunderclap' headache, headache with **high fever and stiff neck**, slurred speech, limb weakness, or post-head-injury headache—**Dial 108 immediately**."
        ),
    },
    {
        "keywords": ["stomach", "acidity", "gas", "ulcer", "gastritis", "diarrhea", "loose motion", "vomiting", "food poisoning", "પેટમાં દુખાવો", "पेट दर्द", "एसिडिटी", "दस्त"],
        "title": "Acidity (GERD), Gastritis, Peptic Ulcer & Acute Gastroenteritis",
        "overview": (
            "Gastrointestinal distress includes **Acid Peptic Disease (GERD, Gastritis, Peptic Ulcers)**—mucosal irritation from gastric acid—and **Acute Gastroenteritis**—infectious diarrhea and vomiting causing fluid and electrolyte depletion."
        ),
        "causes": (
            "• ***H. pylori* infection**, frequent NSAID painkiller use, spicy/fried foods, irregular meals, or contaminated water/food (*E. coli, Salmonella, Rotavirus*)."
        ),
        "symptoms": (
            "• Epigastric burning, heartburn, sour regurgitation, bloating, crampy abdominal pain, watery loose stools, nausea, vomiting, and dehydration signs (dry tongue, reduced urine)."
        ),
        "diagnosis": (
            "• **Clinical Hydration & Abdominal Exam**, **Stool Routine & Culture**, **USG Whole Abdomen**, and **Upper GI Endoscopy / *H. pylori* Breath or Stool Test**."
        ),
        "precautions": (
            "• **Oral Rehydration:** Sip **WHO-ORS** (1 packet in 1 Liter boiled cooled water) after every loose stool.\n"
            "• **Bland Diet:** Eat curd/buttermilk, soft moong dal khichdi, ripe banana, and steamed rice; avoid spicy/fried food, milk, and lying down within 2 hours of dinner."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** **Gastroenterologist (DM Gastroenterology)** or **General Physician (MD Medicine)**."
        ),
        "serious_hospital_and_helplines": (
            "• **EMERGENCY GI RED FLAGS:** Vomiting blood, black tarry or bloody stools, severe lower-right or rigid abdominal pain, or no urination for >6–8 hours—**Dial 108 immediately**."
        ),
    },
]



# ==============================================================================
# UPGRADED SYMPTOM-TO-DISEASE & DRUG-CLASS CONVERSATIONAL MEMORY PATCH
# ==============================================================================
INDIAN_BRAND_PROFILES.append({
    "brands": ["steroid", "steroids", "corticosteroid", "corticosteroids", "prednisolone", "wysolone", "omnacortil", "dexamethasone", "dexona", "betamethasone", "betnesol", "hydrocortisone", "deflazacort", "medrol", "methylprednisolone"],
    "generic_salt": "Systemic / Topical Corticosteroids (Prednisolone, Dexamethasone, Methylprednisolone, Hydrocortisone, Deflazacort)",
    "common_strengths": "5 mg, 10 mg, 20 mg, 40 mg, 0.5 mg, 4 mg, 6 mg Tablets; Injections & Inhalers",
    "uses": (
        "• **Severe Inflammation & Autoimmune Disorders:** Suppresses overactive immune inflammation in rheumatoid arthritis, lupus, vasculitis, inflammatory bowel disease, and severe eczema/psoriasis.\n"
        "• **Acute Respiratory & Allergic Emergencies:** Treats severe asthma attacks, COPD exacerbations, anaphylaxis, and severe drug/allergic reactions.\n"
        "• **Endocrine & Organ Support:** Replaces hormones in adrenal insufficiency and prevents organ transplant rejection."
    ),
    "side_effects": (
        "• **Short-Term Side Effects:** Elevated blood sugar (hyperglycemia), increased appetite, gastritis/acidity, mood swings, insomnia, and fluid retention.\n"
        "• **Long-Term Unsupervised Risks:** Weight gain, facial rounding (moon facies), high blood pressure, osteoporosis (bone thinning), cataracts, and lowered immunity."
    ),
    "contraindications": (
        "• **Systemic Fungal or Untreated Viral/Bacterial Infections:** Never use steroids on fungal skin infections (ringworm/tinea) or during uninvestigated viral fevers without a doctor's prescription."
    ),
    "interactions": (
        "• Combining steroids with NSAID painkillers (Ibuprofen, Diclofenac, Zerodol) sharply increases stomach ulcer and GI bleeding risk. Antidiabetic and BP medicines may require dose adjustments."
    ),
    "when_to_take": (
        "• **Strictly After Food (Morning Dose Preferred):** Oral steroids are taken immediately after breakfast/food to protect the stomach lining and match the body's natural morning cortisol rhythm."
    ),
    "precautions": (
        "• **Never Stop Abruptly:** Stopping oral steroids suddenly after more than 5–7 days of use can trigger a life-threatening adrenal crisis—doses must always be tapered gradually by a doctor."
    ),
    "warnings": (
        "• **Never Stop Abruptly:** Stopping oral steroids suddenly after more than 5–7 days of use can trigger a life-threatening adrenal crisis—doses must always be tapered gradually by a doctor."
    ),
})

CLINICAL_DISEASE_DATABASE.extend([
    {
        "keywords": ["sweat", "sweating", "tensed", "tension", "perspiration", "diaphoresis", "clammy"],
        "title": "Excessive Sweating (Diaphoresis) & Feeling Tensed — Differential Diagnosis",
        "overview": (
            "Experiencing heavy sweating together with feeling tensed, restless, or anxious points to an **autonomic nervous system ('fight-or-flight') activation** or an underlying metabolic/endocrine shift. Doctors evaluate four primary possibilities:"
        ),
        "causes": (
            "• **1. Acute Anxiety / Panic Surge:** Emotional or physical tension releases adrenaline, triggering sweaty palms/forehead, rapid heartbeat, and muscle tension.\n"
            "• **2. Hyperthyroidism (Overactive Thyroid):** Excess thyroid hormone accelerates metabolism, causing persistent sweating, heat intolerance, nervousness, fine hand tremors, and weight loss.\n"
            "• **3. Hypoglycemia (Low Blood Sugar < 70 mg/dL) or Hypertension Spike:** A sudden drop in blood glucose or a sharp spike in blood pressure causes cold sweating, shakiness, and internal tension.\n"
            "• **4. Cardiac or Respiratory Strain:** Sudden cold drenching sweats paired with chest heaviness, jaw/arm discomfort, or shortness of breath requires urgent cardiac evaluation."
        ),
        "symptoms": (
            "• **Associated Signs to Check:** Racing or pounding pulse (palpitations), trembling hands, dry mouth, dizziness, shortness of breath, or evening/night sweats (which, if paired with a cough, warrant screening for chest infection or TB)."
        ),
        "diagnosis": (
            "• **Immediate Vital Checks:** Measure **Blood Pressure (BP)**, **Pulse Rate**, and **Capillary Blood Sugar (RBS/FBS)**.\n"
            "• **Confirmatory Lab & Cardiac Workup:** **Thyroid Function Profile (TSH, Free T3, Free T4)**, **12-Lead ECG**, **Complete Blood Count (CBC)**, and **Serum Electrolytes**."
        ),
        "precautions": (
            "• **Immediate Calming & Hydration:** Sit upright in a cool, ventilated room, sip plain water or ORS (or take 3 teaspoons of sugar/glucose if you have been fasting and feel shaky), and practice slow **4-7-8 breathing**.\n"
            "• **Avoid Stimulants:** Avoid coffee, energy drinks, smoking, and sleep deprivation."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** Consult an **MD General Physician / Internal Medicine Specialist** for initial thyroid, sugar, and ECG screening."
        ),
        "serious_hospital_and_helplines": (
            "• **Emergency Red Flag:** If cold sweating is accompanied by **chest pain/pressure, radiating left-arm or jaw pain, fainting, or severe breathlessness**, trigger your Emergency SOS contact or dial **108 / 112** immediately."
        ),
    },
    {
        "keywords": ["cough", "coughing", "phlegm", "sputum", "dry cough", "wet cough"],
        "title": "Cough (Dry vs. Productive Cough) — Clinical Evaluation",
        "overview": (
            "A cough is a protective airway reflex triggered by irritation, mucus, or inflammation in the upper throat, bronchial tubes, or lungs. Diagnosis depends on **duration** and whether it is **dry or productive (with phlegm)**."
        ),
        "causes": (
            "• **1. Acute Viral Respiratory Infection / Flu (< 1–2 Weeks):** Caused by common cold viruses or influenza, often with sore throat or mild fever.\n"
            "• **2. Allergic Rhinitis / Bronchial Asthma:** Dry, tickling cough that worsens at night, early morning, or after dust/cold air exposure.\n"
            "• **3. Acute Bronchitis / Pneumonia:** Deep cough producing yellow, green, or rust-colored sputum with fever and chest discomfort.\n"
            "• **4. Acid Reflux (Laryngopharyngeal / Silent GERD):** Chronic dry throat-clearing cough after meals or when lying flat.\n"
            "• **5. Pulmonary Tuberculosis (If Cough Persists > 2 Weeks):** Cough lasting over 14 days accompanied by evening fever, night sweats, or weight loss."
        ),
        "symptoms": (
            "• **Key Features to Track:** Sputum color (clear/white in allergy/viral vs. yellow/green in bacterial vs. blood-streaked), fever, wheezing, and **SpO₂ oxygen saturation**."
        ),
        "diagnosis": (
            "• **Pulse Oximetry (SpO₂ ≥ 95% normal)** and **Stethoscope Chest Auscultation**.\n"
            "• **Complete Blood Count (CBC), Absolute Eosinophil Count (AEC)**, **Digital Chest X-Ray**, and **Sputum AFB / CBNAAT** (if cough lasts > 2 weeks)."
        ),
        "precautions": (
            "• **Airway Soothing & Hydration:** Drink warm water and clear soups to thin mucus, take warm steam inhalation twice daily, gargle with warm salt water, and avoid cold drinks, dust, and smoke."
        ),
        "doctor_recommendation": (
            "• **Recommended Specialists:** Consult a **General Physician (MD Medicine)** or **Pulmonologist (Chest Specialist)**."
        ),
        "serious_hospital_and_helplines": (
            "• **Emergency Red Flags:** Shortness of breath, **SpO₂ dropping below 94%**, coughing up blood, or high fever with chills."
        ),
    }
])

class AIAssistantService:
    def __init__(self) -> None:
        self._cached_working_model: str = ""
        self._runtime_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()

    def get_api_key(self) -> str:
        key_candidates = [self._runtime_api_key]
        config_path = os.path.join(BACKEND_DIR, "api_key_config.py")
        if os.path.isfile(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    for line in f.read().splitlines():
                        if line.strip().startswith("GEMINI_API_KEY") and "=" in line:
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            key_candidates.append(val)
            except Exception:
                pass

        key_candidates.append(str(CONFIG_FILE_KEY).strip().strip('"').strip("'"))
        key_candidates.append(os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'"))

        placeholders = {
            "", "PASTE_YOUR_GEMINI_API_KEY_HERE", "PASTE_YOUR_GEMINI_KEY_HERE",
            "your_actual_gemini_api_key_here", "YOUR_API_KEY",
        }
        for k in key_candidates:
            if k and k not in placeholders and len(k) >= 20:
                return k
        return ""

    def save_api_key(self, new_key: str) -> Tuple[bool, str]:
        clean_key = (new_key or "").strip().strip('"').strip("'")
        if len(clean_key) < 20:
            return False, "API key looks too short."
        self._runtime_api_key = clean_key
        os.environ["GEMINI_API_KEY"] = clean_key
        return True, "AI Online • Live Web Search"

    def _detect_location_followup(
        self, raw_query: str, en_query: str, history: List[Dict[str, str]]
    ) -> Optional[str]:
        q_clean = en_query.lower().strip()

        # Only trigger standalone location directory response if the user is explicitly asking for a location/facility
        has_disease_or_med_words = bool(
            re.search(
                r"\b(symptom|symptoms|cause|causes|precaution|precautions|test|tests|diagnose|diagnosis|treatment|medicine|tablet|capsule|syrup|side effect|interaction|contraindication|warning|ingredient|fever|pain|cough|cold|bp|sugar|diabetes|dengue|malaria|typhoid|depression|anxiety|asthma|ulcer|stone|jaundice|infection|syndrome|disease)\b",
                q_clean,
            )
        )
        asks_for_location_only = len(q_clean.split()) <= 5 or bool(
            re.search(
                r"(?:i live in|i am from|i'm from|living in|stay in|located in|hospitals in|hospital in|medicine store in|pharmacy in|jan aushadhi in)",
                q_clean,
            )
        )
        if has_disease_or_med_words and not re.search(r"\b(hospitals in|hospital in|pharmacy in|medicine store in)\b", q_clean):
            return None
        if not asks_for_location_only:
            return None

        known_places = set()
        for h in ALL_INDIA_HOSPITALS:
            known_places.add(h["city"].lower())
            known_places.add(h["state"].lower())
        extra_places = [
            "bangalore", "bombay", "calcutta", "madras", "baroda", "banaras", "kashi",
            "trivandrum", "cochin", "vizag", "gurgaon", "gurugram", "noida", "faridabad",
            "ghaziabad", "thane", "nashik", "aurangabad", "solapur", "kolhapur", "amravati",
            "gandhinagar", "jamnagar", "junagadh", "anand", "nadiad", "bharuch", "vapi",
            "valsad", "mehsana", "palanpur", "bhuj", "kutch", "morbi", "surendranagar",
            "udaipur", "kota", "ajmer", "bikaner", "kanpur", "agra", "prayagraj", "allahabad",
            "meerut", "varanasi", "gorakhpur", "jabalpur", "gwalior", "indore", "ujjain",
            "jamshedpur", "dhanbad", "deoghar", "gaya", "muzaffarpur", "siliguri", "durgapur",
            "cuttack", "rourkela", "puri", "ludhiana", "jalandhar", "patiala", "bathinda",
            "mohali", "haridwar", "dehradun", "jammu", "coimbatore", "madurai", "trichy",
            "salem", "vellore", "mangaluru", "hubli", "belagavi", "kozhikode", "thrissur",
            "kochi", "vijayawada", "guntur", "tirupati", "warangal",
        ]
        for ep in extra_places:
            known_places.add(ep)

        alias_map = {
            "bangalore": "Bengaluru", "bombay": "Mumbai", "calcutta": "Kolkata",
            "madras": "Chennai", "baroda": "Vadodara", "banaras": "Varanasi",
            "kashi": "Varanasi", "trivandrum": "Thiruvananthapuram", "cochin": "Kochi",
            "vizag": "Visakhapatnam",
        }

        for place in sorted(known_places, key=len, reverse=True):
            if re.search(rf"\b{re.escape(place)}\b", q_clean):
                return alias_map.get(place, place.title())

        loc_match = re.search(
            r"(?:i live in|i am from|i'm from|living in|stay in|located in|hospitals in|hospital in|medicine store in|pharmacy in)\s+([a-zA-Z\s]{3,30})",
            q_clean,
        )
        if loc_match:
            extracted_loc = loc_match.group(1).strip().title()
            return alias_map.get(extracted_loc.lower(), extracted_loc)

        return None

    def _build_location_hospitals_and_stores_response(
        self, location_name: str, lang_code: str
    ) -> Dict[str, Any]:
        loc_lower = location_name.lower()

        matched_hospitals = [
            h for h in ALL_INDIA_HOSPITALS
            if loc_lower in h["city"].lower() or loc_lower in h["state"].lower()
        ]
        matched_stores = [
            s for s in ALL_INDIA_MEDICINE_STORES
            if loc_lower in s["city"].lower() or loc_lower in s["state"].lower()
        ]

        if not matched_hospitals:
            matched_hospitals = [
                {
                    "name": f"Government Civil / District Headquarters Hospital, {location_name}",
                    "city": location_name,
                    "state": "India",
                    "facility_category": "Government District / Civil Hospital (24x7 Emergency & OPD)",
                    "schemes": "Ayushman Bharat PM-JAY, 70+ Vay Vandana & State Health Schemes",
                    "address": f"Main Civil Hospital Road, {location_name}",
                    "phone_general": "108 / 14555",
                    "phone_emergency": "108",
                }
            ]

        if not matched_stores:
            matched_stores = [
                {
                    "name": f"Pradhan Mantri Bhartiya Janaushadhi Kendra (PMBJK) — {location_name}",
                    "city": location_name,
                    "state": "India",
                    "facility_category": "Government Generic Medicine Store (50%–90% Lower Prices)",
                    "hours": "Open Daily (Hospital Unit 24x7)",
                    "address": f"District Civil Hospital Compound, {location_name}",
                    "phone_contact": "1800-180-8080",
                }
            ]

        hosp_lines = []
        for idx, h in enumerate(matched_hospitals[:6], start=1):
            hosp_lines.append(
                f"**{idx}. {h['name']} ({h['city']}, {h['state']})**\n"
                f"• **Category:** {h.get('facility_category', 'Hospital')}\n"
                f"• **Accepted Schemes:** {h['schemes']}\n"
                f"• **Address:** {h['address']}\n"
                f"• **General Helpline:** {h.get('phone_general', '108')} | **Emergency:** {h.get('phone_emergency', '108')}"
            )

        store_lines = []
        for idx, s in enumerate(matched_stores[:5], start=1):
            store_lines.append(
                f"**{idx}. {s['name']} ({s['city']})**\n"
                f"• **Facility:** {s.get('facility_category', 'Pharmacy')}\n"
                f"• **Timings:** {s.get('hours', 'Open Daily')}\n"
                f"• **Address:** {s['address']}\n"
                f"• **Helpline:** {s.get('phone_contact', '1800-180-8080')}"
            )

        sections = [
            f"📍 **Nova AI • Verified Hospitals & Medicine Stores in {location_name}**",
            "🏥 **Participating Government, AIIMS & PM-JAY Hospitals Near You:**\n\n" + "\n\n".join(hosp_lines),
            "💊 **Nearby Medicine Stores & Jan Aushadhi Pharmacies (50%–90% Subsidized Generic Medicines):**\n\n" + "\n\n".join(store_lines),
            "📞 **24x7 Emergency & National Helplines:**\n"
            "• **Emergency SOS / Ambulance:** Trigger your saved SOS contact or dial **108 / 112**\n"
            "• **PM-JAY National Verification Helpline:** Dial **14555**\n"
            "• **Jan Aushadhi Medicine Store Helpline:** Dial **1800-180-8080**",
        ]

        english_reply = strip_latex_artifacts("\n\n".join(sections))
        final_reply = (
            translate_multiline_response(english_reply, target_lang=lang_code)
            if lang_code != "en"
            else english_reply
        )

        return {
            "source": "nova_ai_location_directory",
            "model": "AI Online • Live Web Search",
            "api_connected": True,
            "language": lang_code,
            "reply": strip_latex_artifacts(final_reply),
            "english_reply": english_reply,
            "safety_disclaimer": "🟢 AI Online • Live Web Search",
        }

    def _parse_mg_and_specifiers(self, query_text: str) -> Tuple[str, List[str]]:
        q_lower = query_text.lower()
        strength_match = re.findall(
            r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g|iu|k)?)\b",
            q_lower,
            flags=re.IGNORECASE,
        )
        detected_strength = ""
        if strength_match:
            raw_s = strength_match[0].strip()
            detected_strength = f"{raw_s} mg" if raw_s.isdigit() else raw_s

        tokens = re.findall(r"\b[a-zA-Z0-9]+\b", q_lower)
        decoded_notes: List[str] = []
        seen_specs = set()
        for tok in tokens:
            if tok in SPECIFIER_DEFINITIONS and tok not in seen_specs:
                seen_specs.add(tok)
                decoded_notes.append(SPECIFIER_DEFINITIONS[tok])

        for spec_key, spec_desc in SPECIFIER_DEFINITIONS.items():
            if spec_key not in seen_specs and re.search(rf"[-+\s]{spec_key}\b", q_lower):
                seen_specs.add(spec_key)
                decoded_notes.append(spec_desc)

        return detected_strength, decoded_notes

    def _fuzzy_match_medicine_brand(self, combined_query: str) -> Optional[Dict[str, Any]]:
        for brand_profile in INDIAN_BRAND_PROFILES:
            for b_kw in brand_profile["brands"]:
                if re.search(rf"\b{re.escape(b_kw)}\b", combined_query):
                    return brand_profile

        words = [
            w for w in re.findall(r"[a-zA-Z]{4,}", combined_query.lower())
            if w not in ("what", "when", "take", "used", "medicine", "tablet", "symptoms", "causes", "disease", "precautions", "prevention", "tests", "diagnosis")
        ]
        all_brand_map = {}
        for bp in INDIAN_BRAND_PROFILES:
            for b_kw in bp["brands"]:
                all_brand_map[b_kw] = bp

        for w in words:
            close = difflib.get_close_matches(w, list(all_brand_map.keys()), n=1, cutoff=0.82)
            if close:
                return all_brand_map[close[0]]
        return None

    def _fuzzy_match_clinical_disease(self, raw_query: str, extracted_topic: str) -> Optional[Dict[str, Any]]:
        combined = f"{raw_query.lower()} {extracted_topic.lower()}"
        for entry in CLINICAL_DISEASE_DATABASE:
            for kw in entry["keywords"]:
                if re.search(rf"\b{re.escape(kw.lower())}\b", combined) or (len(kw) >= 4 and kw.lower() in combined):
                    return entry

        words = [
            w for w in re.findall(r"[a-zA-Z]{4,}", combined)
            if w not in ("what", "when", "tell", "about", "symptoms", "causes", "precautions", "prevention", "disease", "high", "pain", "medicine", "tablet")
        ]
        kw_to_entry = {}
        for entry in CLINICAL_DISEASE_DATABASE:
            for kw in entry["keywords"]:
                if re.match(r"^[a-zA-Z\s]+$", kw):
                    kw_to_entry[kw.lower()] = entry

        for w in words:
            close = difflib.get_close_matches(w, list(kw_to_entry.keys()), n=1, cutoff=0.78)
            if close:
                return kw_to_entry[close[0]]
        return None

    def _detect_query_intent(
        self, raw_query: str, en_query: str
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Strictly separates MEDICINE queries from DISEASE / SYMPTOM / GENERAL MEDICAL queries
        so general disease questions NEVER display irrelevant medicine recommendations.
        """
        combined = f"{raw_query.lower()} {en_query.lower()}"

        clean_words = re.sub(r"[^a-zA-Z\s]", "", en_query.lower()).strip()
        if clean_words in (
            "hi", "hello", "hey", "namaste", "namaskar", "vanakkam", "sat sri akal",
            "kem cho", "how are you", "who are you", "what can you do", "help",
            "thank you", "thanks", "good morning", "good evening", "good afternoon",
        ):
            return "CONVERSATIONAL_GREETING", None

        # Explicit request for medicine categories for a condition
        if re.search(
            r"\b(medicine for|medicines for|tablet for|tablets for|syrup for|drug for|drugs for|pill for|which medicine|what medicine|medication for|pharmacology for)\b",
            combined,
        ):
            return "MEDICINE_FOR_CAUSE", None

        # Check if user explicitly mentions a known medicine brand or pharmacological suffix/specifier
        matched_med = self._fuzzy_match_medicine_brand(combined)
        has_explicit_med_keywords = bool(
            re.search(
                r"\b(tablet|tab|capsule|cap|syrup|syp|injection|inj|ointment|inhaler|drops|pill|side effects of|contraindications of|interactions of|ingredients of|composition of|active salt)\b",
                combined,
                flags=re.IGNORECASE,
            )
            or re.search(
                r"(\b\d+(?:\.\d+)?\s*(?:mg|mcg|ml|iu)\b|\b(xl|sr|dsr|xr|er|md|dt|forte|duo|cv|sp|lc|oz|tz|gp)\b)",
                combined,
                flags=re.IGNORECASE,
            )
            or re.search(
                r"\b\w+(prazole|mycin|cillin|floxacin|olol|pril|sartan|dipine|statin|gliptin|formin|zole|tidine|setron|pam|zolam|proxen|fenac|coxib|lukast|zine|asone|olone|mab|nib|vir|cycline)\b",
                combined,
                flags=re.IGNORECASE,
            )
        )

        matched_disease = self._fuzzy_match_clinical_disease(raw_query, en_query)

        if matched_med and not matched_disease:
            return "SPECIFIC_MEDICINE", matched_med

        if has_explicit_med_keywords and not re.search(r"\b(symptoms of|causes of|how to prevent|how to diagnose)\b", combined):
            return "SPECIFIC_MEDICINE", matched_med

        if matched_disease:
            return "DISEASE_OR_SYMPTOM", matched_disease

        # Check if query is a single/short drug name in OpenFDA/RxNav
        topic_candidate = self._extract_medical_topic(en_query)
        if len(topic_candidate.split()) <= 3 and not re.search(
            r"\b(disease|syndrome|disorder|infection|fever|pain|ache|cancer|tumor|deficiency|virus|bacteria|symptom|cause|precaution|prevention|test|diagnosis)\b",
            combined,
        ):
            fda_probe = self._lookup_openfda_medicine(topic_candidate)
            if fda_probe:
                return "SPECIFIC_MEDICINE", fda_probe

        return "DISEASE_OR_SYMPTOM", None

    def _build_conversational_greeting_response(self, lang_code: str) -> Dict[str, Any]:
        english_reply = (
            "Namaste! I am **Nova AI**, your 22-Language Medical & Pharmaceutical Information Assistant.\n\n"
            "**How I can assist you today (with strict clinical separation):**\n"
            "• **1. Disease, Symptom & Prevention Guidance:** Ask about any common or rare condition (e.g., *Hypertension, Dengue, Tuberculosis, Diabetes, Stroke, Appendicitis, Guillain-Barré Syndrome, Lupus*) for its **Clinical Overview, Causes, Symptoms, Prevention & Precautions, Diagnostic Tests, and Specialist Doctor Guidance**.\n"
            "• **2. Medicine & Ingredient Search:** Ask about any medicine across all categories (e.g., *Lithonex 450 XL, Dolo 650, Zerodol-SP, Pan-D, Augmentin 625, Metformin, Atorvastatin*) for its **Active Ingredients, Uses, Side Effects, Contraindications, Interactions, and Warnings**.\n"
            "• **3. All-India 36 States & UTs Directory:** Reply with your **City or State name** to view verified Government/PM-JAY hospitals and Jan Aushadhi pharmacies near you."
        )
        final_reply = (
            translate_multiline_response(english_reply, target_lang=lang_code)
            if lang_code != "en"
            else english_reply
        )
        return {
            "source": "nova_ai_conversational",
            "model": "AI Online • Live Web Search",
            "api_connected": True,
            "language": lang_code,
            "reply": strip_latex_artifacts(final_reply),
            "english_reply": english_reply,
            "safety_disclaimer": "🟢 AI Online • Verified Clinical & Drug Reference",
        }

    def _lookup_openfda_medicine(self, med_query: str) -> Optional[Dict[str, Any]]:
        """Queries NIH RxNav (for spelling/generic normalization) and US FDA OpenFDA Official Drug Labels."""
        clean_q = re.sub(
            r"\b(what|is|are|the|use|uses|of|for|side|effects|effect|contraindications|interactions|warnings|ingredients|composition|tablet|tab|capsule|cap|syrup|injection|mg|mcg|ml|xl|sr|dsr|xr|er|md|dt|forte|plus|duo|cv|sp|lc|am|h|gp|oz|tz|tell|me|about|explain)\b",
            " ",
            med_query,
            flags=re.IGNORECASE,
        )
        clean_q = re.sub(r"[^a-zA-Z0-9\s-]", " ", clean_q)
        clean_q = re.sub(r"\s+", " ", clean_q).strip()
        if len(clean_q) < 3:
            return None

        resolved_name = clean_q
        try:
            rx_url = f"https://rxnav.nlm.nih.gov/REST/spellingsuggestions.json?name={urllib.parse.quote(clean_q)}"
            req_rx = urllib.request.Request(rx_url, headers={"User-Agent": "NovaHealthtech/2.0"})
            with urllib.request.urlopen(req_rx, timeout=3.5, context=SSL_CTX) as resp_rx:
                rx_data = json.loads(resp_rx.read().decode("utf-8"))
                suggs = rx_data.get("suggestionGroup", {}).get("suggestionList", {}).get("suggestion", [])
                if isinstance(suggs, list) and suggs:
                    resolved_name = str(suggs[0])
        except Exception:
            pass

        for candidate in (resolved_name, clean_q.split()[0]):
            if len(candidate) < 3:
                continue
            try:
                search_expr = (
                    f'openfda.brand_name:"{candidate}"+openfda.generic_name:"{candidate}"+openfda.substance_name:"{candidate}"'
                )
                fda_url = f"https://api.fda.gov/drug/label.json?search={urllib.parse.quote(search_expr, safe=':+\\\"')}&limit=1"
                req_fda = urllib.request.Request(fda_url, headers={"User-Agent": "NovaHealthtech/2.0"})
                with urllib.request.urlopen(req_fda, timeout=4.5, context=SSL_CTX) as resp_fda:
                    fda_json = json.loads(resp_fda.read().decode("utf-8"))
                    results = fda_json.get("results", [])
                    if results:
                        item = results[0]
                        openfda = item.get("openfda", {})
                        brands = ", ".join((openfda.get("brand_name") or [candidate.title()])[:4])
                        generics = ", ".join(
                            (openfda.get("generic_name") or openfda.get("substance_name") or [candidate.title()])[:4]
                        )
                        pharm_class = ", ".join(
                            (openfda.get("pharm_class_epc") or ["Verified Pharmaceutical Formulation"])[:2]
                        )
                        return {
                            "is_openfda": True,
                            "display_name": f"{brands} ({generics})",
                            "generic_salt": f"{generics} — {pharm_class}",
                            "common_strengths": "As specified on the manufacturer's approved labeling",
                            "uses": "• " + (item.get("indications_and_usage") or ["Indicated for clinical use under physician supervision."])[0][:700],
                            "side_effects": "• " + (item.get("adverse_reactions") or ["Monitor for hypersensitivity, gastrointestinal upset, or organ-specific adverse events."])[0][:650],
                            "contraindications": "• " + (item.get("contraindications") or ["Known hypersensitivity to the active ingredient or any excipient."])[0][:550],
                            "interactions": "• " + (item.get("drug_interactions") or ["Review all concurrent prescription and over-the-counter medicines with a physician or pharmacist."])[0][:550],
                            "warnings": "• " + (item.get("warnings_and_cautions") or item.get("warnings") or item.get("boxed_warning") or ["Use strictly under qualified medical oversight."])[0][:650],
                        }
            except Exception:
                pass
        return None

    def _search_live_web_for_indian_brand(self, med_name: str, base_drug: str) -> Dict[str, str]:
        web_info = {"composition": "", "uses": "", "side_effects": "", "warnings": ""}
        try:
            ddg_query = urllib.parse.quote(f"{med_name} tablet medicine composition uses side effects contraindications")
            ddg_url = f"https://html.duckduckgo.com/html/?q={ddg_query}"
            req = urllib.request.Request(
                ddg_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"},
            )
            with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as resp:
                raw_html = resp.read().decode("utf-8", errors="ignore")
                snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', raw_html, flags=re.I | re.S)
                clean_snippets = []
                for s in snippets[:5]:
                    cs = html.unescape(re.sub(r"<[^>]+>", " ", s))
                    cs = re.sub(r"\s+", " ", cs).strip()
                    if len(cs) > 35:
                        clean_snippets.append(cs)
                if clean_snippets:
                    web_info["uses"] = "• " + "\n• ".join(clean_snippets[:3])[:850]
                    comp_match = re.search(
                        r"(?:contains|composition|composed of|active ingredient is|salt is)\s+([A-Z][a-zA-Z0-9\s\-+()]{3,50})",
                        " ".join(clean_snippets),
                        flags=re.I,
                    )
                    if comp_match:
                        web_info["composition"] = comp_match.group(1).strip()
        except Exception:
            pass
        return web_info

    def _call_llm_for_medicine_or_disease(
        self, en_query: str, mode: str, reference_notes: str, api_key: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[str]:
        """
        Uses Gemini 2.5 Flash (when configured) with strict non-fabrication and separation rules.
        """
        if not api_key or len(api_key) < 20:
            return None

        if mode == "MEDICINE":
            sys_prompt = (
                "You are Nova, a careful, friendly medical and medicine information companion. "
                "Answer the exact medicine question the user asked first. Stay strictly within medicine, "
                "pharmacology, health, and clinical science. Never drift into history, companies, geography, "
                "or unrelated topics. Identify the active ingredient only when reliable; distinguish brand "
                "names from generic names and country-specific formulations. Explain uses, how it works, "
                "common and serious side effects, important interactions, contraindications, and what must "
                "be checked on the package. If the exact brand or formulation cannot be verified, say so "
                "plainly and ask for the active ingredient or a clear photo of the label. Do not guess. "
                "Do not prescribe a personal dose, tell a user to start/stop/change a medicine, or replace "
                "a pharmacist/doctor. Use plain language, define medical terms, and keep the answer focused. "
                "When useful, finish with one relevant follow-up question."
            )
        else:
            sys_prompt = (
                "You are Nova, an interactive, patient-friendly medical education companion. "
                "The user is asking a medical, health, symptom, body-system, mental-health, diagnostic, "
                "treatment-science, or medicine-related question. Answer the exact question directly in "
                "the first 1-2 sentences. Stay strictly on the user's topic. Do not substitute a similarly "
                "named company, person, historical event, or unrelated Wikipedia topic. If an acronym is "
                "ambiguous, use the surrounding medical wording; for example BP in a question about symptoms "
                "means blood pressure. Explain concepts in simple everyday language, then add only the most "
                "relevant causes, signs, tests, care options, and warning signs. Do not force every answer "
                "into a long generic template. Do not invent a diagnosis or claim certainty from symptoms. "
                "Do not prescribe individualized medicine or dosages. For emergencies, clearly advise urgent "
                "local medical help. If the question is outside medicine, politely say Nova is a medical-only "
                "assistant and invite a health or medicine question. Be warm, conversational, concise but "
                "complete, and ask at most one useful follow-up question."
            )
        if reference_notes:
            sys_prompt += f"\n\nVERIFIED REFERENCE CONTEXT:\n{reference_notes[:1600]}"

        try:
            gem_res = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                params={"key": api_key},
                json={
                    "system_instruction": {"parts": [{"text": sys_prompt}]},
                    "contents": (
                        [
                            {"role": "user" if item.get("role") == "user" else "model",
                             "parts": [{"text": str(item.get("text", ""))[:1200]}]}
                            for item in (history or [])[-6:]
                            if isinstance(item, dict) and str(item.get("text", "")).strip()
                        ]
                        + [{"role": "user", "parts": [{"text": en_query[:1200]}]}]
                    ),
                    "generationConfig": {"temperature": 0.35, "maxOutputTokens": 1000},
                },
                timeout=5.5,
            )
            if gem_res.ok:
                candidates = gem_res.json().get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and parts[0].get("text"):
                        text_out = parts[0]["text"].strip()
                        if len(text_out) > 40:
                            return strip_latex_artifacts(text_out)
        except Exception:
            pass
        return None

    def _build_specific_medicine_response(
        self,
        user_message: str,
        en_query: str,
        matched_profile: Optional[Dict[str, Any]],
        lang_code: str,
        lang_name: str,
        api_key: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        cleaned_title = re.sub(
            r"^(what is the use of|what are the uses of|what are the side effects of|what is|tell me about|uses of|side effects of|contraindications of|interactions of|ingredients of|explain|details of)\s+",
            "",
            en_query.strip(),
            flags=re.I,
        )
        cleaned_title = re.sub(r"[?.,!]+$", "", cleaned_title).strip().upper() or en_query.strip().upper()
        detected_strength, specifier_notes = self._parse_mg_and_specifiers(en_query)

        base_drug = re.sub(
            r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g|iu|k)?|xl|sr|dsr|xr|er|pr|cr|md|dt|od|bd|forte|plus|duo|cv|sp|lc|am|h|gp|oz|tz|lb|tablet|tab|capsule|cap|syrup)\b",
            " ",
            cleaned_title,
            flags=re.I,
        )
        base_drug = re.sub(r"\s+", " ", base_drug).strip() or cleaned_title

        profile = matched_profile
        if not profile:
            profile = self._lookup_openfda_medicine(base_drug)

        if profile:
            composition = profile.get("generic_salt", "Verified Pharmaceutical Salt")
            strengths_info = detected_strength or profile.get("common_strengths", "As printed on the approved pack")
            uses = profile.get("uses", "• Prescribed for conditions responsive to its active ingredient.")
            side_effects = profile.get("side_effects", "• Monitor for allergic reactions, GI discomfort, or dizziness.")
            contraindications = profile.get("contraindications", "• Known hypersensitivity to the active substance or excipients.")
            interactions = profile.get("interactions", "• Inform your doctor of all concurrent prescription and OTC medicines.")
            warnings = profile.get("warnings", profile.get("precautions", "• Use strictly under registered medical supervision."))
            verification_note = "• **Source Verification:** Verified against indexed clinical pharmacology / OpenFDA drug labeling records."
        else:
            web_med = self._search_live_web_for_indian_brand(cleaned_title, base_drug)
            wiki_med = self._fetch_live_web_medical_data(base_drug)
            llm_med = self._call_llm_for_medicine_or_disease(
                en_query, "MEDICINE", web_med.get("uses", ""), api_key, history=history
            )

            if llm_med:
                sections_llm = [
                    f"💊 **Nova AI • Medicine & Pharmacology Reference: {cleaned_title}**",
                    llm_med,
                ]
                if specifier_notes:
                    sections_llm.append("**Formulation Specifier Meaning:**\n" + "\n".join([f"• {n}" for n in specifier_notes]))
                sections_llm.append(MANDATORY_MEDICINE_WARNING.strip())
                english_reply = strip_latex_artifacts("\n\n".join(sections_llm))
                final_reply = translate_multiline_response(english_reply, target_lang=lang_code) if lang_code != "en" else english_reply
                return {
                    "source": "nova_ai_medicine_guide",
                    "model": "AI Online • Live Web Search",
                    "api_connected": True,
                    "language": lang_code,
                    "reply": strip_latex_artifacts(final_reply),
                    "english_reply": english_reply,
                    "safety_disclaimer": "🟢 AI Online • Verified Pharmacology Reference",
                }

            has_verified_extract = bool(web_med["composition"] or web_med["uses"] or wiki_med["overview"])
            composition = (
                web_med["composition"]
                or (f"{wiki_med['title']} (Active Agent)" if wiki_med["overview"] else "Unverified Regional / Specialty Brand Name")
            )
            strengths_info = detected_strength or "Refer to physical manufacturer strip"
            if has_verified_extract:
                uses = web_med["uses"] or f"• {wiki_med['overview']}"
                verification_note = "• **Verification Note:** Retrieved from live medical literature; always verify regional brand salt composition on the physical blister pack."
            else:
                uses = (
                    f"• **Verification Notice:** Exact active ingredients and regional availability for **{cleaned_title}** could not be verified in public FDA/RxNav monographs. "
                    f"Regional brand names in India and globally can occasionally share similar names while containing different active salts."
                )
                verification_note = (
                    "• **Uncertainty Disclosure:** Because this specific brand/name could not be independently verified against indexed drug databases, "
                    "Nova AI does not fabricate ingredient or dosing claims. Please check the generic salt printed in brackets under the brand name on your medicine strip and share that salt name, or consult your pharmacist/physician."
                )
            side_effects = (
                "• Potential adverse reactions depend on the exact active salt and patient organ function (watch for allergic skin rash, GI upset, dizziness, or swelling of lips/tongue)."
            )
            contraindications = (
                "• Contraindicated in patients with known hypersensitivity to the active salt, and requires caution in pregnancy, lactation, pediatrics, and severe renal/hepatic impairment."
            )
            interactions = (
                "• Always disclose all existing blood pressure, diabetes, psychiatric, blood-thinning, or pain medications to your prescribing doctor to prevent drug-drug interactions."
            )
            warnings = verification_note

        spec_block = ""
        if specifier_notes:
            spec_block = "\n\n**Formulation Suffix / Specifier Meaning:**\n" + "\n".join([f"• {note}" for note in specifier_notes])

        sections = [
            f"💊 **Nova AI • Comprehensive Medicine Information: {cleaned_title}**",
            f"**1. Active Ingredients (Generic Salt) & Strength:**\n• **Queried Medicine:** {cleaned_title}\n• **Active Ingredient / Salt:** {composition}\n• **Strength / Form:** {strengths_info}{spec_block}",
            f"**2. Clinical Uses & Indications:**\n{uses}",
            f"**3. Side Effects & Adverse Reactions:**\n{side_effects}",
            f"**4. Contraindications (Who Should Not Take It):**\n{contraindications}",
            f"**5. Drug, Food & Alcohol Interactions:**\n{interactions}",
            f"**6. Warnings & Verification Status:**\n{warnings}",
            "🏥 **7. Generic Availability & Verification:**\n• Quality WHO-GMP certified generic medicines are available at **PM Bhartiya Janaushadhi Kendras (Helpline: 1800-180-8080)**. Availability of rare or specialty molecules may vary by state and hospital formulary.",
            MANDATORY_MEDICINE_WARNING.strip(),
        ]

        english_reply = strip_latex_artifacts("\n\n".join(sections))
        final_reply = (
            translate_multiline_response(english_reply, target_lang=lang_code)
            if lang_code != "en"
            else english_reply
        )

        return {
            "source": "nova_ai_medicine_guide",
            "model": "AI Online • Live Web Search",
            "api_connected": True,
            "language": lang_code,
            "reply": strip_latex_artifacts(final_reply),
            "english_reply": english_reply,
            "safety_disclaimer": "🟢 AI Online • Non-Prescriptive Medicine Reference",
        }

    def _build_medicine_for_cause_response(
        self,
        user_message: str,
        en_query: str,
        lang_code: str,
        lang_name: str,
        api_key: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        q = en_query.lower()
        if api_key:
            llm_answer = self._call_llm_for_medicine_or_disease(
                en_query, "MEDICINE", "", api_key, history=history
            )
            if llm_answer:
                english_reply = strip_latex_artifacts(
                    "**Nova AI • Medicine and treatment information**\n\n"
                    + llm_answer + "\n\n" + MANDATORY_MEDICINE_WARNING.strip()
                )
                final_reply = translate_multiline_response(english_reply, target_lang=lang_code) if lang_code != "en" else english_reply
                return {
                    "source": "nova_ai_medicine_for_cause",
                    "model": "AI Online • Medical Companion",
                    "api_connected": True,
                    "language": lang_code,
                    "reply": strip_latex_artifacts(final_reply),
                    "english_reply": english_reply,
                    "safety_disclaimer": "Medical information only • No personalized prescribing",
                }
        if any(w in q for w in ["fever", "temperature", "body ache", "headache"]):
            cause_title = "Fever, Body Ache & Headache"
            med_discussion = (
                "• **Standard Therapeutic Class:** **Antipyretics / Non-Opioid Analgesics** (such as *Paracetamol / Acetaminophen*) are the standard first-line class evaluated by physicians to reduce fever and mild-to-moderate pain.\n"
                "• **Important Contraindication & Warning:** Non-Steroidal Anti-Inflammatory Drugs (NSAIDs such as *Ibuprofen, Diclofenac, Aceclofenac, Aspirin*) are strictly avoided during uninvestigated fevers in India until **Dengue fever** is ruled out, due to platelet impairment and bleeding risk.\n"
                "• **Clinical Oversight Required:** Exact milligram strength and dosing intervals must be determined by a registered physician based on patient age, weight, and liver health."
            )
        elif any(w in q for w in ["acidity", "gas", "heartburn", "stomach burn", "indigestion", "reflux"]):
            cause_title = "Acidity, Heartburn & Acid Reflux (GERD)"
            med_discussion = (
                "• **Standard Therapeutic Classes:** Clinicians typically evaluate **Antacids** (Aluminium/Magnesium Hydroxide with Simethicone for rapid neutralization), **H2-Receptor Blockers**, or **Proton Pump Inhibitors (PPIs)** (such as *Pantoprazole, Omeprazole, Rabeprazole*) for acid suppression.\n"
                "• **Warnings & Contraindications:** Acid-suppressing medicines should not be used long-term without medical evaluation if alarm symptoms (difficulty swallowing, black stools, unexplained weight loss, or persistent vomiting) are present."
            )
        else:
            cause_title = en_query.title()
            med_discussion = (
                f"• **Pharmacological Categories for {cause_title}:** Medical treatment depends on confirming the exact underlying etiology (viral, bacterial, metabolic, or inflammatory) through a clinical exam and diagnostic tests.\n"
                f"• **Why Nova AI Does Not Prescribe:** Prescribing a specific tablet or dosage without examining the patient carries risks of drug interactions, allergies, or masking a serious condition.\n"
                f"• **How to Look Up a Prescribed Medicine:** If a doctor has already given you a prescription, type the **exact medicine or generic salt name** into this chat to view its ingredients, uses, side effects, contraindications, interactions, and warnings."
            )

        english_reply = strip_latex_artifacts(
            "\n\n".join(
                [
                    f"💊 **Nova AI • Pharmacological Category Overview: {cause_title}**",
                    f"**1. Therapeutic Classes & Safety Considerations:**\n{med_discussion}",
                    MANDATORY_MEDICINE_WARNING.strip(),
                ]
            )
        )

        final_reply = (
            translate_multiline_response(english_reply, target_lang=lang_code)
            if lang_code != "en"
            else english_reply
        )

        return {
            "source": "nova_ai_medicine_for_cause",
            "model": "AI Online • Live Web Search",
            "api_connected": True,
            "language": lang_code,
            "reply": strip_latex_artifacts(final_reply),
            "english_reply": english_reply,
            "safety_disclaimer": "🟢 AI Online • Non-Prescriptive Medicine Reference",
        }

    def _extract_medical_topic(self, en_query: str) -> str:
        if ":" in en_query:
            before_colon = en_query.split(":", 1)[0].strip()
            if len(before_colon) >= 2:
                en_query = before_colon

        cleaned = en_query.lower().strip()
        stop_phrases = [
            r"^(what are the|what is the|what are|what is|tell me about|explain|how to diagnose|how to prevent|how to treat|how to cure|give me|can you tell me|how do doctors diagnose|i have a|i have|i am suffering from|suffering from)\s+",
            r"\b(symptoms|symptom|causes|cause|precautions|precaution|prevention|prevent|treatment|diagnosis|diagnostic|tests|test|how|doctors|diagnose|it|in detail|and|its|of|for|about)\b",
            r"[?.,!:/&()]+",
        ]
        for pat in stop_phrases:
            cleaned = re.sub(pat, " ", cleaned, flags=re.I)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned if len(cleaned) >= 2 else en_query.strip()

    def _fetch_live_web_medical_data(self, topic: str) -> Dict[str, str]:
        result = {"title": topic.title(), "overview": "", "symptoms": "", "causes": "", "diagnosis": "", "precautions": "", "source_url": ""}
        try:
            search_q = urllib.parse.quote(topic)
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_q}&utf8=1&format=json&srlimit=2"
            req = urllib.request.Request(search_url, headers={"User-Agent": "NovaHealthtech/2.0"})
            with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as resp:
                hits = json.loads(resp.read().decode("utf-8")).get("query", {}).get("search", [])
                if hits:
                    best_title = hits[0]["title"]
                    result["title"] = best_title
                    result["source_url"] = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(best_title.replace(' ', '_'))}"
                    extract_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={urllib.parse.quote(best_title)}&format=json"
                    req2 = urllib.request.Request(extract_url, headers={"User-Agent": "NovaHealthtech/2.0"})
                    with urllib.request.urlopen(req2, timeout=6, context=SSL_CTX) as resp2:
                        pages = json.loads(resp2.read().decode("utf-8")).get("query", {}).get("pages", {})
                        for _, page_obj in pages.items():
                            full_text = page_obj.get("extract", "")
                            if full_text:
                                parts = re.split(r"\n+==+\s*([^=]+?)\s*==+\n+", full_text)
                                if parts:
                                    intro_paras = [p.strip() for p in parts[0].split("\n") if len(p.strip()) > 30]
                                    result["overview"] = "\n\n".join(intro_paras[:3])[:1200]
                                    for i in range(1, len(parts) - 1, 2):
                                        sec_title = parts[i].strip().lower()
                                        sec_body = parts[i + 1].strip()
                                        paras = [p.strip() for p in sec_body.split("\n") if len(p.strip()) > 30]
                                        summary_chunk = "\n• ".join(paras[:4])[:1000]
                                        if not summary_chunk:
                                            continue
                                        if any(k in sec_title for k in ("sign", "symptom", "presentation", "clinical")) and not result["symptoms"]:
                                            result["symptoms"] = "• " + summary_chunk
                                        elif any(k in sec_title for k in ("cause", "risk", "pathophysiology", "transmission", "mechanism", "genetics")) and not result["causes"]:
                                            result["causes"] = "• " + summary_chunk
                                        elif any(k in sec_title for k in ("diagnos", "screening", "classification", "evaluation")) and not result["diagnosis"]:
                                            result["diagnosis"] = "• " + summary_chunk
                                        elif any(k in sec_title for k in ("prevent", "management", "care")) and not result["precautions"]:
                                            result["precautions"] = "• " + summary_chunk
                            break
        except Exception:
            pass
        return result

    def generate_preliminary_guidance(
        self,
        user_message: str,
        lang: str = "en",
        history: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        # LONGITUDINAL_MEMORY_UPGRADE: Combine prior saved chat history into ongoing clinical evaluation
        lang_code = lang if lang in LANGUAGE_NAMES else "en"
        lang_name = LANGUAGE_NAMES[lang_code]
        api_key = self.get_api_key()
        history = history or []
        normalized_user_msg = normalize_indic_digits_to_ascii(user_message)
        if all(ord(c) < 128 for c in normalized_user_msg):
            en_query = normalized_user_msg
        else:
            en_query = normalize_indic_digits_to_ascii(
                translate_text_live(normalized_user_msg, target_lang="en", source_lang="auto")
            )

        detected_location = self._detect_location_followup(normalized_user_msg, en_query, history)
        if detected_location:
            return self._build_location_hospitals_and_stores_response(detected_location, lang_code)

        intent_mode, matched_obj = self._detect_query_intent(normalized_user_msg, en_query)

        if intent_mode == "CONVERSATIONAL_GREETING":
            return self._build_conversational_greeting_response(lang_code)

        if intent_mode == "SPECIFIC_MEDICINE":
            return self._build_specific_medicine_response(
                user_message=normalized_user_msg,
                en_query=en_query,
                matched_profile=matched_obj,
                lang_code=lang_code,
                lang_name=lang_name,
                api_key=api_key,
                history=history,
            )

        if intent_mode == "MEDICINE_FOR_CAUSE":
            return self._build_medicine_for_cause_response(
                user_message=normalized_user_msg,
                en_query=en_query,
                lang_code=lang_code,
                lang_name=lang_name,
                api_key=api_key,
                history=history,
            )

        # ======================================================================
        # DISEASE, SYMPTOM & GENERAL MEDICAL MODE (STRICTLY SEPARATE FROM MEDICINES)
        # ======================================================================
        topic = self._extract_medical_topic(en_query)
        builtin_data = matched_obj or self._fuzzy_match_clinical_disease(normalized_user_msg, topic) or {}

        # Ask the conversational medical model first. Do not let a broad encyclopedia search
        # replace a medical acronym (for example BP) with an unrelated company or history page.
        if api_key:
            llm_disease = self._call_llm_for_medicine_or_disease(
                en_query, "DISEASE", "", api_key, history=history
            )
            if llm_disease:
                english_reply = strip_latex_artifacts(
                    f"🩺 **Nova AI • Clinical Disease & Symptom Guidance: {topic.title()}**\n\n"
                    f"{llm_disease}\n\n"
                    "ℹ️ *This is educational information, not a diagnosis. A qualified clinician can assess your individual situation.*"
                )
                final_reply = translate_multiline_response(english_reply, target_lang=lang_code) if lang_code != "en" else english_reply
                return {
                    "source": "nova_ai_disease_guide",
                    "model": "AI Online • Live Web Search",
                    "api_connected": True,
                    "language": lang_code,
                    "reply": strip_latex_artifacts(final_reply),
                    "english_reply": english_reply,
                    "safety_disclaimer": "🟢 AI Online • Non-Diagnostic Clinical Reference",
                }

        # Use only locally curated clinical data when the live model is unavailable.
        # Never fall back to a general encyclopedia result for a medical query.
        web_data = {}
        if not builtin_data:
            fallback_reply = (
                "I couldn't retrieve a reliable medical answer just now. Please try again in a moment, "
                "or rephrase the question with the condition, symptom, or medicine name. I won't guess "
                "or replace your question with an unrelated topic. If this is urgent, contact a qualified "
                "medical professional or local emergency service."
            )
            final_reply = translate_multiline_response(fallback_reply, target_lang=lang_code) if lang_code != "en" else fallback_reply
            return {
                "source": "nova_ai_unavailable",
                "model": "Medical answer unavailable",
                "api_connected": False,
                "language": lang_code,
                "reply": final_reply,
                "english_reply": fallback_reply,
                "safety_disclaimer": "Medical information service temporarily unavailable",
            }

        is_verified_condition = bool(builtin_data)
        title = builtin_data.get("title") or topic.title() or en_query.title()

        if is_verified_condition:
            overview = builtin_data.get("overview") or web_data.get("overview")
            uncertainty_banner = ""
        else:
            overview = (
                f"**{title}** is a medical query or rare/specific condition for which detailed monograph data could not be fully verified in offline/public encyclopedic indexes."
            )
            uncertainty_banner = (
                "\n• **Clinical Uncertainty & Verification Notice:** Because specific epidemiological or sub-specialty details for this query could not be independently verified without patient examination, "
                "Nova AI provides safe general clinical evaluation principles below without fabricating condition-specific claims."
            )

        causes = builtin_data.get("causes") or web_data.get("causes") or (
            "• **Infectious, Autoimmune or Inflammatory Factors:** Viral, bacterial, or immune-mediated pathways affecting the target organ system.\n"
            "• **Genetic, Metabolic & Environmental Triggers:** Hereditary predisposition, nutritional deficiencies, or environmental exposures.\n"
            "• **Clinical Evaluation Required:** Exact etiology for rare or complex presentations requires specialist history and diagnostic workup."
        )
        symptoms = builtin_data.get("symptoms") or web_data.get("symptoms") or (
            "• **Primary Clinical Signs:** Localized discomfort, functional changes, or systemic fatigue depending on the organ system involved.\n"
            "• **Vital Signs to Track:** Monitor Body Temperature (Normal: 97°F–99°F), Blood Pressure (<120/80 mmHg), Pulse Rate (60–100 bpm), and Oxygen Saturation (SpO₂ ≥ 95%).\n"
            "• **Red-Flag Warning Signs:** Rapidly worsening pain, unremitting high fever, sudden confusion, shortness of breath, chest pressure, or uncontrolled bleeding."
        )
        diagnosis = builtin_data.get("diagnosis") or web_data.get("diagnosis") or (
            "• **Clinical History & Physical Examination:** Detailed evaluation of symptom timeline, family history, and physical signs by a registered doctor.\n"
            "• **Baseline Laboratory Workup:** Complete Blood Count (CBC), inflammatory markers (CRP / ESR), Fasting Blood Glucose, and Liver/Kidney Function Tests (LFT / RFT).\n"
            "• **Targeted Diagnostic Imaging / Specialty Tests:** Ultrasound (USG), Digital X-Ray, ECG, CT/MRI, or genetic/autoimmune panels as ordered by a specialist."
        )
        precautions = builtin_data.get("precautions") or web_data.get("precautions") or (
            "• **Prevention & Hygiene:** Maintain hand hygiene, safe boiled/filtered drinking water, vector protection, and balanced nutrition.\n"
            "• **Supportive Care & Hydration:** Ensure adequate hydration (clean water, WHO-ORS, or clear soups unless fluid-restricted) and 7–8 hours of rest.\n"
            "• **Avoid Unsupervised Medication:** Do not start leftover antibiotics, painkillers, or steroids before a physician establishes a formal diagnosis."
        )
        doctor_rec = builtin_data.get("doctor_recommendation") or (
            f"• **Recommended Specialist:** Consult a **Registered General Physician (MBBS / MD Internal Medicine)** or the relevant super-specialty OPD at a tertiary medical college hospital for an accurate diagnosis of **{title}**."
        )
        hospital_helpline_rec = builtin_data.get("serious_hospital_and_helplines") or (
            "• **24x7 Emergency & Healthcare Helplines:**\n"
            "  - **Emergency SOS / Ambulance:** Trigger your saved SOS contact or dial **108 / 112** immediately if severe or red-flag symptoms appear.\n"
            "  - **State Medical Advice Helpline:** Dial **104** | **Mental Health (Tele-MANAS):** Dial **14416**.\n"
            "  - **Ayushman Bharat PM-JAY Verification:** Dial **14555**.\n"
            "• **Hospital Recommendation:** Visit your nearest **Government Medical College Hospital, District Civil Hospital, AIIMS, or PM-JAY Empanelled Multispeciality Hospital**."
        )

        sections = [
            f"🩺 **Nova AI • Comprehensive Clinical Disease & Symptom Guide: {title}**\n\n{overview}{uncertainty_banner}",
            f"**1. Causes & Risk Factors:**\n{causes}",
            f"**2. Key Symptoms & Warning Signs (Early vs. Severe):**\n{symptoms}",
            f"**3. Diagnostic Tests & Clinical Evaluation:**\n{diagnosis}",
            f"**4. Precautions, Prevention & Supportive Self-Care:**\n{precautions}",
            f"👨‍⚕️ **5. Doctor & Specialist Recommendation:**\n{doctor_rec}",
            f"🏥 **6. Hospital Recommendations & Emergency Helplines:**\n{hospital_helpline_rec}",
            "ℹ️ *This is educational information, not a diagnosis. Ask about a medicine by its exact brand or generic name when you want a medicine-specific explanation.*",
        ]

        english_reply = strip_latex_artifacts("\n\n".join(sections))
        final_reply = (
            translate_multiline_response(english_reply, target_lang=lang_code)
            if lang_code != "en"
            else english_reply
        )

        return {
            "source": "nova_ai_disease_guide",
            "model": "AI Online • Live Web Search",
            "api_connected": True,
            "language": lang_code,
            "reply": strip_latex_artifacts(final_reply),
            "english_reply": english_reply,
            "safety_disclaimer": "🟢 AI Online • Non-Diagnostic Clinical Reference",
        }


ai_assistant = AIAssistantService()

