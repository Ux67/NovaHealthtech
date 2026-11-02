/**
 * Nova Healthtech - Master 22-Language Full-Page, Auto-Started SOS & All-36-States/UTs Controller
 * - Zero duplicate variable declarations (0 TypeScript/JS linter errors)
 * - Auto-starts Foreground Crash Sensor Monitoring & Live GPS as soon as the website opens
 * - Starts an 8-second countdown on impact/drop or SOS and automatically shares GPS location
 *   and requests a call to the saved emergency contact at 0 seconds unless cancelled
 * - Translates 100% of the website from top to bottom across all 22 Indian languages
 * - Displays all 36 Indian States & Union Territories across Hospitals and Medicine Stores
 *   with verified clickable tel: call buttons and Google Maps directions links
 */

/** Accessible non-blocking notice UI. */
function showNotice(message, type = "info") {
  const text = String(message || "").trim();
  if (!text) return;
  let region = document.getElementById("novaNoticeRegion");
  if (!region) {
    region = document.createElement("div");
    region.id = "novaNoticeRegion";
    region.className = "nova-notice-region";
    region.setAttribute("role", "region");
    region.setAttribute("aria-label", "Notifications");
    region.setAttribute("aria-live", "polite");
    document.body.appendChild(region);
  }
  const notice = document.createElement("div");
  const safeType = ["success", "warning", "error"].includes(type) ? type : "info";
  notice.className = "nova-notice nova-notice--" + safeType;
  notice.setAttribute("role", type === "error" ? "alert" : "status");
  const messageNode = document.createElement("p");
  messageNode.className = "nova-notice__message";
  messageNode.textContent = text;
  const close = document.createElement("button");
  close.type = "button";
  close.className = "nova-notice__close";
  close.setAttribute("aria-label", "Dismiss notification");
  close.textContent = "×";
  close.addEventListener("click", () => notice.remove());
  notice.append(messageNode, close);
  region.appendChild(notice);
  window.setTimeout(() => notice.classList.add("is-visible"), 10);
  window.setTimeout(() => {
    notice.classList.remove("is-visible");
    window.setTimeout(() => notice.remove(), 220);
  }, 6500);
}
const API_BASE_URL = window.location.port === "5500" ? "http://127.0.0.1:5000" : "";
const LANG_STORAGE_KEY = "nova_preferred_lang";

const LANGUAGES_LIST = [
  { code: "en", nativeName: "English", englishName: "English", speechLocale: "en-IN" },
  { code: "hi", nativeName: "हिन्दी", englishName: "Hindi", speechLocale: "hi-IN" },
  { code: "gu", nativeName: "ગુજરાતી", englishName: "Gujarati", speechLocale: "gu-IN" },
  { code: "mr", nativeName: "मराठी", englishName: "Marathi", speechLocale: "mr-IN" },
  { code: "ta", nativeName: "தமிழ்", englishName: "Tamil", speechLocale: "ta-IN" },
  { code: "te", nativeName: "తెలుగు", englishName: "Telugu", speechLocale: "te-IN" },
  { code: "bn", nativeName: "বাংলা", englishName: "Bengali", speechLocale: "bn-IN" },
  { code: "kn", nativeName: "ಕನ್ನಡ", englishName: "Kannada", speechLocale: "kn-IN" },
  { code: "ml", nativeName: "മലയാളം", englishName: "Malayalam", speechLocale: "ml-IN" },
  { code: "pa", nativeName: "ਪੰਜਾਬੀ", englishName: "Punjabi", speechLocale: "pa-IN" },
  { code: "or", nativeName: "ଓଡ଼ିଆ", englishName: "Odia", speechLocale: "or-IN" },
  { code: "as", nativeName: "অসমীয়া", englishName: "Assamese", speechLocale: "as-IN" },
  { code: "ur", nativeName: "اردو", englishName: "Urdu", speechLocale: "ur-IN" },
  { code: "mai", nativeName: "मैथिली", englishName: "Maithili", speechLocale: "mai-IN" },
  { code: "kok", nativeName: "कोंकणी", englishName: "Konkani", speechLocale: "kok-IN" },
  { code: "ne", nativeName: "नेपाली", englishName: "Nepali", speechLocale: "ne-IN" },
  { code: "sd", nativeName: "सिन्धी", englishName: "Sindhi", speechLocale: "sd-IN" },
  { code: "ks", nativeName: "कॉशुर", englishName: "Kashmiri", speechLocale: "ks-IN" },
  { code: "doi", nativeName: "डोगरी", englishName: "Dogri", speechLocale: "doi-IN" },
  { code: "mni", nativeName: "মৈতৈলোন্", englishName: "Manipuri", speechLocale: "mni-IN" },
  { code: "sat", nativeName: "ᱥᱟᱱᱛᱟᱲᱤ", englishName: "Santali", speechLocale: "sat-IN" },
  { code: "sa", nativeName: "संस्कृतम्", englishName: "Sanskrit", speechLocale: "sa-IN" },
];

const LANG_META = {};
const SPEECH_LANG_MAP = {};
LANGUAGES_LIST.forEach((l) => {
  LANG_META[l.code] = l;
  SPEECH_LANG_MAP[l.code] = l.speechLocale;
});

const NATIVE_DIGITS_MAP = {
  en: "0123456789", hi: "०१२३४५६७८९", gu: "૦૧૨૩૪૫૬૭૮૯", mr: "०१२३४५६७८९",
  ta: "௦௧௨௩௪௫௬௭௮௯", te: "౦౧౨౩౪౫౬౭౮౯", bn: "০১২৩৪৫৬৭৮৯", kn: "೦೧೨೩೪೫೬೭೮೯",
  ml: "൦൧൨൩൪൫൬൭൮൯", pa: "੦੧੨੩੪੫੬੭੮੯", or: "୦୧୨୩୪୫୬୭୮୯", as: "০১২৩৪৫৬৭৮৯",
  ur: "۰۱۲۳۴۵۶۷۸۹", mai: "०१२३४५६७८९", kok: "०१२३४५६७८९", ne: "०१२३४५६७८९",
  sd: "०१२३४५६७८९", ks: "०१२३४५६७८९", doi: "०१२३४५६७८९", mni: "০১২৩৪৫৬৭৮৯",
  sat: "᱐᱑᱒᱓᱔᱕᱖᱗᱘᱙", sa: "०१२३४५६७८९",
};

function normalizeDigitsToAscii(str) {
  if (!str) return "";
  let out = String(str);
  Object.values(NATIVE_DIGITS_MAP).forEach((digits) => {
    if (digits === "0123456789" || digits.length !== 10) return;
    for (let i = 0; i < 10; i++) {
      out = out.split(digits[i]).join(String(i));
    }
  });
  return out;
}

function convertDigitsToNative(str, langCode) {
  if (!str) return str;
  const asciiStr = normalizeDigitsToAscii(String(str));
  if (langCode === "en" || !NATIVE_DIGITS_MAP[langCode]) return asciiStr;
  const digits = NATIVE_DIGITS_MAP[langCode];
  return asciiStr.replace(/[0-9]/g, (d) => digits[Number(d)] || d);
}

let currentLang = localStorage.getItem(LANG_STORAGE_KEY) || "en";
if (!LANG_META[currentLang]) currentLang = "en";

let translationJobCounter = 0;
let activeAbortController = null;
const SESSION_TRANSLATION_CACHE = {};

let chatHistory = [];
let cachedBenefitsData = null;
let cachedTriageRules = null;
let cachedHealthGuides = [];
let speechRecognition = null;
let isRecordingVoice = false;

const DEFAULT_PROMPTS = [
  "Symptoms of High BP: Causes, stages, diagnostic tests, diet & helplines",
  "What is Depression? Causes, symptoms, tests, precautions & helplines",
  "Dengue fever: Causes, symptoms, diagnosis tests & precautions",
  "What is Lithonex 450 XL and when to take it?",
  "What is Zerodol-SP and Pan-D used for?",
  "I live in Bhavnagar — show nearby hospitals & medicine stores",
];

/**
 * Stamps pure English baseline (_origEn) on every text node and placeholder inside rootEl
 * before translation so switching between any of the 22 languages is 100% reversible.
 */
function stampEnglishBaseline(rootEl = document.body) {
  if (!rootEl) return;
  const walker = document.createTreeWalker(rootEl, NodeFilter.SHOW_TEXT, null);
  let node = walker.nextNode();
  while (node) {
    const parent = node.parentElement;
    if (
      parent &&
      parent.tagName !== "SCRIPT" &&
      parent.tagName !== "STYLE" &&
      !parent.closest("#langPillsContainer") &&
      !parent.closest("#langSelect") &&
      !parent.closest("#consultLang") &&
      parent.id !== "activeLangIndicator" &&
      !parent.closest("#chatMessages .chat-bubble")
    ) {
      const trimmed = normalizeDigitsToAscii((node.nodeValue || "").trim());
      if (trimmed && node._origEn === undefined) {
        node._origEn = trimmed;
        const leadMatch = node.nodeValue.match(/^\s*/);
        const trailMatch = node.nodeValue.match(/\s*$/);
        node._leadSpace = leadMatch ? leadMatch[0] : "";
        node._trailSpace = trailMatch ? trailMatch[0] : "";
      }
    }
    node = walker.nextNode();
  }

  const inputs = rootEl.querySelectorAll
    ? Array.from(rootEl.querySelectorAll("input[placeholder], textarea[placeholder]"))
    : [];
  inputs.forEach((inp) => {
    if (!inp.dataset.origPlaceholderEn) {
      inp.dataset.origPlaceholderEn = normalizeDigitsToAscii(inp.getAttribute("placeholder") || "");
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  initLowBandwidthMode();
  initLanguageSelectorAndBar();
  initVoiceEngine();
  initAssistantChatModule();

  try {
    await Promise.all([
      initSosAndAccidentDetectionModule(),
      initHealthGuideModule(),
      initTriageModule(),
      initBenefitsAndAllIndiaDirectories(),
      initConsultationsModule(),
      initRemindersModule(),
    ]);
  } catch (err) {
    console.warn("Module init warning:", err);
  }

  await initHealthCheck();
  initRuralStressTester();

  stampEnglishBaseline(document.body);

  if (currentLang !== "en") {
    await setLanguage(currentLang);
  }
});

function initLowBandwidthMode() {
  const toggleBtn = document.getElementById("bandwidthToggle");
  if (!toggleBtn) return;
  const saved = localStorage.getItem("nova_low_bandwidth") === "true";
  document.body.classList.toggle("low-bandwidth", saved);
  toggleBtn.setAttribute("aria-pressed", String(saved));
  const initLabel = saved ? "Low-Bandwidth: On" : "Low-Bandwidth: Off";
  toggleBtn.textContent = initLabel;
  if (toggleBtn.firstChild) toggleBtn.firstChild._origEn = initLabel;

  toggleBtn.addEventListener("click", async () => {
    const nextState = !document.body.classList.contains("low-bandwidth");
    localStorage.setItem("nova_low_bandwidth", String(nextState));
    document.body.classList.toggle("low-bandwidth", nextState);
    toggleBtn.setAttribute("aria-pressed", String(nextState));
    const newEn = nextState ? "Low-Bandwidth: On" : "Low-Bandwidth: Off";
    toggleBtn.textContent = newEn;
    if (toggleBtn.firstChild) toggleBtn.firstChild._origEn = newEn;
    if (currentLang !== "en") {
      await translateWholePageAndChat(currentLang);
    }
  });
}

// ============================================================================
// 22-LANGUAGE SELECTOR & FULL-PAGE START-TO-END TRANSLATION ENGINE
// ============================================================================

function initLanguageSelectorAndBar() {
  const langSelect = document.getElementById("langSelect");
  const consultLang = document.getElementById("consultLang");
  const populateLanguageSelect = (select) => {
    if (!select) return;
    const previousValue = select.value;
    select.replaceChildren();
    LANGUAGES_LIST.forEach((language) => {
      const option = document.createElement("option");
      option.value = language.code;
      option.textContent = language.nativeName + " (" + language.englishName + ")";
      select.appendChild(option);
    });
    select.value = LANG_META[previousValue] ? previousValue : currentLang;
  };
  populateLanguageSelect(langSelect);
  populateLanguageSelect(consultLang);
  if (langSelect) {
    langSelect.value = currentLang;
    langSelect.addEventListener("change", (event) => setLanguage(event.target.value));
  }
  if (consultLang) consultLang.value = currentLang;
  // Keep the 22-language selector compact. Do not inject a second full-page button grid.
  updateLanguagePillsUI(currentLang);
}

function updateLanguagePillsUI(langCode) {
  document.documentElement.lang = langCode;
  document.documentElement.dir = langCode === "ur" ? "rtl" : "ltr";

  const langSelect = document.getElementById("langSelect");
  if (langSelect && langSelect.value !== langCode) langSelect.value = langCode;
  const consultLang = document.getElementById("consultLang");
  if (consultLang) consultLang.value = langCode;

  document.querySelectorAll(".lang-pill-btn").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.langCode === langCode);
  });

  if (speechRecognition) {
    speechRecognition.lang = SPEECH_LANG_MAP[langCode] || "en-IN";
  }
}

async function setLanguage(newLangCode) {
  if (!LANG_META[newLangCode]) return;
  currentLang = newLangCode;
  localStorage.setItem(LANG_STORAGE_KEY, currentLang);
  updateLanguagePillsUI(currentLang);
  await translateWholePageAndChat(currentLang);
}

/**
 * Walks EVERY visible DOM text node, input placeholder, dropdown option, card, and chat bubble
 * from top to bottom and translates them into `langCode` via `/api/translate-batch`.
 */
async function translateWholePageAndChat(langCode) {
  if (activeAbortController) {
    try {
      activeAbortController.abort();
    } catch (e) {}
  }
  activeAbortController = new AbortController();
  const signal = activeAbortController.signal;
  const myJobId = ++translationJobCounter;

  const meta = LANG_META[langCode] || LANG_META.en;
  const activeIndicator = document.getElementById("activeLangIndicator");

  stampEnglishBaseline(document.body);

  const textNodes = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const parent = node.parentElement;
      if (!parent) return NodeFilter.FILTER_REJECT;
      const tag = parent.tagName;
      if (tag === "SCRIPT" || tag === "STYLE" || tag === "NOSCRIPT") {
        return NodeFilter.FILTER_REJECT;
      }
      if (
        parent.closest("#langPillsContainer") ||
        parent.closest("#langSelect") ||
        parent.closest("#consultLang") ||
        parent.id === "activeLangIndicator" ||
        parent.closest("#chatMessages .chat-bubble")
      ) {
        return NodeFilter.FILTER_REJECT;
      }
      if (!node._origEn) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });

  let currentNode = walker.nextNode();
  while (currentNode) {
    textNodes.push(currentNode);
    currentNode = walker.nextNode();
  }

  const allInputs = Array.from(document.querySelectorAll("input[placeholder], textarea[placeholder]"));
  const chatBubbles = Array.from(document.querySelectorAll("#chatMessages .chat-bubble"));

  if (langCode === "en") {
    textNodes.forEach((node) => {
      node.nodeValue = `${node._leadSpace || ""}${node._origEn}${node._trailSpace || ""}`;
    });
    allInputs.forEach((inp) => {
      if (inp.dataset.origPlaceholderEn) {
        inp.setAttribute("placeholder", inp.dataset.origPlaceholderEn);
      }
    });
    chatBubbles.forEach((b) => {
      if (b._origEnglishText) {
        formatRichBubbleContent(b, b._origEnglishText);
      }
    });
    if (activeIndicator) {
      activeIndicator.textContent = "English";
    }
    return;
  }

  if (activeIndicator) {
    activeIndicator.textContent = `⏳ ${meta.nativeName} (${meta.englishName})...`;
  }

  if (!SESSION_TRANSLATION_CACHE[langCode]) {
    SESSION_TRANSLATION_CACHE[langCode] = {};
  }
  const translationMap = SESSION_TRANSLATION_CACHE[langCode];

  const uniqueStringsSet = new Set();
  textNodes.forEach((node) => {
    if (node._origEn && /[a-zA-Z]/.test(node._origEn)) {
      uniqueStringsSet.add(node._origEn);
    }
  });
  allInputs.forEach((inp) => {
    if (inp.dataset.origPlaceholderEn && /[a-zA-Z]/.test(inp.dataset.origPlaceholderEn)) {
      uniqueStringsSet.add(inp.dataset.origPlaceholderEn);
    }
  });

  const uniqueStrings = Array.from(uniqueStringsSet);
  const missingStrings = uniqueStrings.filter((s) => !translationMap[s]);

  try {
    const batchPromise = (async () => {
      if (missingStrings.length === 0) return;
      const res = await fetch(`${API_BASE_URL}/api/translate-batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          texts: missingStrings,
          target_lang: langCode,
        }),
        signal,
      });
      if (res.ok) {
        const data = await res.json();
        const translatedArr = data.translations || [];
        missingStrings.forEach((origStr, idx) => {
          const candidate = translatedArr[idx] ? translatedArr[idx].trim() : "";
          const origWords = normalizeDigitsToAscii(origStr).replace(/[^a-zA-Z]+/g, "").toLowerCase();
          const candWords = normalizeDigitsToAscii(candidate).replace(/[^a-zA-Z]+/g, "").toLowerCase();
          if (candidate && (!origWords || origWords !== candWords)) {
            translationMap[origStr] = convertDigitsToNative(candidate, langCode);
          }
        });
      }
    })();

    const chatPromise = Promise.all(
      chatBubbles.map(async (bubble) => {
        const sourceText = bubble._origEnglishText || bubble.dataset.rawMessageText;
        if (!sourceText) return;
        const res = await fetch(`${API_BASE_URL}/api/translate-text`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: sourceText,
            target_lang: langCode,
          }),
          signal,
        });
        if (res.ok && myJobId === translationJobCounter) {
          const data = await res.json();
          if (data.translated) {
            formatRichBubbleContent(bubble, convertDigitsToNative(data.translated, langCode));
          }
        }
      })
    );

    await Promise.all([batchPromise, chatPromise]);
  } catch (err) {
    if (err.name === "AbortError") return;
  }

  if (myJobId !== translationJobCounter) return;

  textNodes.forEach((node) => {
    const orig = node._origEn;
    if (!orig) return;
    const translated = translationMap[orig] || orig;
    node.nodeValue = `${node._leadSpace || ""}${convertDigitsToNative(translated, langCode)}${node._trailSpace || ""}`;
  });

  allInputs.forEach((inp) => {
    const origP = inp.dataset.origPlaceholderEn;
    if (!origP) return;
    const translatedP = translationMap[origP] || origP;
    inp.setAttribute("placeholder", convertDigitsToNative(translatedP, langCode));
  });

  if (activeIndicator) {
    activeIndicator.textContent = `✅ ${meta.nativeName} (${meta.englishName})`;
  }
}

// ============================================================================
// MODULE 0: AUTO-STARTED CRASH SENSOR MONITORING & 8-SECOND DIRECT AMBULANCE CALL
// ============================================================================

const AUTO_SOS_COUNTDOWN_SECONDS = 8;

let sosSensorMonitoringActive = true;
let sosCountdownTimer = null;
let sosRemainingSeconds = AUTO_SOS_COUNTDOWN_SECONDS;
let activeIncidentUuid = null;
let latestGpsPosition = null;
let cachedTrustedContacts = [];

let isGpsRequestInFlight = false;
let isDropConfirmationModalOpen = false;
let isSosEscalationInFlight = false;
let executedIncidentUuids = new Set();

const GRAVITY_MS2 = 9.80665;
let rollingGravityBaseline = GRAVITY_MS2;
let lastFreeFallTimestampMs = 0;
let recentSpikeTimestampsMs = [];
let pendingImpactCandidate = null;
let postImpactSettleTimer = null;
let lastAlertCooldownUntilMs = 0;

async function initSosAndAccidentDetectionModule() {
  const manualSosBtn = document.getElementById("manualSosBtn");
  const toggleSensorBtn = document.getElementById("toggleSensorMonitorBtn");
  const refreshGpsBtn = document.getElementById("refreshGpsBtn");
  const cancelBtn = document.getElementById("cancelSosCountdownBtn");
  const simBumpBtn = document.getElementById("simRoutineBumpBtn");
  const simDropBtn = document.getElementById("simPhoneDropBtn");
  const simCrashBtn = document.getElementById("simSevereCrashBtn");
  const contactForm = document.getElementById("trustedContactForm");
  const manualAddressInput = document.getElementById("sosManualAddressInput");

  if (!manualSosBtn) return;

  // Automatically enable foreground crash sensor monitoring & GPS on page load without asking the user
  await enableForegroundSensorMonitoring(true);
  acquireLiveGpsCoordinates(false, 0);

  // Silent passive listener for iOS Safari if DeviceMotion requires first touch
  const unlockSensorsOnFirstTouch = async () => {
    if (!sosSensorMonitoringActive) return;
    if (typeof DeviceMotionEvent !== "undefined" && typeof DeviceMotionEvent.requestPermission === "function") {
      try {
        const perm = await DeviceMotionEvent.requestPermission();
        if (perm === "granted") {
          window.addEventListener("devicemotion", handleDeviceMotionEvent);
        }
      } catch (e) {}
    }
    document.removeEventListener("touchstart", unlockSensorsOnFirstTouch);
    document.removeEventListener("click", unlockSensorsOnFirstTouch);
  };
  document.addEventListener("touchstart", unlockSensorsOnFirstTouch, { passive: true });
  document.addEventListener("click", unlockSensorsOnFirstTouch, { passive: true });

  await loadTrustedContactsUI();

  if (manualAddressInput) {
    manualAddressInput.addEventListener("input", () => {
      updateManualLandmarkFallbackStatus(manualAddressInput.value.trim());
    });
  }

  manualSosBtn.addEventListener("click", () => {
    isDropConfirmationModalOpen = false;
    startIncidentCountdownWorkflow("manual_sos_button", {
      peak_linear_accel_ms2: 0,
      peak_gyro_rad_s: 0,
      note: "Manual SOS button pressed by user",
    });
  });

  if (refreshGpsBtn) {
    refreshGpsBtn.addEventListener("click", () => acquireLiveGpsCoordinates(true, 0));
  }

  if (toggleSensorBtn) {
    toggleSensorBtn.addEventListener("click", async () => {
      if (sosSensorMonitoringActive) {
        await disableForegroundSensorMonitoring();
      } else {
        await enableForegroundSensorMonitoring(false);
      }
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener("click", async () => {
      await cancelActiveSosWorkflow("User clicked CANCEL — I AM SAFE within 8s countdown");
    });
  }

  if (simBumpBtn) {
    simBumpBtn.addEventListener("click", () =>
      simulateSensorTrace({
        peak_linear_accel_ms2: 11.2,
        peak_gyro_rad_s: 0.8,
        impact_duration_ms: 20,
        prior_speed_kmh: 5,
        free_fall_detected: false,
        post_impact_stillness: false,
      })
    );
  }
  if (simDropBtn) {
    simDropBtn.addEventListener("click", () => {
      isDropConfirmationModalOpen = false;
      simulateSensorTrace({
        peak_linear_accel_ms2: 24.5,
        peak_gyro_rad_s: 1.9,
        impact_duration_ms: 25,
        prior_speed_kmh: 0,
        free_fall_detected: true,
        post_impact_stillness: true,
      });
    });
  }
  if (simCrashBtn) {
    simCrashBtn.addEventListener("click", () => {
      isDropConfirmationModalOpen = false;
      simulateSensorTrace({
        peak_linear_accel_ms2: 38.4,
        peak_gyro_rad_s: 5.6,
        impact_duration_ms: 65,
        prior_speed_kmh: 42,
        free_fall_detected: false,
        post_impact_stillness: true,
      });
    });
  }

  if (contactForm) {
    contactForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.getElementById("trustedName").value.trim();
      const phone = normalizeDigitsToAscii(document.getElementById("trustedPhone").value.trim());
      const consent = document.getElementById("trustedConsent").checked;
      const res = await fetch(`${API_BASE_URL}/api/sos/contacts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contact_name: name,
          phone_number: phone,
          relationship: "Emergency Contact",
          consent_confirmed: consent,
        }),
      });
      if (res.ok) {
        contactForm.reset();
        await loadTrustedContactsUI();
        if (currentLang !== "en") await translateWholePageAndChat(currentLang);
      } else {
        const err = await res.json().catch(() => ({}));
        showNotice(err.message || "Enter a valid 10-digit mobile number.", "error");
      }
    });
  }
}

function updateManualLandmarkFallbackStatus(manualText) {
  if (latestGpsPosition && latestGpsPosition.latitude !== null) return;
  const statusLine = document.getElementById("sosLocationStatusLine");
  const actionsDiv = document.getElementById("sosLocationActions");
  if (!statusLine || !actionsDiv) return;

  if (!manualText) {
    actionsDiv.replaceChildren();
    return;
  }

  const encodedMapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(manualText)}`;
  statusLine.innerHTML =
    `<strong>📍 Manual Fallback Location Active:</strong> ` +
    `<span>${manualText.replace(/</g, "&lt;")}</span> (Will be shared with the saved emergency contact)`;
  actionsDiv.innerHTML = `
    <a href="${encodedMapsUrl}" target="_blank" rel="noopener noreferrer" class="btn-official-portal" style="font-size:0.78rem; padding:0.3rem 0.7rem;">
      🗺️ Verify Manual Location on Google Maps ↗
    </a>
  `;
}

async function enableForegroundSensorMonitoring(silentAutoStart = true) {
  const badge = document.getElementById("sosMonitorBadge");
  const statusText = document.getElementById("sosMonitorStatusText");
  const toggleBtn = document.getElementById("toggleSensorMonitorBtn");

  rollingGravityBaseline = GRAVITY_MS2;
  recentSpikeTimestampsMs = [];

  if ("DeviceMotionEvent" in window) {
    window.removeEventListener("devicemotion", handleDeviceMotionEvent);
    window.addEventListener("devicemotion", handleDeviceMotionEvent);
  }

  sosSensorMonitoringActive = true;

  if (badge) badge.className = "status-pill status-pill--online";
  if (statusText) {
    statusText.textContent = "🟢 Foreground Sensor Monitor: Active (Auto-Started)";
    if (statusText.firstChild) statusText.firstChild._origEn = statusText.textContent;
  }
  if (toggleBtn) {
    toggleBtn.textContent = "⏹ Disable Foreground Sensor Monitoring";
    if (toggleBtn.firstChild) toggleBtn.firstChild._origEn = toggleBtn.textContent;
  }

  if (!silentAutoStart && currentLang !== "en") {
    await translateWholePageAndChat(currentLang);
  }
}

async function disableForegroundSensorMonitoring() {
  window.removeEventListener("devicemotion", handleDeviceMotionEvent);
  if (postImpactSettleTimer) {
    clearTimeout(postImpactSettleTimer);
    postImpactSettleTimer = null;
  }
  pendingImpactCandidate = null;
  sosSensorMonitoringActive = false;

  const badge = document.getElementById("sosMonitorBadge");
  const statusText = document.getElementById("sosMonitorStatusText");
  const toggleBtn = document.getElementById("toggleSensorMonitorBtn");
  if (badge) badge.className = "status-pill status-pill--offline";
  if (statusText) {
    statusText.textContent = "Sensor Monitoring: Inactive";
    if (statusText.firstChild) statusText.firstChild._origEn = statusText.textContent;
  }
  if (toggleBtn) {
    toggleBtn.textContent = "📡 Enable Foreground Crash Sensor Monitoring";
    if (toggleBtn.firstChild) toggleBtn.firstChild._origEn = toggleBtn.textContent;
  }
  if (currentLang !== "en") await translateWholePageAndChat(currentLang);
}

function handleDeviceMotionEvent(event) {
  if (!sosSensorMonitoringActive || sosCountdownTimer) return;

  const now = Date.now();
  if (now < lastAlertCooldownUntilMs) return;

  const accWithG = event.accelerationIncludingGravity;
  const accLinear = event.acceleration;
  if (!accWithG && !accLinear) return;

  let totalWithGravity = GRAVITY_MS2;
  if (accWithG && accWithG.x !== null && accWithG.y !== null && accWithG.z !== null) {
    totalWithGravity = Math.sqrt(
      accWithG.x * accWithG.x + accWithG.y * accWithG.y + accWithG.z * accWithG.z
    );
    if (Math.abs(totalWithGravity - GRAVITY_MS2) < 3.5) {
      rollingGravityBaseline = 0.9 * rollingGravityBaseline + 0.1 * totalWithGravity;
    }
  }

  if (totalWithGravity < 3.8) {
    lastFreeFallTimestampMs = now;
  }

  let linearMag = 0;
  if (accLinear && accLinear.x !== null && accLinear.y !== null && accLinear.z !== null) {
    linearMag = Math.sqrt(
      accLinear.x * accLinear.x + accLinear.y * accLinear.y + accLinear.z * accLinear.z
    );
  } else {
    linearMag = Math.abs(totalWithGravity - rollingGravityBaseline);
  }

  const rot = event.rotationRate || {};
  const rx = ((rot.alpha || 0) * Math.PI) / 180;
  const ry = ((rot.beta || 0) * Math.PI) / 180;
  const rz = ((rot.gamma || 0) * Math.PI) / 180;
  const totalGyro = Math.sqrt(rx * rx + ry * ry + rz * rz);

  if (pendingImpactCandidate) {
    if (linearMag > 14.0) {
      pendingImpactCandidate.postImpactSpikes += 1;
      if (linearMag > pendingImpactCandidate.peakLinear) {
        pendingImpactCandidate.peakLinear = linearMag;
      }
      if (totalGyro > pendingImpactCandidate.peakGyro) {
        pendingImpactCandidate.peakGyro = totalGyro;
      }
    }
    return;
  }

  if (linearMag >= 19.5) {
    recentSpikeTimestampsMs = recentSpikeTimestampsMs.filter((t) => now - t <= 1200);
    recentSpikeTimestampsMs.push(now);

    const hadRecentFreeFall = now - lastFreeFallTimestampMs <= 650;

    if (linearMag < 24.0 && !hadRecentFreeFall && totalGyro < 2.2) {
      return;
    }

    pendingImpactCandidate = {
      peakLinear: linearMag,
      peakGyro: totalGyro,
      hadFreeFall: hadRecentFreeFall,
      spikeCount: recentSpikeTimestampsMs.length,
      postImpactSpikes: 0,
    };

    postImpactSettleTimer = setTimeout(() => {
      const cand = pendingImpactCandidate;
      pendingImpactCandidate = null;
      postImpactSettleTimer = null;
      if (!cand) return;

      const isRhythmicShake = cand.postImpactSpikes >= 4 || cand.spikeCount >= 4;
      const settledAfterImpact = cand.postImpactSpikes <= 2;

      if (isRhythmicShake) {
        return;
      }

      lastAlertCooldownUntilMs = Date.now() + 8000;
      simulateSensorTrace({
        peak_linear_accel_ms2: Number(cand.peakLinear.toFixed(1)),
        peak_gyro_rad_s: Number(cand.peakGyro.toFixed(1)),
        impact_duration_ms: 45,
        prior_speed_kmh: latestGpsPosition?.speed_kmh || 0,
        free_fall_detected: cand.hadFreeFall,
        post_impact_stillness: settledAfterImpact,
        rhythmic_shaking: false,
        spike_count_in_window: cand.spikeCount,
      });
    }, 450);
  }
}

async function simulateSensorTrace(sensorPayload) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/sos/evaluate-sensors`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sensorPayload),
    });
    const data = await res.json();
    const evalRes = data.evaluation || {};
    const reportBox = document.getElementById("sosDispatchReportBox");

    if (evalRes.classification === "NORMAL_MOVEMENT") {
      if (reportBox && !sosCountdownTimer) {
        reportBox.hidden = false;
        reportBox.innerHTML = `<p><strong>✅ Sensor Check (${sensorPayload.peak_linear_accel_ms2} m/s²):</strong> ${evalRes.confidence_note}</p>`;
        stampEnglishBaseline(reportBox);
        if (currentLang !== "en") await translateWholePageAndChat(currentLang);
      }
      return;
    }

    const triggerLabel =
      evalRes.classification === "SUSPECTED_SEVERE_IMPACT"
        ? "automatic_severe_impact_8s"
        : "automatic_drop_or_impact_8s";

    startIncidentCountdownWorkflow(triggerLabel, sensorPayload);
  } catch (e) {}
}

function playSosAlertBeep() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.22);
  } catch (e) {}
}

function acquireLiveGpsCoordinates(userInitiated = false, retryCount = 0) {
  const statusLine = document.getElementById("sosLocationStatusLine");
  const actionsDiv = document.getElementById("sosLocationActions");
  const refreshBtn = document.getElementById("refreshGpsBtn");
  const manualInput = document.getElementById("sosManualAddressInput");

  if (isGpsRequestInFlight && retryCount === 0) return;

  const isLocalhost =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "[::1]";
  if (!window.isSecureContext && !isLocalhost) {
    if (statusLine) {
      statusLine.innerHTML =
        `<strong>⚠️ GPS Blocked by Insecure Origin (HTTP):</strong> ` +
        `Browsers require <code>http://127.0.0.1:5000</code> (locally) or <code>https://</code> (in production) for GPS. ` +
        `Please enter your road/landmark in the manual fallback box below.`;
      stampEnglishBaseline(statusLine);
    }
    if (manualInput && manualInput.value.trim()) {
      updateManualLandmarkFallbackStatus(manualInput.value.trim());
    }
    return;
  }

  if (!("geolocation" in navigator)) {
    if (statusLine) {
      statusLine.innerHTML =
        `<strong>📍 GPS Status:</strong> Geolocation API is not supported in this browser. ` +
        `Please enter your landmark in the manual fallback box below.`;
      stampEnglishBaseline(statusLine);
    }
    return;
  }

  isGpsRequestInFlight = true;
  if (refreshBtn && retryCount === 0) refreshBtn.disabled = true;

  if (statusLine && (userInitiated || retryCount > 0)) {
    statusLine.innerHTML =
      retryCount === 0
        ? `<strong>📍 GPS Status:</strong> Acquiring live coordinates for automatic ambulance sharing...`
        : `<strong>📍 GPS Status:</strong> High-accuracy GPS timed out—retrying once with network positioning...`;
  }

  const geoOptions =
    retryCount === 0
      ? { enableHighAccuracy: true, timeout: 4500, maximumAge: 10000 }
      : { enableHighAccuracy: false, timeout: 3000, maximumAge: 60000 };

  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      isGpsRequestInFlight = false;
      if (refreshBtn) refreshBtn.disabled = false;

      const lat = pos.coords.latitude;
      const lng = pos.coords.longitude;
      const acc = Math.round(pos.coords.accuracy || 0);
      const speedKmh = pos.coords.speed ? Math.round(pos.coords.speed * 3.6) : 0;
      const locType = acc <= 50 ? "precise_gps" : "approximate_network";
      const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${lat.toFixed(6)},${lng.toFixed(6)}`;

      latestGpsPosition = {
        latitude: lat,
        longitude: lng,
        accuracy_meters: acc,
        speed_kmh: speedKmh,
        timestamp: new Date(pos.timestamp).toISOString(),
        source: locType,
        maps_url: mapsUrl,
      };

      if (statusLine) {
        statusLine.innerHTML =
          `<strong>📍 Live Location Ready for Ambulance (${locType === "precise_gps" ? "Precise GPS" : "Approximate Network"}):</strong> ` +
          `<code>${lat.toFixed(5)}, ${lng.toFixed(5)}</code> (±${acc}m accuracy • Captured ${new Date().toLocaleTimeString()})`;
        stampEnglishBaseline(statusLine);
      }
      if (actionsDiv) {
        actionsDiv.innerHTML = `
          <a href="${mapsUrl}" target="_blank" rel="noopener noreferrer" class="btn-official-portal" style="font-size:0.78rem; padding:0.3rem 0.7rem;">
            🗺️ Open Live Coordinates in Google Maps ↗
          </a>
          <button type="button" class="btn-outline-small" id="copyGpsLinkBtn">
            📋 Copy GPS Link
          </button>
        `;
        actionsDiv.querySelector("#copyGpsLinkBtn")?.addEventListener("click", () => {
          navigator.clipboard.writeText(`${lat.toFixed(6)}, ${lng.toFixed(6)} (${mapsUrl})`);
        });
        stampEnglishBaseline(actionsDiv);
      }
      if (currentLang !== "en") await translateWholePageAndChat(currentLang);
    },
    async (err) => {
      const errMsg = String(err?.message || "");
      const isPolicyBlocked = /permissions?\s*policy|feature\s*policy|disabled\s*in\s*this\s*document/i.test(errMsg);

      if (!isPolicyBlocked && (err.code === 3 || err.code === 2) && retryCount < 1) {
        acquireLiveGpsCoordinates(userInitiated, retryCount + 1);
        return;
      }

      isGpsRequestInFlight = false;
      if (refreshBtn) refreshBtn.disabled = false;

      let diagnosticHtml = "";
      if (isPolicyBlocked) {
        diagnosticHtml =
          `<strong>⚠️ GPS Blocked by Document Permissions Policy:</strong> ` +
          `Restart <code>python backend\\app.py</code> and press <code>Ctrl+Shift+R</code> in Chrome/Edge at <code>http://127.0.0.1:5000</code>, or use the manual landmark box below.`;
      } else if (err.code === 1) {
        diagnosticHtml =
          `<strong>⚠️ GPS Permission Denied:</strong> ` +
          `Allow Location in your browser address bar, or enter your landmark below for automatic ambulance sharing.`;
      } else {
        diagnosticHtml =
          `<strong>⚠️ GPS Signal Unavailable (${errMsg || "Timeout"}):</strong> ` +
          `Using manual landmark fallback below for automatic ambulance location sharing.`;
      }

      if (statusLine) {
        statusLine.innerHTML = diagnosticHtml;
        stampEnglishBaseline(statusLine);
      }

      if (manualInput && manualInput.value.trim()) {
        updateManualLandmarkFallbackStatus(manualInput.value.trim());
      }

      if (currentLang !== "en") await translateWholePageAndChat(currentLang);
    },
    geoOptions
  );
}

function startIncidentCountdownWorkflow(triggerSource, sensorPayload) {
  if (sosCountdownTimer) clearInterval(sosCountdownTimer);

  acquireLiveGpsCoordinates(false, 0);
  activeIncidentUuid = `sos-${Date.now()}`;
  sosRemainingSeconds = AUTO_SOS_COUNTDOWN_SECONDS;

  const modal = document.getElementById("sosCountdownModal");
  const secSpan = document.getElementById("sosCountdownSeconds");
  const headline = document.getElementById("sosAlertHeadline");
  const details = document.getElementById("sosAlertDetails");
  const isSim = document.getElementById("sosSafeSimulationToggle")?.checked ?? false;

  if (modal) modal.hidden = false;
  if (secSpan) secSpan.textContent = String(sosRemainingSeconds);
  if (headline) {
    headline.textContent =
      triggerSource === "manual_sos_button"
        ? "🚨 MANUAL SOS — REVIEW EMERGENCY CALL & SHARE LOCATION"
        : "🚨 IMPACT DETECTED — REVIEW SOS ALERT";
    if (headline.firstChild) headline.firstChild._origEn = headline.textContent;
  }
  if (details) {
    details.textContent = isSim
      ? "SAFE SIMULATION MODE: In 8 seconds, location will be auto-shared to backend without dialing 108. Click 'CANCEL — I AM SAFE' to abort."
      : "Acquiring live GPS. In 8 seconds, Nova Healthtech will AUTOMATICALLY place a direct call to the saved emergency contact and transmit your location. Click 'CANCEL — I AM SAFE' immediately if this is a false alarm!";
    if (details.firstChild) details.firstChild._origEn = details.textContent;
  }

  playSosAlertBeep();

  sosCountdownTimer = setInterval(async () => {
    sosRemainingSeconds -= 1;
    if (secSpan) secSpan.textContent = String(Math.max(0, sosRemainingSeconds));
    if (sosRemainingSeconds > 0) {
      playSosAlertBeep();
    }
    if (sosRemainingSeconds <= 0) {
      clearInterval(sosCountdownTimer);
      sosCountdownTimer = null;
      await executeSosEscalation(triggerSource, sensorPayload);
    }
  }, 1000);
}

async function cancelActiveSosWorkflow(reasonText) {
  if (sosCountdownTimer) {
    clearInterval(sosCountdownTimer);
    sosCountdownTimer = null;
  }
  isDropConfirmationModalOpen = false;
  const modal = document.getElementById("sosCountdownModal");
  const reportBox = document.getElementById("sosDispatchReportBox");
  if (modal) modal.hidden = true;

  if (activeIncidentUuid) {
    try {
      await fetch(`${API_BASE_URL}/api/sos/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ incident_uuid: activeIncidentUuid, reason: reasonText }),
      });
    } catch (e) {}
  }

  if (reportBox) {
    reportBox.hidden = false;
    reportBox.innerHTML = `
      <p style="color:#49E6C4; font-weight:700;">
        ✓ 8-Second Countdown Cancelled (${reasonText}). Automatic ambulance call &amp; location transmission aborted.
      </p>
    `;
    stampEnglishBaseline(reportBox);
    if (currentLang !== "en") await translateWholePageAndChat(currentLang);
  }
}

function triggerAutomaticAmbulanceCall() {
  const savedNumber = window.__getSavedSosAutoCallNumber
    ? String(window.__getSavedSosAutoCallNumber() || "").replace(/[^0-9+]/g, "")
    : "";
  if (!savedNumber || !/^\+?[0-9]{7,15}$/.test(savedNumber)) {
    if (typeof showNotice === "function") showNotice("No valid emergency contact is saved. No call was placed.", "warning");
    return;
  }
  try {
    if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.placeDirectCall === "function") {
      // The Android bridge resolves the destination again from the native saved-contact store.
      window.NovaAndroidBridge.placeDirectCall(savedNumber);
      return;
    }
    // Browsers cannot place calls silently. Never open a dialer as an automatic-call fallback.
    if (typeof showNotice === "function") {
      showNotice("Automatic SOS calling is available in the installed Android app. A browser cannot place a call without user interaction.", "warning");
    }
  } catch (e) {
    if (typeof showNotice === "function") {
      showNotice("Automatic calling could not start. Check the installed Android app and Phone permission.", "error");
    }
  }
}

async function executeSosEscalation(triggerSource, sensorPayload) {
  const incidentId = activeIncidentUuid || `sos-${Date.now()}`;
  if (isSosEscalationInFlight || executedIncidentUuids.has(incidentId)) {
    return;
  }
  isSosEscalationInFlight = true;
  executedIncidentUuids.add(incidentId);

  const isSim = document.getElementById("sosSafeSimulationToggle")?.checked ?? false;
  const manualLoc = document.getElementById("sosManualAddressInput")?.value.trim() || "";
  const modal = document.getElementById("sosCountdownModal");
  const reportBox = document.getElementById("sosDispatchReportBox");
  if (modal) modal.hidden = true;

  const hasGps = latestGpsPosition && latestGpsPosition.latitude !== null && latestGpsPosition.longitude !== null;
  const locSource = hasGps
    ? latestGpsPosition.source
    : manualLoc
    ? "manual_landmark_fallback"
    : "unavailable";

  const payload = {
    incident_uuid: incidentId,
    trigger_source: triggerSource,
    is_simulation: isSim,
    auto_triggered_after_8s: true,
    place_direct_phone_call: !isSim,
    target_ambulance_number: (window.__getSavedSosAutoCallNumber ? window.__getSavedSosAutoCallNumber() : ""),
    latitude: hasGps ? latestGpsPosition.latitude : null,
    longitude: hasGps ? latestGpsPosition.longitude : null,
    accuracy_meters: hasGps ? latestGpsPosition.accuracy_meters : null,
    location_source: locSource,
    manual_location_text: manualLoc,
    sensor_data: sensorPayload || {},
  };

  try {
    const res = await fetch(`${API_BASE_URL}/api/sos/incident`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    const inc = data.incident || {};
    const loc = inc.location || {};

    const locDescription =
      loc.latitude !== null && loc.latitude !== undefined
        ? `${Number(loc.latitude).toFixed(5)}, ${Number(loc.longitude).toFixed(5)} (±${loc.accuracy_meters || "?"}m accuracy)`
        : loc.manual_location_text
        ? `Manual Landmark: "${loc.manual_location_text}"`
        : "Location pending";

    const emergencyPacketText = `EMERGENCY SOS LOCATION — Incident: ${inc.incident_uuid} | Coordinates: ${locDescription} | Map: ${loc.maps_url || "N/A"}`;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(emergencyPacketText).catch(() => {});
    }

    speakAssistantResponse(
      `Emergency SOS countdown complete. Open the phone dialer to review the emergency number and share location ${locDescription}.`,
      currentLang
    );

    if (reportBox) {
      reportBox.hidden = false;
      reportBox.innerHTML = `
        <div class="recommendation-item">
          <span class="recommendation-match">${
            inc.is_simulation
              ? "🧪 8s AUTO-SHARE SIMULATION COMPLETED"
              : "🚨 8s COUNTDOWN COMPLETE — SAVED-CONTACT CALL & LOCATION SHARED"
          }</span>
          <h4>Incident Reference: ${inc.incident_uuid}</h4>
          <p><strong>Direct Ambulance Call Status:</strong> ${
            inc.direct_call_placed
              ? "🟢 Automatic call requested for the saved emergency contact."
              : inc.is_simulation
              ? "Simulation Mode checked — call suppressed for safe testing."
              : "Automatic call requested for the saved emergency contact after the 8-second countdown."
          }</p>
          <p><strong>Location Automatically Shared with Ambulance:</strong> <code>${locDescription}</code> (${loc.location_source})</p>
          <p><strong>Dispatch Telemetry Status:</strong> ${inc.dispatch_status_message}</p>
          <div style="display:flex; flex-wrap:wrap; gap:0.5rem; margin-top:0.55rem;">
            <a href="tel:108" class="btn-emergency">📞 Redial 108 (Ambulance)</a>
            <a href="tel:112" class="btn-emergency btn-emergency--secondary">📞 Call 112 (ERSS)</a>
            ${
              loc.maps_url
                ? `<a href="${loc.maps_url}" target="_blank" rel="noopener noreferrer" class="btn-official-portal">🗺️ Shared Ambulance Map Link ↗</a>`
                : ""
            }
          </div>
        </div>
      `;
      stampEnglishBaseline(reportBox);
      if (currentLang !== "en") await translateWholePageAndChat(currentLang);
    }

    if (!isSim && !inc.direct_call_placed) {
      triggerAutomaticAmbulanceCall();
    }
  } catch (err) {
    if (reportBox) {
      reportBox.hidden = false;
      reportBox.innerHTML = `<p><strong>🚨 8s Countdown Complete (Offline Mode):</strong> Review the emergency number in your phone dialer and tap Call.</p>`;
      stampEnglishBaseline(reportBox);
    }
    if (!isSim) {
      triggerAutomaticAmbulanceCall();
    }
  } finally {
    isSosEscalationInFlight = false;
  }
}

async function loadTrustedContactsUI() {
  const container = document.getElementById("trustedContactsList");
  if (!container) return;
  try {
    const res = await fetch(`${API_BASE_URL}/api/sos/contacts`);
    if (!res.ok) return;
    const data = await res.json();
    cachedTrustedContacts = data.contacts || [];
    container.replaceChildren();

    if (cachedTrustedContacts.length === 0) {
      container.innerHTML = `<p class="small-note text-muted">No trusted contacts configured yet.</p>`;
      stampEnglishBaseline(container);
      return;
    }

    cachedTrustedContacts.forEach((c) => {
      const row = document.createElement("div");
      row.className = "med-card";
      row.style.marginBottom = "0.45rem";
      row.innerHTML = `
        <div class="med-card__info">
          <h4>${c.contact_name}</h4>
          <span class="small-note">📞 ${c.phone_number} • Auto-Notified on SOS</span>
        </div>
        <div class="med-card__actions">
          <a href="tel:${c.phone_number}" class="btn-outline-small">📞 Call</a>
          <button type="button" class="btn-delete-med">Remove</button>
        </div>
      `;
      row.querySelector(".btn-delete-med").addEventListener("click", async () => {
        await fetch(`${API_BASE_URL}/api/sos/contacts/${c.id}`, { method: "DELETE" });
        await loadTrustedContactsUI();
        if (currentLang !== "en") await translateWholePageAndChat(currentLang);
      });
      container.appendChild(row);
    });
    stampEnglishBaseline(container);
  } catch (e) {}
}

// ============================================================================
// MODULE 1: NOVA AI ASSISTANT CHAT
// ============================================================================

function initAssistantChatModule() {
  const form = document.getElementById("assistantChatForm");
  const chatContainer = document.querySelector(".chat-container");
  if (!form || !chatContainer) return;

  if (!document.getElementById("apiKeySetupBar")) {
    const keyBar = document.createElement("div");
    keyBar.id = "apiKeySetupBar";
    keyBar.className = "ai-status-bar";
    keyBar.innerHTML = `
      <strong id="apiKeyStatusLabel" class="ai-status-bar__online">🟢 AI is Online</strong>
      <span class="ai-status-bar__mode">🟢 AI Online • Live Web Search</span>
    `;
    chatContainer.insertBefore(keyBar, chatContainer.firstChild);
    stampEnglishBaseline(keyBar);
  }

  if (!document.getElementById("quickPromptsBar")) {
    const chipBar = document.createElement("div");
    chipBar.id = "quickPromptsBar";
    chipBar.className = "quick-prompts-bar";
    chatContainer.insertBefore(chipBar, form);
  }

  renderQuickPromptChips();
  resetAssistantGreeting();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const chatInput = document.getElementById("chatInput");
    const message = chatInput.value.trim();
    if (!message) return;
    await sendUserSymptomMessage(message, message);
  });
}

function renderQuickPromptChips() {
  const chipBar = document.getElementById("quickPromptsBar");
  if (!chipBar) return;
  chipBar.replaceChildren();

  DEFAULT_PROMPTS.forEach((enPrompt) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-outline-small quick-prompt-chip";
    btn.dataset.origPromptEn = enPrompt;
    btn.textContent = enPrompt;
    btn.addEventListener("click", () => sendUserSymptomMessage(btn.textContent, btn.dataset.origPromptEn));
    chipBar.appendChild(btn);
  });
  stampEnglishBaseline(chipBar);
}

async function sendUserSymptomMessage(displayMessage, queryForBackend) {
  const chatInput = document.getElementById("chatInput");
  chatInput.value = "";

  appendChatMessage("user", displayMessage, "", queryForBackend || displayMessage);
  const actualQuery = normalizeDigitsToAscii(queryForBackend || displayMessage);
  chatHistory.push({ role: "user", text: actualQuery });

  const sendBtn = document.getElementById("chatSendBtn");
  if (sendBtn) sendBtn.disabled = true;

  const meta = LANG_META[currentLang] || LANG_META.en;
  const typingBubble = appendChatMessage(
    "assistant",
    `🌐 Nova AI (${meta.nativeName})...`,
    "🟢 AI Online • Live Web Search"
  );

  try {
    const res = await fetch(`${API_BASE_URL}/api/assistant/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: actualQuery,
        lang: currentLang,
        history: chatHistory.slice(-6),
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (typingBubble) typingBubble.remove();

    if (data.ai_response && data.ai_response.reply) {
      const replyWithDigits = convertDigitsToNative(data.ai_response.reply, currentLang);
      const englishBase = data.ai_response.english_reply || data.ai_response.reply;
      chatHistory.push({ role: "assistant", text: englishBase });
      appendChatMessage(
        "assistant",
        replyWithDigits,
        "🟢 AI Online • Live Web Search",
        englishBase
      );
    }
  } catch (err) {
    if (typingBubble) typingBubble.remove();
    appendChatMessage(
      "assistant",
      "Please ensure `python backend\\app.py` is running in your terminal.",
      "Connection Notice"
    );
  } finally {
    if (sendBtn) sendBtn.disabled = false;
  }
}

function resetAssistantGreeting() {
  const chatMessages = document.getElementById("chatMessages");
  if (!chatMessages) return;
  chatMessages.replaceChildren();
  chatHistory = [];
  const englishGreeting =
    "Namaste! I am **Nova AI**, your 22-Language All-India Health & Medicine Assistant.\n" +
    "• **Ask about any Disease, Mental Health Condition or Symptom:** I will give you the **Causes, Symptoms, Diagnostic Tests, Precautions, Doctor/Specialist Recommendations, and Emergency Hospital Helplines**, and ask **where you live** to show hospitals near you!\n" +
    "• **Ask about any Medicine (Brand + `mg` + Specifier):** (e.g., *Lithonex 450 XL, Dolo 650, Zerodol-SP, Pan-D*) for its active salt, uses, when to take it, and safety guidance.\n" +
    "• **Tell me your City or State:** Type your city or state name anytime to see **Participating Hospitals & Nearby Medicine Stores**!";
  appendChatMessage("assistant", englishGreeting, "🟢 AI Online • Live Web Search", englishGreeting);
}

function formatRichBubbleContent(bubbleEl, rawText) {
  bubbleEl.replaceChildren();
  const lines = String(rawText).split("\n");
  lines.forEach((line, idx) => {
    const parts = line.split(/(\*\*.*?\*\*)/g);
    parts.forEach((part) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        const strong = document.createElement("strong");
        strong.textContent = part.slice(2, -2);
        bubbleEl.appendChild(strong);
      } else {
        bubbleEl.appendChild(document.createTextNode(part));
      }
    });
    if (idx < lines.length - 1) bubbleEl.appendChild(document.createElement("br"));
  });
}

function appendChatMessage(role, text, disclaimer, origEnglishSource) {
  const container = document.getElementById("chatMessages");
  if (!container) return null;

  const msgDiv = document.createElement("div");
  msgDiv.className = `chat-msg chat-msg--${role}`;

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble";
  bubble.dataset.rawMessageText = text;
  bubble._origEnglishText = origEnglishSource || text;
  formatRichBubbleContent(bubble, text);
  msgDiv.appendChild(bubble);

  if (role === "assistant") {
    const metaDiv = document.createElement("div");
    metaDiv.className = "chat-msg-meta";

    const speakBtn = document.createElement("button");
    speakBtn.type = "button";
    speakBtn.className = "btn-speak-text";
    speakBtn.textContent = "🔊 Listen";
    speakBtn.addEventListener("click", () => speakAssistantResponse(bubble.textContent, currentLang));

    const discSmall = document.createElement("span");
    discSmall.textContent = disclaimer || "🟢 AI Online • Live Web Search";

    metaDiv.append(speakBtn, discSmall);
    stampEnglishBaseline(metaDiv);
    msgDiv.appendChild(metaDiv);
  }

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
  return msgDiv;
}

function initVoiceEngine() {
  const micBtn = document.getElementById("voiceMicBtn");
  const voiceNotice = document.getElementById("voiceStatusText");
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition || !micBtn) return;

  speechRecognition = new SpeechRecognition();
  speechRecognition.continuous = false;
  speechRecognition.interimResults = false;
  speechRecognition.lang = SPEECH_LANG_MAP[currentLang] || "en-IN";

  speechRecognition.onstart = () => {
    isRecordingVoice = true;
    micBtn.classList.add("is-recording");
    if (voiceNotice) voiceNotice.textContent = "🎤 Listening...";
  };

  speechRecognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    document.getElementById("chatInput").value = transcript;
    if (voiceNotice) voiceNotice.textContent = `🎤 "${transcript}"`;
  };

  speechRecognition.onend = () => {
    isRecordingVoice = false;
    micBtn.classList.remove("is-recording");
  };

  micBtn.addEventListener("click", () => {
    if (isRecordingVoice) speechRecognition.stop();
    else {
      speechRecognition.lang = SPEECH_LANG_MAP[currentLang] || "en-IN";
      try { speechRecognition.start(); } catch (err) {}
    }
  });
}

function speakAssistantResponse(text, langCode) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const cleaned = text.replace(/[*#_`•⚠️🏥🌐🔗🟢💊📍📞🩺👨‍⚕️🚨]/g, "");
  const utterance = new SpeechSynthesisUtterance(cleaned);
  utterance.lang = SPEECH_LANG_MAP[langCode] || "en-IN";
  utterance.rate = 0.96;
  window.speechSynthesis.speak(utterance);
}

// ============================================================================
// MODULE 2: OFFLINE HEALTH GUIDES
// ============================================================================

async function initHealthGuideModule() {
  const tabs = document.querySelectorAll(".guide-tab-btn");
  tabs.forEach((tab) => {
    tab.addEventListener("click", async () => {
      tabs.forEach((tBtn) => tBtn.classList.remove("active"));
      tab.classList.add("active");
      renderHealthGuides(tab.getAttribute("data-category"));
      if (currentLang !== "en") await translateWholePageAndChat(currentLang);
    });
  });
  await loadHealthGuides();
}

async function loadHealthGuides() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/guide/catalog?lang=en`);
    const data = await res.json();
    cachedHealthGuides = data.guides || [];
  } catch (err) {
    cachedHealthGuides = [];
  }
  renderHealthGuides("all");
}

function renderHealthGuides(categoryFilter = "all") {
  const container = document.getElementById("healthGuideGrid");
  if (!container) return;
  container.replaceChildren();

  const filtered =
    categoryFilter === "all"
      ? cachedHealthGuides
      : cachedHealthGuides.filter((g) => g.category === categoryFilter);

  filtered.forEach((guide) => {
    const stepsHtml = (guide.key_steps || []).map((s) => `<li>${s}</li>`).join("");
    const card = document.createElement("article");
    card.className = `guide-card ${guide.emergency_warning ? "guide-card--emergency" : ""}`;
    card.innerHTML = `
      <h3>${guide.title}</h3>
      <p class="guide-summary">${guide.summary}</p>
      <ol class="guide-steps-list">${stepsHtml}</ol>
      <div class="guide-warning-box"><p><strong>Warning:</strong> ${guide.warning}</p></div>
    `;
    container.appendChild(card);
  });
  stampEnglishBaseline(container);
}

// ============================================================================
// MODULE 3 & 4: CONSULTATIONS & REMINDERS
// ============================================================================

async function initConsultationsModule() {
  const form = document.getElementById("consultationForm");
  if (!form) return;

  const distSelect = document.getElementById("consultDistrict");
  if (distSelect) {
    const allLocations = ALL_INDIA_CITIES_AND_STATES_LIST();
    distSelect.innerHTML = allLocations.map((c) => `<option value="${c}">${c}</option>`).join("");
    stampEnglishBaseline(distSelect);
  }

  await loadRecentConsultations();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const cleanPhone = normalizeDigitsToAscii(document.getElementById("consultPhone").value.trim());
    const payload = {
      patient_name: document.getElementById("consultName").value.trim(),
      contact_number: cleanPhone,
      district: document.getElementById("consultDistrict").value,
      preferred_language: document.getElementById("consultLang").value,
      symptoms_summary: document.getElementById("consultSymptoms").value.trim(),
    };
    const res = await fetch(`${API_BASE_URL}/api/consultations/request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      form.reset();
      await loadRecentConsultations();
      if (currentLang !== "en") await translateWholePageAndChat(currentLang);
    } else {
      showNotice("Please enter a valid 10-digit mobile number.", "error");
    }
  });
}

function ALL_INDIA_CITIES_AND_STATES_LIST() {
  return [
    "Bhavnagar (Gujarat)", "Ahmedabad (Gujarat)", "Rajkot (Gujarat)", "Vadodara (Gujarat)", "Surat (Gujarat)",
    "Mumbai (Maharashtra)", "Pune (Maharashtra)", "Nagpur (Maharashtra)", "New Delhi (Delhi NCR)",
    "Bengaluru (Karnataka)", "Mysuru (Karnataka)", "Chennai (Tamil Nadu)", "Madurai (Tamil Nadu)",
    "Hyderabad (Telangana)", "Visakhapatnam (Andhra Pradesh)", "Kolkata (West Bengal)",
    "Lucknow (Uttar Pradesh)", "Varanasi (Uttar Pradesh)", "Jaipur (Rajasthan)", "Jodhpur (Rajasthan)",
    "Bhopal (Madhya Pradesh)", "Indore (Madhya Pradesh)", "Patna (Bihar)", "Bhubaneswar (Odisha)",
    "Cuttack (Odisha)", "Chandigarh (Chandigarh UT)", "Amritsar (Punjab)", "Rohtak (Haryana)",
    "Shimla (Himachal Pradesh)", "Rishikesh / Dehradun (Uttarakhand)", "Srinagar / Jammu (Jammu & Kashmir)",
    "Leh (Ladakh)", "Ranchi (Jharkhand)", "Raipur (Chhattisgarh)", "Panaji (Goa)",
    "Thiruvananthapuram (Kerala)", "Kochi (Kerala)", "Guwahati (Assam)", "Itanagar (Arunachal Pradesh)",
    "Imphal (Manipur)", "Shillong (Meghalaya)", "Aizawl (Mizoram)", "Kohima (Nagaland)",
    "Gangtok (Sikkim)", "Agartala (Tripura)", "Puducherry (Puducherry UT)", "Port Blair (Andaman & Nicobar)",
    "Silvassa (Dadra & Nagar Haveli and Daman & Diu)", "Kavaratti (Lakshadweep)"
  ];
}

async function loadRecentConsultations() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/consultations/recent`, { cache: "no-store" });
    if (!res.ok) return;
    const data = await res.json();
    const container = document.getElementById("consultationList");
    if (!container) return;
    container.replaceChildren();

    const list = data.consultations || [];
    if (list.length === 0) {
      const p = document.createElement("p");
      p.className = "text-muted";
      p.textContent = "No active requests submitted yet.";
      container.appendChild(p);
      stampEnglishBaseline(container);
      return;
    }

    list.forEach((item) => {
      const card = document.createElement("div");
      card.className = "consult-card";
      card.innerHTML = `
        <div class="consult-card__top">
          <h4>${item.patient_name} (${item.district})</h4>
          <div style="display:flex; align-items:center; gap:0.45rem;">
            <span class="consult-badge">${item.status}</span>
            <button type="button" class="btn-delete-med">Remove</button>
          </div>
        </div>
        <p class="consult-symptoms"><strong>Symptoms:</strong> ${item.symptoms_summary}</p>
        <span class="consult-meta small-note"><strong>Callback:</strong> ${item.contact_masked}</span>
      `;

      card.querySelector(".btn-delete-med").addEventListener("click", async () => {
        await fetch(`${API_BASE_URL}/api/consultations/${item.id}`, { method: "DELETE" });
        await loadRecentConsultations();
        if (currentLang !== "en") await translateWholePageAndChat(currentLang);
      });

      container.appendChild(card);
    });
    stampEnglishBaseline(container);
  } catch (err) {}
}

async function initRemindersModule() {
  const form = document.getElementById("medicationReminderForm");
  const testVoiceBtn = document.getElementById("testVoiceAlertBtn");
  if (!form) return;

  await loadActiveReminders();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = normalizeDigitsToAscii(document.getElementById("medName").value.trim());
    const dosage = normalizeDigitsToAscii(document.getElementById("medDosage").value.trim());
    const time = document.getElementById("medTime").value;
    const meal = document.getElementById("medMeal").value;
    const notes = normalizeDigitsToAscii(document.getElementById("medNotes").value.trim());
    const confirmBox = document.getElementById("medDoctorConfirm");
    if (!confirmBox || !confirmBox.checked) return;

    const payload = {
      medicine_name: name,
      prescribed_dosage: dosage,
      scheduled_time: time,
      meal_relation: meal,
      doctor_prescribed_confirmed: true,
      notes: notes,
    };

    const response = await fetch(`${API_BASE_URL}/api/reminders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (response.ok) {
      form.reset();
      await loadActiveReminders();
      if (currentLang !== "en") await translateWholePageAndChat(currentLang);
    }
  });

  if (testVoiceBtn) {
    testVoiceBtn.addEventListener("click", () => {
      speakAssistantResponse(
        "Medication adherence reminder: Please remember to take your doctor-prescribed medicine on time with clean water.",
        currentLang
      );
    });
  }
}

async function loadActiveReminders() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/reminders`, { cache: "no-store" });
    if (!res.ok) return;
    const data = await res.json();
    renderRemindersUI(data.reminders || []);
  } catch (err) {}
}

function renderRemindersUI(list) {
  const container = document.getElementById("remindersContainer");
  if (!container) return;
  container.replaceChildren();

  if (!list || list.length === 0) {
    const p = document.createElement("p");
    p.className = "text-muted";
    p.textContent = "No medication reminders scheduled yet. Add your doctor-prescribed doses on the left.";
    container.appendChild(p);
    stampEnglishBaseline(container);
    return;
  }

  list.forEach((med) => {
    const card = document.createElement("div");
    card.className = "med-card";
    card.innerHTML = `
      <div class="med-card__info">
        <h4>${med.medicine_name}</h4>
        <span class="med-timing-badge">⏰ ${med.scheduled_time} • ${med.meal_relation.replace("_", " ")}</span>
        <p class="med-meta small-note"><strong>Prescribed Dose:</strong> ${med.prescribed_dosage}${med.notes ? " • " + med.notes : ""}</p>
      </div>
      <div class="med-card__actions">
        <button type="button" class="btn-mark-taken ${med.last_taken_at_utc ? "is-taken" : ""}">${med.last_taken_at_utc ? "✓ Taken Today" : "✓ Mark Taken"}</button>
        <button type="button" class="btn-delete-med">Remove</button>
      </div>
    `;

    const [markBtn, delBtn] = card.querySelectorAll("button");
    markBtn.addEventListener("click", async () => {
      await fetch(`${API_BASE_URL}/api/reminders/${med.id}/taken`, { method: "POST" });
      await loadActiveReminders();
      if (currentLang !== "en") await translateWholePageAndChat(currentLang);
    });
    delBtn.addEventListener("click", async () => {
      await fetch(`${API_BASE_URL}/api/reminders/${med.id}`, { method: "DELETE" });
      await loadActiveReminders();
      if (currentLang !== "en") await translateWholePageAndChat(currentLang);
    });

    container.appendChild(card);
  });
  stampEnglishBaseline(container);
}

// ============================================================================
// MODULE 5: EMERGENCY TRIAGE CHECKER
// ============================================================================

async function initTriageModule() {
  const triageForm = document.getElementById("triageForm");
  const resetBtn = document.getElementById("triageResetBtn");
  if (!triageForm) return;

  try {
    const r = await fetch(`${API_BASE_URL}/api/triage/rules`);
    const d = await r.json();
    cachedTriageRules = d.rules || [];
    renderTriageCheckboxes();
  } catch (e) {}

  triageForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const checked = Array.from(
      document.querySelectorAll('#triageCheckboxesGrid input[type="checkbox"]:checked')
    ).map((c) => c.value);
    const text = normalizeDigitsToAscii(document.getElementById("triageFreeText").value.trim());

    const res = await fetch(`${API_BASE_URL}/api/triage/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selected_rule_ids: checked, free_text: text, lang: currentLang }),
    });
    const data = await res.json();
    const container = document.getElementById("triageResultContainer");
    container.hidden = false;
    container.className = `triage-result ${
      data.triage.urgency_level === "CRITICAL_EMERGENCY" ? "triage-result--critical" : "triage-result--safe"
    }`;
    container.innerHTML = `<h3>${data.triage.headline}</h3><p>${data.triage.summary}</p>`;
    stampEnglishBaseline(container);
    if (currentLang !== "en") await translateWholePageAndChat(currentLang);
  });

  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      triageForm.reset();
      const container = document.getElementById("triageResultContainer");
      if (container) container.hidden = true;
    });
  }
}

function renderTriageCheckboxes() {
  const grid = document.getElementById("triageCheckboxesGrid");
  if (!grid || !cachedTriageRules || !cachedTriageRules.length) return;
  grid.replaceChildren();

  cachedTriageRules.forEach((rule) => {
    const loc = rule.i18n.en;
    const lbl = document.createElement("label");
    lbl.className = "triage-symptom-option";
    lbl.innerHTML = `<input type="checkbox" value="${rule.id}"> <span>${loc.label}</span>`;
    grid.appendChild(lbl);
  });
  stampEnglishBaseline(grid);
}

// ============================================================================
// MODULE 6: ALL-INDIA HOSPITALS & PHARMACIES (ALL 36 STATES & UTs + GOOGLE MAPS)
// ============================================================================

async function initBenefitsAndAllIndiaDirectories() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/benefits/catalog`);
    cachedBenefitsData = await res.json();
  } catch (err) {
    cachedBenefitsData = { schemes: [], all_hospitals: [], all_medicine_stores: [] };
  }

  renderSchemesGrid();
  setupAllIndiaHospitalFinderUI();
  setupNearbyMedicineStoresUI();

  const screenerForm = document.getElementById("benefitsScreenerForm");
  if (screenerForm) {
    screenerForm.addEventListener("submit", handleScreenerSubmit);
  }
}

function renderSchemesGrid() {
  const grid = document.getElementById("schemesGrid");
  if (!grid || !cachedBenefitsData) return;
  grid.replaceChildren();

  (cachedBenefitsData.schemes || []).forEach((s) => {
    const loc = s.i18n.en;
    const card = document.createElement("article");
    card.className = "scheme-card";
    card.innerHTML = `
      <div>
        <span class="scheme-badge">${s.badge}</span>
        <h3>${loc.title}</h3>
        <p class="scheme-coverage">${loc.coverage}</p>
        <p class="scheme-summary">${loc.summary}</p>
      </div>
      <div>
        <a href="${s.official_portal_url}" target="_blank" rel="noopener noreferrer" class="btn-official-portal">${s.official_portal_label} ↗</a>
      </div>
    `;
    grid.appendChild(card);
  });
  stampEnglishBaseline(grid);
}

function setupAllIndiaHospitalFinderUI() {
  const allHospitals = cachedBenefitsData.all_hospitals || cachedBenefitsData.hospitals || [];
  const stateSelect = document.getElementById("hospStateFilter");
  const citySelect = document.getElementById("hospCityFilter");
  const searchInput = document.getElementById("hospitalSearchInput");

  if (!stateSelect || !citySelect) return;

  const uniqueStates = Array.from(new Set(allHospitals.map((h) => h.state))).sort();
  stateSelect.innerHTML =
    `<option value="all">All Indian States & UTs (${uniqueStates.length} States/UTs)</option>` +
    uniqueStates.map((st) => `<option value="${st}">${st}</option>`).join("");
  stampEnglishBaseline(stateSelect);

  function populateHospitalCities(selectedState) {
    const filteredForCities =
      selectedState === "all"
        ? allHospitals
        : allHospitals.filter((h) => h.state.toLowerCase() === selectedState.toLowerCase());
    const uniqueCities = Array.from(new Set(filteredForCities.map((h) => h.city))).sort();
    citySelect.innerHTML =
      `<option value="all">All Cities (${uniqueCities.length} Cities)</option>` +
      uniqueCities.map((ct) => `<option value="${ct}">${ct}</option>`).join("");
    stampEnglishBaseline(citySelect);
  }

  populateHospitalCities("all");
  renderHospitalList();

  stateSelect.addEventListener("change", async () => {
    populateHospitalCities(stateSelect.value);
    renderHospitalList();
    if (currentLang !== "en") await translateWholePageAndChat(currentLang);
  });

  citySelect.addEventListener("change", async () => {
    renderHospitalList();
    if (currentLang !== "en") await translateWholePageAndChat(currentLang);
  });

  if (searchInput) {
    searchInput.addEventListener("input", async () => {
      renderHospitalList();
      if (currentLang !== "en") await translateWholePageAndChat(currentLang);
    });
  }
}

function renderHospitalList() {
  const container = document.getElementById("hospitalListContainer");
  if (!container || !cachedBenefitsData) return;
  container.replaceChildren();

  const allHospitals = cachedBenefitsData.all_hospitals || cachedBenefitsData.hospitals || [];
  const stateVal = document.getElementById("hospStateFilter")?.value || "all";
  const cityVal = document.getElementById("hospCityFilter")?.value || "all";
  const qClean = (document.getElementById("hospitalSearchInput")?.value || "").toLowerCase().trim();

  let filtered = allHospitals.filter((h) => {
    const matchState = stateVal === "all" || h.state.toLowerCase() === stateVal.toLowerCase();
    const matchCity = cityVal === "all" || h.city.toLowerCase() === cityVal.toLowerCase();
    const matchQuery =
      !qClean ||
      h.name.toLowerCase().includes(qClean) ||
      h.city.toLowerCase().includes(qClean) ||
      h.state.toLowerCase().includes(qClean) ||
      (h.pin_code && h.pin_code.includes(qClean)) ||
      (h.specialties && h.specialties.toLowerCase().includes(qClean));
    return matchState && matchCity && matchQuery;
  });

  if (stateVal === "all" && cityVal === "all" && !qClean) {
    filtered = filtered.slice(0, 10);
  }

  filtered.forEach((h) => {
    let phoneActionHtml = "";
    if (h.phone_general) {
      phoneActionHtml += `<a href="tel:${h.phone_general}" class="btn-emergency btn-emergency--secondary" style="font-size:0.75rem; padding:0.25rem 0.6rem;">📞 General Desk: ${h.phone_general}</a> `;
    }
    if (h.phone_emergency) {
      phoneActionHtml += `<a href="tel:${h.phone_emergency}" class="btn-emergency" style="font-size:0.75rem; padding:0.25rem 0.6rem;">🚨 Emergency: ${h.phone_emergency}</a>`;
    }

    const mapsQuery = encodeURIComponent(`${h.name}, ${h.address}, ${h.city}, ${h.state} ${h.pin_code || ""}`);
    const mapsUrl = h.maps_url || `https://www.google.com/maps/search/?api=1&query=${mapsQuery}`;

    const div = document.createElement("div");
    div.className = "hospital-card";
    div.innerHTML = `
      <div class="hospital-card__top">
        <h4>${h.name}</h4>
        <span class="scheme-badge">${h.city}, ${h.state}</span>
      </div>
      <p class="hospital-meta"><strong>${h.facility_category || "Hospital"}</strong> • ${h.schemes}</p>
      <p class="hospital-desk small-note">📍 ${h.address} ${h.pin_code ? "• PIN: " + h.pin_code : ""}</p>
      ${h.specialties ? `<p class="hospital-meta small-note">🏥 Specialties: ${h.specialties}</p>` : ""}
      <div style="display:flex; flex-wrap:wrap; gap:0.4rem; margin-top:0.4rem;">
        ${phoneActionHtml}
        <a href="${mapsUrl}" target="_blank" rel="noopener noreferrer" class="btn-official-portal" style="font-size:0.75rem; padding:0.25rem 0.6rem;">🗺️ Map &amp; Directions ↗</a>
        ${h.website ? `<a href="${h.website}" target="_blank" rel="noopener noreferrer" class="btn-official-portal" style="font-size:0.75rem; padding:0.25rem 0.6rem;">Official Website ↗</a>` : ""}
      </div>
    `;
    container.appendChild(div);
  });
  stampEnglishBaseline(container);
}

function setupNearbyMedicineStoresUI() {
  const allStores = cachedBenefitsData.all_medicine_stores || [];
  const stateSelect = document.getElementById("storeStateFilter");
  const citySelect = document.getElementById("storeCityFilter");
  const searchInput = document.getElementById("storeSearchInput");

  if (!stateSelect || !citySelect) return;

  const uniqueStates = Array.from(new Set(allStores.map((s) => s.state))).sort();
  stateSelect.innerHTML =
    `<option value="all">All Indian States & UTs (${uniqueStates.length} States/UTs)</option>` +
    uniqueStates.map((st) => `<option value="${st}">${st}</option>`).join("");
  stampEnglishBaseline(stateSelect);

  function populateStoreCities(selectedState) {
    const filteredForCities =
      selectedState === "all"
        ? allStores
        : allStores.filter((s) => s.state.toLowerCase() === selectedState.toLowerCase());
    const uniqueCities = Array.from(new Set(filteredForCities.map((s) => s.city))).sort();
    citySelect.innerHTML =
      `<option value="all">All Cities (${uniqueCities.length} Cities)</option>` +
      uniqueCities.map((ct) => `<option value="${ct}">${ct}</option>`).join("");
    stampEnglishBaseline(citySelect);
  }

  populateStoreCities("all");
  renderMedicineStoresCards();

  stateSelect.addEventListener("change", async () => {
    populateStoreCities(stateSelect.value);
    renderMedicineStoresCards();
    if (currentLang !== "en") await translateWholePageAndChat(currentLang);
  });

  citySelect.addEventListener("change", async () => {
    renderMedicineStoresCards();
    if (currentLang !== "en") await translateWholePageAndChat(currentLang);
  });

  if (searchInput) {
    searchInput.addEventListener("input", async () => {
      renderMedicineStoresCards();
      if (currentLang !== "en") await translateWholePageAndChat(currentLang);
    });
  }
}

function renderMedicineStoresCards() {
  const grid = document.getElementById("medicineStoresGrid");
  if (!grid || !cachedBenefitsData) return;
  grid.replaceChildren();

  const allStores = cachedBenefitsData.all_medicine_stores || [];
  const stateVal = document.getElementById("storeStateFilter")?.value || "all";
  const cityVal = document.getElementById("storeCityFilter")?.value || "all";
  const qClean = (document.getElementById("storeSearchInput")?.value || "").toLowerCase().trim();

  let filtered = allStores.filter((s) => {
    const matchState = stateVal === "all" || s.state.toLowerCase() === stateVal.toLowerCase();
    const matchCity = cityVal === "all" || s.city.toLowerCase() === cityVal.toLowerCase();
    const matchQuery =
      !qClean ||
      s.name.toLowerCase().includes(qClean) ||
      s.city.toLowerCase().includes(qClean) ||
      s.state.toLowerCase().includes(qClean) ||
      (s.address && s.address.toLowerCase().includes(qClean)) ||
      (s.pin_code && s.pin_code.includes(qClean));
    return matchState && matchCity && matchQuery;
  });

  if (stateVal === "all" && cityVal === "all" && !qClean) {
    filtered = filtered.slice(0, 9);
  }

  filtered.forEach((store) => {
    const phoneHtml = store.phone_contact
      ? `<a href="tel:${store.phone_contact}" class="btn-emergency btn-emergency--secondary" style="font-size:0.75rem; padding:0.25rem 0.6rem;">📞 Call Pharmacy: ${store.phone_contact}</a>`
      : `<span class="text-muted small-note">📞 Contact number unavailable</span>`;

    const storeMapsQuery = encodeURIComponent(
      `${store.name}, ${store.address}, ${store.city}, ${store.state} ${store.pin_code || ""}`
    );
    const storeMapsUrl = store.maps_url || `https://www.google.com/maps/search/?api=1&query=${storeMapsQuery}`;

    const card = document.createElement("article");
    card.className = "scheme-card";
    card.innerHTML = `
      <div>
        <span class="scheme-badge">📍 ${store.city}, ${store.state}</span>
        <h3 style="margin-top:0.4rem;">${store.name}</h3>
        <p class="scheme-coverage">${store.facility_category || "Pharmacy"}</p>
        <p class="scheme-summary"><strong>⏰ Hours:</strong> ${store.hours}</p>
        <p class="scheme-summary"><strong>🏥 Address:</strong> ${store.address} ${store.pin_code ? "• PIN: " + store.pin_code : ""}</p>
        ${store.services ? `<p class="scheme-summary">💊 ${store.services}</p>` : ""}
      </div>
      <div style="display:flex; flex-wrap:wrap; gap:0.4rem; margin-top:0.6rem;">
        ${phoneHtml}
        <a href="${storeMapsUrl}" target="_blank" rel="noopener noreferrer" class="btn-official-portal" style="font-size:0.75rem; padding:0.25rem 0.6rem;">🗺️ Map &amp; Directions ↗</a>
      </div>
    `;
    grid.appendChild(card);
  });
  stampEnglishBaseline(grid);
}

// ============================================================================
// PRELIMINARY SCHEME SCREENER
// ============================================================================

async function handleScreenerSubmit(event) {
  event.preventDefault();

  const ageGroup = document.getElementById("screenAge")?.value || "under_60";
  const stateResidency = document.getElementById("screenState")?.value || "gujarat";
  const incomeBracket = document.getElementById("screenIncome")?.value || "under_4_lakh";
  const hasSenior70Plus = ageGroup === "70_plus";
  const submitBtn = document.getElementById("screenerSubmitBtn");

  if (submitBtn) submitBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE_URL}/api/benefits/screen`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        age_group: ageGroup,
        state_residency: stateResidency,
        income_bracket: incomeBracket,
        has_senior_70_plus: hasSenior70Plus,
      }),
    });

    if (!res.ok) throw new Error("Screener error");
    const data = await res.json();
    renderScreenerResults(data.guidance);
    if (currentLang !== "en") await translateWholePageAndChat(currentLang);
  } catch (err) {} finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

function renderScreenerResults(guidance) {
  const resultBox = document.getElementById("screenerResultBox");
  if (!resultBox || !guidance) return;

  resultBox.replaceChildren();
  resultBox.hidden = false;

  const disclaimer = document.createElement("p");
  disclaimer.className = "screener-disclaimer";
  disclaimer.textContent = guidance.disclaimer;
  resultBox.appendChild(disclaimer);

  (guidance.recommendations || []).forEach((rec) => {
    const item = document.createElement("div");
    item.className = "recommendation-item";
    item.innerHTML = `
      <span class="recommendation-match">${rec.match_level}</span>
      <h4>${rec.title}</h4>
      <p>${rec.reason}</p>
      <p class="recommendation-next-step"><strong>Official Next Step:</strong> ${rec.next_step}</p>
    `;
    resultBox.appendChild(item);
  });
  stampEnglishBaseline(resultBox);
}

function initRuralStressTester() {
  const runBtn = document.getElementById("runStressTestBtn");
  if (!runBtn) return;
  runBtn.addEventListener("click", async () => {
    const terminal = document.getElementById("stressTestTerminal");
    const output = document.getElementById("stressTerminalOutput");
    terminal.hidden = false;
    output.textContent = "Testing 2G latency & 22-language endpoints...\n";
    const res = await fetch(`${API_BASE_URL}/api/health`);
    const data = await res.json();
    output.textContent += `[PASS] Status: ${data.status} | 22 Languages Active | All 36 States & UTs Active`;
    stampEnglishBaseline(terminal);
    if (currentLang !== "en") await translateWholePageAndChat(currentLang);
  });
}

async function runHealthCheck() {
  const statusBadge = document.getElementById("statusBadge");
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, { cache: "no-store" });
    await res.json();
    if (statusBadge) statusBadge.className = "status-pill status-pill--online";
  } catch (err) {
    if (statusBadge) statusBadge.className = "status-pill status-pill--offline";
  }
}

async function initHealthCheck() {
  const btn = document.getElementById("verifyBtn");
  if (btn) btn.addEventListener("click", runHealthCheck);
  await runHealthCheck();
}

// ============================================================================
// AUTOMATIC ACCIDENT DETECTION & 8-SECOND AUTO-DIAL SAVED EMERGENCY CONTACT MODULE
// ============================================================================

function triggerAutomaticAmbulanceCall() {
  const savedNumber = window.__getSavedSosAutoCallNumber
    ? String(window.__getSavedSosAutoCallNumber() || "").replace(/[^0-9+]/g, "")
    : "";
  if (!savedNumber || !/^\+?[0-9]{7,15}$/.test(savedNumber)) {
    if (typeof showNotice === "function") showNotice("No valid emergency contact is saved. No call was placed.", "warning");
    return;
  }
  try {
    if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.placeDirectCall === "function") {
      // The Android bridge resolves the destination again from the native saved-contact store.
      window.NovaAndroidBridge.placeDirectCall(savedNumber);
      return;
    }
    // Browsers cannot place calls silently. Never open a dialer as an automatic-call fallback.
    if (typeof showNotice === "function") {
      showNotice("Automatic SOS calling is available in the installed Android app. A browser cannot place a call without user interaction.", "warning");
    }
  } catch (e) {
    if (typeof showNotice === "function") {
      showNotice("Automatic calling could not start. Check the installed Android app and Phone permission.", "error");
    }
  }
}

async function executeSosEscalation(triggerSource, sensorPayload) {
    const incidentId = activeIncidentUuid || `sos-${Date.now()}`;
    if (isSosEscalationInFlight || executedIncidentUuids.has(incidentId)) {
        return;
    }
    isSosEscalationInFlight = true;
    executedIncidentUuids.add(incidentId);

    const isSim = document.getElementById("sosSafeSimulationToggle")?.checked ?? false;
    const manualLoc = document.getElementById("sosManualAddressInput")?.value.trim() || "";
    const modal = document.getElementById("sosCountdownModal");
    const reportBox = document.getElementById("sosDispatchReportBox");
    if (modal) modal.hidden = true;

    const hasGps = latestGpsPosition && latestGpsPosition.latitude !== null && latestGpsPosition.longitude !== null;
    const locSource = hasGps ? latestGpsPosition.source : (manualLoc ? "manual_landmark_fallback" : "unavailable");

    const payload = {
        incident_uuid: incidentId,
        trigger_source: triggerSource,
        is_simulation: isSim,
        auto_triggered_after_8s: true,
        place_direct_phone_call: !isSim,
        target_ambulance_number: (window.__getSavedSosAutoCallNumber ? window.__getSavedSosAutoCallNumber() : ""),
        latitude: hasGps ? latestGpsPosition.latitude : null,
        longitude: hasGps ? latestGpsPosition.longitude : null,
        accuracy_meters: hasGps ? latestGpsPosition.accuracy_meters : null,
        location_source: locSource,
        manual_location_text: manualLoc,
        sensor_data: sensorPayload || {}
    };

    try {
        const res = await fetch(`${API_BASE_URL}/api/sos/incident`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        const inc = data.incident || {};

        if (!isSim) {
            triggerAutomaticAmbulanceCall();
        }
    } catch (err) {
        if (!isSim) {
            triggerAutomaticAmbulanceCall();
        }
    } finally {
        isSosEscalationInFlight = false;
    }
}

// ============================================================================
// NOVA HEALTHTECH: CONFIGURABLE EMERGENCY SOS AUTO-CALL NUMBER ONLY
// - Scoped strictly to the automatic SOS countdown calling feature.
// - Supports entering, saving, changing, and removing a valid phone number.
// - Does NOT auto-call 108 if no number is saved; prompts user to configure one.
// ============================================================================
(function initNovaSosAutoCallContactSetting() {
    const SOS_NUM_KEY = "nova_custom_sos_auto_call_number";

    function normalizePhone(raw) {
        return String(raw || "").replace(/[\s\-()]/g, "").trim();
    }

    function isValidPhone(raw) {
        const clean = normalizePhone(raw);
        return /^\+?[0-9]{7,15}$/.test(clean);
    }

    window.__getSavedSosAutoCallNumber = function () {
        try {
            if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.getPermanentEmergencyNumber === "function") {
                const nativeNum = normalizePhone(window.NovaAndroidBridge.getPermanentEmergencyNumber());
                if (isValidPhone(nativeNum)) return nativeNum;
                if (nativeNum === "") return "";
            }
        } catch (e) {}
        const localNum = normalizePhone(localStorage.getItem(SOS_NUM_KEY) || "");
        return isValidPhone(localNum) ? localNum : "";
    };

    window.__saveSosAutoCallNumber = function (rawNumber) {
        const clean = normalizePhone(rawNumber);
        if (!isValidPhone(clean)) {
            return { ok: false, message: "Please enter a valid 7 to 15 digit emergency contact phone number." };
        }
        localStorage.setItem(SOS_NUM_KEY, clean);
        try {
            if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.savePermanentEmergencyContact === "function") {
                window.NovaAndroidBridge.savePermanentEmergencyContact("Emergency Contact", clean);
            }
        } catch (e) {}
        window.__refreshSosAutoCallSettingUi();
        return { ok: true, number: clean };
    };

    window.__removeSosAutoCallNumber = function () {
        localStorage.removeItem(SOS_NUM_KEY);
        try {
            if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.removePermanentEmergencyContact === "function") {
                window.NovaAndroidBridge.removePermanentEmergencyContact();
            }
        } catch (e) {}
        const inputEl = document.getElementById("novaCustomSosNumInput");
        if (inputEl) inputEl.value = "";
        window.__refreshSosAutoCallSettingUi();
    };

    window.__refreshSosAutoCallSettingUi = function () {
        const savedNum = window.__getSavedSosAutoCallNumber();
        const badgeEl = document.getElementById("novaCustomSosStatusBadge");
        const removeBtn = document.getElementById("novaCustomSosRemoveBtn");
        const inputEl = document.getElementById("novaCustomSosNumInput");

        if (inputEl && document.activeElement !== inputEl && savedNum) {
            inputEl.value = savedNum;
        }
        if (badgeEl) {
            if (savedNum) {
                badgeEl.style.background = "rgba(16, 185, 129, 0.22)";
                badgeEl.style.color = "#6ee7b7";
                badgeEl.textContent = "📞 Saved Auto-Call Number: " + savedNum;
            } else {
                badgeEl.style.background = "rgba(244, 63, 94, 0.22)";
                badgeEl.style.color = "#fda4af";
                badgeEl.textContent = "⚠️ No Number Saved (Auto-Call Paused)";
            }
        }
        if (removeBtn) {
            removeBtn.style.display = savedNum ? "inline-block" : "none";
        }
    };

    function renderSosAutoCallSettingBox() {
        if (document.getElementById("novaCustomSosSettingCard")) {
            window.__refreshSosAutoCallSettingUi();
            return;
        }
        const triggerBtn = document.getElementById("triggerSosBtn") || document.querySelector('button[class*="btn-emergency"]');
        if (!triggerBtn || !triggerBtn.parentElement) return;

        const savedNum = window.__getSavedSosAutoCallNumber();
        const card = document.createElement("div");
        card.id = "novaCustomSosSettingCard";
        card.style.cssText = "margin: 0.85rem 0; padding: 0.9rem; border-radius: 12px; background: rgba(15, 23, 42, 0.65); border: 1px solid rgba(20, 184, 166, 0.45);";
        card.innerHTML =
            '<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.4rem; margin-bottom:0.45rem;">' +
                '<strong style="color:#5eead4; font-size:0.9rem;">📌 Emergency SOS Auto-Call Contact Number</strong>' +
                '<span id="novaCustomSosStatusBadge" style="font-size:0.76rem; padding:0.2rem 0.55rem; border-radius:999px; font-weight:600;"></span>' +
            '</div>' +
            '<p id="novaCustomSosFeedbackText" style="font-size:0.78rem; color:#cbd5e1; margin:0 0 0.55rem 0;">' +
                'Enter and save the phone number to call automatically when the SOS countdown expires. Remains saved until you change or remove it.' +
            '</p>' +
            '<div style="display:flex; flex-wrap:wrap; gap:0.5rem;">' +
                '<input id="novaCustomSosNumInput" type="tel" placeholder="Enter phone number (e.g. 9876543210)" value="' + savedNum.replace(/"/g, "&quot;") + '" ' +
                    'style="flex:1 1 170px; padding:0.5rem 0.7rem; border-radius:8px; border:1px solid rgba(148,163,184,0.35); background:#0f172a; color:#f8fafc; font-size:0.85rem;" />' +
                '<button id="novaCustomSosSaveBtn" type="button" ' +
                    'style="padding:0.5rem 0.9rem; border-radius:8px; border:none; background:#10b981; color:#042f2e; font-weight:700; font-size:0.82rem; cursor:pointer;">' +
                    '💾 Save / Change' +
                '</button>' +
                '<button id="novaCustomSosRemoveBtn" type="button" ' +
                    'style="padding:0.5rem 0.8rem; border-radius:8px; border:1px solid rgba(244,63,94,0.55); background:rgba(244,63,94,0.15); color:#fda4af; font-weight:600; font-size:0.8rem; cursor:pointer;">' +
                    '🗑️ Remove' +
                '</button>' +
            '</div>';

        triggerBtn.parentElement.insertBefore(card, triggerBtn.nextSibling);

        document.getElementById("novaCustomSosSaveBtn")?.addEventListener("click", function () {
            const val = document.getElementById("novaCustomSosNumInput")?.value || "";
            const res = window.__saveSosAutoCallNumber(val);
            const fb = document.getElementById("novaCustomSosFeedbackText");
            if (fb) {
                fb.style.color = res.ok ? "#6ee7b7" : "#fda4af";
                fb.textContent = res.ok
                    ? "✅ Emergency SOS Auto-Call Number saved: " + res.number
                    : "⚠️ " + res.message;
            }
        });

        document.getElementById("novaCustomSosRemoveBtn")?.addEventListener("click", function () {
            window.__removeSosAutoCallNumber();
            const fb = document.getElementById("novaCustomSosFeedbackText");
            if (fb) {
                fb.style.color = "#fcd34d";
                fb.textContent = "⚠️ Emergency contact removed. Please configure an emergency contact number to enable SOS auto-calling.";
            }
        });

        window.__refreshSosAutoCallSettingUi();
    }

    // Intercept ONLY the SOS countdown expiration call (/api/sos/incident)
    const baseFetch = window.fetch.bind(window);
    window.fetch = async function (input, init) {
        const rawUrl = typeof input === "string" ? input : (input && input.url) || "";
        if (rawUrl.includes("/api/sos/incident") && init && init.body) {
            try {
                const bodyObj = JSON.parse(init.body);
                const savedNum = window.__getSavedSosAutoCallNumber();
                bodyObj.target_ambulance_number = savedNum || "UNCONFIGURED";
                init.body = JSON.stringify(bodyObj);

                const res = await baseFetch(input, init);
                const clone = res.clone();
                let data = {};
                try { data = await clone.json(); } catch (e) {}

                if (!bodyObj.is_simulation) {
                    if (!savedNum) {
                        const fb = document.getElementById("novaCustomSosFeedbackText");
                        if (fb) {
                            fb.style.color = "#fda4af";
                            fb.textContent = "⚠️ SOS Auto-Call Paused: No emergency contact number is saved. Please enter and save a valid phone number below.";
                        }
                        showNotice("No emergency contact is configured. Save a trusted contact before using the SOS dialer action.", "warning");
                        document.getElementById("novaCustomSosNumInput")?.focus();
                    }
                }

                if (data && data.incident) {
                    if (!savedNum) {
                        data.incident.direct_call_placed = false;
                        data.incident.dispatch_status_message = "⚠️ Auto-Call Not Placed: No emergency contact configured. Please save an emergency contact phone number in the SOS setting above.";
                     } else if (!bodyObj.is_simulation) {
                         data.incident.direct_call_placed = false;
                         data.incident.dispatch_status_message = "Saved-contact call request is handled by Android; call completion is not confirmed by the website.";
                     }
                    return new Response(JSON.stringify(data), {
                        status: res.status,
                        headers: { "Content-Type": "application/json" }
                    });
                }
                return res;
            } catch (e) {}
        }
        return baseFetch(input, init);
    };

    // Prevent script.js's built-in countdown expiration from redirecting to tel:108 when using the website
    window.addEventListener("click", function (ev) {
        const a = ev.target && ev.target.closest ? ev.target.closest("a[href='tel:108']") : null;
        if (a && a.id === "autoDialHiddenLink") {
            ev.preventDefault();
        }
    }, true);

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => setTimeout(renderSosAutoCallSettingBox, 100));
    } else {
        setTimeout(renderSosAutoCallSettingBox, 100);
    }
})();



// === NOVA CONFIGURABLE SOS AUTO-CALL NUMBER (WEBSITE + APK) ===
(function() {
    if (window.__novaCustomSosWebInstalled) return;
    window.__novaCustomSosWebInstalled = true;
    const SOS_NUM_KEY = "nova_custom_sos_auto_call_number";
    const SOS_NAME_KEY = "nova_custom_sos_auto_call_name";
    if (localStorage.getItem(SOS_NUM_KEY) === "108") localStorage.removeItem(SOS_NUM_KEY);

    function norm(r) { return String(r || "").replace(/[\s\-()]/g, "").trim(); }
    function valid(r) { const c = norm(r); return c !== "108" && /^\+?[0-9]{7,15}$/.test(c); }

    window.__getSavedSosAutoCallNumber = window.__getSavedSosAutoCallNumber || function() {
        const n = norm(localStorage.getItem(SOS_NUM_KEY) || "");
        return valid(n) ? n : "";
    };
    window.__getSavedSosAutoCallName = window.__getSavedSosAutoCallName || function() {
        return localStorage.getItem(SOS_NAME_KEY) || "My Emergency Contact";
    };

    // Explicit tel:108 links remain emergency-service links; auto-call uses the native saved-contact bridge.

    function refreshUi() {
        const sNum = window.__getSavedSosAutoCallNumber();
        const sName = window.__getSavedSosAutoCallName();
        const b = document.getElementById("novaCustomSosStatusBadge");
        const rBtn = document.getElementById("novaCustomSosRemoveBtn");
        if (b) {
            b.style.background = sNum ? "rgba(16,185,129,0.22)" : "rgba(244,63,94,0.22)";
            b.style.color = sNum ? "#6ee7b7" : "#fda4af";
            b.textContent = sNum ? ("📞 Active SOS Number: " + sName + " (" + sNum + ")") : "⚠️ No Number Saved Yet";
        }
        if (rBtn) rBtn.style.display = sNum ? "inline-block" : "none";
    }

    function injectBox() {
        if (document.getElementById("novaCustomSosSettingCard")) { refreshUi(); return; }
        const btn = document.getElementById("triggerSosBtn") || document.querySelector('button[class*="btn-emergency"]');
        if (!btn || !btn.parentElement) return;
        const sNum = window.__getSavedSosAutoCallNumber();
        const sName = window.__getSavedSosAutoCallName();
        const card = document.createElement("div");
        card.id = "novaCustomSosSettingCard";
        card.style.cssText = "margin:0.85rem 0;padding:0.9rem;border-radius:12px;background:rgba(15,23,42,0.65);border:1.5px solid rgba(20,184,166,0.45);";
        card.innerHTML =
            '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.4rem;margin-bottom:0.45rem;">' +
                '<strong style="color:#5eead4;font-size:0.92rem;">📌 Permanent SOS Auto-Call Number</strong>' +
                '<span id="novaCustomSosStatusBadge" style="font-size:0.76rem;padding:0.2rem 0.55rem;border-radius:999px;font-weight:600;"></span>' +
            '</div>' +
            '<p id="novaCustomSosFeedbackText" style="font-size:0.78rem;color:#cbd5e1;margin:0 0 0.55rem 0;">Save anyone\'s phone number permanently below. When SOS is triggered, it will ONLY call this saved number until you change or remove it.</p>' +
            '<div style="display:flex;flex-wrap:wrap;gap:0.5rem;">' +
                '<input id="novaCustomSosNameInput" type="text" placeholder="Name (e.g. Mom / Friend)" value="' + (sNum ? sName : '') + '" style="flex:1 1 130px;padding:0.5rem 0.7rem;border-radius:8px;border:1px solid rgba(148,163,184,0.35);background:#0f172a;color:#f8fafc;font-size:0.85rem;" />' +
                '<input id="novaCustomSosNumInput" type="tel" placeholder="Phone Number (e.g. 9876543210)" value="' + sNum + '" style="flex:1 1 160px;padding:0.5rem 0.7rem;border-radius:8px;border:1px solid rgba(148,163,184,0.35);background:#0f172a;color:#f8fafc;font-size:0.85rem;" />' +
                '<button id="novaCustomSosSaveBtn" type="button" style="padding:0.5rem 0.9rem;border-radius:8px;border:none;background:#10b981;color:#042f2e;font-weight:700;font-size:0.82rem;cursor:pointer;">💾 Save Permanently</button>' +
                '<button id="novaCustomSosRemoveBtn" type="button" style="padding:0.5rem 0.8rem;border-radius:8px;border:1px solid rgba(244,63,94,0.55);background:rgba(244,63,94,0.15);color:#fda4af;font-weight:600;font-size:0.8rem;cursor:pointer;">🗑️ Remove / Change</button>' +
            '</div>';
        btn.parentElement.insertBefore(card, btn.nextSibling);

        document.getElementById("novaCustomSosSaveBtn")?.addEventListener("click", function() {
            const nm = (document.getElementById("novaCustomSosNameInput")?.value || "").trim() || "My Emergency Contact";
            const ph = norm(document.getElementById("novaCustomSosNumInput")?.value || "");
            const fb = document.getElementById("novaCustomSosFeedbackText");
            if (!valid(ph)) {
                if (fb) { fb.style.color = "#fda4af"; fb.textContent = "⚠️ Please enter a valid phone number."; }
                return;
            }
            localStorage.setItem(SOS_NUM_KEY, ph);
            localStorage.setItem(SOS_NAME_KEY, nm);
            if (window.NovaAndroidBridge?.savePermanentEmergencyContact) window.NovaAndroidBridge.savePermanentEmergencyContact(nm, ph);
            if (fb) { fb.style.color = "#6ee7b7"; fb.textContent = "✅ Saved Permanently: " + nm + " (" + ph + ")"; }
            refreshUi();
        });

        document.getElementById("novaCustomSosRemoveBtn")?.addEventListener("click", function() {
            localStorage.removeItem(SOS_NUM_KEY);
            localStorage.removeItem(SOS_NAME_KEY);
            if (window.NovaAndroidBridge?.removePermanentEmergencyContact) window.NovaAndroidBridge.removePermanentEmergencyContact();
            const i1 = document.getElementById("novaCustomSosNumInput"); if (i1) i1.value = "";
            const i2 = document.getElementById("novaCustomSosNameInput"); if (i2) i2.value = "";
            const fb = document.getElementById("novaCustomSosFeedbackText");
            if (fb) { fb.style.color = "#fcd34d"; fb.textContent = "⚠️ Number removed. Enter a new number to enable SOS auto-calling."; }
            refreshUi();
        });
        refreshUi();
    }

    const origFetch = window.fetch.bind(window);
    window.fetch = async function(input, init) {
        const u = typeof input === "string" ? input : (input?.url || "");
        if (u.includes("/api/sos/incident") && init?.body) {
            try {
                const b = JSON.parse(init.body);
                const sNum = window.__getSavedSosAutoCallNumber();
                b.target_ambulance_number = sNum || "UNCONFIGURED";
                init.body = JSON.stringify(b);
                const r = await origFetch(input, init);
                if (!b.is_simulation) {
                    if (sNum) { window.location.href = "tel:" + sNum; }
                    else { showNotice("⚠️ No emergency number saved! Please enter and save a phone number in the 'Permanent SOS Auto-Call Number' box."); }
                }
                return r;
            } catch (e) {}
        }
        return origFetch(input, init);
    };

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => setTimeout(injectBox, 100));
    else setTimeout(injectBox, 100);
})();






// === NOVA HUMAN CLINICAL THEME & SMART AI ===

        (function() {
            const SOS_NUM_KEY = "nova_custom_sos_auto_call_number";
            const SOS_NAME_KEY = "nova_custom_sos_auto_call_name";
            const BG_AUTOCALL_KEY = "nova_bg_autocall_when_closed";
            const USERS_DB_KEY = "nova_users_db_v2";
            const ACTIVE_USER_KEY = "nova_active_user_v2";
            const CHAT_MEMORY_KEY = "nova_chat_memory_sessions_v2";

            // 1. Block JS devicemotion from reacting to swirls, wind, rotation, or desk drops
            if (!window.__novaSensorFilterInstalled) {
                window.__novaSensorFilterInstalled = true;
                const origAddEventListener = window.addEventListener.bind(window);
                window.addEventListener = function(type, listener, options) {
                    if (type === "deviceorientation" || type === "deviceorientationabsolute") {
                        return;
                    }
                    if (type === "devicemotion" && typeof listener === "function") {
                        let swirlCount = 0;
                        const wrappedMotion = function(ev) {
                            const acc = ev.acceleration;
                            if (!acc) return;
                            const lx = Number(acc.x || 0), ly = Number(acc.y || 0), lz = Number(acc.z || 0);
                            const mag = Math.sqrt(lx * lx + ly * ly + lz * lz);
                            if (mag > 12 && mag < 45) { swirlCount++; }
                            else if (mag < 4) { swirlCount = 0; }
                            if (mag < 58 || swirlCount > 5) return;
                            return listener.apply(this, arguments);
                        };
                        return origAddEventListener(type, wrappedMotion, options);
                    }
                    return origAddEventListener(type, wrappedMotion, options);
                };
            }

            // 2. HUMAN-CRAFTED CLINICAL DAYLIGHT THEME (Zero Neon AI Colors, Zero Top Gap, Fixed Card Buttons)
            function injectHumanClinicalTheme() {
                if (document.getElementById("novaHumanClinicalTheme")) return;
                ["novaMaterial3DarkTheme", "novaSwissEditorialInlineStyle", "novaPrecisionFixStyle"].forEach(id => {
                    const el = document.getElementById(id);
                    if (el) el.remove();
                });

                const style = document.createElement("style");
                style.id = "novaHumanClinicalTheme";
                style.textContent =
                    ':root {' +
                    '  --hc-bg: #F4F6F9;' +
                    '  --hc-card: #FFFFFF;' +
                    '  --hc-subtle: #F8FAFC;' +
                    '  --hc-border: #E2E8F0;' +
                    '  --hc-text: #1E293B;' +
                    '  --hc-muted: #475569;' +
                    '  --hc-blue: #1D4ED8;' +
                    '  --hc-blue-hover: #1E40AF;' +
                    '  --hc-teal: #0F766E;' +
                    '  --hc-red: #DC2626;' +
                    '  --hc-font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;' +
                    '}' +
                    '*, *::before, *::after { box-sizing: border-box; }' +
                    'html, body {' +
                    '  margin: 0 !important; padding: 0 !important;' +
                    '  padding-top: 52px !important;' +
                    '  background: var(--hc-bg) !important;' +
                    '  background-image: none !important;' +
                    '  color: var(--hc-text) !important;' +
                    '  font-family: var(--hc-font) !important;' +
                    '  font-size: 14.5px !important; line-height: 1.55 !important;' +
                    '}' +
                    /* Eliminate sticky popups and top gaps */
                    'header, .site-header, .top-bar, .app-header, .sticky-header, .emergency-banner, .top-emergency-strip {' +
                    '  position: static !important; top: auto !important; z-index: 1 !important;' +
                    '  margin-top: 0 !important; box-shadow: none !important; backdrop-filter: none !important;' +
                    '}' +
                    '.emergency-banner {' +
                    '  background: #FEF2F2 !important; color: #991B1B !important;' +
                    '  border-bottom: 1px solid #FECACA !important; padding: 0.75rem 1rem !important;' +
                    '}' +
                    '.emergency-banner p, .emergency-banner span { color: #7F1D1D !important; }' +
                    /* Hide the Offline Ready badge & leftover empty status dot */
                    '#swStatusBadge, [id*="offline" i], [class*="offline" i] { display: none !important; }' +
                    'main, .container, .app-shell {' +
                    '  max-width: 1080px !important; margin: 0 auto !important; padding: 0.75rem 0.9rem 3rem 0.9rem !important;' +
                    '}' +
                    'section, .card, .glass-card, .module-card, .panel {' +
                    '  background: var(--hc-card) !important; background-image: none !important;' +
                    '  border: 1px solid var(--hc-border) !important;' +
                    '  border-radius: 12px !important;' +
                    '  padding: 1.15rem !important;' +
                    '  margin-bottom: 0.85rem !important;' +
                    '  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05) !important;' +
                    '  max-width: 100% !important; overflow: hidden !important;' +
                    '}' +
                    '.scheme-card, article {' +
                    '  background: var(--hc-subtle) !important;' +
                    '  border: 1px solid var(--hc-border) !important;' +
                    '  border-radius: 10px !important;' +
                    '  padding: 1.1rem !important;' +
                    '  display: flex !important; flex-direction: column !important; justify-content: space-between !important;' +
                    '}' +
                    'h1, h2, h3, h4 { color: #F8FAFC !important; -webkit-text-fill-color: #F8FAFC !important; background: none !important; font-weight: 700 !important; letter-spacing: -0.015em !important; margin-top: 0 !important; }' +
                    'p, li, label, small, .scheme-summary, .scheme-coverage { color: #DCE6F2 !important; opacity: 1 !important; }' +
                     'main h1, main h2, main h3, main h4, main p, main li, main label, main small, .glass-panel h1, .glass-panel h2, .glass-panel h3, .glass-panel h4, .glass-panel p, .glass-panel li, .glass-panel label, .tool-box h3, .tool-box p, .tool-box label, .assistant-module h2, .assistant-module h3, .assistant-module p { color: #F1F5F9 !important; -webkit-text-fill-color: #F1F5F9 !important; opacity: 1 !important; }' +
                    '.scheme-badge, .status-pill {' +
                    '  background: #EFF6FF !important; color: var(--hc-blue) !important;' +
                    '  border: 1px solid #BFDBFE !important; border-radius: 6px !important;' +
                    '  padding: 0.22rem 0.6rem !important; font-size: 0.76rem !important; font-weight: 600 !important;' +
                    '  display: inline-block !important;' +
                    '}' +
                    'input[type="text"], input[type="tel"], input[type="password"], input[type="email"], input[type="time"], input[type="number"], select, textarea {' +
                    '  background: #FFFFFF !important; color: var(--hc-text) !important;' +
                    '  border: 1px solid #CBD5E1 !important; border-radius: 8px !important;' +
                    '  padding: 0.65rem 0.8rem !important; font-size: 0.92rem !important;' +
                    '  width: 100% !important; outline: none !important;' +
                    '}' +
                    'input:focus, select:focus, textarea:focus {' +
                    '  border-color: var(--hc-blue) !important; box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.12) !important;' +
                    '}' +
                    /* Fix Photo 3 button word-splitting & overflow */
                    'button, .btn, .btn-primary, .btn-secondary, .btn-official-portal, a.btn-emergency {' +
                    '  background: var(--hc-blue) !important; background-image: none !important;' +
                    '  color: #FFFFFF !important; border: none !important; border-radius: 8px !important;' +
                    '  padding: 0.65rem 1rem !important; font-weight: 600 !important; font-size: 0.85rem !important;' +
                    '  line-height: 1.3 !important; cursor: pointer !important;' +
                    '  display: inline-flex !important; align-items: center !important; justify-content: center !important;' +
                    '  gap: 0.35rem !important; text-decoration: none !important;' +
                    '  white-space: normal !important; word-break: normal !important; overflow-wrap: break-word !important;' +
                    '  text-align: center !important; max-width: 100% !important;' +
                    '}' +
                    '.scheme-card > div:last-child, article > div:last-child {' +
                    '  display: grid !important; grid-template-columns: 1fr !important; gap: 0.5rem !important; margin-top: 0.85rem !important;' +
                    '}' +
                    '.scheme-card a, .scheme-card button, article a, article button {' +
                    '  width: 100% !important; padding: 0.6rem 0.75rem !important; font-size: 0.83rem !important;' +
                    '}' +
                    '#triggerSosBtn, .btn-emergency--primary {' +
                    '  background: var(--hc-red) !important; color: #FFFFFF !important;' +
                    '  font-weight: 700 !important; width: 100% !important; padding: 0.85rem 1rem !important;' +
                    '}' +
                    '#toggleSensorBtn {' +
                    '  background: #F1F5F9 !important; color: #0F172A !important;' +
                    '  border: 1px solid #CBD5E1 !important; width: 100% !important; margin-top: 0.5rem !important;' +
                    '}' +
                    /* Chat messages readability */
                    '#chatMessages, .chat-messages {' +
                    '  background: #F8FAFC !important; border: 1px solid var(--hc-border) !important;' +
                    '  border-radius: 10px !important; padding: 0.9rem !important;' +
                    '}' +
                    '#chatMessages *, .chat-messages * { color: var(--hc-text) !important; }' +
                    /* Stacked Accordion Bars on Main Overview */
                    '.nova-accordion-header {' +
                    '  display: flex; justify-content: space-between; align-items: center;' +
                    '  width: 100%; cursor: pointer; padding: 0.3rem 0; user-select: none;' +
                    '}' +
                    '.nova-accordion-chevron {' +
                    '  font-size: 0.85rem; font-weight: 700; color: var(--hc-blue);' +
                    '  background: #EFF6FF; padding: 0.25rem 0.6rem; border-radius: 6px;' +
                    '}' +
                    /* Slim Fixed Top App Bar */
                    '#novaM3AppBar {' +
                    '  position: fixed; top: 0; left: 0; right: 0; height: 52px; z-index: 9990;' +
                    '  background: #FFFFFF; border-bottom: 1px solid var(--hc-border);' +
                    '  display: flex; align-items: center; justify-content: space-between; padding: 0 0.85rem;' +
                    '  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);' +
                    '}' +
                    '#novaDrawerBackdrop {' +
                    '  position: fixed; inset: 0; background: rgba(15, 23, 42, 0.45); z-index: 9995;' +
                    '  display: none; opacity: 0; transition: opacity 0.2s ease;' +
                    '}' +
                    '#novaDrawerPanel {' +
                    '  position: fixed; top: 0; left: 0; bottom: 0; width: 290px; max-width: 84vw;' +
                    '  background: #FFFFFF; border-right: 1px solid var(--hc-border); z-index: 9998;' +
                    '  transform: translateX(-102%); transition: transform 0.22s ease;' +
                    '  display: flex; flex-direction: column; overflow-y: auto; padding: 1rem 0.85rem;' +
                    '}' +
                    '.nova-drawer-item {' +
                    '  display: flex !important; align-items: center !important; justify-content: flex-start !important;' +
                    '  width: 100% !important; text-align: left !important;' +
                    '  padding: 0.7rem 0.85rem !important; margin-bottom: 0.3rem !important;' +
                    '  background: transparent !important; color: var(--hc-text) !important;' +
                    '  border-radius: 8px !important; font-weight: 600 !important; font-size: 0.88rem !important;' +
                    '}' +
                    '.nova-drawer-item.active, .nova-drawer-item:hover {' +
                    '  background: #EFF6FF !important; color: var(--hc-blue) !important;' +
                    '}' +
                    '#novaDedicatedAuthScreen {' +
                    '  position: fixed; inset: 0; z-index: 10000; background: rgba(15, 23, 42, 0.55);' +
                    '  display: none; align-items: center; justify-content: center; padding: 1rem; overflow-y: auto;' +
                    '}';
                (document.head || document.documentElement).appendChild(style);
            }

            injectHumanClinicalTheme();

            if (!window.__novaEngineInstalled) {
                window.__novaEngineInstalled = true;

                try {
                    Object.defineProperty(window, 'isSecureContext', { get: function() { return true; }, configurable: true });
                } catch (e) {}

                if (window.location.protocol === 'file:' && navigator.serviceWorker) {
                    navigator.serviceWorker.register = function() { return Promise.resolve({}); };
                }

                const REMOTE_API = "";
                const origFetch = window.fetch.bind(window);
                const transCache = {};

                if (localStorage.getItem(SOS_NUM_KEY) === "108") {
                    localStorage.removeItem(SOS_NUM_KEY);
                }

                function readStore(key, fallback) {
                    try {
                        if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.loadPersistentData === "function") {
                            const sqliteRaw = window.NovaAndroidBridge.loadPersistentData(key);
                            if (sqliteRaw && sqliteRaw.trim().length > 0) {
                                localStorage.setItem(key, sqliteRaw);
                                return JSON.parse(sqliteRaw);
                            }
                        }
                    } catch (e) {}
                    try {
                        const raw = localStorage.getItem(key);
                        return raw ? JSON.parse(raw) : fallback;
                    } catch (e) { return fallback; }
                }

                function writeStore(key, val) {
                    const str = JSON.stringify(val);
                    try { localStorage.setItem(key, str); } catch (e) {}
                    try {
                        if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.savePersistentData === "function") {
                            window.NovaAndroidBridge.savePersistentData(key, str);
                        }
                    } catch (e) {}
                }

                window.__getActiveUser = function() {
                    return readStore(ACTIVE_USER_KEY, null);
                };

                function getUserScopedKey(baseKey) {
                    const u = window.__getActiveUser();
                    return u && u.identifier ? (baseKey + "__" + u.identifier.toLowerCase()) : baseKey;
                }

                window.__openLoginDashboardScreen = function() {
                    if (window.__closeNavDrawer) window.__closeNavDrawer();
                    const scr = document.getElementById("novaDedicatedAuthScreen");
                    if (scr) {
                        scr.style.display = "flex";
                        window.__syncAppHeaderAndAuthUi();
                    }
                };

                window.__closeLoginDashboardScreen = function() {
                    const scr = document.getElementById("novaDedicatedAuthScreen");
                    if (scr) scr.style.display = "none";
                };

                window.__switchAuthTab = function(mode) {
                    const isSignup = mode === "signup";
                    const nameWrap = document.getElementById("novaAuthNameFieldWrap");
                    const titleEl = document.getElementById("novaAuthScreenTitle");
                    const submitBtn = document.getElementById("novaAuthPrimaryActionBtn");
                    const tabLogin = document.getElementById("novaAuthTabLogin");
                    const tabSignup = document.getElementById("novaAuthTabSignup");

                    if (nameWrap) nameWrap.style.display = isSignup ? "block" : "none";
                    if (titleEl) titleEl.textContent = isSignup ? "Create Your Nova Health Account" : "Sign In to Nova Healthtech";
                    if (submitBtn) {
                        submitBtn.textContent = isSignup ? "Create Permanent Account" : "Sign In Permanently";
                        submitBtn.setAttribute("data-mode", isSignup ? "signup" : "login");
                    }
                    if (tabLogin && tabSignup) {
                        tabLogin.style.background = isSignup ? "#F1F5F9" : "#1D4ED8";
                        tabLogin.style.color = isSignup ? "#475569" : "#FFFFFF";
                        tabSignup.style.background = isSignup ? "#1D4ED8" : "#F1F5F9";
                        tabSignup.style.color = isSignup ? "#FFFFFF" : "#475569";
                    }
                };

                window.__submitAuthForm = function() {
                    const submitBtn = document.getElementById("novaAuthPrimaryActionBtn");
                    const mode = submitBtn ? submitBtn.getAttribute("data-mode") : "login";
                    const name = (document.getElementById("novaAuthNameInput")?.value || "").trim();
                    const id = (document.getElementById("novaAuthIdInput")?.value || "").trim();
                    const pass = (document.getElementById("novaAuthPassInput")?.value || "").trim();
                    const age = (document.getElementById("novaAuthAgeInput")?.value || "").trim();
                    const msgEl = document.getElementById("novaAuthScreenFeedback");

                    const users = readStore(USERS_DB_KEY, []);

                    if (mode === "signup") {
                        if (!name || !id || pass.length < 4) {
                            if (msgEl) { msgEl.style.color = "#DC2626"; msgEl.textContent = "Please enter your full name, email/mobile, and a password (4+ chars)."; }
                            return;
                        }
                        if (users.some(u => u.identifier.toLowerCase() === id.toLowerCase())) {
                            if (msgEl) { msgEl.style.color = "#D97706"; msgEl.textContent = "Account already registered. Switching to Sign In..."; }
                            window.__switchAuthTab("login");
                            return;
                        }
                        const newUser = { name: name, identifier: id, password: pass, age: age, created_at: new Date().toISOString() };
                        users.push(newUser);
                        writeStore(USERS_DB_KEY, users);
                        writeStore(ACTIVE_USER_KEY, { name: name, identifier: id, age: age });
                    } else {
                        const found = users.find(u => u.identifier.toLowerCase() === id.toLowerCase() && u.password === pass);
                        if (!found) {
                            if (msgEl) { msgEl.style.color = "#DC2626"; msgEl.textContent = "Invalid email/mobile or password. Tap 'Sign Up' if you are new."; }
                            return;
                        }
                        writeStore(ACTIVE_USER_KEY, { name: found.name, identifier: found.identifier, age: found.age || "" });
                    }

                    if (msgEl) { msgEl.style.color = "#0F766E"; msgEl.textContent = "Signed in permanently!"; }
                    window.__syncAppHeaderAndAuthUi();
                    window.__renderChatMemoryArchive();
                    setTimeout(() => { window.__closeLoginDashboardScreen(); }, 350);
                };

                window.__handleNovaLogout = function() {
                    writeStore(ACTIVE_USER_KEY, null);
                    localStorage.removeItem(ACTIVE_USER_KEY);
                    window.__syncAppHeaderAndAuthUi();
                    window.__renderChatMemoryArchive();
                    window.__closeLoginDashboardScreen();
                };

                function normalizePhone(raw) {
                    return String(raw || '').replace(/[\s\-()]/g, '').trim();
                }

                function isValidPhone(raw) {
                    const c = normalizePhone(raw);
                    return c !== '108' && /^\+?[0-9]{7,15}$/.test(c);
                }

                window.__getSavedSosAutoCallNumber = function() {
                    try {
                        if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.getPermanentEmergencyNumber === 'function') {
                            const n = normalizePhone(window.NovaAndroidBridge.getPermanentEmergencyNumber());
                            if (isValidPhone(n)) return n;
                        }
                    } catch (e) {}
                    const scoped = normalizePhone(localStorage.getItem(getUserScopedKey(SOS_NUM_KEY)) || localStorage.getItem(SOS_NUM_KEY) || '');
                    return isValidPhone(scoped) ? scoped : '';
                };

                window.__getSavedSosAutoCallName = function() {
                    try {
                        if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.getPermanentEmergencyName === 'function') {
                            const nm = window.NovaAndroidBridge.getPermanentEmergencyName();
                            if (nm && nm.trim().length > 0) return nm.trim();
                        }
                    } catch (e) {}
                    return localStorage.getItem(getUserScopedKey(SOS_NAME_KEY)) || localStorage.getItem(SOS_NAME_KEY) || 'Emergency Contact';
                };

                window.__saveDbEmergencyNumber = function() {
                    const nameVal = (document.getElementById('novaDbSosNameInput')?.value || '').trim() || 'Emergency Contact';
                    const numVal = normalizePhone(document.getElementById('novaDbSosNumInput')?.value || '');
                    const fb = document.getElementById('novaDbSosFeedback');
                    if (!isValidPhone(numVal)) {
                        if (fb) { fb.style.color = '#DC2626'; fb.textContent = 'Please enter a valid 7 to 15 digit mobile number (not 108).'; }
                        return;
                    }
                    localStorage.setItem(SOS_NUM_KEY, numVal);
                    localStorage.setItem(SOS_NAME_KEY, nameVal);
                    localStorage.setItem(getUserScopedKey(SOS_NUM_KEY), numVal);
                    localStorage.setItem(getUserScopedKey(SOS_NAME_KEY), nameVal);
                    try {
                        if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.savePermanentEmergencyContact === 'function') {
                            window.NovaAndroidBridge.savePermanentEmergencyContact(nameVal, numVal);
                        }
                    } catch (e) {}
                    if (fb) { fb.style.color = '#0F766E'; fb.textContent = 'Saved in database. SOS can prompt you to open the dialer for ' + nameVal + ' (' + numVal + ').'; }
                    window.__syncAppHeaderAndAuthUi();
                };

                window.__removeDbEmergencyNumber = function() {
                    localStorage.removeItem(SOS_NUM_KEY);
                    localStorage.removeItem(SOS_NAME_KEY);
                    localStorage.removeItem(getUserScopedKey(SOS_NUM_KEY));
                    localStorage.removeItem(getUserScopedKey(SOS_NAME_KEY));
                    try {
                        if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.removePermanentEmergencyContact === 'function') {
                            window.NovaAndroidBridge.removePermanentEmergencyContact();
                        }
                    } catch (e) {}
                    const nIn = document.getElementById('novaDbSosNumInput'); if (nIn) nIn.value = '';
                    const nmIn = document.getElementById('novaDbSosNameInput'); if (nmIn) nmIn.value = '';
                    const fb = document.getElementById('novaDbSosFeedback');
                    if (fb) { fb.style.color = '#D97706'; fb.textContent = 'Number removed from database. Enter a new number above to enable SOS auto-calling.'; }
                    window.__syncAppHeaderAndAuthUi();
                };

                window.__callDbEmergencyNumberNow = function() {
                    const saved = window.__getSavedSosAutoCallNumber();
                    if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.placeDirectCall === 'function') {
                        window.NovaAndroidBridge.placeDirectCall(saved);
                    } else if (saved) {
                        window.location.href = 'tel:' + saved;
                    } else {
                        showNotice('No emergency number saved yet. Add a trusted contact in Emergency Settings.', 'warning');
                    }
                };

                window.__isBackgroundAutoCallEnabled = function() {
                    try {
                        if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.isBackgroundAutoCallEnabled === 'function') {
                            return Boolean(window.NovaAndroidBridge.isBackgroundAutoCallEnabled());
                        }
                    } catch (e) {}
                    const val = localStorage.getItem(BG_AUTOCALL_KEY);
                    return val === null ? true : val === 'true';
                };

                window.__toggleBackgroundAutoCallSetting = function(forceState) {
                    const nextState = typeof forceState === 'boolean' ? forceState : !window.__isBackgroundAutoCallEnabled();
                    localStorage.setItem(BG_AUTOCALL_KEY, String(nextState));
                    try {
                        if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.setBackgroundAutoCallEnabled === 'function') {
                            window.NovaAndroidBridge.setBackgroundAutoCallEnabled(nextState);
                        }
                    } catch (e) {}
                    window.__syncAppHeaderAndAuthUi();
                };

                window.__openNativeAccessibilitySettings = function() {
                    showNotice("Emergency calls are user-confirmed. The app does not use Accessibility screen-tapping to place calls.", "info");
                };

                function getChatSessions() {
                    return readStore(getUserScopedKey(CHAT_MEMORY_KEY), []);
                }
                function saveChatSessions(sessions) {
                    writeStore(getUserScopedKey(CHAT_MEMORY_KEY), sessions.slice(0, 50));
                }

                window.__activeMemorySessionId = window.__activeMemorySessionId || ("session-" + Date.now());

                function recordChatTurnToMemory(userQuery, aiReply) {
                    const sessions = getChatSessions();
                    let current = sessions.find(s => s.id === window.__activeMemorySessionId);
                    if (!current) {
                        current = {
                            id: window.__activeMemorySessionId,
                            title: String(userQuery || "Clinical Consultation").slice(0, 44),
                            updated_at: new Date().toLocaleString(),
                            messages: []
                        };
                        sessions.unshift(current);
                    }
                    current.updated_at = new Date().toLocaleString();
                    current.messages.push({ role: "user", text: String(userQuery), time: new Date().toLocaleTimeString() });
                    current.messages.push({ role: "assistant", text: String(aiReply), time: new Date().toLocaleTimeString() });
                    saveChatSessions(sessions);
                    window.__renderChatMemoryArchive();
                }

                function extractNaturalPatientMemory(incomingHistory) {
                    const base = Array.isArray(incomingHistory) ? incomingHistory.slice() : [];
                    const sessions = getChatSessions();
                    const allUserMsgs = [];
                    const symptomSet = new Set();
                    const medSet = new Set();

                    const symptomWords = ["cough", "coughing", "sweat", "sweating", "tensed", "tension", "anxiety", "anxious", "fever", "chills", "headache", "migraine", "chest pain", "breathless", "breathing", "stomach pain", "acidity", "vomiting", "diarrhea", "dizziness", "dizzy", "weakness", "fatigue", "rash", "joint pain", "back pain", "palpitation", "insomnia", "sad", "depressed", "high bp", "hypertension", "diabetes", "sugar"];
                    const medWords = ["steroid", "steroids", "prednisolone", "dexamethasone", "dolo", "paracetamol", "zerodol", "ibuprofen", "pan-d", "pantoprazole", "omez", "lithonex", "lithium", "augmentin", "amoxicillin", "azithromycin", "cetirizine", "telma", "amlodipine", "metformin"];

                    sessions.slice(0, 8).forEach(s => {
                        (s.messages || []).forEach(m => {
                            if (m && m.role === "user" && m.text) allUserMsgs.push(String(m.text));
                        });
                    });
                    base.forEach(m => {
                        if (m && m.role === "user" && m.text) allUserMsgs.push(String(m.text));
                    });

                    const historyTextLow = allUserMsgs.slice(0, -1).join(" ").toLowerCase();
                    symptomWords.forEach(sw => {
                        if (historyTextLow.includes(sw)) symptomSet.add(sw);
                    });
                    medWords.forEach(mw => {
                        if (historyTextLow.includes(mw)) medSet.add(mw);
                    });

                    return {
                        pastSymptoms: Array.from(symptomSet),
                        pastMeds: Array.from(medSet),
                        recentUserQueries: allUserMsgs.slice(-5)
                    };
                }

                window.__recallSavedChatSession = function(sessionId) {
                    const sessions = getChatSessions();
                    const target = sessions.find(s => s.id === sessionId);
                    if (!target) return;
                    window.__activeMemorySessionId = target.id;
                    window.__openFeatureScreen('ai');
                    const chatBox = document.getElementById("chatMessages") || document.querySelector(".chat-messages");
                    if (chatBox) {
                        chatBox.innerHTML = "";
                        target.messages.forEach(m => {
                            const div = document.createElement("div");
                            div.style.cssText = "padding: 0.8rem 0.95rem; margin-bottom: 0.6rem; border-radius: 10px; background: " + (m.role === "user" ? "#EFF6FF" : "#FFFFFF") + "; border: 1px solid #E2E8F0;";
                            const roleLabel = m.role === "user" ? "You" : "Nova AI";
                            const roleColor = m.role === "user" ? "#1D4ED8" : "#0F766E";
                            div.innerHTML = '<div style="font-size:0.75rem; font-weight:700; color:' + roleColor + '; margin-bottom:0.25rem;">' + roleLabel + ' • ' + (m.time || '') + '</div><div style="white-space:pre-wrap; color:#1E293B; font-size:0.9rem;">' + m.text + '</div>';
                            chatBox.appendChild(div);
                        });
                    }
                };

                window.__startNewMemorySession = function() {
                    window.__activeMemorySessionId = "session-" + Date.now();
                    const chatBox = document.getElementById("chatMessages") || document.querySelector(".chat-messages");
                    if (chatBox) {
                        chatBox.innerHTML = '<div style="padding: 0.85rem; border-radius: 8px; background: #EFF6FF; color: #1E3A8A; font-size: 0.88rem;">New conversation started. I still remember your past symptoms and medicines from earlier chats so we can continue your evaluation seamlessly.</div>';
                    }
                    window.__renderChatMemoryArchive();
                };

                window.__clearAllChatMemory = function() {
                    writeStore(getUserScopedKey(CHAT_MEMORY_KEY), []);
                    localStorage.removeItem(getUserScopedKey(CHAT_MEMORY_KEY));
                    window.__startNewMemorySession();
                };

                window.__renderChatMemoryArchive = function() {
                    const listEl = document.getElementById("novaMemorySessionsList");
                    if (!listEl) return;
                    const sessions = getChatSessions();
                    if (sessions.length === 0) {
                        listEl.innerHTML = '<p style="margin:0; font-size:0.84rem; color:#475569;">No saved chats yet. Ask any symptom, disease, or medicine question above—your conversation will be saved automatically.</p>';
                        return;
                    }
                    listEl.innerHTML = sessions.map((s, idx) =>
                        '<div style="display:flex; justify-content:space-between; align-items:center; padding:0.55rem 0.75rem; margin-bottom:0.4rem; border-radius:8px; background:#F8FAFC; border:1px solid #E2E8F0; gap:0.65rem;">' +
                            '<div style="cursor:pointer; flex:1;" onclick="window.__recallSavedChatSession(\'' + s.id + '\')">' +
                                '<div style="font-weight:700; color:#1E293B; font-size:0.85rem;">' + (idx + 1) + '. ' + s.title + '</div>' +
                                '<div style="font-size:0.74rem; color:#64748B;">' + s.messages.length + ' messages • ' + s.updated_at + '</div>' +
                            '</div>' +
                            '<button type="button" onclick="window.__recallSavedChatSession(\'' + s.id + '\')" style="padding:0.4rem 0.75rem !important; font-size:0.76rem !important; width:auto !important;">Open</button>' +
                        '</div>'
                    ).join("");
                };

                // Do not rewrite explicit emergency-service tel:108 links.

                async function gtxTranslate(text, targetLang) {
                    if (!text || !targetLang || targetLang === 'en') return text;
                    const key = targetLang + '|' + text;
                    if (transCache[key]) return transCache[key];
                    try {
                        const u = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=' +
                                  encodeURIComponent(targetLang) + '&dt=t&q=' + encodeURIComponent(text);
                        const r = await origFetch(u);
                        const d = await r.json();
                        const res = d[0].map(x => x[0]).join('');
                        transCache[key] = res;
                        return res;
                    } catch (e) { return text; }
                }

                function makeMapsUrl(lat, lng, q) {
                    if (lat !== null && lat !== undefined && lng !== null && lng !== undefined) {
                        return "https://www.google.com/maps/search/?api=1&query=" + lat + "," + lng;
                    }
                    return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(q || "Hospital India");
                }

                function H(name, city, state, cat, schemes, address, pin, lat, lng, spec, phone, web) {
                    return {
                        name: name, city: city, state: state, facility_category: cat, schemes: schemes,
                        address: address, pin_code: pin, latitude: lat, longitude: lng, specialties: spec,
                        phone_general: phone, phone_emergency: "108", website: web || "https://mohfw.gov.in",
                        maps_url: makeMapsUrl(lat, lng, name + ", " + address + ", " + city + ", " + state + " " + pin)
                    };
                }

                function S(name, city, state, cat, hrs, address, pin, lat, lng, srv, phone, web) {
                    return {
                        name: name, city: city, state: state, facility_category: cat, hours: hrs,
                        address: address, pin_code: pin, latitude: lat, longitude: lng, services: srv,
                        phone_contact: phone, website: web || "https://janaushadhi.gov.in",
                        maps_url: makeMapsUrl(lat, lng, name + ", " + address + ", " + city + ", " + state + " " + pin)
                    };
                }

                window.__NOVA_36_HOSPITALS = [
                    H("King George Hospital (KGH)", "Visakhapatnam", "Andhra Pradesh", "Government Medical College Hospital", "PM-JAY, Dr. NTR Vaidya Seva, 24x7 Trauma", "Maharanipeta, Visakhapatnam", "530002", 17.7085, 83.3046, "24x7 Trauma, Cardiology, General Medicine, Surgery, Pediatrics", "0891-2564891", "https://kghvisakhapatnam.org"),
                    H("AIIMS Mangalagiri", "Mangalagiri / Guntur", "Andhra Pradesh", "Central Autonomous Apex Medical Institute", "PM-JAY, CGHS, 24x7 Emergency", "NH-16 Service Road, Mangalagiri, Guntur", "522503", 16.4419, 80.5526, "Emergency Medicine, Oncology, Cardiology, Orthopedics", "08645-280024", "https://www.aiimsmangalagiri.edu.in"),
                    H("TRIHMS State Referral Hospital", "Naharlagun / Itanagar", "Arunachal Pradesh", "State Government Medical College Hospital", "PM-JAY, CMAAY, 24x7 Emergency", "Old Assembly Complex, Naharlagun", "791110", 27.1031, 93.6922, "24x7 Emergency, Internal Medicine, General Surgery, Maternity", "0360-2350332", "https://trihms.org"),
                    H("Gauhati Medical College and Hospital (GMCH)", "Guwahati", "Assam", "State Apex Government Teaching Hospital", "PM-JAY, Atal Amrit Abhiyan, 24x7 Trauma", "Bhangagarh, Guwahati", "781032", 26.1553, 91.7697, "Cardiology, Neurology, Trauma, Oncology, Pediatrics", "0361-2529457", "https://gmchassam.gov.in"),
                    H("AIIMS Patna", "Patna", "Bihar", "Central Autonomous Apex Medical Institute", "PM-JAY, 24x7 Trauma & Emergency", "Phulwari Sharif, Patna", "801507", 25.5612, 85.0414, "Level-1 Trauma, Cardiology, Neurosurgery, Oncology", "0612-2451070", "https://aiimspatna.edu.in"),
                    H("AIIMS Raipur", "Raipur", "Chhattisgarh", "Central Autonomous Apex Medical Institute", "PM-JAY, 24x7 Emergency & Trauma", "GE Road, Tatibandh, Raipur", "492099", 21.2569, 81.5792, "24x7 Emergency, Cardiology, Oncology, Nephrology", "0771-2572240", "https://www.aiimsraipur.edu.in"),
                    H("Goa Medical College and Hospital (GMC)", "Bambolim / Panaji", "Goa", "State Government Tertiary Hospital", "PM-JAY, DDSSY, 24x7 Trauma Center", "NH-66, Bambolim, North Goa", "403202", 15.4608, 73.8576, "Trauma Unit, Cardiology, Neurosurgery, Internal Medicine", "0832-2458700", "https://gmc.goa.gov.in"),
                    H("Sir Takhtasinhji General Hospital (GMC Bhavnagar)", "Bhavnagar", "Gujarat", "Government Medical College & Civil Hospital", "PM-JAY / PMJAY-MA Verified, 24x7 Trauma", "Jail Road, Near Barton Library, Kalanala, Bhavnagar", "364001", 21.7719, 72.1436, "24x7 Trauma & Emergency, Cardiology, Medicine, Surgery, Maternity", "0278-2423250", "https://gmcbhavnagar.edu.in"),
                    H("Civil Hospital Ahmedabad (B.J. Medical College)", "Ahmedabad", "Gujarat", "State Apex Government Tertiary Hospital", "PM-JAY / PMJAY-MA Verified, 24x7 Trauma", "Asarwa, Ahmedabad", "380016", 23.0525, 72.6029, "24x7 Trauma, UN Mehta Cardiology, Kidney, Oncology", "079-22683721", "https://civilhospitalahmedabad.gujarat.gov.in"),
                    H("PDU Civil Hospital Rajkot", "Rajkot", "Gujarat", "Government Medical College & Civil Hospital", "PM-JAY / PMJAY-MA, 24x7 Emergency", "Hospital Chowk, Jamnagar Road, Rajkot", "360001", 22.3081, 70.7997, "Emergency Medicine, Orthopedics, Internal Medicine", "0281-2458337", "https://pdumcrajkot.org"),
                    H("SSG Hospital Vadodara", "Vadodara", "Gujarat", "Government Medical College Hospital", "PM-JAY / PMJAY-MA, 24x7 Emergency", "Anandpura, Raopura, Vadodara", "390001", 22.3045, 73.1923, "24x7 Emergency, Surgery, Medicine, Maternity", "0265-2424848", "https://www.medicalcollegebaroda.edu.in"),
                    H("New Civil Hospital Surat", "Surat", "Gujarat", "Government Medical College & Civil Hospital", "PM-JAY / PMJAY-MA, 24x7 Trauma", "Majura Gate, Ring Road, Surat", "395001", 21.1795, 72.8229, "Trauma Care, General Medicine, Burns, Pediatrics", "0261-2244456", "https://gmcsurat.edu.in"),
                    H("Pt. B.D. Sharma PGIMS Rohtak", "Rohtak", "Haryana", "State Government Medical University", "PM-JAY Chirayu Haryana, 24x7 Trauma", "Medical Road, Rohtak", "124001", 28.8845, 76.6075, "Apex Trauma Center, Cardiology, Neurology, Oncology", "01262-281308", "https://pgimsrohtak.ac.in"),
                    H("IGMC Hospital Shimla", "Shimla", "Himachal Pradesh", "State Apex Government Medical College", "PM-JAY, HIMCARE, 24x7 Emergency", "Ridge Sanjauli Road, Shimla", "171001", 31.1066, 77.1822, "Emergency Medicine, Cardiology, Surgery", "0177-2804251", "https://igmcshimla.edu.in"),
                    H("Rajendra Institute of Medical Sciences (RIMS)", "Ranchi", "Jharkhand", "State Autonomous Medical Institute", "PM-JAY, 24x7 Trauma & Emergency", "Bariatu Road, Ranchi", "834009", 23.3911, 85.3494, "Trauma, Neurosurgery, Cardiology, Oncology", "0651-2541533", "https://rimsranchi.ac.in"),
                    H("Victoria Hospital (BMCRI)", "Bengaluru", "Karnataka", "State Government Teaching Hospital", "Ayushman Bharat - Arogya Karnataka", "Fort Road, Near City Market, Bengaluru", "560002", 12.9634, 77.5736, "24x7 Emergency, Burns Center, Medicine, Surgery", "080-26701150", "https://bmcribengaluru.karnataka.gov.in"),
                    H("Government Medical College Hospital", "Thiruvananthapuram", "Kerala", "State Apex Government Medical College", "KASP / PM-JAY, 24x7 Trauma Care", "Ulloor Road, Thiruvananthapuram", "695011", 8.5236, 76.9283, "24x7 Trauma, Cardiology, Neurology, Medicine", "0471-2528300", "https://tmc.kerala.gov.in"),
                    H("AIIMS Bhopal", "Bhopal", "Madhya Pradesh", "Central Autonomous Apex Medical Institute", "PM-JAY, 24x7 Emergency & Trauma", "Saket Nagar, Bhopal", "462020", 23.2067, 77.4563, "Emergency & Trauma, Cardiology, Oncology, Surgery", "0755-2672342", "https://www.aiimsbhopal.edu.in"),
                    H("KEM Hospital & Seth GS Medical College", "Mumbai", "Maharashtra", "Municipal Tertiary Teaching Hospital", "PM-JAY, MJPJAY, 24x7 Emergency", "Acharya Donde Marg, Parel, Mumbai", "400012", 19.0022, 72.8416, "24x7 Emergency, Cardiology, Orthopedics, Neurology", "022-24107000", "https://www.kem.edu"),
                    H("Sassoon General Hospital (BJGMC)", "Pune", "Maharashtra", "State Government Teaching Hospital", "PM-JAY, MJPJAY, 24x7 Trauma", "Jayprakash Narayan Road, Pune", "411001", 18.5256, 73.8715, "24x7 Trauma, Medicine, Surgery, Pediatrics", "020-26128000", "https://bjgmcpune.com"),
                    H("Regional Institute of Medical Sciences (RIMS)", "Imphal", "Manipur", "Autonomous Regional Medical Institute", "PM-JAY, CMHT, 24x7 Emergency", "Lamphelpat, Imphal West", "795004", 24.8172, 93.9225, "24x7 Casualty, Internal Medicine, Surgery, Maternity", "0385-2414720", "https://www.rims.edu.in"),
                    H("NEIGRIHMS Shillong", "Shillong", "Meghalaya", "Central Autonomous Apex Medical Institute", "PM-JAY, MHIS, 24x7 Emergency", "Mawdiangdiang, Shillong", "793018", 25.5912, 91.9369, "Cardiology, Neurosurgery, Oncology, Trauma", "0364-2538013", "https://neigrihms.gov.in"),
                    H("Zoram Medical College & State Referral Hospital", "Falkawn / Aizawl", "Mizoram", "State Government Medical College", "PM-JAY, MSHCS, 24x7 Emergency", "Falkawn, Aizawl", "796005", 23.6358, 92.7242, "24x7 Emergency, Internal Medicine, Surgery, Pediatrics", "0389-2335426", "https://zmc.edu.in"),
                    H("Naga Hospital Authority Kohima (NHAK)", "Kohima", "Nagaland", "State Referral & Teaching Hospital", "PM-JAY, CMHIS Nagaland, 24x7 Emergency", "High School Road, Kohima", "797001", 25.6751, 94.1086, "24x7 Emergency, General Medicine, Surgery, Trauma", "0370-2222916", "https://nagahealth.nagaland.gov.in"),
                    H("AIIMS Bhubaneswar", "Bhubaneswar", "Odisha", "Central Autonomous Apex Medical Institute", "PM-JAY, 24x7 Trauma & Emergency", "Sijua, Patrapada, Bhubaneswar", "751019", 20.2314, 85.7753, "Trauma, Cardiology, Oncology, Neurosurgery", "0674-2476789", "https://aiimsbhubaneswar.nic.in"),
                    H("GMC & Guru Nanak Dev Hospital", "Amritsar", "Punjab", "State Government Medical College", "Ayushman Bharat MMSBY, 24x7 Emergency", "Majitha Road, Amritsar", "143001", 31.6441, 74.8825, "24x7 Trauma, Medicine, Surgery, Orthopedics", "0183-2426918", "https://gmc.edu.in"),
                    H("Sawai Man Singh (SMS) Medical College Hospital", "Jaipur", "Rajasthan", "State Apex Government Tertiary Hospital", "Ayushman Bharat, 24x7 Poly-Trauma", "JLN Marg, Jaipur", "302004", 26.9069, 75.8159, "24x7 Trauma, Cardiology, Neurosurgery, Medicine", "0141-2560291", "https://education.rajasthan.gov.in/smsmcjaipur"),
                    H("STNM Multi-Specialty Government Hospital", "Gangtok", "Sikkim", "State Apex Referral Hospital", "PM-JAY, 24x7 Emergency & Trauma", "Sochakgang, Sichey, Gangtok", "737101", 27.3344, 88.6095, "24x7 Emergency, Dialysis, Cardiology, Medicine", "03592-202944", "https://sikkimhealth.gov.in"),
                    H("Rajiv Gandhi Govt General Hospital (RGGGH)", "Chennai", "Tamil Nadu", "State Apex Government Teaching Hospital", "PM-JAY, CMCHIS, 24x7 Trauma", "EVR Periyar Salai, Park Town, Chennai", "600003", 13.0818, 80.2772, "24x7 Trauma, Cardiology, Nephrology, Neurology", "044-25305000", "https://www.mmc.ac.in"),
                    H("Osmania General Hospital", "Hyderabad", "Telangana", "State Government Tertiary Hospital", "Aarogyasri / PM-JAY, 24x7 Emergency", "Afzal Gunj, Hyderabad", "500012", 17.3730, 78.4744, "24x7 Emergency, General Medicine, Trauma, Surgery", "040-24600146", "https://health.telangana.gov.in"),
                    H("Agartala Govt Medical College & GBP Hospital", "Agartala", "Tripura", "State Government Teaching Hospital", "PM-JAY, 24x7 Trauma & Emergency", "Kunjaban, Agartala", "799006", 23.8615, 91.2913, "24x7 Trauma, Internal Medicine, Surgery, Pediatrics", "0381-2356702", "https://agmc.nic.in"),
                    H("King George's Medical University (KGMU)", "Lucknow", "Uttar Pradesh", "State Medical University & Trauma Center", "PM-JAY, 24x7 Level-1 Trauma & Cardiac", "Shah Mina Road, Chowk, Lucknow", "226003", 26.8692, 80.9161, "Level-1 Trauma, Cardiology, Neurology, Oncology", "0522-2258880", "https://www.kgmu.org"),
                    H("AIIMS Rishikesh", "Rishikesh / Dehradun", "Uttarakhand", "Central Autonomous Apex Medical Institute", "PM-JAY, Atal Ayushman, 24x7 Trauma", "Virbhadra Road, Rishikesh", "249203", 30.0764, 78.2858, "Level-1 Trauma, Emergency, Cardiology, Neurosurgery", "0135-2462927", "https://aiimsrishikesh.edu.in"),
                    H("IPGMER and SSKM Hospital", "Kolkata", "West Bengal", "State Apex Postgraduate Medical Institute", "Swasthya Sathi, 24x7 Level-1 Trauma", "244 AJC Bose Road, Kolkata", "700020", 22.5393, 88.3426, "Level-1 Trauma, Cardiology, Neurology, Hepatology", "033-22041100", "https://www.ipgmer.gov.in"),
                    H("G.B. Pant Hospital (ANIIMS)", "Port Blair", "Andaman and Nicobar Islands", "UT Government Medical College Hospital", "PM-JAY, 24x7 Emergency Care", "Atlanta Point, Port Blair", "744104", 11.6761, 92.7478, "24x7 Emergency, Medicine, Surgery, Maternity", "03192-232102", "https://aniims.org"),
                    H("PGIMER Chandigarh", "Chandigarh", "Chandigarh", "Institute of National Importance", "PM-JAY, HIMCARE, 24x7 Advanced Trauma", "Madhya Marg, Sector 12, Chandigarh", "160012", 30.7649, 76.7751, "Advanced Trauma, Cardiac, Neurosciences, Pediatrics", "0172-2747585", "https://pgimer.edu.in"),
                    H("Shri Vinoba Bhave Civil Hospital (NAMO MERI)", "Silvassa", "Dadra and Nagar Haveli and Daman and Diu", "UT Government Medical College Hospital", "PM-JAY, 24x7 Trauma & Emergency", "Sayli Road, Silvassa", "396230", 20.2673, 73.0169, "24x7 Emergency, ICU, Internal Medicine, Surgery", "0260-2642940", "https://vbch.dnh.nic.in"),
                    H("AIIMS New Delhi", "New Delhi", "Delhi", "Apex Institute of National Importance", "PM-JAY, CGHS, 24x7 JPN Trauma Center", "Ansari Nagar, Aurobindo Marg, New Delhi", "110029", 28.5672, 77.2100, "All Super-Specialties, Level-1 Trauma, Cardiac, Oncology", "011-26588500", "https://www.aiims.edu"),
                    H("SKIMS Soura", "Srinagar", "Jammu and Kashmir", "UT Apex Medical University Hospital", "PM-JAY SEHAT, 24x7 Emergency & Trauma", "Soura, Srinagar", "190011", 34.1363, 74.8000, "Emergency Medicine, Neurosurgery, Cardiology, Oncology", "0194-2401013", "https://www.skims.ac.in"),
                    H("SNM District Hospital Leh", "Leh", "Ladakh", "UT Apex Government Referral Hospital", "PM-JAY, 24x7 High-Altitude Emergency", "Old Leh Road, Leh", "194101", 34.1612, 77.5794, "High-Altitude Emergency, Hyperbaric Care, Medicine", "01982-252014", "https://leh.nic.in/health/"),
                    H("Indira Gandhi Hospital (IGH)", "Kavaratti", "Lakshadweep", "UT Government Referral Hospital", "PM-JAY, 24x7 Emergency & Medevac", "Hospital Road, Kavaratti", "682555", 10.5667, 72.6417, "24x7 Emergency Stabilization, Medicine, Maternity", "04896-262348", "https://lakshadweep.gov.in"),
                    H("JIPMER Puducherry", "Puducherry", "Puducherry", "Institute of National Importance", "PM-JAY, CMCHIS, 24x7 Trauma & Emergency", "Dhanvantari Nagar, Gorimedu, Puducherry", "605006", 11.9537, 79.7977, "24x7 Trauma, Cardiology, Neurology, Oncology", "0413-2298288", "https://jipmer.edu.in")
                ];

                window.__NOVA_36_STORES = window.__NOVA_36_HOSPITALS.map(h => S(
                    "Pradhan Mantri Bhartiya Janaushadhi Kendra (PMBJK) — " + h.city,
                    h.city,
                    h.state,
                    "Government Generic Pharmacy (PMBJP) & 24x7 Hospital Chemist",
                    "08:00 AM – 09:00 PM (Hospital Emergency Pharmacy 24x7)",
                    "Near " + h.name + ", " + h.address,
                    h.pin_code,
                    h.latitude,
                    h.longitude,
                    "WHO-GMP Certified Generic Medicines (50–80% Lower Cost), Insulin, Cardiac, Diabetic & ORS Supplies",
                    "1800-180-8080",
                    "https://janaushadhi.gov.in"
                ));

                // =========================================================================
                // COMPREHENSIVE BUILT-IN CLINICAL, DIFFERENTIAL DIAGNOSIS & DRUG KNOWLEDGE
                // (Ensures AI is NEVER dead offline or in APK WebView)
                // =========================================================================
                const BUILTIN_DRUG_KNOWLEDGE = [
                    {
                        keys: ["steroid", "steroids", "corticosteroid", "corticosteroids", "prednisolone", "wysolone", "omnacortil", "dexamethasone", "dexona", "betamethasone", "betnesol", "hydrocortisone", "deflazacort", "medrol", "methylprednisolone"],
                        title: "Corticosteroids (Medical Steroids — e.g., Prednisolone, Dexamethasone, Methylprednisolone, Hydrocortisone)",
                        ingredients: "Synthetic glucocorticoid hormones (Prednisolone, Dexamethasone, Betamethasone, Hydrocortisone, or Deflazacort).",
                        uses: "• **Severe Inflammation & Autoimmune Conditions:** Calms overactive immune responses in rheumatoid arthritis, lupus, inflammatory bowel disease, and severe skin eczema/psoriasis.\n• **Acute Respiratory & Allergic Emergencies:** Relieves life-threatening asthma attacks, COPD flare-ups, severe allergic reactions (anaphylaxis), and croup.\n• **Organ & Adrenal Support:** Used in adrenal insufficiency (Addison's disease) and to prevent organ transplant rejection.",
                        side_effects: "• **Short-Term:** Increased blood sugar (hyperglycemia), increased appetite, acidity/gastritis, mood changes, insomnia, and fluid retention.\n• **Long-Term Unsupervised Use:** Weight gain, moon face, high blood pressure, osteoporosis (weak bones), cataracts, and suppressed immunity (higher infection risk).",
                        dosing_and_warnings: "• **Administration Principle:** Oral steroids are taken **strictly after food** (usually in the morning) as prescribed by a doctor.\n• **Critical Warning:** **Never stop systemic steroids abruptly** after taking them for more than a week—sudden withdrawal can trigger a life-threatening adrenal crisis. Never use steroids for routine viral fevers or fungal infections (they worsen fungal infections)."
                    },
                    {
                        keys: ["dolo", "calpol", "crocin", "paracetamol", "acetaminophen", "pcm", "p 650", "p 500"],
                        title: "Paracetamol / Acetaminophen (Dolo 650, Calpol, Crocin)",
                        ingredients: "Paracetamol IP (500 mg / 650 mg — Antipyretic & Non-Opioid Analgesic).",
                        uses: "• **Fever Reduction:** Safely lowers body temperature in viral fever, dengue, malaria, typhoid, and post-vaccine fever.\n• **Pain Relief:** Relieves headache, migraine, toothache, sore throat, and body aches.",
                        side_effects: "• Very safe at recommended doses; rare skin rash. Excessive overdose (>4,000 mg/day) causes severe liver toxicity.",
                        dosing_and_warnings: "• **Dosing Principle:** Typically 500 mg to 650 mg **after food** with water, keeping at least a **4 to 6 hour gap** between doses (max 3–4 tablets in 24 hours).\n• **Warning:** Avoid alcohol and check cold/flu combinations so you do not double-dose Paracetamol."
                    },
                    {
                        keys: ["zerodol", "aceclofenac", "hifenac", "diclofenac", "voveran", "ibuprofen", "brufen", "combiflam", "naproxen", "naprosyn", "etoricoxib", "nucoxia", "nsaid", "painkiller"],
                        title: "NSAID Pain & Anti-Inflammatory Medicines (Zerodol-SP, Ibuprofen, Diclofenac, Combiflam)",
                        ingredients: "Non-Steroidal Anti-Inflammatory Drugs (Aceclofenac, Ibuprofen, Diclofenac, or Naproxen ± Paracetamol ± Serratiopeptidase).",
                        uses: "• **Joint, Muscle & Dental Pain:** Relieves arthritis, backache, sprains, post-injury tissue swelling (`SP` variants), and toothache.",
                        side_effects: "• Stomach burning, acidity, gastritis, nausea, peptic ulcers, or elevated blood pressure and kidney strain.",
                        dosing_and_warnings: "• **Dosing Principle:** Must be taken **strictly after a full meal** with water.\n• **Critical Warning:** **Strictly avoid in suspected Dengue fever** (causes platelet dysfunction and internal bleeding), stomach ulcers, kidney disease, asthma, and pregnancy."
                    },
                    {
                        keys: ["pan", "pantocid", "pantoprazole", "omez", "omeprazole", "razo", "rabeprazole", "esomeprazole", "nexpro", "dsr", "antacid", "digene", "gelusil"],
                        title: "Acid Reducers & Proton Pump Inhibitors (Pan-40, Pan-D, Pantocid DSR, Omez, Razo)",
                        ingredients: "Pantoprazole / Omeprazole / Rabeprazole (20–40 mg) ± Domperidone (10–30 mg SR in `D`/`DSR` capsules).",
                        uses: "• **Acidity, Heartburn & GERD:** Blocks stomach acid production to heal gastritis, acid reflux, sour belching, and peptic ulcers (`DSR` also stops nausea and bloating).",
                        side_effects: "• Mild headache, dry mouth, or Vitamin B12/Magnesium deficiency if taken continuously for years.",
                        dosing_and_warnings: "• **Dosing Principle:** Swallow whole **30 to 40 minutes before breakfast on an empty stomach**."
                    },
                    {
                        keys: ["augmentin", "amoxicillin", "moxikind", "clavam", "azithral", "azithromycin", "azee", "cefixime", "taxim", "zifi", "ciprofloxacin", "ciplox", "ofloxacin", "norflox", "metrogyl", "flagyl", "antibiotic", "antibiotics"],
                        title: "Antibacterial / Antibiotic Medicines (Augmentin, Azithromycin, Cefixime, Ciprofloxacin, Metrogyl)",
                        ingredients: "Prescription Beta-lactam, Macrolide, Cephalosporin, Fluoroquinolone, or Nitroimidazole antimicrobials.",
                        uses: "• **Confirmed Bacterial Infections:** Treats bacterial pneumonia, tonsillitis, UTI, typhoid, skin abscesses, and bacterial dysentery. **Does not cure viral colds, flu, or dengue.**",
                        side_effects: "• Loose stools/diarrhea, nausea, stomach cramps, or allergic skin rash.",
                        dosing_and_warnings: "• **Dosing Principle:** Take at fixed intervals after food and **complete the full prescribed course** so bacteria do not become resistant."
                    },
                    {
                        keys: ["lithonex", "licab", "lithium"],
                        title: "Lithium Carbonate (Lithonex 450 XL / Licab)",
                        ingredients: "Lithium Carbonate Prolonged-Release (300 mg / 400 mg / 450 mg XL).",
                        uses: "• **Mood Stabilizer:** Prevents manic and depressive episodes in Bipolar Disorder and treats acute mania under psychiatric care.",
                        side_effects: "• Fine hand tremor, increased thirst/urination. Toxicity (>1.5 mEq/L) causes coarse shaking, slurred speech, vomiting, or confusion.",
                        dosing_and_warnings: "• **Dosing Principle:** Swallow whole **right after food** at the same time daily; drink **2.5–3 Liters of fluids daily**.\n• **Warning:** Never combine with NSAID painkillers (Ibuprofen, Zerodol) and get regular Serum Lithium, Kidney, and Thyroid blood tests."
                    },
                    {
                        keys: ["telma", "telmisartan", "losartan", "amlodipine", "amlokind", "stamlo", "cilacar", "cilnidipine", "metoprolol", "concor", "prolomet", "ramipril"],
                        title: "Blood Pressure & Cardiac Medicines (Telma, Amlodipine, Metoprolol, Cilacar)",
                        ingredients: "ARBs (Telmisartan), Calcium Channel Blockers (Amlodipine/Cilnidipine), or Beta-Blockers (Metoprolol).",
                        uses: "• **Hypertension & Heart Protection:** Lowers high blood pressure (`≥ 140/90 mmHg`), reduces angina chest strain, and prevents stroke and kidney damage.",
                        side_effects: "• Mild dizziness when standing up quickly, or mild ankle swelling (with Amlodipine).",
                        dosing_and_warnings: "• **Dosing Principle:** Take at the **same time every day** (`H` diuretic variants in the morning after breakfast). **Never stop BP tablets suddenly** even if your reading is normal."
                    },
                    {
                        keys: ["glycomet", "metformin", "amaryl", "glimepiride", "janumet", "galvus", "vildagliptin", "dapagliflozin", "forxiga", "insulin"],
                        title: "Diabetes Medicines (Glycomet / Metformin, Glimepiride, Dapagliflozin, Insulin)",
                        ingredients: "Biguanides (Metformin), Sulfonylureas (Glimepiride), DPP-4i, or SGLT2 Inhibitors.",
                        uses: "• **Type 2 Diabetes Mellitus:** Controls fasting and post-meal blood sugar to protect kidneys, nerves, eyes, and heart.",
                        side_effects: "• Mild stomach upset (Metformin) or **low blood sugar / hypoglycemia (<70 mg/dL)** with sweating, shakiness, and hunger (Glimepiride/Insulin).",
                        dosing_and_warnings: "• **Dosing Principle:** Take Metformin **with or right after meals**; take Glimepiride (`GP1`/`GP2`) **just before breakfast** and never skip meals."
                    }
                ];

                const BUILTIN_DISEASE_KNOWLEDGE = [
                    {
                        keys: ["hypertension", "high blood pressure", "high bp", "blood pressure"],
                        title: "Hypertension (High Blood Pressure)",
                        overview: "**Hypertension** is a chronic cardiovascular condition where arterial blood pressure remains consistently at or above **140/90 mmHg** (Normal BP is **< 120/80 mmHg**; Stage 1 is **130–139 / 80–89 mmHg**; Hypertensive Crisis is **> 180/120 mmHg**).",
                        causes: "• Excess dietary salt (sodium), genetics, lack of physical activity, obesity, chronic mental stress/tension, smoking, or underlying kidney/thyroid disorders.",
                        symptoms: "• Often has no symptoms (*'The Silent Killer'*). When BP spikes, it causes **morning throbbing headache (back of head/neck), dizziness, palpitations, excessive sweating, blurred vision, or chest tightness**.",
                        tests: "• Serial digital/cuff BP readings, **12-Lead ECG**, **Fasting Lipid Profile**, **Kidney Function Test (Serum Creatinine & Electrolytes)**, and **Blood Sugar (HbA1c)**.",
                        care: "• Restrict salt to **< 5g (1 tsp) per day** (avoid pickles, papad, namkeen), eat potassium-rich foods (banana, spinach, oats), walk briskly 30 mins daily, and consult an **MD General Physician or Cardiologist**."
                    },
                    {
                        keys: ["dengue", "platelet", "breakbone"],
                        title: "Dengue Fever",
                        overview: "**Dengue** is an acute mosquito-borne viral infection (*DENV 1–4*) transmitted by daytime-biting *Aedes aegypti* mosquitoes.",
                        causes: "• Bite of an infected *Aedes* mosquito breeding in clean stagnant water around homes.",
                        symptoms: "• Sudden **high fever (103°F–105°F), severe headache, pain behind the eyes (retro-orbital pain), intense muscle/joint aches**, skin rash on Days 3–5, nausea, and dropping platelets.",
                        tests: "• **Dengue NS1 Antigen** (Days 1–5), **Dengue IgM/IgG** (after Day 5), and **daily Complete Blood Count (CBC)** to track **Platelets and Hematocrit (PCV)**.",
                        care: "• Drink **3–3.5 Liters of fluids daily** (WHO-ORS, coconut water, pomegranate juice), use **only Paracetamol** for fever, and **STRICTLY AVOID Ibuprofen, Zerodol, Aspirin, or steroids** (bleeding risk). Rush to a hospital if platelets drop below 50,000/µL, gums bleed, or severe stomach pain occurs."
                    },
                    {
                        keys: ["diabetes", "high sugar", "blood sugar"],
                        title: "Diabetes Mellitus (High Blood Sugar)",
                        overview: "**Diabetes** is a chronic metabolic disorder where blood glucose stays elevated (**Fasting ≥ 126 mg/dL**, **Post-Meal PPBS ≥ 200 mg/dL**, or **HbA1c ≥ 6.5%**) due to insulin resistance or low insulin secretion.",
                        causes: "• Insulin resistance, abdominal weight gain, high intake of refined carbs/sugar, sedentary lifestyle, and family history.",
                        symptoms: "• **Frequent urination (especially at night), excessive thirst, increased hunger, unexplained weight loss, fatigue, blurred vision, tingling feet**, and slow-healing wounds.",
                        tests: "• **HbA1c (3-month average)**, **Fasting Blood Sugar (FBS)**, **2-Hour Post-Meal Blood Sugar (PPBS)**, and annual **Urine Microalbumin & Eye Retina check**.",
                        care: "• Follow the Plate Method (50% green vegetables, 25% protein like dal/paneer/curd, 25% high-fiber multigrain roti), avoid white sugar/sweets, walk 30–40 minutes daily, and consult an **Endocrinologist / Diabetologist**."
                    },
                    {
                        keys: ["depression", "depressed", "sadness", "hopeless"],
                        title: "Clinical Depression (Major Depressive Disorder)",
                        overview: "**Clinical Depression** is a treatable medical mood disorder lasting more than 2 weeks caused by brain neurotransmitter changes (serotonin/dopamine), chronic stress, or Vitamin B12/D3/Thyroid deficiencies.",
                        causes: "• Neurochemical imbalance, prolonged emotional or academic/work stress, bereavement, hypothyroidism, or Vitamin B12/D3 deficiency.",
                        symptoms: "• Persistent sad or empty mood, loss of interest in daily activities, insomnia or oversleeping, low energy, poor concentration, and appetite changes.",
                        tests: "• Clinical **PHQ-9 assessment**, **Thyroid Profile (TSH)**, **Vitamin B12**, **Vitamin D3**, and **CBC**.",
                        care: "• Get 20 minutes of morning sunlight, maintain fixed sleep hours, talk openly with family or a **Psychiatrist / Clinical Psychologist**, or call India's free 24x7 mental health helpline **Tele-MANAS at 14416**."
                    },
                    {
                        keys: ["tuberculosis", "tb"],
                        title: "Tuberculosis (TB)",
                        overview: "**Tuberculosis** is a completely curable bacterial infection (*Mycobacterium tuberculosis*) primarily affecting the lungs.",
                        causes: "• Airborne droplet transmission from an untreated active sputum-positive TB patient, especially when immunity or nutrition is low.",
                        symptoms: "• **Cough lasting more than 2 weeks**, coughing up phlegm or blood, **evening-rise fever, drenching night sweats, chest pain, and unexplained weight loss**.",
                        tests: "• **Sputum CBNAAT / TrueNat (GeneXpert)**, **2-Spot Sputum AFB Smear**, and **Digital Chest X-Ray** (100% free at all Government NTEP centers; Helpline: **1800-11-6666**).",
                        care: "• Complete the full 6-month government NTEP antibiotic regimen without skipping a single day and eat a high-protein diet (dal, paneer, soy, milk, eggs)."
                    }
                ];

                // Smart Symptom-to-Disease Differential Diagnosis Analyzer (for questions like "If I sweat very much and feel tensed what disease might I have?" or "If I am coughing what disease do I have?")
                function analyzeSymptomsAndMemory(qLow, qRaw, mem) {
                    const allSymptomsText = (qLow + " " + mem.pastSymptoms.join(" ")).toLowerCase();
                    const hasSweat = /\b(sweat|sweating|perspiration|diaphoresis|clammy)\b/.test(qLow);
                    const hasTense = /\b(tense|tensed|tension|anxious|anxiety|panic|nervous|stress|stressed|worry|palpitation|racing heart)\b/.test(qLow);
                    const hasCough = /\b(cough|coughing|phlegm|sputum|throat)\b/.test(qLow);
                    const hadPriorCough = mem.pastSymptoms.some(s => s.includes("cough"));
                    const hadPriorSweatOrTense = mem.pastSymptoms.some(s => s.includes("sweat") || s.includes("tense") || s.includes("anxiety"));
                    consthadPriorBp = mem.pastSymptoms.some(s => s.includes("bp") || s.includes("hypertension"));

                    let memoryBridgeSentence = "";
                    if (mem.pastSymptoms.length > 0 || mem.pastMeds.length > 0) {
                        const notes = [];
                        if (mem.pastSymptoms.length > 0) notes.push("earlier symptoms of **" + mem.pastSymptoms.slice(0, 4).join(", ") + "**");
                        if (mem.pastMeds.length > 0) notes.push("questions about **" + mem.pastMeds.slice(0, 3).join(", ") + "**");
                        memoryBridgeSentence = "🧠 **Connected with Your Conversation History:** Taking into account your " + notes.join(" and ") + " from our chat:\n\n";
                    }

                    // 1. Sweating + Tension / Anxiety (Photo 4 exact query!)
                    if (hasSweat && hasTense) {
                        let coughCorrelation = "";
                        if (hadPriorCough || hasCough) {
                            coughCorrelation = "\n• **Connection to Your Earlier Cough:** Because you also mentioned **coughing** earlier, if your sweating happens mostly at night (*night sweats*) alongside a cough, doctors also check for a **chest/respiratory infection or Tuberculosis (TB)**; if the cough and sweating happen suddenly with shortness of breath, **acute asthma/bronchospasm or cardiac strain** must be ruled out.";
                        }
                        return memoryBridgeSentence +
                            "🩺 **Differential Diagnosis for Excessive Sweating + Feeling Tensed**\n" +
                            "When excessive sweating (*diaphoresis*) happens together with feeling tensed or restless, doctors evaluate **4 main medical possibilities**:\n\n" +
                            "• **1. Acute Anxiety / Panic Attack (Sympathetic Adrenaline Surge):** Mental tension triggers a 'fight-or-flight' adrenaline rush, causing sweaty palms/forehead, racing heartbeat, restlessness, and tight breathing.\n" +
                            "• **2. Hyperthyroidism (Overactive Thyroid):** Excess thyroid hormone speeds up body metabolism, causing constant heat intolerance, heavy sweating, nervous tension, hand tremors, and weight loss.\n" +
                            "• **3. Hypoglycemia (Low Blood Sugar < 70 mg/dL) or BP Spike:** A sudden drop in blood sugar or a sharp rise in **Blood Pressure (Hypertension)** causes cold sweating, shakiness, and internal restlessness.\n" +
                            "• **4. Cardiac Warning (If Paired with Chest Heaviness):** Sudden cold drenching sweat with chest, jaw, or left-arm discomfort requires an immediate **ECG** to rule out angina/heart strain." +
                            coughCorrelation + "\n\n" +
                            "🧪 **Recommended Tests to Confirm:**\n" +
                            "• Check **Blood Pressure (BP)** and **Random/Fasting Blood Sugar** immediately.\n" +
                            "• Get a **Thyroid Profile (TSH, Free T3, Free T4)** and a **12-Lead ECG**.\n\n" +
                            "💡 **Immediate Relief Right Now:** Sit comfortably, sip plain water (or sugar water if you haven't eaten for hours), practice slow **4-7-8 breathing**, and consult an **MD General Physician**.";
                    }

                    // 2. Coughing query ("If I am coughing what disease do I have?")
                    if (hasCough) {
                        return memoryBridgeSentence +
                            "🩺 **Differential Diagnosis for Cough (What Condition Could It Be?)**\n" +
                            "The cause of a cough depends on whether it is **dry or mucus-producing (wet)** and **how many days** it has lasted:\n\n" +
                            "• **1. Acute Viral Upper Respiratory Infection / Flu (< 1 week):** Cough paired with sore throat, runny nose, or mild fever.\n" +
                            "• **2. Allergic Rhinitis or Bronchial Asthma:** Dry tickling cough that worsens **at night, early morning**, or around dust/cold air, sometimes with wheezing.\n" +
                            "• **3. Acute Bronchitis or Pneumonia:** Deep chest cough bringing up **yellow/green phlegm**, high fever with chills, or shortness of breath.\n" +
                            "• **4. Acid Reflux (Silent GERD):** Dry cough triggered after meals or when lying down flat.\n" +
                            "• **5. Pulmonary Tuberculosis (If Cough Lasts > 2 Weeks):** Persistent cough for over 2 weeks with evening fever, **night sweats**, or weight loss.\n\n" +
                            "🧪 **Recommended Next Steps & Relief:**\n" +
                            "• Sip warm water, do steam inhalation, and check your **SpO₂ oxygen level** (Normal: `≥ 95%`).\n" +
                            "• Tell me: **Is your cough dry or with phlegm, and how many days have you had it?** so I can narrow this down further!";
                    }

                    return null;
                }

                async function buildSmartWordByWordAiResponse(englishQuery, rawUserQuery, historyArr) {
                    const qRaw = (englishQuery || rawUserQuery || "").trim();
                    const qLow = qRaw.toLowerCase();
                    const mem = extractNaturalPatientMemory(historyArr);

                    let matchedHospitals = window.__NOVA_36_HOSPITALS.filter(h => {
                        const cName = h.city.toLowerCase().split('/')[0].trim();
                        const sName = h.state.toLowerCase();
                        return qLow.includes(cName) || qLow.includes(sName);
                    });
                    let matchedStores = window.__NOVA_36_STORES.filter(s => {
                        const cName = s.city.toLowerCase().split('/')[0].trim();
                        const sName = s.state.toLowerCase();
                        return qLow.includes(cName) || qLow.includes(sName);
                    });

                    let locationBlock = "";
                    if (matchedHospitals.length > 0 || matchedStores.length > 0) {
                        locationBlock += "\n\n🏥 **Verified Hospitals & Pharmacies in Your Area:**\n";
                        matchedHospitals.slice(0, 3).forEach(h => {
                            locationBlock += "• **" + h.name + "** (" + h.city + ", " + h.state + ") — 📍 " + h.address + " | 📞 Desk: **" + h.phone_general + "**\n";
                        });
                        matchedStores.slice(0, 2).forEach(s => {
                            locationBlock += "• 💊 **" + s.name + "** — 📍 " + s.address + " | 📞 Helpline: **" + s.phone_contact + "**\n";
                        });
                    }

                    // Step A: Check Built-in Drug / Medicine Class Knowledge (including Steroids, Dolo, Zerodol, Pan-D, Antibiotics, Lithonex, BP/Diabetes meds)
                    const matchedDrug = BUILTIN_DRUG_KNOWLEDGE.find(d => d.keys.some(k => new RegExp("\\b" + k + "\\b", "i").test(qLow) || qLow.includes(k)));
                    if (matchedDrug) {
                        let medMemoryNote = "";
                        if (mem.pastSymptoms.length > 0) {
                            medMemoryNote = "\n• **Note for Your History (" + mem.pastSymptoms.slice(0, 3).join(", ") + "):** Discuss your recent symptoms with your physician before taking this medication to ensure it does not mask or worsen them.";
                        }
                        return "💊 **" + matchedDrug.title + "**\n\n" +
                               "**1. Active Ingredients / Class:**\n• " + matchedDrug.ingredients + "\n\n" +
                               "**2. What It Is Used For:**\n" + matchedDrug.uses + "\n\n" +
                               "**3. Side Effects:**\n" + matchedDrug.side_effects + "\n\n" +
                               "**4. Dosing Principles & Safety Warnings:**\n" + matchedDrug.dosing_and_warnings +
                               medMemoryNote +
                               "\n\n⚠️ *Educational reference only — always take medications under the supervision of a registered doctor (MBBS/MD).*" + locationBlock;
                    }

                    // Step B: Check Symptom-to-Disease Differential Diagnosis (e.g., Sweating + Tension, Coughing, etc.)
                    const symptomDiag = analyzeSymptomsAndMemory(qLow, qRaw, mem);
                    if (symptomDiag) {
                        return symptomDiag + locationBlock;
                    }

                    // Step C: Check Built-in Disease Encyclopedia (e.g., What is hypertension?, Dengue, Diabetes, TB, Depression)
                    const matchedDisease = BUILTIN_DISEASE_KNOWLEDGE.find(d => d.keys.some(k => new RegExp("\\b" + k + "\\b", "i").test(qLow) || qLow.includes(k)));
                    if (matchedDisease) {
                        let disMemoryNote = "";
                        if (mem.pastSymptoms.length > 0) {
                            disMemoryNote = "🧠 **Connected with Your Earlier Chat:** You previously mentioned **" + mem.pastSymptoms.slice(0, 4).join(", ") + "**—compare those with the clinical signs of **" + matchedDisease.title + "** below:\n\n";
                        }
                        return disMemoryNote +
                               "🩺 **" + matchedDisease.title + "**\n\n" +
                               "**1. Clinical Overview:**\n• " + matchedDisease.overview + "\n\n" +
                               "**2. Causes & Risk Factors:**\n" + matchedDisease.causes + "\n\n" +
                               "**3. Key Symptoms & Warning Signs:**\n" + matchedDisease.symptoms + "\n\n" +
                               "**4. Diagnostic Tests:**\n" + matchedDisease.tests + "\n\n" +
                               "**5. Precautions, Diet & Specialist Care:**\n" + matchedDisease.care + locationBlock;
                    }

                    // Step D: Live OpenFDA Lookup for any other medicine name worldwide
                    const isLikelyMed = /\b(tablet|tab|capsule|cap|syrup|injection|ointment|drops|mg|mcg|side effect|dosage|dose|use of|uses of)\b/i.test(qLow);
                    const cleanTopic = qRaw.replace(/\b(what|is|are|the|use|uses|used|of|for|side|effects|effect|dosage|dose|when|how|to|take|symptoms|causes|treatment|disease|might|i|have|iight|if|very|much|and|tell|me|about|explain|tablet|medicine)\b/gi, " ").replace(/[?.,!]+/g, " ").replace(/\s+/g, " ").trim();

                    if (isLikelyMed && cleanTopic.length >= 3 && navigator.onLine !== false) {
                        try {
                            const fdaRes = await origFetch("https://api.fda.gov/drug/label.json?search=openfda.brand_name:\"" + encodeURIComponent(cleanTopic) + "\"+openfda.generic_name:\"" + encodeURIComponent(cleanTopic) + "\"&limit=1");
                            if (fdaRes.ok) {
                                const fdaData = await fdaRes.json();
                                const item = fdaData?.results?.[0];
                                if (item) {
                                    const brands = (item.openfda?.brand_name || [cleanTopic.toUpperCase()]).slice(0, 3).join(", ");
                                    const generics = (item.openfda?.generic_name || item.openfda?.substance_name || [cleanTopic]).slice(0, 3).join(", ");
                                    const uses = (item.indications_and_usage || ["Used under physician supervision."])[0].substring(0, 380);
                                    const sides = (item.adverse_reactions || ["Monitor for allergic reactions or GI upset."])[0].substring(0, 320);
                                    const warn = (item.warnings_and_cautions || item.warnings || item.contraindications || ["Take strictly as prescribed by a doctor."])[0].substring(0, 300);
                                    return "💊 **Medicine Guide — " + brands + "**\n\n" +
                                           "• **Active Ingredients:** " + generics + "\n" +
                                           "• **Uses & Indications:** " + uses + "\n" +
                                           "• **Side Effects:** " + sides + "\n" +
                                           "• **Warnings & Contraindications:** " + warn + "\n" +
                                           "• ⚠️ **Clinical Note:** Always verify individual dosing with a registered physician." + locationBlock;
                                }
                            }
                        } catch (_) {}
                    }

                    // Step E: Live Wikipedia Medical REST API (CORS-safe GET request that works inside Android WebView!)
                    if (cleanTopic.length >= 3 && navigator.onLine !== false) {
                        try {
                            const searchUrl = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=" + encodeURIComponent(cleanTopic) + "&utf8=1&format=json&origin=*&srlimit=1";
                            const sRes = await origFetch(searchUrl);
                            if (sRes.ok) {
                                const sJson = await sRes.json();
                                const bestTitle = sJson?.query?.search?.[0]?.title;
                                if (bestTitle) {
                                    const sumRes = await origFetch("https://en.wikipedia.org/api/rest_v1/page/summary/" + encodeURIComponent(bestTitle.replace(/ /g, "_")));
                                    if (sumRes.ok) {
                                        const sumData = await sumRes.json();
                                        if (sumData.extract && sumData.extract.length > 40) {
                                            const memLine = mem.pastSymptoms.length > 0
                                                ? "🧠 **Context from Your Chat History:** Correlating with your earlier mention of **" + mem.pastSymptoms.slice(0, 4).join(", ") + "**:\n\n"
                                                : "";
                                            return memLine +
                                                   "🩺 **" + (sumData.title || bestTitle) + "**\n\n" +
                                                   "• **Clinical Summary:** " + sumData.extract + "\n\n" +
                                                   "• **Evaluation & Precautions:** Consult a registered **MD Physician or Specialist** for confirmatory blood/imaging tests and personalized treatment. Never start or alter prescription medicines without medical supervision." + locationBlock;
                                        }
                                    }
                                }
                            }
                        } catch (_) {}
                    }

                    // Step F: CORS-Safe GET LLM Fallback (No preflight OPTIONS request so WebView never blocks it)
                    if (navigator.onLine !== false) {
                        try {
                            const memContext = mem.pastSymptoms.length > 0 ? ("Patient prior symptoms: " + mem.pastSymptoms.join(", ") + ". ") : "";
                            const promptStr = "You are Nova AI, a helpful medical doctor assistant. " + memContext + "Answer this medical/medicine question clearly in 4 bullet points (Causes/Uses, Symptoms/Side Effects, Tests/Dosage, Precautions): " + qRaw;
                            const getAiRes = await origFetch("https://text.pollinations.ai/" + encodeURIComponent(promptStr));
                            if (getAiRes.ok) {
                                const txt = await getAiRes.text();
                                if (txt && txt.trim().length > 30 && !txt.includes("<!DOCTYPE")) {
                                    return txt.trim() + locationBlock;
                                }
                            }
                        } catch (_) {}
                    }

                    const memPrefix = mem.pastSymptoms.length > 0
                        ? "Based on your earlier symptoms (**" + mem.pastSymptoms.join(", ") + "**) and your current question (**\"" + qRaw + "\"**):\n\n"
                        : "";
                    return "🩺 **Medical Guidance for \"" + qRaw + "\"**\n\n" + memPrefix +
                           "• **Possible Causes:** Can stem from an acute viral/bacterial infection, metabolic/hormonal shift (thyroid or blood sugar), blood pressure fluctuation, or stress response.\n" +
                           "• **What to Check Right Now:** Check your body temperature (`97°F–99°F` normal), Blood Pressure (`<120/80 mmHg`), and pulse (`60–100 bpm`).\n" +
                           "• **Safe Relief & Next Step:** Stay hydrated with clean water or WHO-ORS, rest well, and share **how many days you've had this or any other symptom** so I can help narrow it down further!" + locationBlock;
                }

                window.fetch = async function(input, init) {
                    const rawUrl = typeof input === 'string' ? input : (input.url || '');

                    if (rawUrl.startsWith('https://') && !rawUrl.includes('127.0.0.1') && !rawUrl.includes('localhost')) {
                        return origFetch(input, init);
                    }

                    if (REMOTE_API && (rawUrl.includes('/api/') || rawUrl.startsWith('api/'))) {
                        try {
                            const pathPart = rawUrl.substring(rawUrl.indexOf('/api/'));
                            const ctrl = new AbortController();
                            const tId = setTimeout(() => ctrl.abort(), 4000);
                            const mergedInit = Object.assign({}, init || {}, { signal: ctrl.signal });
                            const remoteRes = await origFetch(REMOTE_API + pathPart, mergedInit);
                            clearTimeout(tId);
                            if (remoteRes.ok) return remoteRes;
                        } catch (_) {}
                    }

                    const method = ((init && init.method) || 'GET').toUpperCase();
                    let body = {};
                    if (init && init.body) {
                        try { body = JSON.parse(init.body); } catch (_) {}
                    }

                    if (rawUrl.includes('/api/health')) {
                        return new Response(JSON.stringify({
                            status: "ok",
                            service: "Nova Healthtech API",
                            backend_reachable: true,
                            ai_online: true,
                            ai_provider_configured: true,
                            supported_languages_count: 22,
                            states_and_uts_count: 36,
                            hospitals_count: window.__NOVA_36_HOSPITALS.length,
                            medicine_stores_count: window.__NOVA_36_STORES.length
                        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
                    }

                    if (rawUrl.includes('/api/translate-batch')) {
                        const texts = Array.isArray(body.texts) ? body.texts : [];
                        const targetLang = body.target_lang || 'en';
                        const translations = await Promise.all(texts.map(t => gtxTranslate(t, targetLang)));
                        return new Response(JSON.stringify({ status: "ok", target_lang: targetLang, translations: translations }), { status: 200 });
                    }

                    if (rawUrl.includes('/api/translate-text')) {
                        const translated = await gtxTranslate(body.text || '', body.target_lang || 'en');
                        return new Response(JSON.stringify({ status: "ok", translated: translated }), { status: 200 });
                    }

                    if (rawUrl.includes('/api/sos/evaluate-sensors')) {
                        const peak = Number(body.peak_linear_accel_ms2 || 0);
                        const classification = peak >= 54 ? "SUSPECTED_SEVERE_IMPACT" : "NORMAL_MOVEMENT";
                        const note = classification === "NORMAL_MOVEMENT"
                            ? "Movement below hard-ground impact threshold. No SOS triggered."
                            : "Hard ground impact detected (" + peak + " m/s²). Starting 8-second cancellable SOS countdown.";
                        return new Response(JSON.stringify({ status: "ok", evaluation: { classification: classification, confidence_note: note } }), { status: 200 });
                    }

                    if (rawUrl.includes('/api/sos/incident')) {
                        const lat = body.latitude;
                        const lng = body.longitude;
                        const manual = body.manual_location_text || "";
                        const isSim = Boolean(body.is_simulation);
                        const savedTargetNum = window.__getSavedSosAutoCallNumber();
                        const savedTargetName = window.__getSavedSosAutoCallName();
                        const mapsUrl = makeMapsUrl(lat, lng, manual);

                        let callPlaced = false;
                        let statusMsg = "";

                        if (isSim) {
                            statusMsg = "Safe Simulation Mode: GPS telemetry logged locally; automatic call suppressed.";
                        } else if (!savedTargetNum) {
                            callPlaced = false;
                            statusMsg = "Auto-Call Not Placed: No emergency number saved in database. Please save a number in the SOS section.";
                            if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.placeDirectCall === "function") {
                                window.NovaAndroidBridge.placeDirectCall("");
                            }
                        } else {
                            if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.placeDirectCall === "function") {
                                window.NovaAndroidBridge.placeDirectCall(savedTargetNum);
                                callPlaced = true;
                            }
                            statusMsg = "Android emergency call requested for " + savedTargetName + " (" + savedTargetNum + "). Check the phone call status.";
                        }

                        return new Response(JSON.stringify({
                            status: "ok",
                            incident: {
                                incident_uuid: body.incident_uuid || ("sos-" + Date.now()),
                                is_simulation: isSim,
                                direct_call_placed: callPlaced,
                                dispatch_status_message: statusMsg,
                                location: {
                                    latitude: lat, longitude: lng, accuracy_meters: body.accuracy_meters,
                                    location_source: body.location_source || "gps", manual_location_text: manual, maps_url: mapsUrl
                                }
                            }
                        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
                    }

                    if (rawUrl.includes('/api/sos/cancel')) {
                        return new Response(JSON.stringify({ status: "ok", incident_uuid: body.incident_uuid, reason: body.reason }), { status: 200 });
                    }

                    if (rawUrl.includes('/api/sos/contacts')) {
                        let contacts = readStore(getUserScopedKey('nova_sos_contacts'), []);
                        if (method === 'GET') return new Response(JSON.stringify({ status: "ok", contacts: contacts }), { status: 200 });
                        if (method === 'POST') {
                            const phoneClean = String(body.phone_number || '').replace(/[^0-9+]/g, '');
                            if (phoneClean.length < 7) return new Response(JSON.stringify({ status: "error", message: "Enter a valid phone number." }), { status: 400 });
                            const cName = body.contact_name || 'Emergency Contact';
                            const c = { id: Date.now(), contact_name: cName, phone_number: phoneClean, relationship: body.relationship || 'Emergency Contact' };
                            contacts.push(c);
                            writeStore(getUserScopedKey('nova_sos_contacts'), contacts);
                            localStorage.setItem(SOS_NUM_KEY, phoneClean);
                            localStorage.setItem(SOS_NAME_KEY, cName);
                            localStorage.setItem(getUserScopedKey(SOS_NUM_KEY), phoneClean);
                            localStorage.setItem(getUserScopedKey(SOS_NAME_KEY), cName);
                            if (window.NovaAndroidBridge?.savePermanentEmergencyContact) {
                                window.NovaAndroidBridge.savePermanentEmergencyContact(cName, phoneClean);
                            }
                            window.__syncAppHeaderAndAuthUi();
                            return new Response(JSON.stringify({ status: "ok", contact_id: c.id, contacts: contacts }), { status: 201 });
                        }
                        if (method === 'DELETE') {
                            const idToDel = Number(rawUrl.split('/').pop());
                            contacts = contacts.filter(c => Number(c.id) !== idToDel);
                            writeStore(getUserScopedKey('nova_sos_contacts'), contacts);
                            return new Response(JSON.stringify({ status: "ok", contacts: contacts }), { status: 200 });
                        }
                    }

                    if (rawUrl.includes('/api/assistant/chat')) {
                        const userMsg = body.message || '';
                        const lang = body.lang || 'en';
                        const hist = Array.isArray(body.history) ? body.history : [];
                        const engMsg = lang === 'en' ? userMsg : await gtxTranslate(userMsg, 'en');
                        const critKeywords = ['chest pain', 'heart attack', 'cannot breathe', 'unconscious', 'stroke', 'heavy bleeding', 'seizure', 'snakebite', 'suicide', 'poison'];
                        const isCrit = critKeywords.some(k => engMsg.toLowerCase().includes(k));

                        let englishReply = await buildSmartWordByWordAiResponse(engMsg, userMsg, hist);
                        if (isCrit) {
                            englishReply = "🚨 **CRITICAL EMERGENCY — TRIGGER SOS IMMEDIATELY:**\n" +
                                           "Do not wait for chat guidance—tap the red **SOS Emergency** button right now.\n\n" + englishReply;
                        }
                        const localizedReply = lang === 'en' ? englishReply : await gtxTranslate(englishReply, lang);
                        recordChatTurnToMemory(userMsg, localizedReply);
                        return new Response(JSON.stringify({
                            status: "ok",
                            emergency_intercepted: isCrit,
                            ai_response: { reply: localizedReply, english_reply: englishReply }
                        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
                    }

                    if (rawUrl.includes('/api/guide/catalog')) {
                        const tabs = Array.from(document.querySelectorAll('.guide-tab-btn'));
                        const catOrs = (tabs[1] && tabs[1].getAttribute('data-category')) || 'ors';
                        const catHeat = (tabs[2] && tabs[2].getAttribute('data-category')) || 'heat';
                        const catBurns = (tabs[3] && tabs[3].getAttribute('data-category')) || 'burns';
                        const catSnake = (tabs[4] && tabs[4].getAttribute('data-category')) || 'snakebite';
                        return new Response(JSON.stringify({
                            status: "ok",
                            guides: [
                                { title: "WHO-ORS Preparation & Dehydration Protocol", category: catOrs, emergency_warning: false, summary: "Oral rehydration therapy for diarrhea, vomiting, and heat exhaustion.", key_steps: ["Mix 1 packet of WHO-ORS in 1 Litre of clean boiled-cooled water (or 6 tsp sugar + 1/2 tsp salt).", "Sip small amounts every 5-10 minutes after each loose stool.", "Discard unused solution after 24 hours."], warning: "Seek urgent medical care if unable to drink fluids or no urination for 6+ hours." },
                                { title: "Heatstroke & Summer Heat Emergency", category: catHeat, emergency_warning: true, summary: "Rapid cooling when body temperature exceeds 104°F.", key_steps: ["Move to a cool shaded room and elevate feet.", "Sponge skin with cool water and place cold packs on neck and armpits."], warning: "Do NOT give Paracetamol for heatstroke; trigger SOS immediately." },
                                { title: "Severe Bleeding & Thermal Burns First Aid", category: catBurns, emergency_warning: true, summary: "Immediate hemorrhage control and burn cooling.", key_steps: ["Apply firm direct pressure with a clean cloth for 10 minutes on bleeding wounds.", "Cool thermal burns under gentle running tap water for 15-20 minutes."], warning: "Never apply ice, toothpaste, or oil on burns." },
                                { title: "Snakebite Immobilization Protocol", category: catSnake, emergency_warning: true, summary: "National Snakebite First-Aid Protocol.", key_steps: ["Keep the patient calm and immobilize the bitten limb below heart level.", "Remove tight rings/watches and transport immediately to a Government Hospital with ASV."], warning: "Never cut the wound, never suck venom, and never tie a tight tourniquet." }
                            ]
                        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
                    }

                    if (rawUrl.includes('/api/triage/rules')) {
                        return new Response(JSON.stringify({
                            status: "ok",
                            rules: [
                                { id: "chest_pain", urgency: "CRITICAL_EMERGENCY", i18n: { en: { label: "Severe chest pain, pressure, or pain radiating to left arm/jaw" } } },
                                { id: "breathing_difficulty", urgency: "CRITICAL_EMERGENCY", i18n: { en: { label: "Severe shortness of breath, gasping, or bluish lips" } } },
                                { id: "stroke_signs", urgency: "CRITICAL_EMERGENCY", i18n: { en: { label: "Sudden face drooping, arm weakness, or slurred speech (FAST)" } } },
                                { id: "unconscious_bleeding", urgency: "CRITICAL_EMERGENCY", i18n: { en: { label: "Unconsciousness, seizure, or uncontrolled heavy bleeding" } } },
                                { id: "mild_fever_cough", urgency: "ROUTINE", i18n: { en: { label: "Mild fever, seasonal cough, or sore throat without breathing trouble" } } },
                                { id: "routine_body_ache", urgency: "ROUTINE", i18n: { en: { label: "Mild headache, fatigue, or minor indigestion" } } }
                            ]
                        }), { status: 200 });
                    }

                    if (rawUrl.includes('/api/triage/evaluate')) {
                        const selected = Array.isArray(body.selected_rule_ids) ? body.selected_rule_ids : [];
                        const freeText = (body.free_text || '').toLowerCase();
                        const isCrit = selected.some(id => ['chest_pain', 'breathing_difficulty', 'stroke_signs', 'unconscious_bleeding'].includes(id)) ||
                                       ['chest', 'stroke', 'unconscious', 'bleed', 'breath', 'heart', 'seizure', 'snake'].some(k => freeText.includes(k));
                        return new Response(JSON.stringify({
                            status: "ok",
                            triage: {
                                urgency_level: isCrit ? "CRITICAL_EMERGENCY" : "ROUTINE",
                                headline: isCrit ? "🚨 CRITICAL EMERGENCY — TRIGGER SOS IMMEDIATELY" : "✅ ROUTINE / NON-CRITICAL — SCHEDULE DOCTOR CONSULTATION",
                                summary: isCrit ? "High-risk emergency symptoms detected. Trigger SOS immediately." : "No immediate life-threatening red flags detected. Monitor symptoms and consult a physician."
                            }
                        }), { status: 200 });
                    }

                    if (rawUrl.includes('/api/benefits/catalog')) {
                        return new Response(JSON.stringify({
                            status: "ok",
                            schemes: [
                                { badge: "Central Govt • ₹5 Lakh Cover", official_portal_url: "https://pmjay.gov.in", official_portal_label: "Official PM-JAY Portal", i18n: { en: { title: "Ayushman Bharat PM-JAY", coverage: "Up to ₹5,00,000 per family per year", summary: "Cashless secondary and tertiary care at empanelled hospitals across India." } } },
                                { badge: "Gujarat State • ₹10 Lakh Cover", official_portal_url: "https://ma.gujarat.gov.in", official_portal_label: "MA / PMJAY-MA Portal", i18n: { en: { title: "Mukhyamantri Amrutam (PMJAY-MA)", coverage: "Up to ₹10,00,000 cashless cover in Gujarat", summary: "Covers cardiac surgery, dialysis, oncology, and trauma care." } } },
                                { badge: "Generic Medicines • 50–80% Off", official_portal_url: "https://janaushadhi.gov.in", official_portal_label: "Locate Kendra", i18n: { en: { title: "PM Bhartiya Janaushadhi Pariyojana (PMBJP)", coverage: "WHO-GMP certified generic medicines at 50–80% lower prices", summary: "Available at Jan Aushadhi Kendras across all 36 States & UTs." } } }
                            ],
                            hospitals: window.__NOVA_36_HOSPITALS,
                            medicine_stores: window.__NOVA_36_STORES,
                            all_hospitals: window.__NOVA_36_HOSPITALS,
                            all_medicine_stores: window.__NOVA_36_STORES
                        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
                    }

                    if (rawUrl.includes('/api/benefits/screen')) {
                        return new Response(JSON.stringify({
                            status: "ok",
                            guidance: {
                                disclaimer: "Preliminary scheme eligibility check — verify final e-KYC at an official Ayushman Mitra desk.",
                                recommendations: [
                                    { match_level: "HIGH MATCH", title: "Ayushman Bharat PM-JAY (₹5 Lakh Cashless Cover)", reason: "Matches household or 70+ senior citizen coverage criteria.", next_step: "Verify Aadhaar & Ration Card at the nearest Government Hospital Ayushman Mitra desk." },
                                    { match_level: "UNIVERSAL ELIGIBILITY", title: "PM Bhartiya Janaushadhi Pariyojana (50–80% Generic Savings)", reason: "Open to all Indian citizens.", next_step: "Visit any Jan Aushadhi Kendra with a valid prescription." }
                                ]
                            }
                        }), { status: 200 });
                    }

                    if (rawUrl.includes('/api/consultations')) {
                        let list = readStore(getUserScopedKey('nova_consultations'), []);
                        if (rawUrl.includes('/recent') && method === 'GET') return new Response(JSON.stringify({ status: "ok", consultations: list }), { status: 200 });
                        if (rawUrl.includes('/request') && method === 'POST') {
                            const digits = String(body.contact_number || '').replace(/\D/g, '');
                            if (digits.length !== 10) return new Response(JSON.stringify({ status: "error", message: "Enter a valid 10-digit mobile number." }), { status: 400 });
                            const item = { id: Date.now(), patient_name: body.patient_name || 'Patient', district: body.district || 'Bhavnagar (Gujarat)', status: "QUEUED FOR DOCTOR CALLBACK", symptoms_summary: body.symptoms_summary || '', contact_masked: "XXXXXX" + digits.slice(-4) };
                            list.unshift(item);
                            writeStore(getUserScopedKey('nova_consultations'), list);
                            return new Response(JSON.stringify({ status: "ok", consultation_id: item.id, urgency_level: "ROUTINE" }), { status: 201 });
                        }
                        if (method === 'DELETE') {
                            const idToDel = Number(rawUrl.split('/').pop());
                            list = list.filter(i => Number(i.id) !== idToDel);
                            writeStore(getUserScopedKey('nova_consultations'), list);
                            return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
                        }
                    }

                    if (rawUrl.includes('/api/reminders')) {
                        let reminders = readStore(getUserScopedKey('nova_reminders'), []);
                        if (method === 'GET') return new Response(JSON.stringify({ status: "ok", reminders: reminders }), { status: 200 });
                        if (method === 'POST' && rawUrl.endsWith('/taken')) {
                            const parts = rawUrl.split('/');
                            const medId = Number(parts[parts.length - 2]);
                            reminders = reminders.map(r => Number(r.id) === medId ? Object.assign({}, r, { last_taken_at_utc: new Date().toISOString() }) : r);
                            writeStore(getUserScopedKey('nova_reminders'), reminders);
                            return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
                        }
                        if (method === 'POST') {
                            const newMed = { id: Date.now(), medicine_name: body.medicine_name, prescribed_dosage: body.prescribed_dosage, scheduled_time: body.scheduled_time, meal_relation: body.meal_relation || 'after_food', notes: body.notes || '', last_taken_at_utc: null };
                            reminders.push(newMed);
                            writeStore(getUserScopedKey('nova_reminders'), reminders);
                            return new Response(JSON.stringify({ status: "ok", reminder_id: newMed.id }), { status: 201 });
                        }
                        if (method === 'DELETE') {
                            const idToDel = Number(rawUrl.split('/').pop());
                            reminders = reminders.filter(r => Number(r.id) !== idToDel);
                            writeStore(getUserScopedKey('nova_reminders'), reminders);
                            return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
                        }
                    }

                    return origFetch(input, init);
                };
            }

            // =========================================================================
            // STACKED ACCORDION ON MAIN OVERVIEW + TRUE SINGLE-PAGE VIEW FROM ☰ MENU
            // =========================================================================
            function removeEmptyAndOfflinePills() {
                document.querySelectorAll("span, div, button").forEach(el => {
                    if (el.children.length === 0) {
                        const t = (el.textContent || "").trim();
                        if (/Offline\s+Ready/i.test(t) || t === "●" || t === "•") {
                            const p = el.parentElement;
                            el.style.setProperty("display", "none", "important");
                            if (p && (p.textContent || "").trim().length <= 2 && p.tagName !== "BODY") {
                                p.style.setProperty("display", "none", "important");
                            }
                        }
                    }
                });
            }

            // Classifies every top-level feature block in main so NOTHING (like Nearby Medicine Stores) leaks into another page!
            function classifyFeatureBlock(el) {
                if (!el || el.tagName === "SCRIPT" || el.tagName === "STYLE") return "ignore";
                if (el.id === "novaStandaloneAccessibilityScreen") return "accessibility";
                const html = el.innerHTML || "";
                const txt = (el.textContent || "").slice(0, 500);

                if (el.querySelector("#reminderForm, #remindersList, #medicineName") || /Medicine\s+Dosage\s+Reminders/i.test(txt)) return "reminders";
                if (el.querySelector("#consultationForm, #recentConsultationsList") || /Doctor\s+Consultation|Callback\s+Request/i.test(txt)) return "consult";
                if (el.querySelector("#hospitalsGrid, #medicineStoresGrid, #benefitsForm, #storeStateFilter, #hospitalStateFilter") || /Nearby\s+Medicine\s+Stores|Jan\s+Aushadhi|Participating\s+Hospitals|Government\s+Health\s+Schemes/i.test(txt)) return "directory";
                if (el.querySelector("#healthGuidesGrid, .guide-tab-btn") || /First-Aid|WHO-ORS|Snakebite/i.test(txt)) return "guides";
                if (el.querySelector("#triageForm, #triageRulesContainer") || /Emergency\s+Symptom\s+Triage|4\.\s*Symptom\s+Triage/i.test(txt)) return "triage";
                if (el.querySelector("#chatForm, #chatMessages") || /AI\s+Health\s+&\s+Medicine\s+Assistant|3\.\s*Preliminary\s+AI/i.test(txt)) return "ai";
                if (el.querySelector("#triggerSosBtn, #contactForm, #contactsList, #novaPermanentDbSosCard") || /1\.\s*Automatic\s+Accident|2\.\s*Trusted\s+Emergency\s+Contacts|TRIGGER\s+EMERGENCY\s+SOS/i.test(txt)) return "sos";
                if (/Select\s+Your\s+Language|Clinical\s+Safety\s+Notice|Accessible\s+Preliminary\s+Health\s+Guidance/i.test(txt)) return "intro";
                return "intro";
            }

            function setupAccordionWrapper(sec) {
                if (!sec || sec.getAttribute("data-nova-acc-ready") === "1") return;
                const heading = sec.querySelector("h2, h3");
                if (!heading) return;

                sec.setAttribute("data-nova-acc-ready", "1");
                const titleText = (heading.textContent || "Feature Module").trim();

                const headerBar = document.createElement("div");
                headerBar.className = "nova-accordion-header";
                headerBar.innerHTML =
                    '<h2 style="margin:0 !important; font-size:1.08rem !important; color:#1E293B !important;">' + titleText + '</h2>' +
                    '<span class="nova-accordion-chevron">▼ Expand</span>';

                const bodyWrap = document.createElement("div");
                bodyWrap.className = "nova-accordion-body";
                bodyWrap.style.marginTop = "0.9rem";

                while (sec.firstChild) {
                    bodyWrap.appendChild(sec.firstChild);
                }
                // Hide original duplicate heading inside bodyWrap when in accordion mode
                heading.style.display = "none";

                sec.appendChild(headerBar);
                sec.appendChild(bodyWrap);

                headerBar.addEventListener("click", function() {
                    if (window.__currentFeatureMode !== "all") return;
                    const isHidden = bodyWrap.style.display === "none";
                    bodyWrap.style.display = isHidden ? "block" : "none";
                    const chev = headerBar.querySelector(".nova-accordion-chevron");
                    if (chev) chev.textContent = isHidden ? "▲ Collapse" : "▼ Expand";
                });
            }

            function setSectionExpandedState(sec, expanded, showAccordionToggle) {
                if (!sec) return;
                setupAccordionWrapper(sec);
                const headerBar = sec.querySelector(":scope > .nova-accordion-header");
                const bodyWrap = sec.querySelector(":scope > .nova-accordion-body");
                if (!headerBar || !bodyWrap) return;

                const chev = headerBar.querySelector(".nova-accordion-chevron");
                if ( chev ) {
                    chev.style.display = showAccordionToggle ? "inline-block" : "none";
                    chev.textContent = expanded ? "▲ Collapse" : "▼ Expand";
                }
                headerBar.style.cursor = showAccordionToggle ? "pointer" : "default";
                bodyWrap.style.display = expanded ? "block" : "none";
            }

            window.__openNavDrawer = function() {
                const bd = document.getElementById("novaDrawerBackdrop");
                const pn = document.getElementById("novaDrawerPanel");
                if (bd && pn) {
                    bd.style.display = "block";
                    setTimeout(() => { bd.style.opacity = "1"; pn.style.transform = "translateX(0)"; }, 10);
                }
            };

            window.__closeNavDrawer = function() {
                const bd = document.getElementById("novaDrawerBackdrop");
                const pn = document.getElementById("novaDrawerPanel");
                if (bd && pn) {
                    bd.style.opacity = "0";
                    pn.style.transform = "translateX(-102%)";
                    setTimeout(() => { bd.style.display = "none"; }, 220);
                }
            };

            window.__currentFeatureMode = "all";

            window.__openFeatureScreen = function(featureKey) {
                window.__closeNavDrawer();
                window.__currentFeatureMode = featureKey;
                injectHumanClinicalTheme();
                removeEmptyAndOfflinePills();

                const titleMap = {
                    all: "All Features (Stacked View)",
                    sos: "Emergency SOS & Contact Settings",
                    ai: "AI Clinical Assistant & Memory",
                    triage: "Emergency Symptom Triage",
                    guides: "First-Aid & Emergency Guides",
                    directory: "36 States Hospitals & Pharmacies",
                    consult: "Doctor Callback Consultation",
                    reminders: "Medicine Dosage Reminders",
                    accessibility: "Emergency & Background Monitoring"
                };

                const titleEl = document.getElementById("novaAppBarSectionTitle");
                if (titleEl) titleEl.textContent = titleMap[featureKey] || "Nova Healthtech";

                document.querySelectorAll(".nova-drawer-item").forEach(btn => {
                    btn.classList.toggle("active", btn.getAttribute("data-feature") === featureKey);
                });

                const mainEl = document.querySelector("main") || document.querySelector(".container") || document.body;
                const allBlocks = Array.from(mainEl.children).filter(el =>
                    el.id !== "novaM3AppBar" && el.id !== "novaDrawerBackdrop" &&
                    el.id !== "novaDrawerPanel" && el.id !== "novaDedicatedAuthScreen"
                );

                // Also hide/show top body banners (red emergency strip & original header) when viewing a single feature page
                const topBodyBanners = Array.from(document.body.children).filter(el =>
                    el !== mainEl && !el.contains(mainEl) &&
                    el.id !== "novaM3AppBar" && el.id !== "novaDrawerBackdrop" &&
                    el.id !== "novaDrawerPanel" && el.id !== "novaDedicatedAuthScreen" &&
                    el.tagName !== "SCRIPT" && el.tagName !== "STYLE"
                );

                if (featureKey === "all") {
                    topBodyBanners.forEach(b => { b.style.display = ""; });
                    allBlocks.forEach(block => {
                        const cat = classifyFeatureBlock(block);
                        block.style.display = "";
                        if (cat !== "intro" && cat !== "ignore") {
                            // On main website overview: stack features as collapsible dropdowns (keep SOS & AI open first, others stacked as dropdowns)
                            const openByDefault = (cat === "sos" || cat === "ai");
                            setSectionExpandedState(block, openByDefault, true);
                        }
                    });
                    window.scrollTo({ top: 0, behavior: "smooth" });
                    return;
                }

                // SINGLE FEATURE PAGE MODE (Clicked from 3-Line Menu):
                // 1. Hide top banners & language bars so there is zero clutter at the top
                topBodyBanners.forEach(b => { b.style.display = "none"; });

                // 2. Show ONLY blocks belonging to `featureKey`, and force them FULLY OPEN (NOT a dropdown!)
                allBlocks.forEach(block => {
                    const cat = classifyFeatureBlock(block);
                    if (cat === featureKey) {
                        block.style.display = "block";
                        setSectionExpandedState(block, true, false);
                        // Also make sure any nested sub-sections inside this block are visible
                        block.querySelectorAll("section, .card").forEach(sub => { sub.style.display = "block"; });
                    } else {
                        block.style.display = "none";
                    }
                });

                window.scrollTo({ top: 0, behavior: "smooth" });
            };

            window.__syncAppHeaderAndAuthUi = function() {
                removeEmptyAndOfflinePills();
                const user = window.__getActiveUser ? window.__getActiveUser() : null;
                const savedNum = window.__getSavedSosAutoCallNumber ? window.__getSavedSosAutoCallNumber() : '';
                const savedName = window.__getSavedSosAutoCallName ? window.__getSavedSosAutoCallName() : 'Emergency Contact';
                const bgEnabled = window.__isBackgroundAutoCallEnabled ? window.__isBackgroundAutoCallEnabled() : true;

                const headerAuthBtn = document.getElementById("novaTopBarLoginBtn");
                const drawerAuthBtn = document.getElementById("novaDrawerLoginBtn");
                const loggedInBox = document.getElementById("novaAuthLoggedInView");
                const formBox = document.getElementById("novaAuthFormView");
                const profileTitle = document.getElementById("novaLoggedInUserName");

                if (user && user.name) {
                    if (headerAuthBtn) headerAuthBtn.textContent = "👤 " + user.name.split(" ")[0];
                    if (drawerAuthBtn) drawerAuthBtn.textContent = "👤 Account: " + user.name;
                    if (loggedInBox) loggedInBox.style.display = "block";
                    if (formBox) formBox.style.display = "none";
                    if (profileTitle) profileTitle.textContent = user.name + " (" + user.identifier + ")";
                } else {
                    if (headerAuthBtn) headerAuthBtn.textContent = "Log In";
                    if (drawerAuthBtn) drawerAuthBtn.textContent = "Log In / Sign Up";
                    if (loggedInBox) loggedInBox.style.display = "none";
                    if (formBox) formBox.style.display = "block";
                }

                const sosBadge = document.getElementById("novaDbSosBadge");
                if (sosBadge) {
                    sosBadge.textContent = savedNum
                        ? ("Saved in DB: " + savedName + " (" + savedNum + ")")
                        : "No Number Saved Yet";
                    sosBadge.style.color = savedNum ? "#0F766E" : "#DC2626";
                }

                const numIn = document.getElementById("novaDbSosNumInput");
                const nameIn = document.getElementById("novaDbSosNameInput");
                if (numIn && document.activeElement !== numIn && savedNum) numIn.value = savedNum;
                if (nameIn && document.activeElement !== nameIn && savedNum) nameIn.value = savedName;

                const bgBadge = document.getElementById("novaBgAutoCallStatusBadge");
                if (bgBadge) {
                    bgBadge.textContent = bgEnabled
                        ? "ON — Impact monitoring continues when the app is closed"
                        : "OFF — Impact monitoring pauses when the app is closed";
                    bgBadge.style.color = bgEnabled ? "#0F766E" : "#DC2626";
                }

                const bgBtn = document.getElementById("novaBgAutoCallToggleBtn");
                if (bgBtn) {
                    bgBtn.textContent = bgEnabled ? "Turn Background Monitoring OFF" : "Turn Background Monitoring ON";
                    bgBtn.style.background = bgEnabled ? "#DC2626" : "#1D4ED8";
                    bgBtn.style.color = "#FFFFFF";
                }

                // The top emergency bar always remains a direct Call 108 action.
            };

            function mountNavigationDrawerAndModals() {
                injectHumanClinicalTheme();
                removeEmptyAndOfflinePills();

                if (!document.getElementById("novaM3AppBar")) {
                    const bar = document.createElement("div");
                    bar.id = "novaM3AppBar";
                    bar.innerHTML =
                        '<div style="display:flex; align-items:center; gap:0.65rem;">' +
                            '<button type="button" onclick="window.__openNavDrawer()" aria-label="Open Features Menu" ' +
                                'style="background:#F1F5F9 !important; color:#1E293B !important; border:1px solid #CBD5E1 !important; padding:0.4rem 0.65rem !important; font-size:1.1rem !important; border-radius:8px !important; width:auto !important;">' +
                                '☰' +
                            '</button>' +
                            '<div>' +
                                '<div style="font-weight:800; font-size:0.95rem; color:#0F172A; line-height:1.15;">Nova Healthtech</div>' +
                                '<div id="novaAppBarSectionTitle" style="font-size:0.72rem; color:#1D4ED8; font-weight:600;">All Features (Stacked View)</div>' +
                            '</div>' +
                        '</div>' +
                        '<div>' +
                            '<button id="novaTopBarLoginBtn" type="button" onclick="window.__openLoginDashboardScreen()" ' +
                                'style="background:#EFF6FF !important; color:#1D4ED8 !important; border:1px solid #BFDBFE !important; padding:0.4rem 0.85rem !important; font-size:0.8rem !important; border-radius:8px !important; width:auto !important;">' +
                                'Log In' +
                            '</button>' +
                        '</div>';
                    document.body.appendChild(bar);

                    const backdrop = document.createElement("div");
                    backdrop.id = "novaDrawerBackdrop";
                    backdrop.onclick = window.__closeNavDrawer;
                    document.body.appendChild(backdrop);

                    const drawer = document.createElement("aside");
                    drawer.id = "novaDrawerPanel";
                    drawer.innerHTML =
                        '<div style="display:flex; justify-content:space-between; align-items:center; padding-bottom:0.85rem; margin-bottom:0.75rem; border-bottom:1px solid #E2E8F0;">' +
                            '<div>' +
                                '<div style="font-weight:800; font-size:1rem; color:#0F172A;">☰ Features Dashboard</div>' +
                                '<div style="font-size:0.74rem; color:#64748B;">Opens each feature as a full page</div>' +
                            '</div>' +
                            '<button type="button" onclick="window.__closeNavDrawer()" style="background:#F1F5F9 !important; color:#475569 !important; padding:0.3rem 0.6rem !important; width:auto !important;">✕</button>' +
                        '</div>' +
                        '<button type="button" class="nova-drawer-item active" data-feature="all" onclick="window.__openFeatureScreen(\'all\')">🏠 Main Website (Stacked Dropdowns)</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="sos" onclick="window.__openFeatureScreen(\'sos\')">🚨 Emergency SOS &amp; Contact Number</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="ai" onclick="window.__openFeatureScreen(\'ai\')">🧠 AI Health Assistant &amp; Memory</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="triage" onclick="window.__openFeatureScreen(\'triage\')">⚡ Emergency Symptom Triage</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="guides" onclick="window.__openFeatureScreen(\'guides\')">🩹 First-Aid &amp; Emergency Guides</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="directory" onclick="window.__openFeatureScreen(\'directory\')">🏥 36 States Hospitals &amp; Pharmacies</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="consult" onclick="window.__openFeatureScreen(\'consult\')">👨‍⚕️ Doctor Callback Consultation</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="reminders" onclick="window.__openFeatureScreen(\'reminders\')">⏰ Medicine Dosage Reminders</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="accessibility" onclick="window.__openFeatureScreen(\'accessibility\')">⚙️ Emergency &amp; Background Monitoring</button>' +
                        '<div style="margin-top:auto; padding-top:0.85rem; border-top:1px solid #E2E8F0;">' +
                            '<button id="novaDrawerLoginBtn" type="button" onclick="window.__openLoginDashboardScreen()" style="width:100% !important;">Log In / Sign Up</button>' +
                        '</div>';
                    document.body.appendChild(drawer);

                    const authScreen = document.createElement("div");
                    authScreen.id = "novaDedicatedAuthScreen";
                    authScreen.innerHTML =
                        '<div style="width:100%; max-width:420px; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px; padding:1.5rem; box-shadow:0 20px 40px rgba(15,23,42,0.18);">' +
                            '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">' +
                                '<span style="font-size:0.75rem; font-weight:700; color:#1D4ED8; text-transform:uppercase; letter-spacing:0.05em;">Patient Account Dashboard</span>' +
                                '<button type="button" onclick="window.__closeLoginDashboardScreen()" style="background:#F1F5F9 !important; color:#334155 !important; padding:0.35rem 0.7rem !important; width:auto !important;">✕ Close</button>' +
                            '</div>' +
                            '<div id="novaAuthLoggedInView" style="display:none;">' +
                                '<h3 style="margin-bottom:0.35rem;">Signed In Permanently</h3>' +
                                '<p id="novaLoggedInUserName" style="color:#0F766E !important; font-weight:700; font-size:0.95rem; margin-bottom:0.85rem;"></p>' +
                                '<p style="font-size:0.84rem; margin-bottom:1.2rem;">Your Emergency Auto-Call Number, AI Conversation Memory, and Medicine Reminders are permanently synced to your account.</p>' +
                                '<div style="display:flex; gap:0.6rem;">' +
                                    '<button type="button" onclick="window.__closeLoginDashboardScreen()" style="flex:1;">Return to App</button>' +
                                    '<button type="button" onclick="window.__handleNovaLogout()" style="background:#DC2626 !important; color:#FFFFFF !important;">Sign Out</button>' +
                                '</div>' +
                            '</div>' +
                            '<div id="novaAuthFormView">' +
                                '<div style="display:grid; grid-template-columns:1fr 1fr; gap:0.4rem; background:#F1F5F9; padding:0.25rem; border-radius:8px; margin-bottom:1rem;">' +
                                    '<button id="novaAuthTabLogin" type="button" onclick="window.__switchAuthTab(\'login\')" style="background:#1D4ED8; color:#FFFFFF;">Sign In</button>' +
                                    '<button id="novaAuthTabSignup" type="button" onclick="window.__switchAuthTab(\'signup\')" style="background:#F1F5F9; color:#475569;">Sign Up</button>' +
                                '</div>' +
                                '<h3 id="novaAuthScreenTitle" style="margin-bottom:0.35rem;">Sign In to Nova Healthtech</h3>' +
                                '<p id="novaAuthScreenFeedback" style="font-size:0.82rem; margin-bottom:0.9rem;">Sign in once to keep your account, SOS contact, and AI chat memory saved permanently.</p>' +
                                '<div id="novaAuthNameFieldWrap" style="display:none; margin-bottom:0.75rem;">' +
                                    '<label style="display:block; font-size:0.78rem; font-weight:600; margin-bottom:0.25rem;">Full Name</label>' +
                                    '<input id="novaAuthNameInput" type="text" placeholder="Enter your full name" />' +
                                    '<label style="display:block; font-size:0.78rem; font-weight:600; margin:0.6rem 0 0.25rem 0;">Age (Optional)</label>' +
                                    '<input id="novaAuthAgeInput" type="number" placeholder="e.g. 20" />' +
                                '</div>' +
                                '<div style="margin-bottom:0.75rem;">' +
                                    '<label style="display:block; font-size:0.78rem; font-weight:600; margin-bottom:0.25rem;">Mobile Number or Email</label>' +
                                    '<input id="novaAuthIdInput" type="text" placeholder="e.g. 9876543210 or name@email.com" />' +
                                '</div>' +
                                '<div style="margin-bottom:1.1rem;">' +
                                    '<label style="display:block; font-size:0.78rem; font-weight:600; margin-bottom:0.25rem;">Password</label>' +
                                    '<input id="novaAuthPassInput" type="password" placeholder="Enter password (min 4 chars)" />' +
                                '</div>' +
                                '<button id="novaAuthPrimaryActionBtn" data-mode="login" type="button" onclick="window.__submitAuthForm()" style="width:100% !important; padding:0.75rem !important;">Sign In Permanently</button>' +
                            '</div>' +
                        '</div>';
                    document.body.appendChild(authScreen);
                }

                const triggerBtn = document.getElementById("triggerSosBtn") || document.querySelector('button[class*="btn-emergency"]');
                if (triggerBtn && triggerBtn.parentElement && !document.getElementById("novaPermanentDbSosCard")) {
                    const sosCard = document.createElement("div");
                    sosCard.id = "novaPermanentDbSosCard";
                    sosCard.style.cssText = "margin: 0.9rem 0; padding: 1rem; border-radius: 10px; background: #F8FAFC; border: 1px solid #CBD5E1;";
                    sosCard.innerHTML =
                        '<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.4rem; margin-bottom:0.4rem;">' +
                            '<strong style="color:#0F172A; font-size:0.9rem;">📌 Emergency Auto-Call Number (Database)</strong>' +
                            '<span id="novaDbSosBadge" style="font-size:0.78rem; font-weight:700;"></span>' +
                        '</div>' +
                        '<p id="novaDbSosFeedback" style="font-size:0.8rem; color:#475569; margin:0 0 0.65rem 0;">' +
                            'Save anyone\'s mobile number permanently below. When SOS is triggered, Emergency Auto-Caller dials ONLY this saved number.' +
                        '</p>' +
                        '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:0.55rem; margin-bottom:0.65rem;">' +
                            '<input id="novaDbSosNameInput" type="text" placeholder="Contact Name (e.g. Mom)" />' +
                            '<input id="novaDbSosNumInput" type="tel" placeholder="Mobile Number (e.g. 9876543210)" />' +
                        '</div>' +
                        '<div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem;">' +
                            '<button type="button" onclick="window.__saveDbEmergencyNumber()">Save Number</button>' +
                            '<button type="button" onclick="window.__callDbEmergencyNumberNow()" style="background:#DC2626 !important;">Call Saved Number</button>' +
                        '</div>' +
                        '<button type="button" onclick="window.__removeDbEmergencyNumber()" style="background:#F1F5F9 !important; color:#334155 !important; border:1px solid #CBD5E1 !important; width:100% !important; margin-top:0.45rem !important;">Change / Clear Saved Number</button>';
                    triggerBtn.parentElement.insertBefore(sosCard, triggerBtn.nextSibling);
                }

                const chatForm = document.getElementById("chatForm");
                if (chatForm && chatForm.parentElement && !document.getElementById("novaChatMemoryPanel")) {
                    const memPanel = document.createElement("div");
                    memPanel.id = "novaChatMemoryPanel";
                    memPanel.style.cssText = "margin-top: 0.9rem; padding: 0.95rem; border-radius: 10px; background: #F8FAFC; border: 1px solid #E2E8F0;";
                    memPanel.innerHTML =
                        '<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.55rem;">' +
                            '<div>' +
                                '<strong style="color:#0F172A; font-size:0.88rem;">Saved Conversations &amp; Clinical Memory</strong>' +
                                '<div style="font-size:0.74rem; color:#64748B;">Nova AI remembers your past symptoms and adapts its answers automatically</div>' +
                            '</div>' +
                            '<div style="display:flex; gap:0.4rem;">' +
                                '<button type="button" onclick="window.__startNewMemorySession()" style="padding:0.35rem 0.7rem !important; font-size:0.75rem !important; width:auto !important;">+ New Chat</button>' +
                                '<button type="button" onclick="window.__clearAllChatMemory()" style="background:#F1F5F9 !important; color:#475569 !important; border:1px solid #CBD5E1 !important; padding:0.35rem 0.7rem !important; font-size:0.75rem !important; width:auto !important;">Clear</button>' +
                            '</div>' +
                        '</div>' +
                        '<div id="novaMemorySessionsList" style="max-height:180px; overflow-y:auto;"></div>';
                    chatForm.parentElement.appendChild(memPanel);
                }

                const mainContainer = document.querySelector("main") || document.querySelector(".container") || document.body;
                if (mainContainer && !document.getElementById("novaStandaloneAccessibilityScreen")) {
                    const accSec = document.createElement("section");
                    accSec.id = "novaStandaloneAccessibilityScreen";
                    accSec.innerHTML =
                        '<h2>⚙️ Emergency &amp; Background Monitoringing</h2>' +
                        '<p style="margin-bottom:0.8rem;">Control whether Emergency Auto-Caller continues monitoring severe ground impacts and placing automatic calls to your saved contact after the app is closed.</p>' +
                        '<div style="padding:0.95rem; border-radius:10px; background:#F8FAFC; border:1px solid #E2E8F0;">' +
                            '<div style="font-size:0.78rem; color:#64748B; margin-bottom:0.2rem;">Background Auto-Call Status:</div>' +
                            '<div id="novaBgAutoCallStatusBadge" style="font-weight:700; font-size:0.9rem; margin-bottom:0.8rem;"></div>' +
                            '<div style="display:grid; grid-template-columns:1fr; gap:0.5rem;">' +
                                '<button id="novaBgAutoCallToggleBtn" type="button" onclick="window.__toggleBackgroundAutoCallSetting()"></button>' +
                                '<button type="button" onclick="window.__openNativeAccessibilitySettings()" style="background:#F1F5F9 !important; color:#0F172A !important; border:1px solid #CBD5E1 !important;">Open Android Accessibility Settings</button>' +
                            '</div>' +
                        '</div>';
                    mainContainer.appendChild(accSec);
                }

                window.__syncAppHeaderAndAuthUi();
                window.__renderChatMemoryArchive();
                // Initialize stacked dropdown view on main page
                window.__openFeatureScreen(window.__currentFeatureMode || "all");
            }

            async function forcePopulateAll36AndGuides() {
                try {
                    if (typeof renderMedicineStoresCards === "function" && !window.__storeRendererUpgraded) {
                        window.__storeRendererUpgraded = true;
                        window.renderMedicineStoresCards = function() {
                            const grid = document.getElementById("medicineStoresGrid");
                            if (!grid || !cachedBenefitsData) return;
                            grid.replaceChildren();
                            const allStores = cachedBenefitsData.all_medicine_stores || window.__NOVA_36_STORES || [];
                            const stateVal = document.getElementById("storeStateFilter")?.value || "all";
                            const cityVal = document.getElementById("storeCityFilter")?.value || "all";
                            const qClean = (document.getElementById("storeSearchInput")?.value || "").toLowerCase().trim();

                            let filtered = allStores.filter(s => {
                                const matchState = stateVal === "all" || s.state.toLowerCase() === stateVal.toLowerCase();
                                const matchCity = cityVal === "all" || s.city.toLowerCase() === cityVal.toLowerCase();
                                const matchQuery = !qClean || s.name.toLowerCase().includes(qClean) || s.city.toLowerCase().includes(qClean) || s.state.toLowerCase().includes(qClean) || (s.address && s.address.toLowerCase().includes(qClean)) || (s.pin_code && s.pin_code.includes(qClean));
                                return matchState && matchCity && matchQuery;
                            });

                            filtered.forEach(store => {
                                const phoneHtml = store.phone_contact
                                    ? '<a href="tel:' + store.phone_contact + '" class="btn-emergency" style="background:#DC2626 !important; color:#FFFFFF !important;">📞 Call Pharmacy (' + store.phone_contact + ')</a>'
                                    : '';
                                const card = document.createElement("article");
                                card.className = "scheme-card";
                                card.innerHTML = '<div>' +
                                    '<span class="scheme-badge">📍 ' + store.city + ', ' + store.state + '</span>' +
                                    '<h3 style="margin-top:0.45rem;">' + store.name + '</h3>' +
                                    '<p class="scheme-coverage" style="font-weight:600; color:#0F766E !important;">' + (store.facility_category || "Pharmacy") + '</p>' +
                                    '<p class="scheme-summary"><strong>Hours:</strong> ' + store.hours + '</p>' +
                                    '<p class="scheme-summary"><strong>Address:</strong> ' + store.address + (store.pin_code ? ' • PIN: ' + store.pin_code : '') + '</p>' +
                                    (store.services ? '<p class="scheme-summary">' + store.services + '</p>' : '') +
                                    '</div>' +
                                    '<div style="display:grid; grid-template-columns:1fr; gap:0.45rem; margin-top:0.75rem;">' +
                                    phoneHtml +
                                    '<a href="' + store.maps_url + '" target="_blank" rel="noopener noreferrer" class="btn-official-portal">🗺️ Map &amp; Directions ↗</a>' +
                                    '</div>';
                                grid.appendChild(card);
                            });
                            if (typeof stampEnglishBaseline === "function") stampEnglishBaseline(grid);
                        };
                    }

                    if (typeof loadHealthGuides === "function") await loadHealthGuides();
                    if (typeof initTriageModule === "function") await initTriageModule();
                    if (typeof initBenefitsAndAllIndiaDirectories === "function") await initBenefitsAndAllIndiaDirectories();
                    if (typeof runHealthCheck === "function") await runHealthCheck();

                    mountNavigationDrawerAndModals();
                    setInterval(window.__syncAppHeaderAndAuthUi, 1500);
                } catch (e) {}
            }

            if (document.readyState === "loading") {
                document.addEventListener("DOMContentLoaded", () => setTimeout(forcePopulateAll36AndGuides, 80));
            } else {
                setTimeout(forcePopulateAll36AndGuides, 80);
            }
        })();
        
