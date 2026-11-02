package `in`.novahealthtech.companion

import android.Manifest
import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.media.AudioAttributes
import android.media.RingtoneManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.PowerManager
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.telecom.TelecomManager
import android.widget.Toast
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import kotlin.math.abs
import kotlin.math.sqrt

class AccidentDetectionService : Service(), SensorEventListener {

    companion object {
        const val ACTION_START_MONITORING = "in.novahealthtech.companion.ACTION_START_MONITORING"
        const val ACTION_STOP_MONITORING = "in.novahealthtech.companion.ACTION_STOP_MONITORING"
        const val ACTION_CANCEL_SOS_COUNTDOWN = "in.novahealthtech.companion.ACTION_CANCEL_SOS_COUNTDOWN"
        const val ACTION_CALL_SAVED_NOW = "in.novahealthtech.companion.ACTION_CALL_SAVED_NOW"

        const val PREFS_NAME = "nova_emergency_prefs"
        const val KEY_SAVED_SOS_NUMBER = "saved_sos_number"
        const val KEY_SAVED_SOS_NAME = "saved_sos_name"
        const val KEY_BG_AUTO_CALL_ENABLED = "bg_auto_call_when_closed_enabled"

        private const val MONITOR_CHANNEL_ID = "nova_crash_monitor_channel"
        private const val ALERT_CHANNEL_ID = "nova_crash_emergency_alert_channel"
        private const val MONITOR_NOTIF_ID = 10801
        private const val ALERT_NOTIF_ID = 10802

        // =========================================================================
        // STRICT HARD-GROUND IMPACT CALIBRATION (NO ROTATION, NO SWIRLS, NO DESK DROPS)
        // =========================================================================
        // 1. True Free-Fall Requirement: Total acceleration (with gravity) must stay < 2.2 m/s²
        //    continuously for at least 180 ms (rules out short 15-30cm desk drops & hand shakes)
        private const val FREE_FALL_G_LIMIT_MS2 = 2.2f
        private const val MIN_CONTINUOUS_FREE_FALL_MS = 180L
        private const val FREE_FALL_IMPACT_WINDOW_MS = 450L

        // 2. Hard Ground Hit Thresholds (Linear Acceleration without gravity):
        //    - Direct collision hit without free-fall: >= 65.0 m/s² (~6.6G hard impact)
        //    - Ground hit immediately after >=180ms free-fall: >= 54.0 m/s² (~5.5G hard impact)
        private const val DIRECT_COLLISION_LINEAR_MS2 = 65.0f
        private const val GROUND_HIT_AFTER_FALL_LINEAR_MS2 = 54.0f

        // 3. Instantaneous Shock Jerk Filter:
        //    Swirling in hand has smooth acceleration (jerk < 400 m/s³).
        //    Hitting hard ground creates an abrupt deceleration spike (jerk >= 1400 m/s³).
        private const val MIN_HARD_IMPACT_JERK_MS3 = 1400.0f

        // 4. Anti-Swirl Filter: If linear acceleration was already high (> 14 m/s²) for multiple
        //    samples right before the peak (continuous swinging/swirling in hand), reject it.
        private const val SWIRL_CONTINUOUS_ACCEL_MS2 = 14.0f
        private const val MAX_SWIRL_SAMPLES_BEFORE_HIT = 6

        // 5. Post-Hit Ground Stillness Verification:
        //    Phone must lie motionless on the ground (< 1.6 m/s²) after bouncing settles.
        private const val POST_HIT_BOUNCE_SETTLE_MS = 1500L
        private const val STILLNESS_VERIFY_WINDOW_MS = 2800L
        private const val STILLNESS_MAX_LINEAR_MS2 = 1.6f
        private const val MAX_MOVEMENT_SAMPLES_ALLOWED = 4

        private const val SOS_COUNTDOWN_SECONDS = 8
        private const val COOLDOWN_BETWEEN_TRIGGERS_MS = 25000L
    }

    private enum class DetectorState {
        MONITORING,
        POST_IMPACT_SETTLING,
        VERIFYING_STILLNESS,
        COUNTDOWN_ACTIVE
    }

    private lateinit var sensorManager: SensorManager
    private var rawAccelSensor: Sensor? = null
    private var linearAccelSensor: Sensor? = null

    private val mainHandler = Handler(Looper.getMainLooper())
    private var wakeLock: PowerManager.WakeLock? = null

    private val gravity = FloatArray(3) { 0f }
    private var hasGravityBaseline = false

    // Free-fall & anti-swirl tracking (Zero Gyroscope usage)
    private var freeFallStartMs: Long = 0L
    private var lastConfirmedFreeFallMs: Long = 0L
    private var consecutiveSwirlSamples: Int = 0
    private var prevLinearMag: Float = 0f
    private var prevLinearTimestampNs: Long = 0L

    @Volatile
    private var currentState: DetectorState = DetectorState.MONITORING
    private var candidateImpactPeakMs2: Float = 0f
    private var impactDetectedAtMs: Long = 0L
    private var stillnessActiveMovementCount: Int = 0
    private var lastTriggerCompletedAtMs: Long = 0L
    private var countdownRemainingSec: Int = SOS_COUNTDOWN_SECONDS

    private fun getSavedEmergencyNumber(): String {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val num = prefs.getString(KEY_SAVED_SOS_NUMBER, "")?.trim() ?: ""
        return if (num == "108") "" else num
    }

    private fun getSavedEmergencyName(): String {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val name = prefs.getString(KEY_SAVED_SOS_NAME, "Emergency Contact")?.trim() ?: "Emergency Contact"
        return name.ifEmpty { "Emergency Contact" }
    }

    private fun isBackgroundAutoCallingAllowed(): Boolean {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getBoolean(KEY_BG_AUTO_CALL_ENABLED, true)
    }

    private val countdownTickRunnable = object : Runnable {
        override fun run() {
            if (currentState != DetectorState.COUNTDOWN_ACTIVE) return

            if (!NovaAutoCallCoordinator.isAppInForeground && !isBackgroundAutoCallingAllowed()) {
                abortActiveCountdown()
                return
            }

            val targetNumber = getSavedEmergencyNumber()
            if (countdownRemainingSec <= 0) {
                currentState = DetectorState.MONITORING
                lastTriggerCompletedAtMs = System.currentTimeMillis()
                releaseWakeLock()
                showHighPriorityCountdownNotification(
                    0,
                    candidateImpactPeakMs2,
                    targetNumber,
                    getSavedEmergencyName()
                )
                return
            }
            showHighPriorityCountdownNotification(
                countdownRemainingSec,
                candidateImpactPeakMs2,
                targetNumber,
                getSavedEmergencyName()
            )
            vibrateWarningPulse()
            countdownRemainingSec--
            mainHandler.postDelayed(this, 1000L)
        }
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        rawAccelSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        linearAccelSensor = sensorManager.getDefaultSensor(Sensor.TYPE_LINEAR_ACCELERATION)
        registerSensors()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP_MONITORING -> {
                abortActiveCountdown()
                sensorManager.unregisterListener(this)
                stopForeground(true)
                stopSelf()
                return START_NOT_STICKY
            }
            ACTION_CANCEL_SOS_COUNTDOWN -> {
                abortActiveCountdown()
                return START_STICKY
            }
            ACTION_CALL_SAVED_NOW -> {
                mainHandler.removeCallbacks(countdownTickRunnable)
                currentState = DetectorState.MONITORING
                lastTriggerCompletedAtMs = System.currentTimeMillis()
                cancelAlertNotification()
                executeBackgroundEmergencyCall(
                    getSavedEmergencyNumber(),
                    candidateImpactPeakMs2.coerceAtLeast(55.0f)
                )
                return START_STICKY
            }
        }

        if (!NovaAutoCallCoordinator.isAppInForeground && !isBackgroundAutoCallingAllowed()) {
            sensorManager.unregisterListener(this)
            stopForeground(true)
            stopSelf()
            return START_NOT_STICKY
        }

        startForegroundSafely()
        registerSensors()
        return if (isBackgroundAutoCallingAllowed()) START_STICKY else START_NOT_STICKY
    }

    private fun startForegroundSafely() {
        val notification = buildPersistentMonitoringNotification()
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val fgType = if (hasLocationPermission()) {
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION
                } else {
                    0
                }
                if (fgType != 0) {
                    startForeground(MONITOR_NOTIF_ID, notification, fgType)
                } else {
                    startForeground(MONITOR_NOTIF_ID, notification)
                }
            } else {
                startForeground(MONITOR_NOTIF_ID, notification)
            }
        } catch (_: Exception) {
            try {
                startForeground(MONITOR_NOTIF_ID, notification)
            } catch (_: Exception) {}
        }
    }

    private fun registerSensors() {
        sensorManager.unregisterListener(this)
        rawAccelSensor?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
        }
        linearAccelSensor?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
        }
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event == null) return

        if (!NovaAutoCallCoordinator.isAppInForeground && !isBackgroundAutoCallingAllowed()) {
            return
        }

        val nowMs = System.currentTimeMillis()

        when (event.sensor.type) {
            Sensor.TYPE_ACCELEROMETER -> {
                val ax = event.values[0]
                val ay = event.values[1]
                val az = event.values[2]
                val totalMag = sqrt(ax * ax + ay * ay + az * az)

                // Track continuous free-fall duration (must stay < 2.2 m/s² for >= 180 ms)
                if (totalMag < FREE_FALL_G_LIMIT_MS2) {
                    if (freeFallStartMs == 0L) {
                        freeFallStartMs = nowMs
                    } else if (nowMs - freeFallStartMs >= MIN_CONTINUOUS_FREE_FALL_MS) {
                        lastConfirmedFreeFallMs = nowMs
                    }
                } else {
                    freeFallStartMs = 0L
                }

                if (linearAccelSensor == null) {
                    val alpha = 0.85f
                    if (!hasGravityBaseline) {
                        gravity[0] = ax
                        gravity[1] = ay
                        gravity[2] = az
                        hasGravityBaseline = true
                    } else {
                        gravity[0] = alpha * gravity[0] + (1f - alpha) * ax
                        gravity[1] = alpha * gravity[1] + (1f - alpha) * ay
                        gravity[2] = alpha * gravity[2] + (1f - alpha) * az
                    }
                    val lx = ax - gravity[0]
                    val ly = ay - gravity[1]
                    val lz = az - gravity[2]
                    val linearMag = sqrt(lx * lx + ly * ly + lz * lz)
                    processLinearImpactSample(linearMag, event.timestamp, nowMs)
                }
            }

            Sensor.TYPE_LINEAR_ACCELERATION -> {
                val lx = event.values[0]
                val ly = event.values[1]
                val lz = event.values[2]
                val linearMag = sqrt(lx * lx + ly * ly + lz * lz)
                processLinearImpactSample(linearMag, event.timestamp, nowMs)
            }
        }
    }

    private fun processLinearImpactSample(linearMag: Float, timestampNs: Long, nowMs: Long) {
        val dtSec = if (prevLinearTimestampNs > 0L && timestampNs > prevLinearTimestampNs) {
            ((timestampNs - prevLinearTimestampNs) / 1_000_000_000.0f).coerceAtLeast(0.005f)
        } else {
            0.02f
        }
        val jerkMs3 = abs(linearMag - prevLinearMag) / dtSec
        prevLinearMag = linearMag
        prevLinearTimestampNs = timestampNs

        when (currentState) {
            DetectorState.MONITORING -> {
                if (nowMs - lastTriggerCompletedAtMs < COOLDOWN_BETWEEN_TRIGGERS_MS) return

                // Anti-Swirl check: Hand swirling keeps linear acceleration elevated (14..38 m/s²)
                // across many consecutive samples without a true free-fall.
                if (linearMag in SWIRL_CONTINUOUS_ACCEL_MS2..45.0f) {
                    consecutiveSwirlSamples++
                } else if (linearMag < 5.0f) {
                    consecutiveSwirlSamples = 0
                }

                val isSwirlingInHand = consecutiveSwirlSamples > MAX_SWIRL_SAMPLES_BEFORE_HIT
                val hadTrueFreeFall = (nowMs - lastConfirmedFreeFallMs) <= FREE_FALL_IMPACT_WINDOW_MS

                val requiredImpactMs2 = if (hadTrueFreeFall) {
                    GROUND_HIT_AFTER_FALL_LINEAR_MS2
                } else {
                    DIRECT_COLLISION_LINEAR_MS2
                }

                // Trigger ONLY on a sharp ground/collision hit with extreme shock jerk (never on swirls)
                if (!isSwirlingInHand && linearMag >= requiredImpactMs2 && jerkMs3 >= MIN_HARD_IMPACT_JERK_MS3) {
                    candidateImpactPeakMs2 = linearMag
                    impactDetectedAtMs = nowMs
                    stillnessActiveMovementCount = 0
                    currentState = DetectorState.POST_IMPACT_SETTLING
                }
            }

            DetectorState.POST_IMPACT_SETTLING -> {
                if (linearMag > candidateImpactPeakMs2) {
                    candidateImpactPeakMs2 = linearMag
                }
                if (nowMs - impactDetectedAtMs >= POST_HIT_BOUNCE_SETTLE_MS) {
                    currentState = DetectorState.VERIFYING_STILLNESS
                    stillnessActiveMovementCount = 0
                }
            }

            DetectorState.VERIFYING_STILLNESS -> {
                // If the phone is still moving in hand after the hit, cancel immediately
                if (linearMag > STILLNESS_MAX_LINEAR_MS2) {
                    stillnessActiveMovementCount++
                }

                if (stillnessActiveMovementCount > MAX_MOVEMENT_SAMPLES_ALLOWED) {
                    currentState = DetectorState.MONITORING
                    candidateImpactPeakMs2 = 0f
                    consecutiveSwirlSamples = 0
                    return
                }

                val elapsedSinceImpact = nowMs - impactDetectedAtMs
                if (elapsedSinceImpact >= (POST_HIT_BOUNCE_SETTLE_MS + STILLNESS_VERIFY_WINDOW_MS)) {
                    beginEmergencyCountdown(candidateImpactPeakMs2)
                }
            }

            DetectorState.COUNTDOWN_ACTIVE -> {}
        }
    }

    private fun beginEmergencyCountdown(peakAccelMs2: Float) {
        if (!NovaAutoCallCoordinator.isAppInForeground && !isBackgroundAutoCallingAllowed()) {
            currentState = DetectorState.MONITORING
            return
        }

        currentState = DetectorState.COUNTDOWN_ACTIVE
        countdownRemainingSec = SOS_COUNTDOWN_SECONDS
        acquireTemporaryWakeLock()

        try {
            val uiIntent = Intent(this, MainActivity::class.java).apply {
                addFlags(
                    Intent.FLAG_ACTIVITY_NEW_TASK or
                    Intent.FLAG_ACTIVITY_SINGLE_TOP or
                    Intent.FLAG_ACTIVITY_CLEAR_TOP
                )
                putExtra("CRASH_DETECTED", true)
                putExtra("PEAK_ACCEL", peakAccelMs2)
            }
            startActivity(uiIntent)
        } catch (_: Exception) {}

        mainHandler.removeCallbacks(countdownTickRunnable)
        mainHandler.post(countdownTickRunnable)
    }

    private fun abortActiveCountdown() {
        mainHandler.removeCallbacks(countdownTickRunnable)
        currentState = DetectorState.MONITORING
        candidateImpactPeakMs2 = 0f
        consecutiveSwirlSamples = 0
        lastTriggerCompletedAtMs = System.currentTimeMillis()
        cancelAlertNotification()
        releaseWakeLock()
    }

    @SuppressLint("MissingPermission")
    private fun executeBackgroundEmergencyCall(emergencyNumber: String, peakAccelMs2: Float) {
        if (!NovaAutoCallCoordinator.isAppInForeground && !isBackgroundAutoCallingAllowed()) {
            return
        }

        val cleanNumber = emergencyNumber.replace(Regex("[^0-9+]"), "")
        if (cleanNumber.isEmpty() || cleanNumber == "108") {
            Toast.makeText(
                applicationContext,
                "SOS Triggered: No emergency contact number saved. Configure a contact in Nova Healthtech.",
                Toast.LENGTH_LONG
            ).show()
            try {
                val configUi = Intent(this, MainActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
                }
                startActivity(configUi)
            } catch (_: Exception) {}
            return
        }

        // Invoked only after the user taps the notification action.
        // ACTION_DIAL opens the system dialer; the user reviews and places the call.
        val dialIntent = Intent(
            Intent.ACTION_DIAL,
            Uri.fromParts("tel", cleanNumber, null)
        ).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        try {
            startActivity(dialIntent)
        } catch (_: Exception) {
            val fallbackUi = Intent(this, MainActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
                putExtra("CRASH_DETECTED", true)
                putExtra("PEAK_ACCEL", peakAccelMs2)
            }
            try {
                startActivity(fallbackUi)
            } catch (_: Exception) {
                Toast.makeText(applicationContext, "Unable to open the phone dialer. Use your phone's emergency calling feature.", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun acquireTemporaryWakeLock() {
        try {
            val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
            if (wakeLock == null) {
                @Suppress("DEPRECATION")
                wakeLock = pm.newWakeLock(
                    PowerManager.PARTIAL_WAKE_LOCK or PowerManager.ACQUIRE_CAUSES_WAKEUP,
                    "NovaHealthtech::CrashAlertWakeLock"
                )
            }
            if (wakeLock?.isHeld == false) {
                wakeLock?.acquire(15000L)
            }
        } catch (_: Exception) {}
    }

    private fun releaseWakeLock() {
        try {
            if (wakeLock?.isHeld == true) {
                wakeLock?.release()
            }
        } catch (_: Exception) {}
    }

    private fun vibrateWarningPulse() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vm = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                vm.defaultVibrator.vibrate(
                    VibrationEffect.createOneShot(350L, VibrationEffect.DEFAULT_AMPLITUDE)
                )
            } else {
                @Suppress("DEPRECATION")
                val v = getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    v.vibrate(VibrationEffect.createOneShot(350L, VibrationEffect.DEFAULT_AMPLITUDE))
                } else {
                    @Suppress("DEPRECATION")
                    v.vibrate(350L)
                }
            }
        } catch (_: Exception) {}
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

            val monitorChannel = NotificationChannel(
                MONITOR_CHANNEL_ID,
                "Nova Crash and Fall Guard",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Monitors for severe ground-hit impacts."
                setShowBadge(false)
            }

            val alarmSound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
            val audioAttrs = AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_ALARM)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build()

            val alertChannel = NotificationChannel(
                ALERT_CHANNEL_ID,
                "Nova Critical SOS Countdown Alerts",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Emergency countdown with a user-controlled dialer action."
                enableVibration(true)
                setSound(alarmSound, audioAttrs)
                lockscreenVisibility = Notification.VISIBILITY_PUBLIC
            }

            nm.createNotificationChannel(monitorChannel)
            nm.createNotificationChannel(alertChannel)
        }
    }

    private fun buildPersistentMonitoringNotification(): Notification {
        val openAppIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val contentPi = PendingIntent.getActivity(
            this,
            101,
            openAppIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val savedNum = getSavedEmergencyNumber()
        val bgEnabled = isBackgroundAutoCallingAllowed()
        val statusText = when {
            !bgEnabled -> "Background impact monitoring is OFF when app is closed"
            savedNum.isNotEmpty() -> "Impact monitor active • Saved contact: $savedNum"
            else -> "Hard-Impact Guard Active • Tap to save SOS Number"
        }

        return NotificationCompat.Builder(this, MONITOR_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_menu_call)
            .setContentTitle("Nova Emergency Monitor")
            .setContentText(statusText)
            .setContentIntent(contentPi)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build()
    }

    private fun showHighPriorityCountdownNotification(
        secondsLeft: Int,
        peakMs2: Float,
        targetNum: String,
        targetName: String
    ) {
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        val fullScreenIntent = Intent(this, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
            putExtra("CRASH_DETECTED", true)
            putExtra("PEAK_ACCEL", peakMs2)
        }
        val fullScreenPi = PendingIntent.getActivity(
            this,
            201,
            fullScreenIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val cancelIntent = Intent(this, AccidentDetectionService::class.java).apply {
            action = ACTION_CANCEL_SOS_COUNTDOWN
        }
        val cancelPi = PendingIntent.getService(
            this,
            202,
            cancelIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val callNowIntent = Intent(this, AccidentDetectionService::class.java).apply {
            action = ACTION_CALL_SAVED_NOW
        }
        val callNowPi = PendingIntent.getService(
            this,
            203,
            callNowIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val peakFormatted = String.format("%.1f", peakMs2)
        val hasTarget = targetNum.isNotEmpty()
        val titleText = if (hasTarget) {
            "POTENTIAL EMERGENCY ($peakFormatted m/s²) — REVIEW CALL"
        } else {
            "SEVERE IMPACT ($peakFormatted m/s²) — NO SOS CONTACT SAVED"
        }
        val bodyText = if (hasTarget) {
            (if (secondsLeft > 0) "Possible severe impact. Review the alert. $secondsLeft seconds remaining; tap CANCEL if safe." else "Emergency alert active. Tap OPEN DIALER to review the saved contact and place a call.")
        } else {
            "No emergency contact configured (${secondsLeft}s). Tap to configure contact."
        }
        val callBtnLabel = if (hasTarget) "OPEN DIALER" else "CONFIGURE CONTACT"

        val alertNotif = NotificationCompat.Builder(this, ALERT_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_sys_warning)
            .setContentTitle(titleText)
            .setContentText(bodyText)
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setOngoing(true)
            .setAutoCancel(false)
            .setFullScreenIntent(fullScreenPi, true)
            .addAction(android.R.drawable.ic_delete, "I AM SAFE (CANCEL)", cancelPi)
            .addAction(android.R.drawable.ic_menu_call, callBtnLabel, callNowPi)
            .build()

        nm.notify(ALERT_NOTIF_ID, alertNotif)
    }

    private fun cancelAlertNotification() {
        try {
            val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            nm.cancel(ALERT_NOTIF_ID)
        } catch (_: Exception) {}
    }

    private fun hasLocationPermission(): Boolean {
        val fine = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
        val coarse = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.ACCESS_COARSE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
        return fine || coarse
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    override fun onTaskRemoved(rootIntent: Intent?) {
        super.onTaskRemoved(rootIntent)
        NovaAutoCallCoordinator.isAppInForeground = false

        if (!isBackgroundAutoCallingAllowed()) {
            abortActiveCountdown()
            sensorManager.unregisterListener(this)
            stopForeground(true)
            stopSelf()
            return
        }

        try {
            val restartIntent = Intent(applicationContext, AccidentDetectionService::class.java).apply {
                action = ACTION_START_MONITORING
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                applicationContext.startForegroundService(restartIntent)
            } else {
                applicationContext.startService(restartIntent)
            }
        } catch (_: Exception) {}
    }

    override fun onDestroy() {
        mainHandler.removeCallbacks(countdownTickRunnable)
        sensorManager.unregisterListener(this)
        releaseWakeLock()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}