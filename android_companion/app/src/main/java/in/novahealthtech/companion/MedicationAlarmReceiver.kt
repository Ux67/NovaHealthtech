package `in`.novahealthtech.companion

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.RingtoneManager
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import androidx.core.app.NotificationCompat
import java.util.Locale

class MedicationAlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            MedicationAlarmScheduler.restoreAll(context)
            return
        }
        if (intent.action != MedicationAlarmScheduler.ACTION_MEDICATION_ALARM) return

        val id = intent.getStringExtra("reminder_id").orEmpty()
        val name = intent.getStringExtra("medicine_name").orEmpty()
        val dose = intent.getStringExtra("prescribed_dose").orEmpty()
        val time = intent.getStringExtra("scheduled_time").orEmpty()
        val meal = intent.getStringExtra("meal_relation").orEmpty()
        if (id.isBlank() || name.isBlank()) return

        showNotification(context, id, name, dose, time, meal)
        speakReminder(context, name, dose, meal)

        // Re-arm tomorrow's reminder after today's alarm fires.
        val saved = context.getSharedPreferences("nova_medication_alarms", Context.MODE_PRIVATE)
            .getString("reminder_" + id, null)
        if (saved != null) {
            try { MedicationAlarmScheduler.scheduleNext(context, org.json.JSONObject(saved)) } catch (_: Exception) {}
        }
    }

    private fun showNotification(context: Context, id: String, name: String, dose: String, time: String, meal: String) {
        val channelId = "nova_medication_reminders"
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && manager.getNotificationChannel(channelId) == null) {
            val channel = NotificationChannel(channelId, "Medication reminders", NotificationManager.IMPORTANCE_HIGH).apply {
                description = "Daily reminders entered by the user"
                enableVibration(true)
                setSound(RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM),
                    AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build())
            }
            manager.createNotificationChannel(channel)
        }
        val openApp = PendingIntent.getActivity(context, id.hashCode(),
            Intent(context, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val detail = buildString {
            append("Time: ").append(time)
            if (dose.isNotBlank()) append(" • Prescribed dose: ").append(dose)
            if (meal.isNotBlank()) append(" • ").append(meal.replace('_', ' '))
        }
        val notification = NotificationCompat.Builder(context, channelId)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle("Medication reminder: $name")
            .setContentText(detail)
            .setStyle(NotificationCompat.BigTextStyle().bigText(detail))
            .setCategory(NotificationCompat.CATEGORY_REMINDER)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(openApp)
            .build()
        // Spoken reminder should still run if notification permission is denied.
        try {
            manager.notify(id.hashCode(), notification)
        } catch (_: SecurityException) {
            // Android notification permission is optional; TextToSpeech remains available.
        }
    }

    private fun speakReminder(context: Context, name: String, dose: String, meal: String) {
        val pending = goAsync()
        val message = buildString {
            append("Medication reminder. It is time for ").append(name).append(".")
            if (dose.isNotBlank()) append(" Prescribed dose: ").append(dose).append(".")
            if (meal.isNotBlank()) append(meal.replace('_', ' ')).append(".")
            append(" Please follow your doctor's prescription.")
        }
        var tts: TextToSpeech? = null
        var finished = false
        fun finish() {
            if (!finished) {
                finished = true
                try { tts?.stop(); tts?.shutdown() } catch (_: Exception) {}
                pending.finish()
            }
        }
        Handler(Looper.getMainLooper()).postDelayed({ finish() }, 25000L)
        tts = TextToSpeech(context.applicationContext) { status ->
            if (status == TextToSpeech.SUCCESS) {
                try {
                    tts?.language = Locale.getDefault()
                    tts?.setSpeechRate(0.92f)
                    tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                        override fun onStart(utteranceId: String?) {}
                        override fun onDone(utteranceId: String?) { finish() }
                        @Deprecated("Deprecated in Java")
                        override fun onError(utteranceId: String?) { finish() }
                    })
                    tts?.speak(message, TextToSpeech.QUEUE_FLUSH, null,
                        "nova-med-" + System.currentTimeMillis())
                } catch (_: Exception) { finish() }
            } else {
                finish()
            }
        }
    }
}
