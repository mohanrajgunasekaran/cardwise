package com.cardwise.app.domain.engine

import com.cardwise.app.domain.model.*
import java.math.BigDecimal
import java.math.RoundingMode
import java.time.LocalDate

object CardMatcherEngine {

    fun evaluateCard(
        card: CreditCard,
        offers: List<CardOffer>,
        context: PurchaseContext
    ): EvaluationResult {
        val categoryUpper = context.category.trim().uppercase()
        val merchantLower = context.merchant?.trim()?.lowercase().orEmpty()
        val txDate = context.transactionDate

        val applicableOffers = offers.filter { offer ->
            // Check card association
            val cardMatch = offer.cardId == null || offer.cardId == card.id
            val issuerMatch = offer.issuer.equals(card.issuer, ignoreCase = true) &&
                    (offer.variant.isNullOrBlank() || offer.variant.equals(card.variant, ignoreCase = true))

            val isDateValid = !txDate.isBefore(offer.validFrom) && !txDate.isAfter(offer.validTo)
            val isCatValid = offer.category.equals(categoryUpper, ignoreCase = true) || offer.category.equals("ALL", ignoreCase = true)
            val isMerchantValid = offer.merchantKeyword.isNullOrBlank() || merchantLower.contains(offer.merchantKeyword.lowercase())

            (cardMatch || issuerMatch) && isDateValid && isCatValid && isMerchantValid
        }

        var isExcluded = false
        var exclusionReason = ""
        var appliedRule = "Base ${card.baseEarnRate}% ${card.rewardType.name}"
        var eligibilityNotes = "Standard card base reward"
        var bestRate = card.baseEarnRate
        var expiryDate: LocalDate? = null
        var maxCap: BigDecimal? = null
        var confidence = if (card.isVerified) "VERIFIED" else "ESTIMATED"

        if (categoryUpper == "FUEL") {
            val fuelOffer = applicableOffers.firstOrNull { it.title.contains("surcharge", ignoreCase = true) }
            if (fuelOffer != null) {
                appliedRule = fuelOffer.title
                eligibilityNotes = "Fuel surcharge waiver on valid transaction limits"
            } else {
                isExcluded = true
                exclusionReason = "Fuel transactions commonly excluded from standard reward points"
            }
        }

        if (applicableOffers.isNotEmpty() && !isExcluded) {
            val topOffer = applicableOffers.maxByOrNull { it.benefitValue }!!
            if (context.purchaseAmount >= topOffer.minSpend) {
                bestRate = topOffer.benefitValue
                appliedRule = topOffer.title
                eligibilityNotes = topOffer.exclusionDetails ?: "Valid on ${context.category}"
                expiryDate = topOffer.validTo
                maxCap = topOffer.maxBenefitCap
                confidence = topOffer.confidence
            } else {
                eligibilityNotes = "Minimum spend of ₹${topOffer.minSpend} not met; applied base earn rate."
            }
        }

        val netBenefit: BigDecimal
        val breakdown: String
        val effectiveRate: BigDecimal

        if (isExcluded) {
            netBenefit = BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP)
            effectiveRate = BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP)
            breakdown = "Category '${context.category}' is excluded: $exclusionReason"
        } else {
            val rawBenefit = when (card.rewardType) {
                RewardType.REWARD_POINTS -> {
                    // points = (amount / 100) * bestRate, monetary = points * pointRedemptionInr
                    val points = context.purchaseAmount
                        .divide(BigDecimal("100"), 4, RoundingMode.HALF_UP)
                        .multiply(bestRate)
                    points.multiply(card.pointRedemptionInr)
                }
                RewardType.CASHBACK, RewardType.MILES -> {
                    context.purchaseAmount
                        .multiply(bestRate)
                        .divide(BigDecimal("100"), 4, RoundingMode.HALF_UP)
                }
            }

            if (maxCap != null && rawBenefit > maxCap) {
                netBenefit = maxCap.setScale(2, RoundingMode.HALF_UP)
                breakdown = "Calculated benefit ₹${rawBenefit.setScale(2, RoundingMode.HALF_UP)} exceeded cap. Capped at ₹${netBenefit}."
            } else {
                netBenefit = rawBenefit.setScale(2, RoundingMode.HALF_UP)
                breakdown = "Earned on ₹${context.purchaseAmount.setScale(2, RoundingMode.HALF_UP)} with rule '$appliedRule' = ₹$netBenefit"
            }

            effectiveRate = if (context.purchaseAmount > BigDecimal.ZERO) {
                netBenefit.divide(context.purchaseAmount, 4, RoundingMode.HALF_UP)
                    .multiply(BigDecimal("100"))
                    .setScale(2, RoundingMode.HALF_UP)
            } else {
                BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP)
            }
        }

        return EvaluationResult(
            cardId = card.id,
            cardName = card.displayName,
            issuer = card.issuer,
            variant = card.variant,
            maskedNumber = card.maskedNumber,
            estimatedNetBenefitInr = netBenefit,
            effectiveRatePercent = effectiveRate,
            calculationBreakdown = breakdown,
            appliedRule = appliedRule,
            eligibilityConditions = eligibilityNotes,
            offerExpiry = expiryDate,
            confidence = confidence
        )
    }

    fun rankCards(
        cards: List<CreditCard>,
        offers: List<CardOffer>,
        context: PurchaseContext
    ): List<EvaluationResult> {
        return cards
            .filter { !it.isArchived }
            .map { evaluateCard(it, offers, context) }
            .sortedByDescending { it.estimatedNetBenefitInr }
    }
}
