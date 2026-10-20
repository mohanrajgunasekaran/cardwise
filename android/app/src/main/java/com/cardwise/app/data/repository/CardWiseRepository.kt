package com.cardwise.app.data.repository

import com.cardwise.app.data.local.CardWiseDatabase
import com.cardwise.app.data.local.SampleData
import com.cardwise.app.data.local.entities.*
import com.cardwise.app.domain.engine.PaymentPlanCalculator
import com.cardwise.app.domain.model.*
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import java.math.BigDecimal
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.util.UUID

class CardWiseRepository(private val database: CardWiseDatabase) {

    private val cardDao = database.creditCardDao()
    private val statementDao = database.statementDao()
    private val paymentDao = database.paymentDao()
    private val offerDao = database.cardOfferDao()

    private val dateFormatter = DateTimeFormatter.ISO_LOCAL_DATE

    // --- Cards ---
    fun getActiveCards(): Flow<List<CreditCard>> {
        return cardDao.getAllActiveCards().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    suspend fun insertCard(card: CreditCard) {
        cardDao.insertCard(card.toEntity())
    }

    suspend fun archiveCard(cardId: String) {
        cardDao.archiveCard(cardId)
    }

    // --- Statements ---
    fun getAllStatements(): Flow<List<Statement>> {
        return combine(
            statementDao.getAllStatements(),
            paymentDao.getAllPayments()
        ) { stmtEntities, paymentEntities ->
            val allPayments = paymentEntities.map { it.toDomain() }
            stmtEntities.map { entity ->
                val stmtDomain = entity.toDomain()
                val stmtPayments = allPayments.filter { it.statementId == stmtDomain.id }
                val recon = PaymentPlanCalculator.calculateReconciliation(
                    statementBalance = stmtDomain.totalBalance,
                    minimumDue = stmtDomain.minimumDue,
                    payments = stmtPayments
                )
                stmtDomain.copy(
                    confirmedPaidAmount = recon.confirmedPaymentsTotal,
                    plannedPaidAmount = recon.plannedPaymentsTotal,
                    remainingToPlan = recon.remainingToPlan
                )
            }
        }
    }

    suspend fun addStatement(statement: Statement): Boolean {
        // Check for duplicate
        val dateStr = statement.statementDate.format(dateFormatter)
        val duplicate = statementDao.findDuplicateStatement(statement.cardId, dateStr)
        if (duplicate != null) {
            return false // Duplicate rejected
        }
        statementDao.insertStatement(statement.toEntity())
        return true
    }

    // --- Payments ---
    fun getPaymentsForStatement(statementId: String): Flow<List<Payment>> {
        return paymentDao.getPaymentsForStatement(statementId).map { entities ->
            entities.map { it.toDomain() }
        }
    }

    suspend fun planPayment(statementId: String, amount: BigDecimal, plannedDate: LocalDate, notes: String?): Payment {
        val payment = Payment(
            id = UUID.randomUUID().toString(),
            statementId = statementId,
            amount = amount,
            plannedDate = plannedDate,
            status = PaymentStatus.PLANNED,
            notes = notes
        )
        paymentDao.insertPayment(payment.toEntity())
        return payment
    }

    suspend fun confirmPayment(paymentId: String, notes: String? = null) {
        val nowEpoch = System.currentTimeMillis()
        paymentDao.confirmPayment(paymentId, nowEpoch)
    }

    // --- Offers ---
    fun getActiveOffers(): Flow<List<CardOffer>> {
        val todayStr = LocalDate.now().format(dateFormatter)
        return offerDao.getActiveOffers(todayStr).map { entities ->
            entities.map { it.toDomain() }
        }
    }

    // --- Home Metrics Aggregation ---
    fun getHomeMetrics(): Flow<HomeMetrics> {
        return combine(
            getActiveCards(),
            getAllStatements(),
            paymentDao.getAllPayments()
        ) { cards, statements, paymentEntities ->
            val payments = paymentEntities.map { it.toDomain() }
            val today = LocalDate.now()

            val unpaidStatements = statements.filter { !it.isPaid }
            val totalStatementBalances = unpaidStatements.fold(BigDecimal.ZERO) { acc, s -> acc.add(s.totalBalance) }
            val totalMinimumDue = unpaidStatements.fold(BigDecimal.ZERO) { acc, s -> acc.add(s.minimumDue) }

            val upcoming = unpaidStatements.count { !it.paymentDueDate.isBefore(today) }
            val overdue = unpaidStatements.count { it.paymentDueDate.isBefore(today) }

            var plannedTotal = BigDecimal.ZERO
            var confirmedTotal = BigDecimal.ZERO

            for (p in payments) {
                when (p.status) {
                    PaymentStatus.CONFIRMED -> confirmedTotal = confirmedTotal.add(p.amount)
                    PaymentStatus.PLANNED, PaymentStatus.SUBMITTED -> plannedTotal = plannedTotal.add(p.amount)
                    else -> {}
                }
            }

            var remaining = totalStatementBalances.subtract(confirmedTotal).subtract(plannedTotal)
            if (remaining < BigDecimal.ZERO) remaining = BigDecimal.ZERO

            HomeMetrics(
                totalStatementBalances = totalStatementBalances,
                totalMinimumDue = totalMinimumDue,
                upcomingDeadlinesCount = upcoming,
                overdueCount = overdue,
                verifiedCardsCount = cards.count { it.isVerified },
                totalCardsCount = cards.size,
                plannedPaymentTotal = plannedTotal,
                confirmedPaymentTotal = confirmedTotal,
                remainingUnplannedTotal = remaining
            )
        }
    }

    // --- Seed Demo Fixtures (User initiated only) ---
    suspend fun seedDemoData() {
        val cardEntities = SampleData.DEMO_CARDS.map { it.toEntity() }
        cardDao.insertCards(cardEntities)

        val offerEntities = SampleData.DEMO_OFFERS.map { it.toEntity() }
        offerDao.insertOffers(offerEntities)

        val stmtEntities = SampleData.DEMO_STATEMENTS.map { it.toEntity() }
        statementDao.insertStatements(stmtEntities)
    }

    // --- Entity Mappers ---
    private fun CreditCardEntity.toDomain(): CreditCard {
        return CreditCard(
            id = id,
            issuer = issuer,
            variant = variant,
            nickname = nickname,
            maskedNumber = maskedNumber,
            network = try { NetworkType.valueOf(network) } catch (e: Exception) { NetworkType.VISA },
            creditLimit = creditLimit?.let { BigDecimal(it) },
            availableLimit = availableLimit?.let { BigDecimal(it) },
            billingCycleDay = billingCycleDay,
            paymentDueDays = paymentDueDays,
            annualFee = BigDecimal(annualFee),
            joiningFee = BigDecimal(joiningFee),
            rewardType = try { RewardType.valueOf(rewardType) } catch (e: Exception) { RewardType.CASHBACK },
            baseEarnRate = BigDecimal(baseEarnRate),
            pointRedemptionInr = BigDecimal(pointRedemptionInr),
            isVerified = isVerified,
            isArchived = isArchived,
            createdAt = LocalDateTime.ofEpochSecond(createdAtEpoch / 1000, 0, ZoneOffset.UTC)
        )
    }

    private fun CreditCard.toEntity(): CreditCardEntity {
        return CreditCardEntity(
            id = id,
            issuer = issuer,
            variant = variant,
            nickname = nickname,
            maskedNumber = maskedNumber,
            network = network.name,
            creditLimit = creditLimit?.toPlainString(),
            availableLimit = availableLimit?.toPlainString(),
            billingCycleDay = billingCycleDay,
            paymentDueDays = paymentDueDays,
            annualFee = annualFee.toPlainString(),
            joiningFee = joiningFee.toPlainString(),
            rewardType = rewardType.name,
            baseEarnRate = baseEarnRate.toPlainString(),
            pointRedemptionInr = pointRedemptionInr.toPlainString(),
            isVerified = isVerified,
            isArchived = isArchived,
            createdAtEpoch = createdAt.toEpochSecond(ZoneOffset.UTC) * 1000
        )
    }

    private fun StatementEntity.toDomain(): Statement {
        return Statement(
            id = id,
            cardId = cardId,
            statementDate = LocalDate.parse(statementDate, dateFormatter),
            paymentDueDate = LocalDate.parse(paymentDueDate, dateFormatter),
            periodStart = LocalDate.parse(periodStart, dateFormatter),
            periodEnd = LocalDate.parse(periodEnd, dateFormatter),
            totalBalance = BigDecimal(totalBalance),
            minimumDue = BigDecimal(minimumDue),
            isPaid = isPaid,
            source = source,
            documentRef = documentRef,
            createdAt = LocalDateTime.ofEpochSecond(createdAtEpoch / 1000, 0, ZoneOffset.UTC)
        )
    }

    private fun Statement.toEntity(): StatementEntity {
        return StatementEntity(
            id = id,
            cardId = cardId,
            statementDate = statementDate.format(dateFormatter),
            paymentDueDate = paymentDueDate.format(dateFormatter),
            periodStart = periodStart.format(dateFormatter),
            periodEnd = periodEnd.format(dateFormatter),
            totalBalance = totalBalance.toPlainString(),
            minimumDue = minimumDue.toPlainString(),
            isPaid = isPaid,
            source = source,
            documentRef = documentRef,
            createdAtEpoch = createdAt.toEpochSecond(ZoneOffset.UTC) * 1000
        )
    }

    private fun PaymentEntity.toDomain(): Payment {
        return Payment(
            id = id,
            statementId = statementId,
            amount = BigDecimal(amount),
            plannedDate = LocalDate.parse(plannedDate, dateFormatter),
            status = try { PaymentStatus.valueOf(status) } catch (e: Exception) { PaymentStatus.PLANNED },
            confirmedAt = confirmedAtEpoch?.let { LocalDateTime.ofEpochSecond(it / 1000, 0, ZoneOffset.UTC) },
            notes = notes,
            createdAt = LocalDateTime.ofEpochSecond(createdAtEpoch / 1000, 0, ZoneOffset.UTC)
        )
    }

    private fun Payment.toEntity(): PaymentEntity {
        return PaymentEntity(
            id = id,
            statementId = statementId,
            amount = amount.toPlainString(),
            plannedDate = plannedDate.format(dateFormatter),
            status = status.name,
            confirmedAtEpoch = confirmedAt?.toEpochSecond(ZoneOffset.UTC)?.times(1000),
            notes = notes,
            createdAtEpoch = createdAt.toEpochSecond(ZoneOffset.UTC) * 1000
        )
    }

    private fun CardOfferEntity.toDomain(): CardOffer {
        return CardOffer(
            id = id,
            cardId = cardId,
            issuer = issuer,
            variant = variant,
            title = title,
            category = category,
            merchantKeyword = merchantKeyword,
            benefitType = try { BenefitType.valueOf(benefitType) } catch (e: Exception) { BenefitType.CASHBACK_PERCENT },
            benefitValue = BigDecimal(benefitValue),
            minSpend = BigDecimal(minSpend),
            maxBenefitCap = maxBenefitCap?.let { BigDecimal(it) },
            exclusionDetails = exclusionDetails,
            validFrom = LocalDate.parse(validFrom, dateFormatter),
            validTo = LocalDate.parse(validTo, dateFormatter),
            confidence = confidence
        )
    }

    private fun CardOffer.toEntity(): CardOfferEntity {
        return CardOfferEntity(
            id = id,
            cardId = cardId,
            issuer = issuer,
            variant = variant,
            title = title,
            category = category,
            merchantKeyword = merchantKeyword,
            benefitType = benefitType.name,
            benefitValue = benefitValue.toPlainString(),
            minSpend = minSpend.toPlainString(),
            maxBenefitCap = maxBenefitCap?.toPlainString(),
            exclusionDetails = exclusionDetails,
            validFrom = validFrom.format(dateFormatter),
            validTo = validTo.format(dateFormatter),
            confidence = confidence
        )
    }
}
