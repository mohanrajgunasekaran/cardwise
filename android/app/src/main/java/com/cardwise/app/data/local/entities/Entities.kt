package com.cardwise.app.data.local.entities

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.math.BigDecimal

@Entity(tableName = "credit_cards")
data class CreditCardEntity(
    @PrimaryKey val id: String,
    val issuer: String,
    val variant: String,
    val nickname: String?,
    val maskedNumber: String,
    val network: String,
    val creditLimit: String?,  // Stored as String for lossless BigDecimal persistence
    val availableLimit: String?,
    val billingCycleDay: Int,
    val paymentDueDays: Int,
    val annualFee: String,
    val joiningFee: String,
    val rewardType: String,
    val baseEarnRate: String,
    val pointRedemptionInr: String,
    val isVerified: Boolean,
    val isArchived: Boolean,
    val createdAtEpoch: Long
)

@Entity(tableName = "statements")
data class StatementEntity(
    @PrimaryKey val id: String,
    val cardId: String,
    val statementDate: String, // ISO-8601 YYYY-MM-DD
    val paymentDueDate: String,
    val periodStart: String,
    val periodEnd: String,
    val totalBalance: String,
    val minimumDue: String,
    val isPaid: Boolean,
    val source: String,
    val documentRef: String?,
    val createdAtEpoch: Long
)

@Entity(tableName = "payments")
data class PaymentEntity(
    @PrimaryKey val id: String,
    val statementId: String,
    val amount: String,
    val plannedDate: String,
    val status: String,
    val confirmedAtEpoch: Long?,
    val notes: String?,
    val createdAtEpoch: Long
)

@Entity(tableName = "card_offers")
data class CardOfferEntity(
    @PrimaryKey val id: String,
    val cardId: String?,
    val issuer: String,
    val variant: String?,
    val title: String,
    val category: String,
    val merchantKeyword: String?,
    val benefitType: String,
    val benefitValue: String,
    val minSpend: String,
    val maxBenefitCap: String?,
    val exclusionDetails: String?,
    val validFrom: String,
    val validTo: String,
    val confidence: String
)
