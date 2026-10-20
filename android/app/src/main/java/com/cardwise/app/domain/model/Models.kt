package com.cardwise.app.domain.model

import java.math.BigDecimal
import java.time.LocalDate
import java.time.LocalDateTime

enum class NetworkType {
    VISA, MASTERCARD, RUPAY, AMEX
}

enum class RewardType {
    CASHBACK, REWARD_POINTS, MILES
}

enum class PaymentStatus {
    PLANNED, SUBMITTED, CONFIRMED, CANCELLED, FAILED
}

enum class BenefitType {
    CASHBACK_PERCENT, MULTIPLIER, FLAT_DISCOUNT
}

data class CreditCard(
    val id: String,
    val issuer: String,
    val variant: String,
    val nickname: String?,
    val maskedNumber: String,
    val network: NetworkType = NetworkType.VISA,
    val creditLimit: BigDecimal?,
    val availableLimit: BigDecimal?,
    val billingCycleDay: Int,
    val paymentDueDays: Int = 20,
    val annualFee: BigDecimal = BigDecimal.ZERO,
    val joiningFee: BigDecimal = BigDecimal.ZERO,
    val rewardType: RewardType = RewardType.CASHBACK,
    val baseEarnRate: BigDecimal = BigDecimal("1.00"),
    val pointRedemptionInr: BigDecimal = BigDecimal("0.2500"),
    val isVerified: Boolean = false,
    val isArchived: Boolean = false,
    val createdAt: LocalDateTime = LocalDateTime.now()
) {
    val displayName: String
        get() = if (!nickname.isNullOrBlank()) "$nickname ($issuer $variant)" else "$issuer $variant"
}

data class Statement(
    val id: String,
    val cardId: String,
    val statementDate: LocalDate,
    val paymentDueDate: LocalDate,
    val periodStart: LocalDate,
    val periodEnd: LocalDate,
    val totalBalance: BigDecimal,
    val minimumDue: BigDecimal,
    val isPaid: Boolean = false,
    val source: String = "MANUAL",
    val documentRef: String? = null,
    val createdAt: LocalDateTime = LocalDateTime.now(),
    val confirmedPaidAmount: BigDecimal = BigDecimal.ZERO,
    val plannedPaidAmount: BigDecimal = BigDecimal.ZERO,
    val remainingToPlan: BigDecimal = BigDecimal.ZERO
)

data class Payment(
    val id: String,
    val statementId: String,
    val amount: BigDecimal,
    val plannedDate: LocalDate,
    val status: PaymentStatus = PaymentStatus.PLANNED,
    val confirmedAt: LocalDateTime? = null,
    val notes: String? = null,
    val createdAt: LocalDateTime = LocalDateTime.now()
)

data class CardOffer(
    val id: String,
    val cardId: String? = null,
    val issuer: String,
    val variant: String? = null,
    val title: String,
    val category: String,
    val merchantKeyword: String? = null,
    val benefitType: BenefitType,
    val benefitValue: BigDecimal,
    val minSpend: BigDecimal = BigDecimal.ZERO,
    val maxBenefitCap: BigDecimal? = null,
    val exclusionDetails: String? = null,
    val validFrom: LocalDate,
    val validTo: LocalDate,
    val confidence: String = "VERIFIED"
)

data class PurchaseContext(
    val purchaseAmount: BigDecimal,
    val category: String,
    val merchant: String? = null,
    val transactionDate: LocalDate = LocalDate.now()
)

data class EvaluationResult(
    val cardId: String,
    val cardName: String,
    val issuer: String,
    val variant: String,
    val maskedNumber: String,
    val estimatedNetBenefitInr: BigDecimal,
    val effectiveRatePercent: BigDecimal,
    val calculationBreakdown: String,
    val appliedRule: String,
    val eligibilityConditions: String,
    val offerExpiry: LocalDate? = null,
    val confidence: String
)

data class HomeMetrics(
    val totalStatementBalances: BigDecimal = BigDecimal.ZERO,
    val totalMinimumDue: BigDecimal = BigDecimal.ZERO,
    val upcomingDeadlinesCount: Int = 0,
    val overdueCount: Int = 0,
    val verifiedCardsCount: Int = 0,
    val totalCardsCount: Int = 0,
    val plannedPaymentTotal: BigDecimal = BigDecimal.ZERO,
    val confirmedPaymentTotal: BigDecimal = BigDecimal.ZERO,
    val remainingUnplannedTotal: BigDecimal = BigDecimal.ZERO
)
