package com.cardwise.app.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.cardwise.app.data.local.dao.*
import com.cardwise.app.data.local.entities.*

@Database(
    entities = [
        CreditCardEntity::class,
        StatementEntity::class,
        PaymentEntity::class,
        CardOfferEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class CardWiseDatabase : RoomDatabase() {

    abstract fun creditCardDao(): CreditCardDao
    abstract fun statementDao(): StatementDao
    abstract fun paymentDao(): PaymentDao
    abstract fun cardOfferDao(): CardOfferDao

    companion object {
        @Volatile
        private var INSTANCE: CardWiseDatabase? = null

        fun getDatabase(context: Context): CardWiseDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    CardWiseDatabase::class.java,
                    "cardwise_local.db"
                ).fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
