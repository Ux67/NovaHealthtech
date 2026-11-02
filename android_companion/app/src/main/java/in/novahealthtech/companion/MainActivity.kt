package `in`.novahealthtech.companion

import android.Manifest
import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.accessibilityservice.GestureDescription
import android.annotation.SuppressLint
import android.app.AlertDialog
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import android.graphics.Bitmap
import android.graphics.Path
import android.graphics.Rect
import android.media.AudioManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.telecom.TelecomManager
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.webkit.GeolocationPermissions
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import kotlin.math.abs

class EmergencyContactDbHelper(context: Context) :
    SQLiteOpenHelper(context, "nova_emergency_contact.db", null, 3) {

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            "CREATE TABLE IF NOT EXISTS emergency_auto_call_config (" +
            "id INTEGER PRIMARY KEY CHECK (id = 1), " +
            "contact_name TEXT NOT NULL, " +
            "phone_number TEXT NOT NULL, " +
            "updated_at_ms INTEGER NOT NULL)"
        )
        db.execSQL(
            "CREATE TABLE IF NOT EXISTS app_kv_store (" +
            "store_key TEXT PRIMARY KEY, " +
            "store_val TEXT NOT NULL)"
        )
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        onCreate(db)
    }

    fun saveEmergencyNumber(name: String, number: String) {
        val cleanNum = number.replace(Regex("[^0-9+]"), "")
        val cleanName = name.trim().ifEmpty { "Emergency Contact" }
        val values = ContentValues().apply {
            put("id", 1)
            put("contact_name", cleanName)
            put("phone_number", cleanNum)
            put("updated_at_ms", System.currentTimeMillis())
        }
        writableDatabase.insertWithOnConflict(
            "emergency_auto_call_config",
            null,
            values,
            SQLiteDatabase.CONFLICT_REPLACE
        )
    }

    fun getEmergencyNumber(): Pair<String, String> {
        readableDatabase.rawQuery(
            "SELECT contact_name, phone_number FROM emergency_auto_call_config WHERE id = 1",
            null
        ).use { cursor ->
            if (cursor.moveToFirst()) {
                val nm = cursor.getString(0) ?: "Emergency Contact"
                val ph = cursor.getString(1) ?: ""
                if (ph != "108" && ph.isNotEmpty()) {
                    return Pair(nm, ph)
                }
            }
        }
        return Pair("", "")
    }

    fun clearEmergencyNumber() {
        writableDatabase.delete("emergency_auto_call_config", "id = 1", null)
    }

    fun putKv(key: String, value: String) {
        val values = ContentValues().apply {
            put("store_key", key)
            put("store_val", value)
        }
        writableDatabase.insertWithOnConflict(
            "app_kv_store",
            null,
            values,
            SQLiteDatabase.CONFLICT_REPLACE
        )
    }

    fun getKv(key: String): String {
        readableDatabase.rawQuery(
            "SELECT store_val FROM app_kv_store WHERE store_key = ?",
            arrayOf(key)
        ).use { cursor ->
            if (cursor.moveToFirst()) {
                return cursor.getString(0) ?: ""
            }
        }
        return ""
    }
}

object NovaAutoCallCoordinator {
    const val PREFS_NAME = "nova_emergency_prefs"
    const val KEY_SAVED_SOS_NUMBER = "saved_sos_number"
    const val KEY_SAVED_SOS_NAME = "saved_sos_name"
    const val KEY_BG_AUTO_CALL_ENABLED = "bg_auto_call_when_closed_enabled"

    @Volatile
    var autoCallRequestedAtMs: Long = 0L

    @Volatile
    var targetNumber: String = ""

    @Volatile
    var isAppInForeground: Boolean = false

    @Volatile
    var serviceInstance: NovaAutoCallAccessibilityService? = null

    // Intentionally disabled: accessibility automation must never tap a phone call button.
    fun scheduleImmediateDialerTap() = Unit
}

class NovaAutoCallAccessibilityService : AccessibilityService() {

    private val mainHandler = Handler(Looper.getMainLooper())
    private var lastEventTapMs: Long = 0L

    override fun onServiceConnected() {
        super.onServiceConnected()
        NovaAutoCallCoordinator.serviceInstance = this
        try {
            val info = serviceInfo ?: AccessibilityServiceInfo()
            info.eventTypes = AccessibilityEvent.TYPES_ALL_MASK
            info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            info.flags = AccessibilityServiceInfo.DEFAULT or
                    AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS or
                    AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS
            info.notificationTimeout = 50
            serviceInfo = info
        } catch (_: Exception) {}

        Toast.makeText(
            applicationContext,
            "Emergency Auto-Caller is ON",
            Toast.LENGTH_LONG
        ).show()
    }

    override fun onDestroy() {
        if (NovaAutoCallCoordinator.serviceInstance == this) {
            NovaAutoCallCoordinator.serviceInstance = null
        }
        super.onDestroy()
    }

    private fun isBackgroundAutoCallAllowed(): Boolean {
        val prefs = getSharedPreferences(NovaAutoCallCoordinator.PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getBoolean(NovaAutoCallCoordinator.KEY_BG_AUTO_CALL_ENABLED, true)
    }

    @SuppressLint("MissingPermission")
    private fun isCallAlreadyActive(): Boolean {
        try {
            val tm = getSystemService(Context.TELECOM_SERVICE) as TelecomManager
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_PHONE_STATE) == PackageManager.PERMISSION_GRANTED) {
                if (tm.isInCall) return true
            }
        } catch (_: Exception) {}
        try {
            val am = getSystemService(Context.AUDIO_SERVICE) as AudioManager
            if (am.mode == AudioManager.MODE_IN_CALL || am.mode == AudioManager.MODE_IN_COMMUNICATION) {
                return true
            }
        } catch (_: Exception) {}
        return false
    }

    // Accessibility is not used to simulate taps or accept phone-call dialogs.
    fun triggerTimedDialerTaps() = Unit

    override fun onAccessibilityEvent(event: AccessibilityEvent?) = Unit

    private fun getRealScreenDimensions(): Pair<Float, Float> {
        try {
            val wm = getSystemService(Context.WINDOW_SERVICE) as WindowManager
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                val b = wm.currentWindowMetrics.bounds
                if (b.width() > 0 && b.height() > 0) {
                    return Pair(b.width().toFloat(), b.height().toFloat())
                }
            }
        } catch (_: Exception) {}
        val dm = resources.displayMetrics
        return Pair(dm.widthPixels.toFloat(), dm.heightPixels.toFloat())
    }

    private fun performDialerGreenButtonClick() {
        val (screenW, screenH) = getRealScreenDimensions()

        val roots = mutableListOf<AccessibilityNodeInfo>()
        try {
            rootInActiveWindow?.let { roots.add(it) }
            for (w in windows) {
                w.root?.let { r -> if (!roots.contains(r)) roots.add(r) }
            }
        } catch (_: Exception) {}

        for (root in roots) {
            if (searchAndClickGreenCallNode(root, screenW, screenH)) {
                return
            }
        }

        if (screenW > 0f && screenH > 0f) {
            dispatchScreenTap(screenW * 0.50f, screenH * 0.853f)
        }
    }

    private fun searchAndClickGreenCallNode(
        root: AccessibilityNodeInfo,
        screenW: Float,
        screenH: Float
    ): Boolean {
        if (findAndClickByDescOrId(root)) return true
        if (screenW > 0f && screenH > 0f && findAndClickBottomCenterButton(root, screenW, screenH)) {
            return true
        }
        return false
    }

    private fun findAndClickByDescOrId(node: AccessibilityNodeInfo?): Boolean {
        if (node == null) return false
        val desc = (node.contentDescription?.toString() ?: "").lowercase()
        val resId = (node.viewIdResourceName ?: "").lowercase()

        if (desc == "call" || desc.startsWith("call ") || desc == "dial" ||
            resId.contains("call_button") || resId.contains("single_call") ||
            resId.contains("dialpad_floating_action_button") || resId.contains("normal_call") ||
            resId.contains("dialbutton")
        ) {
            clickNodeAndTapBounds(node)
            return true
        }

        for (i in 0 until node.childCount) {
            if (findAndClickByDescOrId(node.getChild(i))) return true
        }
        return false
    }

    private fun findAndClickBottomCenterButton(
        node: AccessibilityNodeInfo?,
        screenW: Float,
        screenH: Float
    ): Boolean {
        if (node == null) return false
        if (node.isClickable && node.isVisibleToUser) {
            val r = Rect()
            node.getBoundsInScreen(r)
            val cx = r.centerX().toFloat()
            val cy = r.centerY().toFloat()
            if (abs(cx - screenW * 0.50f) < screenW * 0.12f &&
                cy >= screenH * 0.79f && cy <= screenH * 0.90f
            ) {
                node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                dispatchScreenTap(cx, cy)
                return true
            }
        }
        for (i in 0 until node.childCount) {
            if (findAndClickBottomCenterButton(node.getChild(i), screenW, screenH)) return true
        }
        return false
    }

    private fun clickNodeAndTapBounds(node: AccessibilityNodeInfo) {
        var curr: AccessibilityNodeInfo? = node
        var depth = 0
        while (curr != null && depth < 5) {
            if (curr.isClickable) {
                curr.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                break
            }
            curr = curr.parent
            depth++
        }
        val rect = Rect()
        node.getBoundsInScreen(rect)
        if (!rect.isEmpty) {
            dispatchScreenTap(rect.centerX().toFloat(), rect.centerY().toFloat())
        }
    }

    private fun dispatchScreenTap(x: Float, y: Float): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return false
        return try {
            val path = Path().apply {
                moveTo(x, y)
                lineTo(x + 1f, y + 1f)
            }
            val stroke = GestureDescription.StrokeDescription(path, 0L, 95L)
            val gesture = GestureDescription.Builder().addStroke(stroke).build()
            dispatchGesture(gesture, null, null)
        } catch (_: Exception) {
            false
        }
    }

    override fun onInterrupt() {}
}

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var dbHelper: EmergencyContactDbHelper
    private var lastAutoCallTimestampMs: Long = 0L
    private var accessibilityDialogShown: Boolean = false

    private val REMOTE_BACKEND_URL = "https://novahealthtech-2-0.onrender.com"

    companion object {
        private const val PERMISSION_REQ_CODE = 1080
    }

    private fun getSavedPermanentSosNumber(): String {
        val (_, dbNum) = dbHelper.getEmergencyNumber()
        if (dbNum.isNotEmpty() && dbNum != "108") return dbNum

        val prefs = getSharedPreferences(NovaAutoCallCoordinator.PREFS_NAME, Context.MODE_PRIVATE)
        val prefNum = prefs.getString(NovaAutoCallCoordinator.KEY_SAVED_SOS_NUMBER, "")?.trim() ?: ""
        if (prefNum.isNotEmpty() && prefNum != "108") {
            val prefName = prefs.getString(NovaAutoCallCoordinator.KEY_SAVED_SOS_NAME, "Emergency Contact") ?: "Emergency Contact"
            dbHelper.saveEmergencyNumber(prefName, prefNum)
            return prefNum
        }
        return ""
    }

    private fun getSavedPermanentSosName(): String {
        val (dbName, dbNum) = dbHelper.getEmergencyNumber()
        if (dbNum.isNotEmpty() && dbName.isNotEmpty()) return dbName

        val prefs = getSharedPreferences(NovaAutoCallCoordinator.PREFS_NAME, Context.MODE_PRIVATE)
        val name = prefs.getString(NovaAutoCallCoordinator.KEY_SAVED_SOS_NAME, "Emergency Contact")?.trim() ?: "Emergency Contact"
        return name.ifEmpty { "Emergency Contact" }
    }

    private fun savePermanentSosContact(name: String, number: String) {
        val cleanNum = number.replace(Regex("[^0-9+]"), "")
        val cleanName = name.trim().ifEmpty { "Emergency Contact" }
        dbHelper.saveEmergencyNumber(cleanName, cleanNum)

        val prefs = getSharedPreferences(NovaAutoCallCoordinator.PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit()
            .putString(NovaAutoCallCoordinator.KEY_SAVED_SOS_NUMBER, cleanNum)
            .putString(NovaAutoCallCoordinator.KEY_SAVED_SOS_NAME, cleanName)
            .apply()
        NovaAutoCallCoordinator.targetNumber = cleanNum
        syncBackgroundServiceState()
    }

    private fun removePermanentSosContact() {
        dbHelper.clearEmergencyNumber()
        val prefs = getSharedPreferences(NovaAutoCallCoordinator.PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit()
            .remove(NovaAutoCallCoordinator.KEY_SAVED_SOS_NUMBER)
            .remove(NovaAutoCallCoordinator.KEY_SAVED_SOS_NAME)
            .apply()
        NovaAutoCallCoordinator.targetNumber = ""
        syncBackgroundServiceState()
    }

    private fun isBgAutoCallWhenClosedEnabled(): Boolean {
        val prefs = getSharedPreferences(NovaAutoCallCoordinator.PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getBoolean(NovaAutoCallCoordinator.KEY_BG_AUTO_CALL_ENABLED, true)
    }

    private fun setBgAutoCallWhenClosedEnabled(enabled: Boolean) {
        val prefs = getSharedPreferences(NovaAutoCallCoordinator.PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putBoolean(NovaAutoCallCoordinator.KEY_BG_AUTO_CALL_ENABLED, enabled).apply()
        syncBackgroundServiceState()
    }

    private fun syncBackgroundServiceState() {
        try {
            val serviceIntent = Intent(this, AccidentDetectionService::class.java).apply {
                action = AccidentDetectionService.ACTION_START_MONITORING
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent)
            } else {
                startService(serviceIntent)
            }
        } catch (_: Exception) {}
    }

    private fun showConfigureEmergencyContactPrompt() {
        Toast.makeText(
            this,
            "Please save an Emergency Auto-Call Number in the SOS section first.",
            Toast.LENGTH_LONG
        ).show()
        try {
            AlertDialog.Builder(this)
                .setTitle("Save Emergency Auto-Call Number")
                .setMessage("No emergency phone number is saved in the database yet.\n\nEnter the mobile number you want to call in the 'Emergency Auto-Call Number' box and tap Save Number.")
                .setPositiveButton("Go to SOS Setting") { _, _ ->
                    webView.evaluateJavascript(
                        "(function(){ if(window.__openFeatureScreen) window.__openFeatureScreen('sos'); var el = document.getElementById('novaDbSosNumInput'); if(el){ el.scrollIntoView({behavior:'smooth',block:'center'}); el.focus(); } })();",
                        null
                    )
                }
                .show()
        } catch (_: Exception) {}
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        NovaAutoCallCoordinator.isAppInForeground = true

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
        }

        dbHelper = EmergencyContactDbHelper(this)

        val prefs = getSharedPreferences(NovaAutoCallCoordinator.PREFS_NAME, Context.MODE_PRIVATE)
        if (prefs.getString(NovaAutoCallCoordinator.KEY_SAVED_SOS_NUMBER, "") == "108") {
            prefs.edit().remove(NovaAutoCallCoordinator.KEY_SAVED_SOS_NUMBER).apply()
        }

        NovaAutoCallCoordinator.targetNumber = getSavedPermanentSosNumber()

        webView = WebView(this)
        setContentView(webView)

        val settings: WebSettings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.databaseEnabled = true
        settings.setGeolocationEnabled(true)
        settings.allowFileAccess = true
        settings.allowContentAccess = true
        @Suppress("DEPRECATION")
        settings.allowFileAccessFromFileURLs = true
        @Suppress("DEPRECATION")
        settings.allowUniversalAccessFromFileURLs = true
        settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW

        webView.webViewClient = object : WebViewClient() {

            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                super.onPageStarted(view, url, favicon)
                injectNovaStandaloneEngine()
            }

            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                val url = request?.url?.toString() ?: return false
                return handleCustomAndExternalSchemes(url)
            }

            @Deprecated("Deprecated in Java")
            override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                if (url == null) return false
                return handleCustomAndExternalSchemes(url)
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                injectNovaStandaloneEngine()
                if (intent?.getBooleanExtra("CRASH_DETECTED", false) == true) {
                    val peak = intent?.getFloatExtra("PEAK_ACCEL", 58.0f) ?: 58.0f
                    intent?.removeExtra("CRASH_DETECTED")
                    triggerCrashCountdownInJs(peak)
                }
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onGeolocationPermissionsShowPrompt(
                origin: String?,
                callback: GeolocationPermissions.Callback?
            ) {
                callback?.invoke(origin, true, false)
            }
        }

        webView.addJavascriptInterface(NovaJsBridge(), "NovaAndroidBridge")

        loadIndexHtmlWithPreInjectedEngine()
        checkPermissionsAndStartServiceSafely()
    }

    override fun onResume() {
        super.onResume()
        NovaAutoCallCoordinator.isAppInForeground = true
        // The app does not require Accessibility permission to open the system dialer.
    }

    override fun onStop() {
        super.onStop()
        if (!isChangingConfigurations) {
            NovaAutoCallCoordinator.isAppInForeground = false
            if (!isBgAutoCallWhenClosedEnabled()) {
                try {
                    val stopIntent = Intent(this, AccidentDetectionService::class.java).apply {
                        action = AccidentDetectionService.ACTION_STOP_MONITORING
                    }
                    startService(stopIntent)
                } catch (_: Exception) {}
            }
        }
    }

    override fun onDestroy() {
        NovaAutoCallCoordinator.isAppInForeground = false
        if (!isBgAutoCallWhenClosedEnabled()) {
            try {
                val stopIntent = Intent(this, AccidentDetectionService::class.java).apply {
                    action = AccidentDetectionService.ACTION_STOP_MONITORING
                }
                startService(stopIntent)
            } catch (_: Exception) {}
        }
        super.onDestroy()
    }


    private fun loadIndexHtmlWithPreInjectedEngine() {
        try {
            var rawHtml = assets.open("index.html").bufferedReader(Charsets.UTF_8).use { it.readText() }
            // Preserve the visible emergency-service label: Call 108.
            rawHtml = rawHtml.replace(
                Regex("automatic\\s*108\\s*phone\\s*call", RegexOption.IGNORE_CASE),
                "automatic emergency phone call"
            )
            rawHtml = rawHtml.replace(
                Regex("Auto-Calling\\s*108", RegexOption.IGNORE_CASE),
                "Emergency Dialer Ready"
            )
            rawHtml = rawHtml.replace(
                Regex("CALLING\\s*AMBULANCE\\s*\\(108\\)", RegexOption.IGNORE_CASE),
                "OPENING EMERGENCY DIALER"
            )
            // Saved-contact SOS action is labeled separately in the countdown UI.

            val scriptTag = "<script>\n" + buildStandaloneEngineScript() + "\n</script>"
            val patchedHtml = if (rawHtml.contains("<head>", ignoreCase = true)) {
                rawHtml.replaceFirst(Regex("<head>", RegexOption.IGNORE_CASE), "<head>\n$scriptTag")
            } else {
                "$scriptTag\n$rawHtml"
            }

            webView.loadDataWithBaseURL(
                "file:///android_asset/",
                patchedHtml,
                "text/html",
                "UTF-8",
                null
            )
        } catch (_: Exception) {
            webView.loadUrl("file:///android_asset/index.html")
        }
    }

    private fun handleCustomAndExternalSchemes(url: String): Boolean {
        if (url.startsWith("tel:")) {
            // Explicit tel: links must dial exactly the number the user selected.
            // Automatic SOS uses NovaJsBridge.placeDirectCall(), which resolves only the saved contact.
            val rawNum = Uri.decode(url.removePrefix("tel:")).trim()
            if (rawNum.isEmpty()) return true
            executeDirectHardwareCall(rawNum)
            return true
        }
        if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("geo:")) {
            if (!url.contains("127.0.0.1") && !url.contains("localhost")) {
                try {
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                } catch (_: Exception) {}
                return true
            }
        }
        return false
    }

    private fun triggerCrashCountdownInJs(peakAccel: Float) {
        webView.evaluateJavascript(
            "if(typeof startIncidentCountdownWorkflow==='function'){startIncidentCountdownWorkflow('automatic_severe_impact_8s',{peak_linear_accel_ms2:$peakAccel,peak_gyro_rad_s:0.0});}",
            null
        )
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        setIntent(intent)
        if (intent?.getBooleanExtra("CRASH_DETECTED", false) == true) {
            val peak = intent.getFloatExtra("PEAK_ACCEL", 58.0f)
            intent.removeExtra("CRASH_DETECTED")
            triggerCrashCountdownInJs(peak)
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (this::webView.isInitialized && webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    inner class NovaJsBridge {
        @JavascriptInterface
        fun placeDirectCall(phoneNumber: String) {
            runOnUiThread {
                // Automatic SOS calls may only use the currently saved emergency contact.
                // Ignore any number supplied by legacy JavaScript call paths.
                val savedNumber = getSavedPermanentSosNumber()
                if (savedNumber.isEmpty()) {
                    showConfigureEmergencyContactPrompt()
                    return@runOnUiThread
                }
                executeDirectHardwareCall(savedNumber)
            }
        }

        @JavascriptInterface
        fun savePermanentEmergencyContact(name: String, phoneNumber: String) {
            runOnUiThread {
                savePermanentSosContact(name, phoneNumber)
                Toast.makeText(
                    this@MainActivity,
                    "Saved in Database: ${getSavedPermanentSosName()} (${getSavedPermanentSosNumber()})",
                    Toast.LENGTH_LONG
                ).show()
            }
        }

        @JavascriptInterface
        fun removePermanentEmergencyContact() {
            runOnUiThread {
                removePermanentSosContact()
                Toast.makeText(
                    this@MainActivity,
                    "Emergency number cleared from database.",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }

        @JavascriptInterface
        fun getPermanentEmergencyNumber(): String {
            return getSavedPermanentSosNumber()
        }

        @JavascriptInterface
        fun getPermanentEmergencyName(): String {
            return getSavedPermanentSosName()
        }

        @JavascriptInterface
        fun scheduleMedicationReminder(
            id: String,
            medicineName: String,
            prescribedDose: String,
            scheduledTime: String,
            mealRelation: String,
            notes: String
        ) {
            MedicationAlarmScheduler.schedule(
                this@MainActivity, id, medicineName, prescribedDose, scheduledTime, mealRelation, notes
            )
        }

        @JavascriptInterface
        fun cancelMedicationReminder(id: String) {
            MedicationAlarmScheduler.cancel(this@MainActivity, id)
        }

        @JavascriptInterface
        fun savePersistentData(key: String, jsonValue: String) {
            dbHelper.putKv(key, jsonValue)
        }

        @JavascriptInterface
        fun loadPersistentData(key: String): String {
            return dbHelper.getKv(key)
        }

        @JavascriptInterface
        fun isBackgroundAutoCallEnabled(): Boolean {
            return isBgAutoCallWhenClosedEnabled()
        }

        @JavascriptInterface
        fun setBackgroundAutoCallEnabled(enabled: Boolean) {
            runOnUiThread {
                setBgAutoCallWhenClosedEnabled(enabled)
                val stateLabel = if (enabled) "ON (Active when app is closed)" else "OFF (Paused when app is closed)"
                Toast.makeText(
                    this@MainActivity,
                    "Background Auto-Calling: $stateLabel",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }

        @JavascriptInterface
        fun openAccessibilitySettings() {
            runOnUiThread {
                try {
                    startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                } catch (_: Exception) {}
            }
        }

        @JavascriptInterface
        fun isAutoCallerAccessibilityEnabled(): Boolean {
            return isAccessibilityServiceEnabled()
        }
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        if (NovaAutoCallCoordinator.serviceInstance != null) return true
        val enabledServices = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: return false
        return enabledServices.contains(packageName, ignoreCase = true) ||
               enabledServices.contains("NovaAutoCallAccessibilityService", ignoreCase = true)
    }

    private fun executeDirectHardwareCall(phoneNumber: String) {
        val cleanNumber = phoneNumber.replace(Regex("[^0-9+]"), "")
        if (cleanNumber.isEmpty()) {
            showConfigureEmergencyContactPrompt()
            return
        }
        // Show the OS dialer with the saved/selected number. The user makes the final call action.
        try {
            startActivity(Intent(Intent.ACTION_DIAL, Uri.fromParts("tel", cleanNumber, null)))
        } catch (_: Exception) {
            Toast.makeText(this, "Unable to open the phone dialer. Please use your phone's calling app.", Toast.LENGTH_LONG).show()
        }
    }

    private fun checkPermissionsAndStartServiceSafely() {
        val needed = mutableListOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.CALL_PHONE
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            needed.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        val missing = needed.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, missing.toTypedArray(), PERMISSION_REQ_CODE)
        } else {
            syncBackgroundServiceState()
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQ_CODE) {
            syncBackgroundServiceState()
        }
    }

    private fun injectNovaStandaloneEngine() {
        webView.evaluateJavascript(buildStandaloneEngineScript(), null)
    }

    private fun buildStandaloneEngineScript(): String {
        val remoteBase = REMOTE_BACKEND_URL.trimEnd('/')
        return """
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
                    'h1, h2, h3, h4 { color: var(--hc-text) !important; font-weight: 700 !important; letter-spacing: -0.015em !important; margin-top: 0 !important; }' +
                    'p, li, label, small, .scheme-summary, .scheme-coverage { color: var(--hc-muted) !important; }' +
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

                const REMOTE_API = "$remoteBase";
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
                    return c !== '108' && /^\+?[0-9]{7,15}${'$'}/.test(c);
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
                    if (fb) { fb.style.color = '#0F766E'; fb.textContent = 'Saved in Database! SOS will automatically call ' + nameVal + ' (' + numVal + ').'; }
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
                        if (window.showNotice) window.showNotice('No emergency number saved yet. Add a trusted contact in Emergency Settings.', 'warning'); else console.warn('No emergency contact saved.');
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
                    try {
                        if (window.NovaAndroidBridge && typeof window.NovaAndroidBridge.openAccessibilitySettings === 'function') {
                            window.NovaAndroidBridge.openAccessibilitySettings();
                            return;
                        }
                    } catch (e) {}
                    if (window.showNotice) window.showNotice("Emergency calls are user-confirmed. Accessibility screen-tapping is not used.", "info");
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

                // Do not globally rewrite tel:108 links. The emergency bar must always call 108.

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
                        let timeoutId = null;
                        try {
                            const parsedUrl = new URL(rawUrl, window.location.href);
                            const apiPath = parsedUrl.pathname + parsedUrl.search;
                            if (!apiPath.startsWith('/api/')) {
                                return new Response(JSON.stringify({
                                    status: "error",
                                    message: "Invalid API path."
                                }), { status: 400, headers: { 'Content-Type': 'application/json' } });
                            }
                            const controller = new AbortController();
                            timeoutId = setTimeout(() => controller.abort(), 30000);
                            const requestInit = Object.assign({}, init || {}, {
                                signal: controller.signal,
                                cache: "no-store"
                            });
                            // Return the real backend response, including HTTP errors.
                            // Never replace a failed live request with a fake success response.
                            return await origFetch(REMOTE_API + apiPath, requestInit);
                        } catch (error) {
                            const message = error && error.name === "AbortError"
                                ? "Nova Healthtech backend timed out. Please retry when the connection is stable."
                                : "Nova Healthtech backend is unreachable. Check the internet connection and Render service status.";
                            return new Response(JSON.stringify({
                                status: "error",
                                backend_reachable: false,
                                message: message
                            }), { status: 503, headers: { 'Content-Type': 'application/json' } });
                        } finally {
                            if (timeoutId !== null) clearTimeout(timeoutId);
                        }
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
                            statusMsg = "Emergency Auto-Caller dialing " + savedTargetName + " (" + savedTargetNum + ").";
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
                    sos: "Emergency SOS & Auto-Call Config",
                    ai: "AI Clinical Assistant & Memory",
                    triage: "Emergency Symptom Triage",
                    guides: "First-Aid & Emergency Guides",
                    directory: "36 States Hospitals & Pharmacies",
                    consult: "Doctor Callback Consultation",
                    reminders: "Medicine Dosage Reminders",
                    accessibility: "Accessibility & Background Auto-Call"
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
                        ? "ON — Auto-Calling continues in background when app is closed"
                        : "OFF — Auto-Calling stops when app is closed";
                    bgBadge.style.color = bgEnabled ? "#0F766E" : "#DC2626";
                }

                const bgBtn = document.getElementById("novaBgAutoCallToggleBtn");
                if (bgBtn) {
                    bgBtn.textContent = bgEnabled ? "Turn Background Auto-Call OFF" : "Turn Background Auto-Call ON";
                    bgBtn.style.background = bgEnabled ? "#DC2626" : "#1D4ED8";
                    bgBtn.style.color = "#FFFFFF";
                }

                // Only the countdown's saved-contact action follows the stored contact.
                // The top emergency bar and all explicit 108 links remain unchanged.
                const savedContactAction = document.getElementById("sosDirectCall108");
                if (savedContactAction) {
                    savedContactAction.textContent = savedNum ? ("📞 Call " + savedName + " (" + savedNum + ")") : "Save SOS Number";
                    savedContactAction.href = savedNum ? ("tel:" + savedNum) : "javascript:window.__openFeatureScreen('sos')";
                }
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
                        '<button type="button" class="nova-drawer-item" data-feature="sos" onclick="window.__openFeatureScreen(\'sos\')">🚨 Emergency SOS &amp; Auto-Call Number</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="ai" onclick="window.__openFeatureScreen(\'ai\')">🧠 AI Health Assistant &amp; Memory</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="triage" onclick="window.__openFeatureScreen(\'triage\')">⚡ Emergency Symptom Triage</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="guides" onclick="window.__openFeatureScreen(\'guides\')">🩹 First-Aid &amp; Emergency Guides</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="directory" onclick="window.__openFeatureScreen(\'directory\')">🏥 36 States Hospitals &amp; Pharmacies</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="consult" onclick="window.__openFeatureScreen(\'consult\')">👨‍⚕️ Doctor Callback Consultation</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="reminders" onclick="window.__openFeatureScreen(\'reminders\')">⏰ Medicine Dosage Reminders</button>' +
                        '<button type="button" class="nova-drawer-item" data-feature="accessibility" onclick="window.__openFeatureScreen(\'accessibility\')">⚙️ Accessibility &amp; Background Auto-Call</button>' +
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
                        '<h2>⚙️ Accessibility &amp; Background Auto-Calling</h2>' +
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
        """.trimIndent()
    }
}