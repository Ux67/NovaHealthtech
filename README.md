# Nova Healthtech (Demonstration Prototype)

Nova Healthtech is an AI-assisted preliminary health guidance, emergency orientation, and doctor-access platform designed with rural and low-bandwidth Indian users in mind (supporting English, Gujarati, and Hindi).

## Important Clinical & Safety Disclaimer

- **Not Clinically Validated:** This software is a demonstration prototype and is **not** a certified medical device or clinically validated healthcare service.
- **No Autonomous Diagnosis or Prescribing:** The platform does not diagnose diseases, prescribe medicines, or independently alter doctor-prescribed treatment plans.
- **Deterministic Emergency Guidance:** Life-threatening emergencies must never rely solely on generative AI. Users experiencing medical emergencies in India are directed immediately to **108 (Ambulance)** or **112 (National Emergency Response)**.

## Project Structure

```text
NovaHealthtech/
├── frontend/
│   ├── index.html       # Responsive UI shell & deterministic emergency bar
│   ├── style.css        # Glass-inspired styling + low-bandwidth mode
│   └── script.js        # Safe backend fetch logic & localization preview
├── backend/
│   ├── app.py           # Flask server & /api/health endpoint
│   └── requirements.txt # Locked Python dependencies
├── .gitignore           # Excludes venv, .env, caches, and databases
└── README.md            # Project documentation