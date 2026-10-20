package com.cardwise.app

import com.cardwise.app.data.local.SampleData
import com.cardwise.app.domain.engine.CardMatcherEngine
import com.cardwise.app.domain.model.PurchaseContext
import org.junit.Assert.*
import org.junit.Test
import java.math.BigDecimal

class CardMatcherEngineTest {

    @Test
    fun testAmazonShoppingPicksAmazonPayIciciTopRanked() {
        val cards = SampleData.DEMO_CARDS
        val offers = SampleData.DEMO_OFFERS
        val context = PurchaseContext(
            purchaseAmount = BigDecimal("5000.00"),
            category = "SHOPPING",
            merchant = "Amazon"
        )

        val ranked = CardMatcherEngine.rankCards(cards, offers, context)

        assertFalse(ranked.isEmpty())
        val top = ranked.first()

        // Amazon Pay ICICI should earn 5% cashback on Amazon shopping = ₹250.00
        assertTrue(top.variant.contains("Amazon Pay", ignoreCase = true) || top.issuer.contains("ICICI", ignoreCase = true))
        assertEquals(BigDecimal("250.00"), top.estimatedNetBenefitInr)
        assertEquals(BigDecimal("5.00"), top.effectiveRatePercent)
        assertEquals("VERIFIED", top.confidence)
    }

    @Test
    fun testGroceryCapEnforcementOnRblShoprite() {
        val card = SampleData.DEMO_CARDS.first { it.variant == "Shoprite" }
        val offers = SampleData.DEMO_OFFERS
        // Spend ₹25,000 on Groceries
        val context = PurchaseContext(
            purchaseAmount = BigDecimal("25000.00"),
            category = "GROCERIES"
        )

        val result = CardMatcherEngine.evaluateCard(card, offers, context)

        // Offer is capped at ₹1,000
        assertEquals(BigDecimal("1000.00"), result.estimatedNetBenefitInr)
        assertTrue(result.calculationBreakdown.contains("exceeded cap", ignoreCase = true))
    }

    @Test
    fun testFuelExclusionReturnsZeroWhenNoWaiver() {
        val card = SampleData.DEMO_CARDS.first { it.variant == "Coral" }
        val offers = SampleData.DEMO_OFFERS
        val context = PurchaseContext(
            purchaseAmount = BigDecimal("3000.00"),
            category = "FUEL"
        )

        val result = CardMatcherEngine.evaluateCard(card, offers, context)

        assertEquals(BigDecimal("0.00"), result.estimatedNetBenefitInr)
        assertTrue(result.calculationBreakdown.contains("excluded", ignoreCase = true))
    }
}
