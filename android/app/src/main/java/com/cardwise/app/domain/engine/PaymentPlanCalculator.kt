package com.cardwise.app.domain.engine

import com.cardwise.app.domain.model.Payment
import com.cardwise.app.domain.model.PaymentStatus
import java.math.BigDecimal
import java.math.RoundingMode

object PaymentPlanCalculator {

    const val MINIMUM_DUE_WARNING =
        "Paying only the minimum due generally does not prevent interest on the unpaid statement balance. " +
        "Interest is charged from the date of transaction on revolving balances."

    data class ReconciliationResult(
        val statementBalance: BigDecimal,
        val minimumDue: BigDecimal,
        val confirmedPaymentsTotal: BigDecimal,
        val plannedPaymentsTotal: BigDecimal,
        val remainingToPlan: BigDecimal,
        val isFullyPlanned: Boolean,
        val isFullyConfirmed: Boolean,
        val hasOverpayment: Boolean,
        val warningMessage: String = MINIMUM_DUE_WARNING
    )

    fun calculateReconciliation(
        statementBalance: BigDecimal,
        minimumDue: BigDecimal,
        payments: List<Payment>,
        allowOverpayment: Boolean = false
    ): ReconciliationResult {
        var confirmedTotal = BigDecimal.ZERO
        var plannedTotal = BigDecimal.ZERO

        for (payment in payments) {
            when (payment.status) {
                PaymentStatus.CONFIRMED -> {
                    confirmedTotal = confirmedTotal.add(payment.amount)
                }
                PaymentStatus.PLANNED, PaymentStatus.SUBMITTED -> {
                    plannedTotal = plannedTotal.add(payment.amount)
                }
                PaymentStatus.CANCELLED, PaymentStatus.FAILED -> {
                    // Excluded from ledger balance
                }
            }
        }

        val rawRemaining = statementBalance.subtract(confirmedTotal).subtract(plannedTotal)
        val hasOverpayment = rawRemaining < BigDecimal.ZERO

        val remainingToPlan = if (hasOverpayment && !allowOverpayment) {
            BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP)
        } else {
            rawRemaining.setScale(2, RoundingMode.HALF_UP)
        }

        val isFullyConfirmed = confirmedTotal >= statementBalance && statementBalance > BigDecimal.ZERO
        val isFullyPlanned = confirmedTotal.add(plannedTotal) >= statementBalance && statementBalance > BigDecimal.ZERO

        return ReconciliationResult(
            statementBalance = statementBalance.setScale(2, RoundingMode.HALF_UP),
            minimumDue = minimumDue.setScale(2, RoundingMode.HALF_UP),
            confirmedPaymentsTotal = confirmedTotal.setScale(2, RoundingMode.HALF_UP),
            plannedPaymentsTotal = plannedTotal.setScale(2, RoundingMode.HALF_UP),
            remainingToPlan = remainingToPlan,
            isFullyPlanned = isFullyPlanned,
            isFullyConfirmed = isFullyConfirmed,
            hasOverpayment = hasOverpayment
        )
    }
}
