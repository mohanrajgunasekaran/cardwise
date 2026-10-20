package com.cardwise.app

import com.cardwise.app.domain.engine.PaymentPlanCalculator
import com.cardwise.app.domain.model.Payment
import com.cardwise.app.domain.model.PaymentStatus
import org.junit.Assert.*
import org.junit.Test
import java.math.BigDecimal
import java.time.LocalDate

class PaymentPlanCalculatorTest {

    @Test
    fun testExactDecimalPrecisionReconciliation() {
        val statementBalance = BigDecimal("18450.00")
        val minDue = BigDecimal("950.00")
        val payments = listOf(
            Payment(
                id = "p1",
                statementId = "s1",
                amount = BigDecimal("5000.00"),
                plannedDate = LocalDate.now(),
                status = PaymentStatus.CONFIRMED
            ),
            Payment(
                id = "p2",
                statementId = "s1",
                amount = BigDecimal("10000.00"),
                plannedDate = LocalDate.now().plusDays(2),
                status = PaymentStatus.PLANNED
            ),
            Payment(
                id = "p3",
                statementId = "s1",
                amount = BigDecimal("2000.00"),
                plannedDate = LocalDate.now().plusDays(4),
                status = PaymentStatus.PLANNED
            ),
            Payment(
                id = "p4",
                statementId = "s1",
                amount = BigDecimal("1450.00"),
                plannedDate = LocalDate.now().plusDays(1),
                status = PaymentStatus.CANCELLED // Must be ignored
            )
        )

        val result = PaymentPlanCalculator.calculateReconciliation(statementBalance, minDue, payments)

        // Confirmed = 5000, Planned = 10000 + 2000 = 12000, Remaining = 18450 - 5000 - 12000 = 1450.00
        assertEquals(BigDecimal("5000.00"), result.confirmedPaymentsTotal)
        assertEquals(BigDecimal("12000.00"), result.plannedPaymentsTotal)
        assertEquals(BigDecimal("1450.00"), result.remainingToPlan)
        assertFalse(result.isFullyPlanned)
        assertFalse(result.isFullyConfirmed)
        assertFalse(result.hasOverpayment)
    }

    @Test
    fun testFullyConfirmedSettlement() {
        val statementBalance = BigDecimal("7500.50")
        val minDue = BigDecimal("400.00")
        val payments = listOf(
            Payment(
                id = "p1",
                statementId = "s1",
                amount = BigDecimal("7500.50"),
                plannedDate = LocalDate.now(),
                status = PaymentStatus.CONFIRMED
            )
        )

        val result = PaymentPlanCalculator.calculateReconciliation(statementBalance, minDue, payments)

        assertEquals(BigDecimal("0.00"), result.remainingToPlan)
        assertTrue(result.isFullyConfirmed)
        assertTrue(result.isFullyPlanned)
    }

    @Test
    fun testOverpaymentFloorHandling() {
        val statementBalance = BigDecimal("5000.00")
        val minDue = BigDecimal("250.00")
        val payments = listOf(
            Payment(
                id = "p1",
                statementId = "s1",
                amount = BigDecimal("6000.00"),
                plannedDate = LocalDate.now(),
                status = PaymentStatus.CONFIRMED
            )
        )

        // Default floor at 0.00 without negative remaining unless allowOverpayment=true
        val resultDefault = PaymentPlanCalculator.calculateReconciliation(statementBalance, minDue, payments, allowOverpayment = false)
        assertEquals(BigDecimal("0.00"), resultDefault.remainingToPlan)
        assertTrue(resultDefault.hasOverpayment)

        val resultAllowed = PaymentPlanCalculator.calculateReconciliation(statementBalance, minDue, payments, allowOverpayment = true)
        assertEquals(BigDecimal("-1000.00"), resultAllowed.remainingToPlan)
        assertTrue(resultAllowed.hasOverpayment)
    }
}
