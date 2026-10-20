package com.cardwise.app.worker

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.*
import com.cardwise.app.data.local.CardWiseDatabase
import kotlinx.coroutines.flow.first
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.concurrent.TimeUnit

class PaymentReminderWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    companion object {
        const val CHANNEL_ID = "cardwise_payment_reminders"
        const val CHANNEL_NAME = "Payment Due Date Reminders"
        const val WORK_NAME = "cardwise_periodic_payment_check"

        fun schedulePeriodicCheck(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiresBatteryNotLow(false)
                .build()

            val periodicRequest = PeriodicWorkRequestBuilder<PaymentReminderWorker>(
                12, TimeUnit.HOURS
            ).setConstraints(constraints).build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                periodicRequest
            )
        }
    }

    override suspend fun doWork(): Result {
        val database = CardWiseDatabase.getDatabase(applicationContext)
        val statementDao = database.statementDao()
        val cardDao = database.creditCardDao()

        val statements = statementDao.getAllStatements().first()
        val cards = cardDao.getAllCards().first().associateBy { it.id }

        val today = LocalDate.now()
        val dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE

        for (stmt in statements) {
            if (stmt.isPaid) continue

            val dueDate = try { LocalDate.parse(stmt.paymentDueDate, dateFormatter) } catch (e: Exception) { null } ?: continue
            val card = cards[stmt.cardId]
            val cardLabel = card?.let { "${it.issuer} ${it.variant} (${it.maskedNumber})" } ?: "Credit Card"

            val daysUntilDue = java.time.temporal.ChronoUnit.DAYS.between(today, dueDate)

            if (daysUntilDue in 0..5) {
                val title = if (daysUntilDue == 0L) "Payment Due Today!" else "Upcoming Payment: $daysUntilDue Days Remaining"
                val message = "Statement balance of ₹${stmt.totalBalance} on $cardLabel is due on ${stmt.paymentDueDate}."
                sendNotification(stmt.id.hashCode(), title, message)
            } else if (daysUntilDue < 0) {
                val overdueDays = -daysUntilDue
                val title = "Overdue Payment Alert ($overdueDays days late)"
                val message = "Statement balance of ₹${stmt.totalBalance} on $cardLabel is overdue since ${stmt.paymentDueDate}."
                sendNotification(stmt.id.hashCode(), title, message)
            }
        }

        return Result.success()
    }

    private fun sendNotification(notificationId: Int, title: String, content: String) {
        val notificationManager = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                CHANNEL_NAME,
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Reminders for credit card bill deadlines and minimum payments"
            }
            notificationManager.createNotificationChannel(channel)
        }

        val notification = NotificationCompat.Builder(applicationContext, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle(title)
            .setContentText(content)
            .setStyle(NotificationCompat.BigTextStyle().bigText(content))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()

        notificationManager.notify(notificationId, notification)
    }
}
