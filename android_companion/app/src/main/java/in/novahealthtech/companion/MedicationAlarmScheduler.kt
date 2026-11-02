package `in`.novahealthtech.companion

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import org.json.JSONObject
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.ZoneId

/** Schedules recurring reminders exactly as entered by the user. */
object MedicationAlarmScheduler {
    private const val PREFS = "nova_medication_alarms"
    private const val KEY_PREFIX = "reminder_"
    const val ACTION_MEDICATION_ALARM = "in.novahealthtech.companion.MEDICATION_ALARM"

    fun schedule(context: Context, id: String, medicineName: String, prescribedDose: String,
                 scheduledTime: String, mealRelation: String, notes: String) {
        if (id.isBlank() || medicineName.isBlank()) return
        val parsedTime = try { LocalTime.parse(scheduledTime.take(5)) } catch (_: Exception) { return }
        val payload = JSONObject().apply {
            put("id", id)
            put("name", medicineName)
            put("dose", prescribedDose)
            put("time", parsedTime.toString())
            put("meal", mealRelation)
            put("notes", notes)
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(KEY_PREFIX + id, payload.toString()).apply()
        scheduleNext(context, payload)
    }

    fun cancel(context: Context, id: String) {
        if (id.isBlank()) return
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().remove(KEY_PREFIX + id).apply()
        val manager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        val pending = pendingIntent(context, id)
        manager.cancel(pending)
        pending.cancel()
    }

    fun restoreAll(context: Context) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).all.forEach { (key, value) ->
            if (key.startsWith(KEY_PREFIX) && value is String) {
                try { scheduleNext(context, JSONObject(value)) } catch (_: Exception) {}
            }
        }
    }

    fun scheduleNext(context: Context, payload: JSONObject) {
        val id = payload.optString("id")
        if (id.isBlank()) return
        val time = try { LocalTime.parse(payload.optString("time")) } catch (_: Exception) { return }
        val now = LocalDateTime.now()
        var next = now.toLocalDate().atTime(time)
        if (!next.isAfter(now)) next = next.plusDays(1)
        val triggerAt = next.atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
        val intent = Intent(context, MedicationAlarmReceiver::class.java).apply {
            action = ACTION_MEDICATION_ALARM
            putExtra("reminder_id", id)
            putExtra("medicine_name", payload.optString("name"))
            putExtra("prescribed_dose", payload.optString("dose"))
            putExtra("scheduled_time", payload.optString("time"))
            putExtra("meal_relation", payload.optString("meal"))
        }
        val pending = PendingIntent.getBroadcast(context, id.hashCode(), intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val manager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !manager.canScheduleExactAlarms()) {
                // Android may defer this fallback during Doze if exact-alarm access is not granted.
                manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pending)
            } else {
                manager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pending)
            }
        } catch (_: SecurityException) {
            manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pending)
        }
    }

    private fun pendingIntent(context: Context, id: String): PendingIntent {
        val intent = Intent(context, MedicationAlarmReceiver::class.java).apply {
            action = ACTION_MEDICATION_ALARM
            putExtra("reminder_id", id)
        }
        return PendingIntent.getBroadcast(context, id.hashCode(), intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    }
}
