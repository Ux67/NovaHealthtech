# Nova Healthtech

Nova Healthtech is a prototype platform for preliminary health information, emergency orientation, doctor-access workflows, multilingual access, and hospital/pharmacy discovery for communities in India.

## Project status

This repository contains a web frontend, a Flask API, and an Android companion application. Features and integrations are under active development. Do not treat the application as a certified medical device or a substitute for professional care.

## Safety boundaries

- The application does not provide a medical diagnosis or prescribe treatment.
- AI-generated information is informational and must not replace assessment by a qualified clinician.
- In India, users facing an emergency should contact local emergency services directly (112; ambulance availability may also be reached through 108 where supported).
- SOS and accident-detection features are assistive prototypes. Sensor events can be wrong, location can be unavailable, and network/OS restrictions can prevent delivery.
- A phone call or dispatch request must never be represented as completed until the operating system or authorized service confirms it. Provide a clear user-controlled cancellation/confirmation path and never silently place calls.

## Repository layout

```text
NovaHealthtech/
├── frontend/                 # Web application assets
├── backend/                  # Flask API and service modules
├── android_companion/        # Android Studio project
├── .gitignore
├── Procfile
└── README.md
```

## Local development

1. Create a Python virtual environment.
2. Install dependencies from `backend/requirements.txt`.
3. Configure secrets in an untracked root `.env` file. Never commit API keys.
4. Start the Flask application from the repository root using the project's configured entry point.
5. Open the Android project in Android Studio and sync its Gradle configuration.

Exact deployment commands depend on the hosting provider and must be configured separately for the frontend and API.

## Privacy and security

Do not commit API keys, personal data, SQLite databases, local IDE state, Android build outputs, or machine-specific configuration. If a credential was ever committed, revoke/rotate it; deleting the latest copy does not remove it from Git history.

## Verification

Run the backend tests and build the Android debug variant locally before releasing changes. Test SOS flows on a controlled test device with non-emergency test contacts. Never test by placing an unintended call to emergency services.
