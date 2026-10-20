package com.cardwise.app.data.local.dao

import androidx.room.*
import com.cardwise.app.data.local.entities.CardOfferEntity
import com.cardwise.app.data.local.entities.CreditCardEntity
import com.cardwise.app.data.local.entities.PaymentEntity
import com.cardwise.app.data.local.entities.StatementEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface CreditCardDao {
    @Query("SELECT * FROM credit_cards WHERE isArchived = 0 ORDER BY createdAtEpoch DESC")
    fun getAllActiveCards(): Flow<List<CreditCardEntity>>

    @Query("SELECT * FROM credit_cards ORDER BY createdAtEpoch DESC")
    fun getAllCards(): Flow<List<CreditCardEntity>>

    @Query("SELECT * FROM credit_cards WHERE id = :id LIMIT 1")
    suspend fun getCardById(id: String): CreditCardEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCard(card: CreditCardEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCards(cards: List<CreditCardEntity>)

    @Update
    suspend fun updateCard(card: CreditCardEntity)

    @Query("UPDATE credit_cards SET isArchived = 1 WHERE id = :id")
    suspend fun archiveCard(id: String)

    @Delete
    suspend fun deleteCard(card: CreditCardEntity)
}

@Dao
interface StatementDao {
    @Query("SELECT * FROM statements ORDER BY paymentDueDate ASC")
    fun getAllStatements(): Flow<List<StatementEntity>>

    @Query("SELECT * FROM statements WHERE cardId = :cardId ORDER BY statementDate DESC")
    fun getStatementsForCard(cardId: String): Flow<List<StatementEntity>>

    @Query("SELECT * FROM statements WHERE id = :id LIMIT 1")
    suspend fun getStatementById(id: String): StatementEntity?

    @Query("SELECT * FROM statements WHERE cardId = :cardId AND statementDate = :statementDate LIMIT 1")
    suspend fun findDuplicateStatement(cardId: String, statementDate: String): StatementEntity?

    @Insert(onConflict = OnConflictStrategy.ABORT)
    suspend fun insertStatement(statement: StatementEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertStatements(statements: List<StatementEntity>)

    @Update
    suspend fun updateStatement(statement: StatementEntity)

    @Delete
    suspend fun deleteStatement(statement: StatementEntity)
}

@Dao
interface PaymentDao {
    @Query("SELECT * FROM payments WHERE statementId = :statementId ORDER BY plannedDate ASC")
    fun getPaymentsForStatement(statementId: String): Flow<List<PaymentEntity>>

    @Query("SELECT * FROM payments ORDER BY plannedDate DESC")
    fun getAllPayments(): Flow<List<PaymentEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPayment(payment: PaymentEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPayments(payments: List<PaymentEntity>)

    @Update
    suspend fun updatePayment(payment: PaymentEntity)

    @Query("UPDATE payments SET status = 'CONFIRMED', confirmedAtEpoch = :confirmedEpoch WHERE id = :id")
    suspend fun confirmPayment(id: String, confirmedEpoch: Long)

    @Delete
    suspend fun deletePayment(payment: PaymentEntity)
}

@Dao
interface CardOfferDao {
    @Query("SELECT * FROM card_offers ORDER BY validTo ASC")
    fun getAllOffers(): Flow<List<CardOfferEntity>>

    @Query("SELECT * FROM card_offers WHERE validTo >= :todayDate ORDER BY validTo ASC")
    fun getActiveOffers(todayDate: String): Flow<List<CardOfferEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOffers(offers: List<CardOfferEntity>)
}
