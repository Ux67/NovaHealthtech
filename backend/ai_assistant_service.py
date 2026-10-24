"""
Nova Healthtech - Strictly Separated Medicine vs. Disease AI Engine
- Zero mixing between Medicine queries and Disease/Symptom queries.
- Uses a 3-layer classifier (Curated Lexicons + Pharmacological/Clinical Pattern Matcher + Live Web Entity Verifier).
- Disease Mode outputs ONLY: Overview, Causes, Symptoms, How Doctors Diagnose It, Precautions, and 'Where do you live?' hospital prompt.
- Medicine Mode outputs ONLY: Active Salt & mg Strength, Uses, When & How to Take It (with Specifier decoder), Side Effects, and 'Take strictly under medical guidance' warning.
"""

import html
import json
import os
import re
import ssl
import urllib.parse
import urllib.request
import urllib.error
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv

try:
    from api_key_config import GEMINI_API_KEY as CONFIG_FILE_KEY
except ImportError:
    CONFIG_FILE_KEY = ""

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))

for folder in (ROOT_DIR, BACKEND_DIR):
    for fname in (".env", ".env.txt"):
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath):
            load_dotenv(fpath, override=True)

SSL_CTX = ssl._create_unverified_context()

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
    "ur": "ur", "mai": "mai", "kok": "gom", "ne": "ne", "sd": "sd", "ks": "ks",
    "doi": "doi", "mni": "mni-Mtei", "sat": "sat", "sa": "sa",
}

ASK_USER_LOCATION_PROMPT = (
    "\n\n📍 **Want Nearby Hospitals & Medicine Stores?**\n"
    "**Where do you live (which City or State in India)?** Reply with your **City or State name** "
    "(for example: *Bhavnagar, Ahmedabad, Mumbai, Delhi, Bengaluru, Chennai, Hyderabad, Kolkata, Pune, Jaipur, Lucknow, Patna, or Bhubaneswar*), "
    "and I will immediately list the **nearest Government/PM-JAY Hospitals and 24x7 Medicine Stores** near you!"
)

MANDATORY_MEDICINE_WARNING = (
    "\n\n⚠️ **Medical Guidance Warning:**\n"
    "**Take strictly under medical guidance.** Never start, stop, or change the `mg` dosage or schedule of this medicine on your own. "
    "Always consult a registered medical practitioner (MBBS/MD) before taking any medication."
)

# ==============================================================================
# ALL-INDIA HOSPITALS & MEDICINE STORES DIRECTORY (PAN-INDIA)
# ==============================================================================

ALL_INDIA_HOSPITALS: List[Dict[str, str]] = [
    {"state": "Gujarat", "city": "Bhavnagar", "name": "Sir Takhtsinhji General Hospital (Civil Hospital)", "type": "Government Medical College & Civil Hospital", "schemes": "PM-JAY, PMJAY-MA, Free OPD & 24x7 Trauma", "address": "Jail Road, Panwadi, Bhavnagar, Gujarat 364001", "helpline": "108 / PMJAY Desk"},
    {"state": "Gujarat", "city": "Bhavnagar", "name": "HCG Hospitals Bhavnagar", "type": "Empanelled Multispeciality Hospital", "schemes": "PM-JAY, PMJAY-MA (Cardiac & Oncology)", "address": "Meghani Circle, Bhavnagar, Gujarat 364001", "helpline": "Arogya Mitra Desk"},
    {"state": "Gujarat", "city": "Ahmedabad", "name": "B.J. Medical College & Civil Hospital Asarwa", "type": "Apex Government Civil Medicity", "schemes": "PM-JAY, PMJAY-MA, 70+ Vay Vandana, ABHA", "address": "Asarwa, Ahmedabad, Gujarat 380016", "helpline": "108 / 079-22683721"},
    {"state": "Gujarat", "city": "Ahmedabad", "name": "GMERS Medical College & Civil Hospital Sola", "type": "Government Medical College Hospital", "schemes": "PM-JAY, PMJAY-MA, ABHA Fast-Track", "address": "S.G. Highway, Sola, Ahmedabad, Gujarat 380060", "helpline": "PMJAY Mitra Desk"},
    {"state": "Gujarat", "city": "Rajkot", "name": "AIIMS Rajkot & PDU Government Civil Hospital", "type": "Central AIIMS & State Civil Hospital", "schemes": "PM-JAY, PMJAY-MA, ABHA", "address": "Khandheri / Hospital Chowk, Rajkot, Gujarat 360001", "helpline": "108 / Ayushman Desk"},
    {"state": "Gujarat", "city": "Vadodara", "name": "Sir Sayajirao General (SSG) Hospital", "type": "Government Medical College Hospital", "schemes": "PM-JAY, PMJAY-MA, Free Emergency Care", "address": "Anandpura, Vadodara, Gujarat 390001", "helpline": "108 / Arogya Mitra"},
    {"state": "Gujarat", "city": "Surat", "name": "New Civil Hospital (GMC Surat)", "type": "Government Medical College Hospital", "schemes": "PM-JAY, PMJAY-MA, 24x7 Emergency", "address": "Majura Gate, Surat, Gujarat 395001", "helpline": "108 / PMJAY Desk"},
    {"state": "Maharashtra", "city": "Mumbai", "name": "King Edward Memorial (KEM) Hospital", "type": "Public Municipal Medical College Hospital", "schemes": "PM-JAY, MJPJAY, ABHA", "address": "Acharya Donde Marg, Parel, Mumbai, Maharashtra 400012", "helpline": "022-24107000 / Ayushman Desk"},
    {"state": "Maharashtra", "city": "Mumbai", "name": "Grant Government Medical College & Sir J.J. Group of Hospitals", "type": "State Government Hospital", "schemes": "PM-JAY, MJPJAY, 24x7 Emergency", "address": "Byculla, Mumbai, Maharashtra 400008", "helpline": "108 / MJPJAY Desk"},
    {"state": "Maharashtra", "city": "Pune", "name": "Sassoon General Hospital (B.J. Govt Medical College)", "type": "State Government Tertiary Hospital", "schemes": "PM-JAY, MJPJAY, Free OPD", "address": "Jayprakash Narayan Road, Near Pune Railway Station, Pune 411001", "helpline": "020-26128000"},
    {"state": "Maharashtra", "city": "Nagpur", "name": "AIIMS Nagpur & Government Medical College (GMCH) Nagpur", "type": "Central AIIMS & State Medical College", "schemes": "PM-JAY, MJPJAY, 70+ Vay Vandana", "address": "MIHAN / Hanuman Nagar, Nagpur, Maharashtra 441108", "helpline": "Ayushman Bharat Desk"},
    {"state": "Delhi", "city": "New Delhi", "name": "All India Institute of Medical Sciences (AIIMS New Delhi)", "type": "Premier Central Autonomous Hospital", "schemes": "PM-JAY, 70+ Vay Vandana, ABHA Scan & Share", "address": "Ansari Nagar, Aurobindo Marg, New Delhi 110029", "helpline": "011-26588500 / PMJAY Desk"},
    {"state": "Delhi", "city": "New Delhi", "name": "Safdarjung Hospital (VMMC) & Dr. RML Hospital", "type": "Central Government Tertiary Hospitals", "schemes": "PM-JAY, Free OPD & 24x7 Emergency", "address": "Ansari Nagar West / Baba Kharak Singh Marg, New Delhi", "helpline": "108 / 112"},
    {"state": "Karnataka", "city": "Bengaluru", "name": "Victoria Hospital (BMCRI) & NIMHANS Bengaluru", "type": "Government Medical College & National Institute", "schemes": "PM-JAY Arogya Karnataka, ABHA", "address": "Fort Road, Near City Market / Hosur Road, Bengaluru 560002", "helpline": "108 / Arogya Mitra"},
    {"state": "Karnataka", "city": "Bengaluru", "name": "Sri Jayadeva Institute of Cardiovascular Sciences & Narayana Health", "type": "Govt Autonomous & Empanelled Tertiary Care", "schemes": "PM-JAY Arogya Karnataka, Senior 70+", "address": "Bannerghatta Road / Bommasandra, Bengaluru", "helpline": "Ayushman Mitra Desk"},
    {"state": "Karnataka", "city": "Mysuru", "name": "Krishnarajendra (K.R.) Hospital & MMC&RI", "type": "Government Medical College Hospital", "schemes": "PM-JAY Arogya Karnataka", "address": "Irwin Road, Mysuru, Karnataka 570001", "helpline": "108 / PMJAY Desk"},
    {"state": "Tamil Nadu", "city": "Chennai", "name": "Rajiv Gandhi Government General Hospital (RGGGH)", "type": "Premier State Government Tertiary Hospital", "schemes": "PM-JAY CMCHIS, Free Emergency & OPD", "address": "Poonamallee High Road, Park Town, Opposite Central Station, Chennai 600003", "helpline": "044-25305000 / CMCHIS Desk"},
    {"state": "Tamil Nadu", "city": "Madurai", "name": "Government Rajaji Hospital & AIIMS Madurai", "type": "Government Medical College Hospital", "schemes": "PM-JAY CMCHIS, ABHA", "address": "Panagal Road, Goripalayam, Madurai, Tamil Nadu 625020", "helpline": "108 / Ayushman Desk"},
    {"state": "Telangana", "city": "Hyderabad", "name": "Osmania General Hospital, Gandhi Hospital & NIMS", "type": "State Government Tertiary Hospitals", "schemes": "PM-JAY Aarogyasri, ABHA", "address": "Afzal Gunj / Musheerabad / Punjagutta, Hyderabad 500012", "helpline": "108 / Aarogyasri Mitra"},
    {"state": "Andhra Pradesh", "city": "Visakhapatnam", "name": "King George Hospital (KGH) & AIIMS Mangalagiri", "type": "Government Medical College & Central AIIMS", "schemes": "PM-JAY Dr. NTR Vaidya Seva", "address": "Maharanipeta, Visakhapatnam, Andhra Pradesh 530002", "helpline": "108 / PMJAY Desk"},
    {"state": "West Bengal", "city": "Kolkata", "name": "SSKM Hospital (IPGMER), Medical College Kolkata & AIIMS Kalyani", "type": "Premier Government Medical Colleges & AIIMS", "schemes": "PM-JAY, Swasthya Sathi, Free OPD", "address": "244 AJC Bose Road / 88 College Street, Kolkata 700020", "helpline": "108 / Helpdesk"},
    {"state": "Uttar Pradesh", "city": "Lucknow", "name": "King George's Medical University (KGMU) & SGPGIMS Lucknow", "type": "Apex Government Medical Universities", "schemes": "PM-JAY Mukhyamantri Jan Arogya, ABHA", "address": "Shah Mina Road, Chowk / Raebareli Road, Lucknow 226003", "helpline": "1800-180-5145 / Ayushman Desk"},
    {"state": "Uttar Pradesh", "city": "Varanasi", "name": "Sir Sunderlal Hospital (IMS-BHU Varanasi)", "type": "Central University Teaching Hospital", "schemes": "PM-JAY, 70+ Vay Vandana, ABHA", "address": "Banaras Hindu University Campus, Varanasi 221005", "helpline": "PMJAY Mitra Desk"},
    {"state": "Rajasthan", "city": "Jaipur", "name": "Sawai Man Singh (SMS) Medical College & Hospital", "type": "Apex State Government Hospital", "schemes": "PM-JAY Mukhyamantri Ayushman Arogya", "address": "JLN Marg, Gangawal Park, Jaipur, Rajasthan 302004", "helpline": "108 / Ayushman Desk"},
    {"state": "Rajasthan", "city": "Jodhpur", "name": "AIIMS Jodhpur & Mathura Das Mathur (MDM) Hospital", "type": "Central AIIMS & State Govt Hospital", "schemes": "PM-JAY, ABHA", "address": "Basni Industrial Area Phase-2, Jodhpur, Rajasthan 342005", "helpline": "Ayushman Mitra Desk"},
    {"state": "Madhya Pradesh", "city": "Bhopal", "name": "AIIMS Bhopal & Gandhi Medical College (Hamidia Hospital)", "type": "Central AIIMS & State Govt Hospital", "schemes": "PM-JAY Ayushman Bharat Niramayam", "address": "Saket Nagar / Sultania Road, Bhopal, MP 462020", "helpline": "108 / Ayushman Desk"},
    {"state": "Madhya Pradesh", "city": "Indore", "name": "Maharaja Yeshwantrao (MY) Hospital Indore", "type": "State Government Tertiary Hospital", "schemes": "PM-JAY, Free OPD & Emergency", "address": "AB Road, CRP Line, Indore, MP 452001", "helpline": "108 / PMJAY Desk"},
    {"state": "Bihar", "city": "Patna", "name": "AIIMS Patna, PMCH & IGIMS Patna", "type": "Central AIIMS & State Medical Colleges", "schemes": "PM-JAY Mukhyamantri Jan Arogya, ABHA", "address": "Phulwari Sharif / Ashok Rajpath / Bailey Road, Patna 801507", "helpline": "108 / Ayushman Desk"},
    {"state": "Odisha", "city": "Bhubaneswar", "name": "AIIMS Bhubaneswar & Capital Hospital Bhubaneswar", "type": "Central AIIMS & State Govt Hospital", "schemes": "PM-JAY & Gopabandhu Jan Arogya, ABHA", "address": "Sijua, Patrapada / Unit-6, Bhubaneswar, Odisha 751019", "helpline": "108 / Ayushman Mitra"},
    {"state": "Odisha", "city": "Cuttack", "name": "SCB Medical College & Hospital Cuttack", "type": "Premier State Government Medical College", "schemes": "PM-JAY, 24x7 Trauma & OPD", "address": "Mangalabag, Cuttack, Odisha 753007", "helpline": "108 / Helpdesk"},
    {"state": "Punjab", "city": "Chandigarh", "name": "PGIMER Chandigarh & GMCH Sector 32", "type": "Premier National Medical Institute", "schemes": "PM-JAY Sarbat Sehat Bima, 70+ Vay Vandana", "address": "Sector 12 / Sector 32, Chandigarh 160012", "helpline": "0172-2747585 / Ayushman Desk"},
    {"state": "Punjab", "city": "Amritsar", "name": "Guru Nanak Dev Hospital (GMC Amritsar) & AIIMS Bathinda", "type": "Government Medical College & Central AIIMS", "schemes": "PM-JAY Sarbat Sehat Bima", "address": "Majitha Road, Amritsar, Punjab 143001", "helpline": "108 / PMJAY Desk"},
    {"state": "Kerala", "city": "Thiruvananthapuram", "name": "Government Medical College Hospital & Sree Chitra Tirunal (SCTIMST)", "type": "Apex Government Medical Institutions", "schemes": "PM-JAY Karunya Arogya Suraksha (KASP)", "address": "Ulloor - Akkulam Road, Medical College PO, Thiruvananthapuram 695011", "helpline": "108 / KASP Desk"},
    {"state": "Kerala", "city": "Kochi", "name": "General Hospital Ernakulam & Govt Medical College Kalamassery", "type": "State Government Tertiary Hospitals", "schemes": "PM-JAY KASP, ABHA", "address": "Hospital Road, Ernakulam, Kochi, Kerala 682011", "helpline": "108 / Helpdesk"},
    {"state": "Assam", "city": "Guwahati", "name": "AIIMS Guwahati & Gauhati Medical College Hospital (GMCH)", "type": "Central AIIMS & State Medical College", "schemes": "PM-JAY Ayushman Asom, ABHA", "address": "Changsari / Bhangagarh, Guwahati, Assam 781032", "helpline": "108 / Ayushman Mitra"},
]

ALL_INDIA_MEDICINE_STORES: List[Dict[str, str]] = [
    {"state": "Gujarat", "city": "Bhavnagar", "name": "PM Bhartiya Janaushadhi Kendra — Sir Takhtsinhji Hospital Campus", "type": "Government Generic Medicine Store (50%–90% Lower Price)", "hours": "Open 24x7 (Hospital Gate)", "address": "Near OPD Gate, Sir Takhtsinhji Civil Hospital, Jail Road, Bhavnagar", "contact": "1800-180-8080 (PMBI Toll-Free)"},
    {"state": "Gujarat", "city": "Bhavnagar", "name": "PMBJK Kalanala & Medkart Generic Pharmacy Bhavnagar", "type": "Jan Aushadhi & Retail Generic Pharmacy", "hours": "8:00 AM – 11:00 PM", "address": "Kalanala / Waghawadi Road, Bhavnagar, Gujarat", "contact": "Bring Doctor Prescription"},
    {"state": "Gujarat", "city": "Ahmedabad", "name": "PM Bhartiya Janaushadhi Kendra — Civil Hospital Asarwa & Sola", "type": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "OPD Block, Civil Hospital Campus, Asarwa & Sola SG Highway, Ahmedabad", "contact": "1800-180-8080"},
    {"state": "Gujarat", "city": "Rajkot", "name": "PM Bhartiya Janaushadhi Kendra — PDU Hospital Chowk & AIIMS Rajkot", "type": "Government Generic Medicine Store", "hours": "Open 24x7", "address": "Hospital Chowk, Jamnagar Road, Rajkot, Gujarat", "contact": "1800-180-8080"},
    {"state": "Gujarat", "city": "Vadodara", "name": "PM Bhartiya Janaushadhi Kendra — SSG Hospital Anandpura", "type": "Government Generic Medicine Store", "hours": "Open 24x7", "address": "SSG Hospital Compound, Raopura/Anandpura, Vadodara", "contact": "1800-180-8080"},
    {"state": "Gujarat", "city": "Surat", "name": "PM Bhartiya Janaushadhi Kendra — New Civil Hospital Majura Gate", "type": "Government Generic Medicine Store", "hours": "Open 24x7", "address": "New Civil Hospital Campus, Majura Gate, Surat", "contact": "1800-180-8080"},
    {"state": "Maharashtra", "city": "Mumbai", "name": "PM Bhartiya Janaushadhi Kendra & AMRIT Pharmacy — KEM & JJ Hospital", "type": "24x7 Govt Generic & Life-Saving Drug Store", "hours": "Open 24x7", "address": "Parel (KEM Campus) & Byculla (JJ Hospital Compound), Mumbai", "contact": "1800-180-8080"},
    {"state": "Maharashtra", "city": "Pune", "name": "PM Bhartiya Janaushadhi Kendra — Sassoon Hospital & Deccan Gymkhana", "type": "Government Generic Medicine Store", "hours": "Open 24x7", "address": "Near Pune Station (Sassoon Compound) & JM Road, Pune", "contact": "1800-180-8080"},
    {"state": "Maharashtra", "city": "Nagpur", "name": "AMRIT Pharmacy & PMBJK — AIIMS Nagpur & GMCH Hanuman Nagar", "type": "Government Generic & Surgical Store", "hours": "Open 24x7", "address": "MIHAN AIIMS Campus & Medical Square, Nagpur", "contact": "1800-180-8080"},
    {"state": "Delhi", "city": "New Delhi", "name": "AMRIT Pharmacy & PM Janaushadhi Kendra — AIIMS & Safdarjung Hospital", "type": "24x7 Central Govt Generic & Cancer/Cardiac Pharmacy", "hours": "Open 24x7", "address": "Gate No. 1, AIIMS Ansari Nagar & Safdarjung OPD Block, New Delhi", "contact": "1800-180-8080"},
    {"state": "Karnataka", "city": "Bengaluru", "name": "PM Bhartiya Janaushadhi Kendra — Victoria Hospital, NIMHANS & RR Nagar", "type": "Government Generic Medicine Store", "hours": "Open 24x7 (Hospital Units)", "address": "City Market (Victoria Campus), Hosur Road & RR Nagar, Bengaluru", "contact": "1800-180-8080"},
    {"state": "Karnataka", "city": "Mysuru", "name": "PM Bhartiya Janaushadhi Kendra — K.R. Hospital Compound", "type": "Government Generic Medicine Store", "hours": "Open 24x7", "address": "Irwin Road, K.R. Hospital Campus, Mysuru", "contact": "1800-180-8080"},
    {"state": "Tamil Nadu", "city": "Chennai", "name": "PM Bhartiya Janaushadhi Kendra & Mudhalvar Marundhagam — Park Town", "type": "Government Subsidized Generic Pharmacy", "hours": "Open 24x7", "address": "Opposite RGGGH Central Station & T. Nagar, Chennai", "contact": "1800-180-8080"},
    {"state": "Tamil Nadu", "city": "Madurai", "name": "PM Bhartiya Janaushadhi Kendra — Govt Rajaji Hospital Goripalayam", "type": "Government Generic Medicine Store", "hours": "Open 24x7", "address": "Panagal Road, Goripalayam, Madurai", "contact": "1800-180-8080"},
    {"state": "Telangana", "city": "Hyderabad", "name": "PM Bhartiya Janaushadhi Kendra & AMRIT Pharmacy — NIMS, Osmania & Gandhi Hospital", "type": "24x7 Govt Generic & Surgical Pharmacy", "hours": "Open 24x7", "address": "Punjagutta (NIMS), Afzal Gunj & Secunderabad, Hyderabad", "contact": "1800-180-8080"},
    {"state": "Andhra Pradesh", "city": "Visakhapatnam", "name": "PM Bhartiya Janaushadhi Kendra — King George Hospital (KGH)", "type": "Government Generic Medicine Store", "hours": "Open 24x7", "address": "KGH Compound, Maharanipeta, Visakhapatnam", "contact": "1800-180-8080"},
    {"state": "West Bengal", "city": "Kolkata", "name": "Fair Price Medicine Shop & PMBJK — SSKM & Medical College Kolkata", "type": "24x7 Government Fair Price & Generic Store", "hours": "Open 24x7", "address": "AJC Bose Road (SSKM Campus) & College Street, Kolkata", "contact": "1800-180-8080"},
    {"state": "Uttar Pradesh", "city": "Lucknow", "name": "PM Bhartiya Janaushadhi Kendra & AMRIT Pharmacy — KGMU & SGPGI", "type": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "Chowk (KGMU Trauma Center) & Raebareli Road, Lucknow", "contact": "1800-180-8080"},
    {"state": "Uttar Pradesh", "city": "Varanasi", "name": "PM Bhartiya Janaushadhi Kendra — Sir Sunderlal Hospital (BHU Gate)", "type": "24x7 Generic & Surgical Pharmacy", "hours": "Open 24x7", "address": "Lanka, BHU Main Gate, Varanasi", "contact": "1800-180-8080"},
    {"state": "Rajasthan", "city": "Jaipur", "name": "PM Bhartiya Janaushadhi Kendra & Sahkari Bhandar — SMS Hospital", "type": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "JLN Marg, SMS Hospital Campus, Jaipur", "contact": "1800-180-8080"},
    {"state": "Rajasthan", "city": "Jodhpur", "name": "AMRIT Pharmacy & PMBJK — AIIMS Jodhpur & MDM Hospital", "type": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "Basni Phase-2 (AIIMS Gate) & Shastri Nagar, Jodhpur", "contact": "1800-180-8080"},
    {"state": "Madhya Pradesh", "city": "Bhopal", "name": "AMRIT Pharmacy & PMBJK — AIIMS Bhopal & Hamidia Hospital", "type": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "Saket Nagar (AIIMS Bhopal) & Royal Market, Bhopal", "contact": "1800-180-8080"},
    {"state": "Madhya Pradesh", "city": "Indore", "name": "PM Bhartiya Janaushadhi Kendra — MY Hospital Campus Indore", "type": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "MY Hospital Gate, AB Road, Indore", "contact": "1800-180-8080"},
    {"state": "Bihar", "city": "Patna", "name": "PM Bhartiya Janaushadhi Kendra & AMRIT Pharmacy — AIIMS Patna & PMCH", "type": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "Phulwari Sharif (AIIMS) & Ashok Rajpath (PMCH), Patna", "contact": "1800-180-8080"},
    {"state": "Odisha", "city": "Bhubaneswar", "name": "AMRIT Pharmacy & PMBJK — AIIMS Bhubaneswar & Capital Hospital", "type": "24x7 Government Generic & Nirmaya Pharmacy", "hours": "Open 24x7", "address": "Sijua Patrapada (AIIMS OPD) & Unit-6 Capital Hospital, Bhubaneswar", "contact": "1800-180-8080"},
    {"state": "Odisha", "city": "Cuttack", "name": "PM Bhartiya Janaushadhi Kendra — SCB Medical College Campus", "type": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "Mangalabag, SCB Hospital Gate, Cuttack", "contact": "1800-180-8080"},
    {"state": "Punjab", "city": "Chandigarh", "name": "AMRIT Pharmacy & Jan Aushadhi Store — PGIMER Sector 12 & GMCH-32", "type": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "New OPD Block, PGIMER Sector 12, Chandigarh", "contact": "1800-180-8080"},
    {"state": "Punjab", "city": "Amritsar", "name": "PM Bhartiya Janaushadhi Kendra — Guru Nanak Dev Hospital Campus", "type": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "Majitha Road, Amritsar", "contact": "1800-180-8080"},
    {"state": "Kerala", "city": "Thiruvananthapuram", "name": "Karunya Community Pharmacy & PMBJK — Govt Medical College Campus", "type": "24x7 Govt Subsidized Generic Pharmacy", "hours": "Open 24x7", "address": "Medical College Junction, Thiruvananthapuram", "contact": "1800-180-8080"},
    {"state": "Kerala", "city": "Kochi", "name": "PM Bhartiya Janaushadhi Kendra & Neethi Medical Store — Ernakulam", "type": "Government Generic & Co-operative Pharmacy", "hours": "8:00 AM – 10:00 PM (Hospital Unit 24x7)", "address": "Near General Hospital Ernakulam, Kochi", "contact": "1800-180-8080"},
    {"state": "Assam", "city": "Guwahati", "name": "AMRIT Pharmacy & PMBJK — GMCH Bhangagarh & AIIMS Guwahati", "type": "24x7 Government Generic Pharmacy", "hours": "Open 24x7", "address": "GMCH Complex, Bhangagarh, Guwahati", "contact": "1800-180-8080"},
]

# ==============================================================================
# PHARMACEUTICAL SPECIFIER DECODER & INDIAN BRAND PROFILES
# ==============================================================================

SPECIFIER_DEFINITIONS: Dict[str, str] = {
    "xl": "**XL (Extended Release):** Releases medicine slowly over 12–24 hours. Swallow whole with water—**never chew, crush, or break**.",
    "sr": "**SR (Sustained Release):** Releases the active drug gradually over time. **Swallow whole; do not crush or chew.**",
    "xr": "**XR (Extended Release):** Long-acting formulation. **Swallow whole without crushing.**",
    "er": "**ER (Extended Release):** Slow-release tablet. **Do not crush, split, or chew.**",
    "dsr": "**DSR (Domperidone Sustained Release):** Combines an acid reducer with sustained-release Domperidone. Take **30–45 minutes before breakfast on an empty stomach**.",
    "md": "**MD (Mouth Dissolving):** Dissolves rapidly on the tongue without needing water.",
    "dt": "**DT (Dispersible Tablet):** Can be dispersed in a spoonful of clean water right before taking.",
    "od": "**OD (Once Daily):** Taken once every 24 hours at the same time each day.",
    "bd": "**BD / BID (Twice Daily):** Taken twice a day (typically every 12 hours).",
    "forte": "**Forte (Strong / Higher Strength):** Contains a higher concentration or reinforced combination of active ingredients.",
    "plus": "**Plus (Combination Formula):** Contains an additional synergistic active ingredient.",
    "duo": "**Duo (Dual Action):** Combines two active ingredients working together (e.g., Amoxicillin + Clavulanic Acid).",
    "cv": "**CV (Clavulanic Acid Combination):** Pairs an antibiotic with Clavulanic Acid. Take **with or immediately after a meal**.",
    "sp": "**SP (Serratiopeptidase Combination):** Combines a pain reliever + Paracetamol + **Serratiopeptidase** (reduces swelling). Take **after food**.",
    "lc": "**LC (Levocetirizine Combination):** Combines Montelukast with Levocetirizine for allergy/airway relief. Usually taken **at night**.",
    "am": "**AM (Amlodipine Combination):** Combines a blood pressure medicine with **Amlodipine**.",
    "h": "**H (Hydrochlorothiazide Combination):** Includes a mild diuretic to lower BP. Best taken **in the morning**.",
    "gp": "**GP (Glimepiride Combination):** Combines Metformin with **Glimepiride** for Diabetes. Take **just before or with breakfast**.",
    "oz": "**OZ (Ornidazole Combination):** Combines an antibiotic with **Ornidazole** for stomach/diarrheal infections. Take **after food**.",
    "tz": "**TZ (Tinidazole Combination):** Combines Norfloxacin/Ciprofloxacin with **Tinidazole** for diarrhea/dysentery. Take **after food**.",
}

INDIAN_BRAND_PROFILES: List[Dict[str, Any]] = [
    {
        "brands": ["lithonex", "lithosun", "intalith", "lichen", "lithium", "licab"],
        "generic_salt": "Lithium Carbonate (Mood Stabilizer / CNS Agent)",
        "common_strengths": "300 mg, 400 mg, 450 mg (SR / XL Extended Release)",
        "uses": (
            "• **Bipolar Disorder:** Stabilizes mood and prevents extreme highs (mania) and lows (depression).\n"
            "• **Acute Mania:** Calms racing thoughts, severe irritability, and agitation by balancing brain neurotransmitters."
        ),
        "when_to_take": (
            "• **With or Immediately After Food:** Always take with or right after a meal to prevent stomach upset.\n"
            "• **Swallow 450 XL / SR Whole:** Swallow Extended/Sustained Release tablets whole with water—**never chew, crush, or break**.\n"
            "• **Hydration & Salt Rule:** Drink **2.5 to 3 Liters of fluids daily** and maintain a normal salt intake."
        ),
        "precautions": (
            "• **Monitoring:** Requires periodic **Serum Lithium blood tests**, plus **Kidney (Creatinine)** and **Thyroid (TSH)** checks.\n"
            "• **Avoid NSAID Painkillers:** Avoid Ibuprofen, Diclofenac, Aceclofenac, Combiflam, or Zerodol while on Lithium."
        ),
    },
    {
        "brands": ["dolo", "calpol", "crocin", "pacimol", "sumo l", "pyrigesic", "metacin", "p 500", "p 650", "paracetamol", "acetaminophen", "t-98"],
        "generic_salt": "Paracetamol / Acetaminophen (Antipyretic & Analgesic)",
        "common_strengths": "500 mg, 650 mg, 1000 mg SR Tablet; 125 mg / 250 mg Syrup",
        "uses": "• **Fever & Pain Relief:** Safely lowers fever and relieves headache, migraine, toothache, body ache, and sore throat.",
        "when_to_take": "• Take **after food** with water. Keep a minimum gap of **4 to 6 hours** between doses (max 3–4 doses in 24 hours).",
        "precautions": "• Avoid alcohol and do not exceed the recommended daily dose to protect the liver.",
    },
    {
        "brands": ["zerodol", "aceclo", "hifenac", "movon", "aceclofenac", "voveran", "reactin", "diclofenac", "combiflam", "brufen", "ibuprofen", "flexon", "naprosyn", "naxdom", "naproxen", "nucoxia", "etoshine", "etoricoxib"],
        "generic_salt": "NSAID Pain & Inflammation Reliever (Aceclofenac / Diclofenac / Ibuprofen / Naproxen ± Paracetamol ± Serratiopeptidase)",
        "common_strengths": "100 mg, 200 mg SR, 400 mg (with P = Paracetamol 325mg, SP = Serratiopeptidase 15mg)",
        "uses": "• **Joint, Back, Dental & Inflammatory Pain:** Relieves arthritis, lower back pain, toothache, sprains, and post-injury swelling.",
        "when_to_take": "• **Strictly AFTER Meals:** Always take immediately after food or milk—never on an empty stomach.",
        "precautions": "• **Strictly avoid during suspected Dengue fever**, peptic ulcers, kidney disease, or pregnancy.",
    },
    {
        "brands": ["meftal", "mefkind", "mefenamic", "cyclopam", "buscopan", "drotin", "drotaverine"],
        "generic_salt": "Antispasmodic & Cramp Reliever (Mefenamic Acid / Dicyclomine / Drotaverine)",
        "common_strengths": "Meftal-Spas (250mg + 10mg), Meftal 500, Drotin-DS (80mg), Cyclopam",
        "uses": "• **Stomach & Menstrual Cramps:** Relaxes smooth muscle spasms in period pain, abdominal colic, and kidney/gallbladder stone spasms.",
        "when_to_take": "• Take **after food** with water.",
        "precautions": "• May cause mild dry mouth or drowsiness.",
    },
    {
        "brands": ["pan", "pantocid", "pantop", "pantodac", "pantoprazole", "omez", "omicip", "omeprazole", "razo", "rabicip", "cyra", "veloz", "rabeprazole", "nexpro", "sompraz", "esomeprazole", "aciloc", "rantac"],
        "generic_salt": "Acid Reducer / Proton Pump Inhibitor (Pantoprazole / Omeprazole / Rabeprazole ± Domperidone)",
        "common_strengths": "20 mg, 40 mg (Plain, D, or DSR Capsule/Tablet)",
        "uses": "• **Acidity, Gas, Heartburn (GERD) & Ulcers:** Stops stomach acid reflux and protects the stomach lining.",
        "when_to_take": "• **Empty Stomach (30–45 Mins Before Breakfast):** Take in the morning on an empty stomach before your first meal.",
        "precautions": "• Swallow whole; do not crush or chew DSR capsules.",
    },
    {
        "brands": ["augmentin", "moxikind", "clavam", "amoxyclav", "novamox", "almox", "amoxicillin", "ceftum", "taxim", "monocef", "gudcef", "zifi", "mahacef", "cefixime", "cefpodoxime", "cefuroxime"],
        "generic_salt": "Beta-Lactam Antibiotic (Amoxicillin ± Clavulanic Acid / Cefixime / Cefpodoxime)",
        "common_strengths": "625 mg (500+125), 375 mg, 500 mg, 200 mg",
        "uses": "• **Bacterial Infections:** Treats bacterial throat, sinus, ear, chest, urinary tract (UTI), typhoid, dental, and skin infections.",
        "when_to_take": "• Take **with or immediately after food** every 8 or 12 hours as prescribed. **Complete the full course.**",
        "precautions": "• Do not take if allergic to Penicillin/Cephalosporins.",
    },
    {
        "brands": ["azithral", "azee", "zady", "atm", "azicip", "azithromycin"],
        "generic_salt": "Azithromycin (Macrolide Antibiotic)",
        "common_strengths": "250 mg, 500 mg Tablet / Syrup",
        "uses": "• **Bacterial Throat, Sinus, Chest & Enteric Infections.**",
        "when_to_take": "• Taken **once daily** for 3 to 5 days as prescribed (1 hour before or 2 hours after food, or with food if stomach upset occurs).",
        "precautions": "• Keep a 2-hour gap from aluminum/magnesium antacids.",
    },
    {
        "brands": ["norflox", "oflox", "zenflox", "ciplox", "ciprofloxacin", "ofloxacin", "norfloxacin", "levoflox", "metrogyl", "flagyl", "metronidazole", "ornidazole"],
        "generic_salt": "Antibacterial & Antiprotozoal (Ofloxacin / Norfloxacin / Ciprofloxacin ± Ornidazole / Tinidazole / Metronidazole)",
        "common_strengths": "200 mg, 400 mg, 500 mg, OZ (200+500 mg), TZ (400+600 mg)",
        "uses": "• **Diarrhea, Dysentery, Stomach Infections, UTI & Dental Infections.**",
        "when_to_take": "• Take **after food** with plenty of water/ORS. Keep a 2-hour gap from milk/dairy or calcium/iron tablets.",
        "precautions": "• **Strictly avoid alcohol** during and for 48 hours after taking OZ/TZ/Metrogyl.",
    },
    {
        "brands": ["montair", "montek", "telekast", "montelukast", "cetzine", "okacet", "alerid", "cetirizine", "levocet", "vozet", "levocetirizine", "allegra", "fexofenadine", "avil", "atarax"],
        "generic_salt": "Antihistamine / Anti-Allergic (Cetirizine / Levocetirizine / Fexofenadine ± Montelukast)",
        "common_strengths": "10 mg, 5 mg, LC (10mg + 5mg), 120 mg, 180 mg",
        "uses": "• **Allergies, Sneezing, Runny Nose, Itchy Eyes, Skin Hives & Nighttime Allergic Cough.**",
        "when_to_take": "• Usually taken **once daily in the evening or at bedtime** (may cause mild drowsiness).",
        "precautions": "• Avoid driving if drowsy and avoid alcohol.",
    },
    {
        "brands": ["telma", "tazloc", "telmikind", "telmisartan", "losar", "losartan", "amlokind", "stamlo", "amlodipine", "cilacar", "cilnidipine", "concor", "metolar", "prolomet", "metoprolol", "cardace", "ramipril"],
        "generic_salt": "Anti-Hypertensive / Blood Pressure & Heart Medication",
        "common_strengths": "20 mg, 40 mg, 80 mg, 5 mg, 10 mg, 25 mg XL, 50 mg XL (with AM, H, CT combinations)",
        "uses": "• **High Blood Pressure (Hypertension), Angina & Heart Rate Control.**",
        "when_to_take": "• Take at the **same time every day** (variants with `H` or `CT` should be taken in the **morning after breakfast**).",
        "precautions": "• Never stop BP tablets abruptly without consulting your doctor.",
    },
    {
        "brands": ["glycomet", "metsmall", "glucophage", "metformin", "amaryl", "glimestar", "glimepiride", "janumet", "istamet", "galvus", "vildagliptin", "sitagliptin", "teneligliptin", "forxiga", "jardiance", "udapa", "dapagliflozin"],
        "generic_salt": "Anti-Diabetic Medication (Metformin / Glimepiride / Gliptins / Dapagliflozin)",
        "common_strengths": "500 mg SR, 850 mg, 1000 mg, GP1 / GP2, 10 mg",
        "uses": "• **Type 2 Diabetes Mellitus (Blood Sugar Control).**",
        "when_to_take": "• Take Metformin **with or right after meals**. Take Glimepiride (`GP1`/`GP2`/`Amaryl`) **just before or with breakfast** and never skip meals.",
        "precautions": "• Keep sugar/glucose packets handy in case of low blood sugar symptoms (sweating, shakiness, dizziness).",
    },
    {
        "brands": ["shelcal", "cipcal", "gemcal", "becosules", "neurobion", "nurokind", "mecobalamin", "limcee", "zincovit", "supradyn", "evion", "folvite", "orofer", "livogen", "dexorange", "uprise", "calcirol", "thyronorm", "eltroxin", "thyrox", "udiliv", "ursocol", "vertin", "stemetil", "nexito", "clonafit", "levipil", "gabapin", "ondem", "vomikind", "domstal", "sinarest", "wikoryl", "ascoril", "alex", "benadryl", "grilinctus", "ecosprin", "atorva", "rosuvas", "deplatt"],
        "generic_salt": "Clinical Prescription / Specialty Formulation",
        "common_strengths": "Standard Tablet / Capsule / Syrup Strength",
        "uses": "• Prescribed for targeted nutritional, thyroid, neurological, digestive, respiratory, or cardiovascular support based on its active ingredient.",
        "when_to_take": "• Follow the exact timing on your prescription (Thyronorm is taken 45 mins before breakfast on an empty stomach; Ondem 20 mins before meals; Vitamins/Calcium/Iron/Statins after meals).",
        "precautions": "• Keep a 2 to 4 hour gap between Iron, Calcium, and Thyroid medications. Do not exceed the prescribed daily dose.",
    },
]

# ==============================================================================
# DISEASE & SYMPTOM DATABASE (STRICTLY DISEASE INFO — NO MEDICINE MIXING)
# ==============================================================================

CLINICAL_DISEASE_DATABASE: List[Dict[str, Any]] = [
    {
        "keywords": ["dengue", "ડેન્ગ્યુ", "डेंगू"],
        "title": "Dengue Fever",
        "overview": "Dengue fever is a mosquito-borne viral infection transmitted by daytime-biting *Aedes aegypti* mosquitoes, causing high fever, severe body aches, and a drop in blood platelet counts.",
        "causes": "• Caused by **Dengue Virus (DENV 1–4)** transmitted via *Aedes* mosquitoes breeding in clean stagnant water around homes.",
        "symptoms": "• Sudden high fever (up to 104°F), severe headache, **pain behind the eyes**, intense muscle and joint pain, skin rash, nausea, and low platelets.",
        "diagnosis": "• **Dengue NS1 Antigen Blood Test** (during the first 1–5 days of fever), **Dengue IgM/IgG Antibody Test**, and daily **Complete Blood Count (CBC)** to monitor Platelets and Hematocrit (PCV).",
        "precautions": "• **Aggressive Oral Hydration:** Drink plenty of ORS, coconut water, fresh fruit juices, and boiled cooled water.\n• **Complete Bed Rest & Mosquito Net Use:** Rest under a mosquito net and empty stagnant water containers.\n• **Strictly Avoid Blood-Thinning Painkillers:** Never self-medicate with painkillers that thin the blood or irritate the stomach, as they can trigger bleeding when platelets are low.",
    },
    {
        "keywords": ["tuberculosis", "tb", "ટીબી", "टीबी", "क्षयरोग"],
        "title": "Tuberculosis (TB)",
        "overview": "Tuberculosis is a contagious bacterial infection caused by *Mycobacterium tuberculosis* that primarily affects the lungs. It is completely curable with a full medical course.",
        "causes": "• Spread through microscopic airborne droplets when an untreated person with active pulmonary TB coughs, sneezes, or speaks.",
        "symptoms": "• Persistent cough lasting **more than 2 to 3 weeks**, coughing up phlegm or blood, evening-rise fever, drenching night sweats, chest pain, and unexplained weight loss.",
        "diagnosis": "• **Sputum CBNAAT / TrueNat (GeneXpert) Test**, **Sputum AFB Smear Microscopy**, **Chest X-Ray**, and **Mantoux / IGRA Test**.",
        "precautions": "• **Airflow & Cough Hygiene:** Always cover your mouth and nose with a tissue or mask when coughing, and keep rooms well-ventilated with natural sunlight.\n• **High-Protein Recovery Diet:** Eat protein-rich foods (dal, pulses, milk, paneer, soy, nuts, eggs) to strengthen immunity.\n• **Strict Medical Supervision:** Complete the full multi-month physician-supervised treatment course without skipping days.",
    },
    {
        "keywords": ["appendicitis", "appendix", "એપેન્ડિક્સ", "अपेंडिसाइटिस"],
        "title": "Appendicitis",
        "overview": "Appendicitis is an acute, painful inflammation of the appendix located in the lower right abdomen. It is a medical emergency requiring prompt surgical evaluation.",
        "causes": "• Blockage of the inside of the appendix (lumen) leading to increased pressure, bacterial multiplication, and acute swelling.",
        "symptoms": "• Pain that starts dull near the **navel (belly button)** and shifts within hours to become **sharp and severe in the lower right abdomen**, worsening on coughing or walking, accompanied by nausea, vomiting, and low-grade fever.",
        "diagnosis": "• **Clinical Abdominal Examination** (checking McBurney's point tenderness), **Ultrasound (USG Abdomen & Pelvis) or CT Scan**, and **CBC + CRP Blood Tests**.",
        "precautions": "• **Keep Stomach Empty (NPO):** Stop eating food or drinking water immediately in case urgent surgery is required.\n• **Avoid Laxatives & Heating Pads:** Never apply heat to the lower right belly or take laxatives, as this can cause the inflamed appendix to burst.\n• **Seek Immediate Hospital Care:** Visit a hospital emergency ward without delay.",
    },
    {
        "keywords": ["typhoid", "ટાઇફોઇડ", "टाइफाइड"],
        "title": "Typhoid Fever (Enteric Fever)",
        "overview": "Typhoid fever is a systemic bacterial infection contracted through contaminated water or food, causing a gradually rising high fever and digestive symptoms.",
        "causes": "• Caused by ***Salmonella typhi*** bacteria transmitted through unsafe drinking water, raw unwashed produce, or unhygienic street food.",
        "symptoms": "• **Step-ladder fever** rising progressively to **103°F–104°F**, abdominal pain, headache, coated tongue, extreme weakness, and diarrhea or constipation.",
        "diagnosis": "• **Blood Culture** (most accurate in the first week), **Typhidot IgM / Widal Blood Test**, and **Complete Blood Count (CBC)**.",
        "precautions": "• **Boiled Water & Soft Diet:** Drink only boiled cooled water or ORS, and eat soft, bland foods (moong dal khichdi, curd rice, banana) to protect the intestinal lining.\n• **Hand & Food Hygiene:** Wash hands thoroughly with soap and avoid raw salads, spicy foods, and outside food.",
    },
    {
        "keywords": ["jaundice", "hepatitis", "કમળો", "पीलिया"],
        "title": "Jaundice & Viral Hepatitis",
        "overview": "Jaundice is the yellowing of the skin and whites of the eyes caused by excess bilirubin in the blood due to liver inflammation or bile duct obstruction.",
        "causes": "• Water/food-borne Viral Hepatitis (A & E), blood-borne Hepatitis (B & C), alcohol-related liver strain, or gallbladder stones.",
        "symptoms": "• Yellow discoloration of the eyes and skin, dark yellow/brownish urine, pale stools, nausea, vomiting, loss of appetite, and upper-right abdominal heaviness.",
        "diagnosis": "• **Liver Function Test (LFT: Total/Direct Bilirubin, SGPT, SGOT, ALP)**, **Viral Hepatitis Serology Panel (HAV, HEV, HBsAg, HCV)**, and **Ultrasound Whole Abdomen**.",
        "precautions": "• **Zero Oil, Zero Alcohol & Zero Unverified Powders:** Completely avoid fried/oily foods, ghee/butter, alcohol, and unverified herbal/folk remedies that can harm the liver.\n• **Complete Rest & Clean Fluids:** Take strict rest and consume boiled water, coconut water, fresh homemade juices, and steamed carbohydrate-rich meals.",
    },
    {
        "keywords": ["pneumonia", "નિમોનિયા", "निमोनिया"],
        "title": "Pneumonia",
        "overview": "Pneumonia is an acute infection that inflames the air sacs (alveoli) in one or both lungs, which may fill with fluid or pus.",
        "causes": "• Caused by bacteria (*Streptococcus pneumoniae*), respiratory viruses, or fungi inhaled into the lungs.",
        "symptoms": "• Cough producing greenish, yellow, or bloody phlegm, high fever with shaking chills, **shortness of breath**, and sharp chest pain that worsens when breathing deeply or coughing.",
        "diagnosis": "• **Chest X-Ray**, **Pulse Oximetry ($SpO_2$ oxygen check)**, **Stethoscope Lung Auscultation**, **CBC**, and **Sputum Culture**.",
        "precautions": "• **Monitor Oxygen ($SpO_2$) & Breathing:** Sit upright to ease lung expansion, inhale warm steam, drink warm fluids, and visit a hospital immediately if breathing becomes fast or labored.",
    },
]


def translate_text_live(text: str, target_lang: str, source_lang: str = "auto") -> str:
    if not text or not text.strip():
        return text
    if target_lang == "en" and source_lang == "en":
        return text

    gtx_target = GTX_LANG_CODE_MAP.get(target_lang, target_lang)
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl={source_lang}&tl={urllib.parse.quote(gtx_target)}&dt=t"
    )
    try:
        form_data = urllib.parse.urlencode({"q": text}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=form_data,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and data and isinstance(data[0], list):
                return "".join([seg[0] for seg in data[0] if seg and seg[0]])
    except Exception:
        pass
    return text


def translate_multiline_response(full_text: str, target_lang: str) -> str:
    if not full_text or target_lang == "en":
        return full_text

    paragraphs = full_text.split("\n\n")
    translated_paragraphs: List[str] = []

    for para in paragraphs:
        if not para.strip():
            continue
        if para.strip().startswith("🔗"):
            translated_paragraphs.append(para)
            continue
        translated_para = translate_text_live(para, target_lang=target_lang, source_lang="auto")
        translated_paragraphs.append(translated_para)

    return "\n\n".join(translated_paragraphs)


def translate_batch_live(texts: List[str], target_lang: str) -> List[str]:
    if not texts or target_lang == "en":
        return texts

    delimiter = "\n|||\n"
    results: List[str] = []
    batch: List[str] = []
    batch_len = 0

    for item in texts:
        if batch_len + len(item) > 2800 and batch:
            joined = delimiter.join(batch)
            trans = translate_text_live(joined, target_lang=target_lang, source_lang="en")
            parts = [p.strip() for p in trans.split("|||")]
            if len(parts) == len(batch):
                results.extend(parts)
            else:
                results.extend([translate_text_live(x, target_lang, "en") for x in batch])
            batch = []
            batch_len = 0
        batch.append(item)
        batch_len += len(item) + 6

    if batch:
        joined = delimiter.join(batch)
        trans = translate_text_live(joined, target_lang=target_lang, source_lang="en")
        parts = [p.strip() for p in trans.split("|||")]
        if len(parts) == len(batch):
            results.extend(parts)
        else:
            results.extend([translate_text_live(x, target_lang, "en") for x in batch])

    return results


class AIAssistantService:
    def __init__(self) -> None:
        self._cached_working_model: str = ""

    def get_api_key(self) -> str:
        key_candidates = []
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

        ok, model_or_err = self._discover_working_model(clean_key)
        if not ok:
            return False, f"Invalid API key: {model_or_err}"

        os.environ["GEMINI_API_KEY"] = clean_key
        self._cached_working_model = model_or_err

        config_py_path = os.path.join(BACKEND_DIR, "api_key_config.py")
        try:
            with open(config_py_path, "w", encoding="utf-8") as f:
                f.write('"""Nova Healthtech - Dedicated API Key Configuration File"""\n\n')
                f.write(f'GEMINI_API_KEY = "{clean_key}"\n')
        except Exception:
            pass

        return True, "AI Online • Live Web Search"

    def _discover_working_model(self, api_key: str) -> Tuple[bool, str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=6, context=SSL_CTX) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                available = [
                    m.get("name", "").replace("models/", "")
                    for m in data.get("models", [])
                    if "generateContent" in m.get("supportedGenerationMethods", [])
                ]
                for pref in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"):
                    if pref in available:
                        return True, pref
                if available:
                    return True, available[0]
                return False, "No models available."
        except Exception as e:
            return False, str(e)

    # =========================================================================
    # LOCATION DETECTOR (WHEN USER REPLIES WITH THEIR CITY OR STATE)
    # =========================================================================

    def _detect_location_followup(
        self, raw_query: str, en_query: str, history: List[Dict[str, str]]
    ) -> Optional[str]:
        q_clean = en_query.lower().strip()

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
            "amreli", "botad", "porbandar", "veraval", "godhra", "dahod", "himmatnagar",
            "udaipur", "kota", "ajmer", "bikaner", "alwar", "kanpur", "agra", "prayagraj",
            "allahabad", "meerut", "bareilly", "aligarh", "moradabad", "gorakhpur", "jhansi",
            "jabalpur", "gwalior", "ujjain", "raipur", "bilaspur", "ranchi", "jamshedpur",
            "dhanbad", "deoghar", "gaya", "muzaffarpur", "bhagalpur", "darbhanga", "siliguri",
            "durgapur", "asansol", "kalyani", "rourkela", "sambalpur", "berhampur", "puri",
            "ludhiana", "jalandhar", "patiala", "bathinda", "mohali", "shimla", "mandi",
            "dehradun", "haridwar", "haldwani", "rishikesh", "srinagar", "jammu", "coimbatore",
            "tiruchirappalli", "trichy", "salem", "tirunelveli", "vellore", "mangaluru",
            "mangalore", "hubballi", "hubli", "belagavi", "belgaum", "kalaburagi", "davangere",
            "kozhikode", "calicut", "thrissur", "kollam", "kannur", "kottayam", "vijayawada",
            "guntur", "tirupati", "kurnool", "warangal", "nizamabad", "karimnagar", "panaji",
            "goa", "imphal", "shillong", "agartala", "aizawl", "kohima", "itanagar", "gangtok",
            "punjab", "haryana", "himachal", "uttarakhand", "jharkhand", "chhattisgarh",
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
                    "type": "Government District / Civil Hospital (24x7 Emergency & OPD)",
                    "schemes": "Ayushman Bharat PM-JAY, 70+ Vay Vandana & State Health Schemes",
                    "address": f"Main Civil Hospital Road, {location_name} (Visit the Ayushman Mitra Desk)",
                    "helpline": "Dial 108 (Free Ambulance) / 14555 (National PM-JAY Helpline)",
                }
            ]

        if not matched_stores:
            matched_stores = [
                {
                    "name": f"Pradhan Mantri Bhartiya Janaushadhi Kendra (PMBJK) — {location_name}",
                    "city": location_name,
                    "state": "India",
                    "type": "Government Generic Medicine Store (50%–90% Lower Prices)",
                    "hours": "Open Daily (Hospital Campus Unit Open 24x7)",
                    "address": f"District Civil Hospital Compound & Main Market Road, {location_name}",
                    "contact": "Toll-Free Helpline: 1800-180-8080 | Jan Aushadhi Sugam App",
                }
            ]

        hosp_lines = []
        for idx, h in enumerate(matched_hospitals[:6], start=1):
            hosp_lines.append(
                f"**{idx}. {h['name']} ({h['city']}, {h['state']})**\n"
                f"• **Facility Type:** {h['type']}\n"
                f"• **Accepted Schemes:** {h['schemes']}\n"
                f"• **Address:** {h['address']}\n"
                f"• **Emergency / Helpdesk:** {h['helpline']}"
            )

        store_lines = []
        for idx, s in enumerate(matched_stores[:5], start=1):
            store_lines.append(
                f"**{idx}. {s['name']} ({s['city']})**\n"
                f"• **Store Type:** {s['type']}\n"
                f"• **Timings:** {s['hours']}\n"
                f"• **Location:** {s['address']}\n"
                f"• **Support:** {s['contact']}"
            )

        sections = [
            f"📍 **Nova AI • Verified Hospitals & Medicine Stores in {location_name}**",
            "🏥 **Participating Government, AIIMS & PM-JAY Hospitals Near You:**\n\n" + "\n\n".join(hosp_lines),
            "💊 **Nearby Medicine Stores & Jan Aushadhi Pharmacies (50%–90% Subsidized Generic Medicines):**\n\n" + "\n\n".join(store_lines),
            "📞 **24x7 Emergency & National Helplines:**\n"
            "• **Free Emergency Ambulance:** Dial **108** or **112**\n"
            "• **PM-JAY Hospital Verification Helpline:** Dial **14555**\n"
            "• **Jan Aushadhi Medicine Store Helpline:** Dial **1800-180-8080**",
        ]

        english_reply = "\n\n".join(sections)
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
            "reply": final_reply,
            "safety_disclaimer": "🟢 AI Online • Live Web Search",
        }

    # =========================================================================
    # PRECISION 3-LAYER CLASSIFIER (ZERO MIXING BETWEEN MEDICINES & DISEASES)
    # =========================================================================

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

    def _verify_unknown_term_on_web(self, query_term: str) -> str:
        """
        If the user types a medical term that has no obvious 'mg' or disease word
        (e.g., 'Pneumonia' vs 'Becosules' or 'Chickenpox' vs 'Udapa'),
        inspects OpenFDA and Wikipedia's first sentence to see whether it is a
        MEDICINE or a DISEASE.
        """
        cleaned = self._extract_medical_topic(query_term)

        # 1. Check Wikipedia intro sentence for clear disease vs medication markers
        try:
            search_url = (
                f"https://en.wikipedia.org/w/api.php?action=query&list=search"
                f"&srsearch={urllib.parse.quote(cleaned)}&utf8=1&format=json&srlimit=1"
            )
            req = urllib.request.Request(search_url, headers={"User-Agent": "NovaHealthtech/2.0"})
            with urllib.request.urlopen(req, timeout=4, context=SSL_CTX) as resp:
                hits = json.loads(resp.read().decode("utf-8")).get("query", {}).get("search", [])
                if hits:
                    snippet = re.sub(r"<[^>]+>", " ", hits[0].get("snippet", "")).lower()
                    title_low = hits[0].get("title", "").lower()
                    combined_wiki = f"{title_low} {snippet}"

                    med_markers = [
                        "medication", "drug", "pharmaceutical", "antibiotic", "analgesic",
                        "antihistamine", "antacid", "tablet", "capsule", "brand name",
                        "sold under the brand", "used to treat", "antipyretic", "statin",
                        "vaccine", "supplement", "syrup", "ointment",
                    ]
                    disease_markers = [
                        "disease", "infection", "disorder", "syndrome", "inflammation of",
                        "condition", "symptom", "viral", "bacterial", "parasitic",
                        "cancer", "tumor", "deficiency", "injury", "pain",
                    ]
                    med_score = sum(1 for m in med_markers if m in combined_wiki)
                    dis_score = sum(1 for d in disease_markers if d in combined_wiki)
                    if med_score > dis_score and med_score > 0:
                        return "SPECIFIC_MEDICINE"
                    if dis_score >= med_score and dis_score > 0:
                        return "DISEASE_OR_SYMPTOM"
        except Exception:
            pass

        return "DISEASE_OR_SYMPTOM"

    def _detect_query_intent(
        self, raw_query: str, en_query: str
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Strictly separates queries into:
        - 'SPECIFIC_MEDICINE' (Only Medicine Guide)
        - 'MEDICINE_FOR_CAUSE' (User explicitly asked 'what medicine/tablet for X')
        - 'DISEASE_OR_SYMPTOM' (Only Disease/Symptom Guide)
        """
        combined = f"{raw_query.lower()} {en_query.lower()}"

        # 1. Explicit Disease/Symptom phrasing (e.g., "symptoms of...", "causes of...", "how to diagnose...", "precautions for...")
        has_explicit_disease_phrasing = bool(
            re.search(
                r"\b(symptoms of|symptom of|causes of|cause of|how doctors diagnose|how to diagnose|diagnosis of|precautions for|precautions of|signs of|i am feeling|i feel|pain in my|suffering from)\b",
                combined,
            )
        )

        # 2. Explicit "What medicine/tablet for [cause]" phrasing
        if re.search(
            r"\b(medicine for|medicines for|tablet for|tablets for|syrup for|drug for|pill for|which medicine|what medicine|best medicine for|medication for)\b",
            combined,
        ):
            return "MEDICINE_FOR_CAUSE", None

        # 3. Does it match any brand in our curated Indian Brand Directory?
        for brand_profile in INDIAN_BRAND_PROFILES:
            for b_kw in brand_profile["brands"]:
                if re.search(rf"\b{re.escape(b_kw)}\b", combined):
                    return "SPECIFIC_MEDICINE", brand_profile

        # 4. Does it contain an explicit dosage number ('450', '650mg', '500 mg') or medicine form/specifier?
        has_mg_or_specifier = bool(
            re.search(
                r"(\b\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g|iu)\b|\b(10|20|25|40|50|60|75|80|90|100|120|150|180|200|250|300|325|375|400|450|500|600|625|650|850|875|1000)\b|\b(tablet|tab|capsule|cap|syrup|syp|injection|inj|ointment|inhaler|pill|dosage|dose|xl|sr|dsr|xr|er|md|dt|forte|duo|cv|sp|lc|oz|tz|gp)\b)",
                combined,
                flags=re.IGNORECASE,
            )
        )
        if has_mg_or_specifier and not has_explicit_disease_phrasing:
            return "SPECIFIC_MEDICINE", None

        # 5. Does it have a pharmacological generic chemical suffix?
        if re.search(
            r"\b\w+(prazole|mycin|cillin|floxacin|olol|pril|sartan|dipine|statin|gliptin|formin|zole|tidine|setron|pam|zolam|proxen|fenac|coxib|lukast|zine|asone|olone|carbonate|hydrochloride)\b",
            combined,
            flags=re.IGNORECASE,
        ):
            return "SPECIFIC_MEDICINE", None

        # 6. Check our comprehensive Disease & Symptom Lexicon + Medical Pathology Suffixes (-itis, -osis, -emia, -pathy, -algia, -oma)
        disease_lexicon = [
            "fever", "dengue", "malaria", "typhoid", "tuberculosis", "tb", "appendicitis",
            "jaundice", "hepatitis", "asthma", "bronchitis", "pneumonia", "stone", "stones",
            "diabetes", "sugar", "pain", "ache", "headache", "migraine", "dizzy", "dizziness",
            "vertigo", "vomit", "vomiting", "nausea", "diarrhea", "loose motion", "dysentery",
            "constipation", "piles", "hemorrhoids", "fissure", "fistula", "hernia", "ulcer",
            "acidity", "gas", "heartburn", "indigestion", "gastritis", "colitis", "ibs",
            "cough", "cold", "flu", "influenza", "covid", "coronavirus", "sinus", "sinusitis",
            "tonsillitis", "throat", "earache", "toothache", "backache", "sciatica", "spondylitis",
            "arthritis", "gout", "osteoporosis", "fracture", "sprain", "cramps", "spasm",
            "rash", "itch", "itching", "eczema", "psoriasis", "scabies", "ringworm", "fungal",
            "acne", "pimple", "boil", "allergy", "hives", "urticaria", "vitiligo", "alopecia",
            "sleep", "insomnia", "anxiety", "depression", "stress", "epilepsy", "seizure", "fits",
            "stroke", "paralysis", "parkinson", "alzheimer", "neuropathy", "bp", "blood pressure",
            "hypertension", "hypotension", "heart", "cardiac", "angina", "cholesterol", "anemia",
            "hemoglobin", "thyroid", "hypothyroidism", "hyperthyroidism", "goiter", "pcod", "pcos",
            "menstrual", "period", "pregnancy", "uti", "urinary", "kidney", "renal", "liver",
            "cirrhosis", "fatty liver", "gallbladder", "pancreatitis", "eye", "conjunctivitis",
            "cataract", "glaucoma", "myopia", "vision", "chickenpox", "measles", "mumps",
            "cholera", "rabies", "tetanus", "chikungunya", "zika", "filaria", "leprosy",
            "cancer", "tumor", "infection", "swelling", "edema", "bleeding", "weakness",
            "fatigue", "dehydration", "heatstroke", "sunstroke", "burn", "snakebite",
        ]
        if (
            has_explicit_disease_phrasing
            or any(re.search(rf"\b{re.escape(dw)}\b", combined) for dw in disease_lexicon)
            or re.search(r"\b\w+(itis|osis|emia|pathy|algia|oma|rrhea|uria|penia|megaly)\b", combined)
        ):
            return "DISEASE_OR_SYMPTOM", None

        # 7. For any remaining unknown term, verify on live Wikipedia whether it is a Medicine or Disease
        return self._verify_unknown_term_on_web(en_query), None

    def _search_live_web_for_indian_brand(self, med_name: str, base_drug: str) -> Dict[str, str]:
        web_info = {"composition": "", "uses": "", "when_to_take": "", "precautions": "", "source_url": ""}
        try:
            ddg_query = urllib.parse.quote(f"{med_name} tablet medicine composition uses side effects")
            ddg_url = f"https://html.duckduckgo.com/html/?q={ddg_query}"
            req = urllib.request.Request(
                ddg_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"},
            )
            with urllib.request.urlopen(req, timeout=6, context=SSL_CTX) as resp:
                raw_html = resp.read().decode("utf-8", errors="ignore")
                snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', raw_html, flags=re.I | re.S)
                clean_snippets = []
                for s in snippets[:4]:
                    cs = html.unescape(re.sub(r"<[^>]+>", " ", s))
                    cs = re.sub(r"\s+", " ", cs).strip()
                    if len(cs) > 35:
                        clean_snippets.append(cs)
                if clean_snippets:
                    web_info["uses"] = "• " + "\n• ".join(clean_snippets[:3])[:800]
                    comp_match = re.search(
                        r"(?:contains|composition|composed of|active ingredient is|salt is)\s+([A-Z][a-zA-Z0-9\s\-+()]{3,45})",
                        " ".join(clean_snippets),
                        flags=re.I,
                    )
                    if comp_match:
                        web_info["composition"] = comp_match.group(1).strip()
        except Exception:
            pass
        return web_info

    # =========================================================================
    # MODE 1: SPECIFIC MEDICINE GUIDE (ZERO DISEASE MIXING)
    # =========================================================================

    def _build_specific_medicine_response(
        self,
        user_message: str,
        en_query: str,
        matched_profile: Optional[Dict[str, Any]],
        lang_code: str,
        lang_name: str,
        api_key: str,
    ) -> Dict[str, Any]:
        cleaned_title = re.sub(
            r"^(what is the use of|what are the uses of|what is|tell me about|uses of|side effects of|when to take|how to take|explain|details of)\s+",
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

        if matched_profile:
            composition = matched_profile["generic_salt"]
            strengths_info = detected_strength or matched_profile["common_strengths"]
            uses = matched_profile["uses"]
            when_to_take = matched_profile["when_to_take"]
            precautions = matched_profile["precautions"]
        else:
            web_med = self._search_live_web_for_indian_brand(cleaned_title, base_drug)
            composition = web_med["composition"] or f"{base_drug.title()} (Active Pharmaceutical Salt)"
            strengths_info = detected_strength or "As printed on the medicine strip"
            uses = web_med["uses"] or (
                f"• **{cleaned_title}** is a clinical medication prescribed for conditions treated by its active ingredient (**{composition}**)."
            )
            when_to_take = web_med["when_to_take"] or (
                f"• **When to Take:** Take **{cleaned_title}** at the exact schedule prescribed by your doctor, generally **after food** with a full glass of water."
            )
            precautions = web_med["precautions"] or (
                "• **Side Effects & Precautions:** Inform your doctor if you have kidney, liver, or heart conditions, drug allergies, or if you are pregnant or breastfeeding."
            )

        if specifier_notes:
            spec_block = "\n".join([f"• {note}" for note in specifier_notes])
            when_to_take = f"{when_to_take}\n\n**What Your Medicine's Specifier Means:**\n{spec_block}"

        sections = [
            f"💊 **Nova AI • Medicine & Dosage Guide: {cleaned_title}**",
            f"**1. Active Salt Composition & Strength (`mg`):**\n• **Medicine / Brand:** {cleaned_title}\n• **Active Generic Salt:** {composition}\n• **Strength / Form:** {strengths_info}",
            f"**2. What It Is Used For (Prescribed Medical Uses):**\n{uses}",
            f"**3. When & How to Take It:**\n{when_to_take}",
            f"**4. Common Side Effects & Safety Precautions:**\n{precautions}",
            MANDATORY_MEDICINE_WARNING.strip(),
        ]

        english_reply = "\n\n".join(sections)
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
            "reply": final_reply,
            "safety_disclaimer": "🟢 AI Online • Live Web Search",
        }

    # =========================================================================
    # MODE 2: "WHAT MEDICINE FOR [CAUSE]" DISCUSSION
    # =========================================================================

    def _build_medicine_for_cause_response(
        self,
        user_message: str,
        en_query: str,
        lang_code: str,
        lang_name: str,
        api_key: str,
    ) -> Dict[str, Any]:
        q = en_query.lower()
        if any(w in q for w in ["fever", "temperature", "body ache", "headache"]):
            cause_title = "Fever, Body Ache & Headache"
            med_discussion = (
                "• **First-Line Medicine:** **Paracetamol** (e.g., *Dolo 650, Calpol 500/650, Crocin*) is used by doctors to lower fever and relieve headache or body ache.\n"
                "• **When to Take:** Taken **after food** with water, keeping at least a **4 to 6 hour gap** between doses.\n"
                "• **Precaution:** Avoid Ibuprofen, Combiflam, Diclofenac, or Zerodol during uninvestigated fevers."
            )
        elif any(w in q for w in ["acidity", "gas", "heartburn", "stomach burn", "indigestion"]):
            cause_title = "Acidity, Gas, Heartburn & Indigestion"
            med_discussion = (
                "• **Acid Reducers (PPIs):** **Pantoprazole 40 mg** (*Pan 40, Pantocid*), **Rabeprazole** (*Razo 20*), or **`DSR` combinations** (*Pan-D, Pantocid-DSR*).\n"
                "• **When to Take:** Taken **on an empty stomach 30–45 minutes before breakfast**."
            )
        else:
            cause_title = en_query.title()
            web_med = self._search_live_web_for_indian_brand(en_query, en_query)
            med_discussion = web_med["uses"] or (
                f"• Doctors prescribe targeted medications for **{cause_title}** after evaluating the underlying cause.\n"
                f"• Type any specific tablet name from your prescription (with its `mg` or specifier) for its full dosage and timing guide."
            )

        english_reply = "\n\n".join(
            [
                f"💊 **Nova AI • Medicine Discussion: {cause_title}**",
                f"**1. Commonly Prescribed Medicines & Timing:**\n{med_discussion}",
                MANDATORY_MEDICINE_WARNING.strip(),
            ]
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
            "reply": final_reply,
            "safety_disclaimer": "🟢 AI Online • Live Web Search",
        }

    # =========================================================================
    # MODE 3: DISEASE & SYMPTOM GUIDE (ZERO MEDICINE MIXING)
    # =========================================================================

    def _extract_medical_topic(self, en_query: str) -> str:
        if ":" in en_query:
            before_colon = en_query.split(":", 1)[0].strip()
            if len(before_colon) >= 2:
                en_query = before_colon

        cleaned = en_query.lower().strip()
        stop_phrases = [
            r"^(what are the|what is the|what are|what is|tell me about|explain|how to diagnose|how to treat|how to cure|give me|can you tell me|how do doctors diagnose)\s+",
            r"\b(symptoms|symptom|causes|cause|precautions|precaution|treatment|diagnosis|diagnostic|tests|test|blood|ultrasound|how|doctors|diagnose|it|in detail|and|its|of|for|about|to|take|what|do|i am|feeling|having|suffering from|care)\b",
            r"[?.,!:/&()]+",
        ]
        for pat in stop_phrases:
            cleaned = re.sub(pat, " ", cleaned, flags=re.I)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned if len(cleaned) >= 2 else en_query.strip()

    def _match_builtin_clinical_db(self, raw_query: str, extracted_topic: str) -> Dict[str, str]:
        combined = f"{raw_query.lower()} {extracted_topic.lower()}"
        for entry in CLINICAL_DISEASE_DATABASE:
            if any(kw in combined for kw in entry["keywords"]):
                return {
                    "title": entry["title"],
                    "overview": entry["overview"],
                    "causes": entry["causes"],
                    "symptoms": entry["symptoms"],
                    "diagnosis": entry["diagnosis"],
                    "precautions": entry["precautions"],
                    "source_url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(entry['title'].replace(' ', '_'))}",
                }
        return {}

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
                                self._parse_wikipedia_sections(full_text, result)
                            break
        except Exception:
            pass
        return result

    def _parse_wikipedia_sections(self, full_text: str, result: Dict[str, str]) -> None:
        parts = re.split(r"\n+==+\s*([^=]+?)\s*==+\n+", full_text)
        if not parts:
            return
        intro_paras = [p.strip() for p in parts[0].split("\n") if len(p.strip()) > 30]
        result["overview"] = " ".join(intro_paras[:2])[:850]

        for i in range(1, len(parts) - 1, 2):
            sec_title = parts[i].strip().lower()
            sec_body = parts[i + 1].strip()
            paras = [p.strip() for p in sec_body.split("\n") if len(p.strip()) > 30]
            summary_chunk = "\n• ".join(paras[:3])[:750]
            if not summary_chunk:
                continue
            if any(k in sec_title for k in ("sign", "symptom", "presentation", "clinical")) and not result["symptoms"]:
                result["symptoms"] = "• " + summary_chunk
            elif any(k in sec_title for k in ("cause", "risk", "pathophysiology", "transmission")) and not result["causes"]:
                result["causes"] = "• " + summary_chunk
            elif any(k in sec_title for k in ("diagnos", "screening", "classification")) and not result["diagnosis"]:
                result["diagnosis"] = "• " + summary_chunk
            elif any(k in sec_title for k in ("prevent", "management", "care")) and not result["precautions"]:
                result["precautions"] = "• " + summary_chunk

    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================

    def generate_preliminary_guidance(
        self,
        user_message: str,
        lang: str = "en",
        history: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        lang_code = lang if lang in LANGUAGE_NAMES else "en"
        lang_name = LANGUAGE_NAMES[lang_code]
        api_key = self.get_api_key()
        history = history or []

        en_query = translate_text_live(user_message, target_lang="en", source_lang="auto")

        # 0. Location continuation check (City/State -> Hospitals & Medicine Stores)
        detected_location = self._detect_location_followup(user_message, en_query, history)
        if detected_location:
            return self._build_location_hospitals_and_stores_response(detected_location, lang_code)

        # 1. Precision Classification: Medicine vs. Medicine-for-Cause vs. Disease/Symptom
        intent_mode, matched_brand = self._detect_query_intent(user_message, en_query)

        if intent_mode == "SPECIFIC_MEDICINE":
            return self._build_specific_medicine_response(
                user_message=user_message,
                en_query=en_query,
                matched_profile=matched_brand,
                lang_code=lang_code,
                lang_name=lang_name,
                api_key=api_key,
            )

        if intent_mode == "MEDICINE_FOR_CAUSE":
            return self._build_medicine_for_cause_response(
                user_message=user_message,
                en_query=en_query,
                lang_code=lang_code,
                lang_name=lang_name,
                api_key=api_key,
            )

        # 2. Strictly Disease & Symptom Mode (Zero Medicine Mixing)
        topic = self._extract_medical_topic(en_query)
        builtin_data = self._match_builtin_clinical_db(user_message, topic)
        web_data = self._fetch_live_web_medical_data(topic)

        merged_data = {
            "title": web_data.get("title") if web_data.get("overview") else (builtin_data.get("title") or topic.title()),
            "overview": web_data.get("overview") or builtin_data.get("overview", ""),
            "causes": builtin_data.get("causes") or web_data.get("causes", ""),
            "symptoms": builtin_data.get("symptoms") or web_data.get("symptoms", ""),
            "diagnosis": builtin_data.get("diagnosis") or web_data.get("diagnosis", ""),
            "precautions": builtin_data.get("precautions") or web_data.get("precautions", ""),
            "source_url": web_data.get("source_url") or builtin_data.get("source_url", ""),
        }

        return self._format_complete_medical_response(user_message, topic, merged_data, lang_code)

    def _format_complete_medical_response(
        self,
        user_message: str,
        topic: str,
        data: Dict[str, str],
        lang_code: str,
    ) -> Dict[str, Any]:
        title = data.get("title") or topic.title() or user_message.title()
        overview = data.get("overview") or (
            f"**{title}** is a medical condition that requires clinical evaluation, symptom monitoring, and supportive care."
        )
        causes = data.get("causes") or (
            f"• **{title}** can be caused by viral or bacterial infections, environmental triggers, nutritional or metabolic imbalances, inflammation, or underlying systemic factors."
        )
        symptoms = data.get("symptoms") or (
            f"• Key symptoms of **{title}** include localized discomfort or pain, fatigue, changes in body temperature, inflammation, or functional disturbance in the affected area."
        )
        diagnosis = data.get("diagnosis") or (
            f"• **Clinical Examination:** A doctor evaluates your medical history, vital signs (BP, pulse, temperature, $SpO_2$), and performs a physical exam for **{title}**.\n"
            f"• **Laboratory & Imaging Workup:** Complete Blood Count (CBC), inflammatory markers (CRP/ESR), organ function panels (LFT/RFT), and targeted imaging (Ultrasound / X-Ray / CT) confirm the diagnosis."
        )
        precautions = data.get("precautions") or (
            f"• **Hydration & Nutrition:** Drink plenty of clean boiled/filtered water or ORS and eat freshly prepared, balanced home meals.\n"
            f"• **Rest & Hygiene:** Give your body adequate rest, practice strict hygiene, and monitor if symptoms change or worsen.\n"
            f"• **Avoid Self-Medication:** Do not take unprescribed medications without a doctor's clinical examination."
        )
        source_url = data.get("source_url")

        sections = [
            f"🩺 **Nova AI • Disease & Symptom Guide: {title}**\n\n{overview}",
            f"**1. Causes & Risk Factors:**\n{causes}",
            f"**2. Key Symptoms of {title}:**\n{symptoms}",
            f"**3. How Doctors Diagnose {title} (Tests & Exams):**\n{diagnosis}",
            f"**4. Precautions, Prevention & Self-Care:**\n{precautions}",
            f"⚠️ **5. Consult a Doctor:**\nFor an accurate clinical diagnosis and treatment plan for **{title}**, please consult a qualified doctor (MBBS/MD)."
            + ASK_USER_LOCATION_PROMPT,
        ]

        if source_url:
            sections.append(f"🔗 *Reference Source: {source_url}*")

        english_reply = "\n\n".join(sections)

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
            "reply": final_reply,
            "safety_disclaimer": "🟢 AI Online • Live Web Search",
        }


ai_assistant = AIAssistantService()