package com.cardwise.app

import android.app.Application
import com.cardwise.app.data.local.CardWiseDatabase
import com.cardwise.app.data.repository.CardWiseRepository
import com.cardwise.app.worker.PaymentReminderWorker

class CardWiseApplication : Application() {

    val database by lazy { CardWiseDatabase.getDatabase(this) }
    val repository by lazy { CardWiseRepository(database) }

    override fun onCreate() {
        super.onCreate()
        // Schedule periodic local checks for upcoming statement due dates
        PaymentReminderWorker.schedulePeriodicCheck(this)
    }
}
