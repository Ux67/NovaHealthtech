package in.novahealthtech.companion

import android.app.*
import android.content.Context
import android.content.Intent
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationManager
import android.net.Uri
import android.os.*
import androidx.core.app.NotificationCompat
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import kotlin.math.sqrt

/**
 * Nova Healthtech - Native Android Foreground Sensor-Fusion & 8s Direct Ambulance Call Service
 * - Continuously monitors TYPE_LINEAR_ACCELERATION and TYPE_GYROSCOPE.
 * - Starts an 8-second countdown on impact and automatically transmits GPS coordinates
 *   to /api/sos/incident AND places a direct cellular call to 108 via Intent.ACTION_CALL.
 */
class AccidentDetectionService : Service(), SensorEventListener {

    private lateinit var sensorManager: SensorManager
    private var linearAccelSensor: Sensor? = null
    private var gyroSensor: Sensor? = null

    private var latestGyroMagnitude: Float = 0f
    private var lastIncidentTriggerElapsedMs: Long = 0L
    private var countdownTimer: CountDownTimer? = null

    companion object {
        const val CHANNEL_ID = "nova_sos_monitor_channel"
        const val NOTIFICATION_ID = 108112
        const val ACTION_CANCEL_SOS = "in.novahealthtech.companion.ACTION_CANCEL_SOS"
        var BACKEND_BASE_URL = "http://10.0.2.2:5000"
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        linearAccelSensor = sensorManager.getDefaultSensor(Sensor.TYPE_LINEAR_ACCELERATION)
            ?: sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        gyroSensor = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_CANCEL_SOS) {
            cancelActiveCountdown()
            return START_STICKY
        }

        val notification = buildPersistentNotification(
            "Nova Crash Monitor Active (8s Auto-Call)",
            "Monitoring accelerometer & gyroscope. Force-stopping or powering off disables monitoring."
        )
        startForeground(NOTIFICATION_ID, notification)

        linearAccelSensor?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
        }
        gyroSensor?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
        }

        return START_STICKY
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event == null) return

        if (event.sensor.type == Sensor.TYPE_GYROSCOPE) {
            val rx = event.values[0]
            val ry = event.values[1]
            val rz = event.values[2]
            latestGyroMagnitude = sqrt(rx * rx + ry * ry + rz * rz)
        } else if (event.sensor.type == Sensor.TYPE_LINEAR_ACCELERATION || event.sensor.type == Sensor.TYPE_ACCELEROMETER) {
            val ax = event.values[0]
            val ay = event.values[1]
            val az = event.values[2]
            val accelMag = sqrt(ax * ax + ay * ay + az * az)

            val nowElapsed = SystemClock.elapsedRealtime()
            if (accelMag >= 24.0f && (nowElapsed - lastIncidentTriggerElapsedMs) > 20000L) {
                lastIncidentTriggerElapsedMs = nowElapsed
                startCancellationCountdown(accelMag, latestGyroMagnitude)
            }
        }
    }

    private fun startCancellationCountdown(peakAccel: Float, peakGyro: Float) {
        countdownTimer?.cancel()
        val cancelIntent = Intent(this, AccidentDetectionService::class.java).apply {
            action = ACTION_CANCEL_SOS
        }
        val cancelPendingIntent = PendingIntent.getService(
            this, 0, cancelIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        countdownTimer = object : CountDownTimer(8000, 1000) {
            override fun onTick(millisUntilFinished: Long) {
                val sec = millisUntilFinished / 1000
                val alertNotif = NotificationCompat.Builder(this@AccidentDetectionService, CHANNEL_ID)
                    .setSmallIcon(android.R.drawable.ic_dialog_alert)
                    .setContentTitle("🚨 AUTO-CALLING 108 AMBULANCE IN ${sec}s")
                    .setContentText("Sharing GPS location & dialing 108 automatically. Tap CANCEL if safe.")
                    .setPriority(NotificationCompat.PRIORITY_MAX)
                    .addAction(android.R.drawable.ic_delete, "CANCEL — I AM SAFE", cancelPendingIntent)
                    .build()
                val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                nm.notify(NOTIFICATION_ID, alertNotif)
            }

            override fun onFinish() {
                transmitSosToBackend(peakAccel, peakGyro)
                placeAutomaticAmbulanceCall("108")
            }
        }.start()
    }

    private fun cancelActiveCountdown() {
        countdownTimer?.cancel()
        countdownTimer = null
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        nm.notify(
            NOTIFICATION_ID,
            buildPersistentNotification("SOS Cancelled — User Safe", "Active monitoring resumed.")
        )
    }

    private fun placeAutomaticAmbulanceCall(number: String) {
        try {
            val callIntent = Intent(Intent.ACTION_CALL).apply {
                data = Uri.parse("tel:$number")
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            startActivity(callIntent)
        } catch (_: SecurityException) {
            val dialIntent = Intent(Intent.ACTION_DIAL).apply {
                data = Uri.parse("tel:$number")
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            startActivity(dialIntent)
        }
    }

    private fun transmitSosToBackend(peakAccel: Float, peakGyro: Float) {
        val locManager = getSystemService(Context.LOCATION_SERVICE) as LocationManager
        var lastLoc: Location? = null
        try {
            lastLoc = locManager.getLastKnownLocation(LocationManager.GPS_PROVIDER)
                ?: locManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
        } catch (_: SecurityException) {}

        Thread {
            try {
                val url = URL("$BACKEND_BASE_URL/api/sos/incident")
                val conn = (url.openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 6000
                    readTimeout = 6000
                    doOutput = true
                    setRequestProperty("Content-Type", "application/json")
                }
                val payload = JSONObject().apply {
                    put("incident_uuid", "android-sos-${System.currentTimeMillis()}")
                    put("trigger_source", "android_foreground_service_8s")
                    put("is_simulation", false)
                    put("place_direct_phone_call", true)
                    put("target_ambulance_number", "108")
                    put("latitude", lastLoc?.latitude)
                    put("longitude", lastLoc?.longitude)
                    put("accuracy_meters", lastLoc?.accuracy)
                    put("location_source", if (lastLoc != null) "android_gps" else "unavailable")
                    put("sensor_data", JSONObject().apply {
                        put("peak_linear_accel_ms2", peakAccel)
                        put("peak_gyro_rad_s", peakGyro)
                        put("impact_duration_ms", 60)
                    })
                }
                conn.outputStream.use { it.write(payload.toString().toByteArray()) }
                conn.responseCode
            } catch (_: Exception) {}
        }.start()
    }

    private fun buildPersistentNotification(title: String, body: String): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setContentTitle(title)
            .setContentText(body)
            .setOngoing(true)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Nova Crash & SOS Monitoring",
                NotificationManager.IMPORTANCE_HIGH
            )
            val nm = getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(channel)
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    override fun onDestroy() {
        countdownTimer?.cancel()
        sensorManager.unregisterListener(this)
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}