package com.cardwise.app.ui.screens.matcher

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.cardwise.app.data.repository.CardWiseRepository
import com.cardwise.app.domain.engine.CardMatcherEngine
import com.cardwise.app.domain.model.EvaluationResult
import com.cardwise.app.domain.model.PurchaseContext
import com.cardwise.app.ui.components.ExplainableCalculationCard
import java.math.BigDecimal

val CATEGORIES = listOf(
    "SHOPPING",
    "GROCERIES",
    "DINING",
    "TRAVEL",
    "FLIGHTS",
    "HOTELS",
    "UTILITIES",
    "SUBSCRIPTIONS",
    "FUEL",
    "INSURANCE",
    "OTHER"
)

@Composable
fun MatcherScreen(
    repository: CardWiseRepository,
    modifier: Modifier = Modifier
) {
    val cards by repository.getActiveCards().collectAsState(initial = emptyList())
    val offers by repository.getActiveOffers().collectAsState(initial = emptyList())

    var purchaseAmountStr by remember { mutableStateOf("5000") }
    var selectedCategory by remember { mutableStateOf("SHOPPING") }
    var merchantName by remember { mutableStateOf("") }
    var recommendations by remember { mutableStateOf<List<EvaluationResult>>(emptyList()) }

    // Re-evaluate whenever inputs or card lists change
    LaunchedEffect(cards, offers, purchaseAmountStr, selectedCategory, merchantName) {
        val amount = purchaseAmountStr.toBigDecimalOrNull() ?: BigDecimal.ZERO
        if (amount > BigDecimal.ZERO && cards.isNotEmpty()) {
            val context = PurchaseContext(
                purchaseAmount = amount,
                category = selectedCategory,
                merchant = if (merchantName.isNotBlank()) merchantName.trim() else null
            )
            recommendations = CardMatcherEngine.rankCards(cards, offers, context)
        } else {
            recommendations = emptyList()
        }
    }

    LazyColumn(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Smart Card Matcher",
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "Find the most beneficial card for your planned purchase",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
            )
        }

        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                shape = MaterialTheme.shapes.large,
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    OutlinedTextField(
                        value = purchaseAmountStr,
                        onValueChange = { purchaseAmountStr = it },
                        label = { Text("Planned Purchase Amount (₹)") },
                        leadingIcon = { Text("₹", style = MaterialTheme.typography.titleMedium) },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Text(
                        text = "Category",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                    )

                    LazyRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        items(CATEGORIES) { cat ->
                            FilterChip(
                                selected = selectedCategory == cat,
                                onClick = { selectedCategory = cat },
                                label = { Text(cat.replace("_", " ").lowercase().replaceFirstChar { it.uppercase() }) }
                            )
                        }
                    }

                    OutlinedTextField(
                        value = merchantName,
                        onValueChange = { merchantName = it },
                        label = { Text("Merchant / Platform (Optional)") },
                        placeholder = { Text("e.g. Amazon, Swiggy, MakeMyTrip") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }

        if (cards.isEmpty()) {
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.6f))
                ) {
                    Column(
                        modifier = Modifier.padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "Please add credit cards in the 'My Cards' wallet to run the recommendation engine.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f)
                        )
                    }
                }
            }
        } else if (recommendations.isNotEmpty()) {
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Top Recommended Cards",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "${recommendations.size} cards evaluated",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                    )
                }
            }

            itemsIndexed(recommendations) { index, rec ->
                ExplainableCalculationCard(
                    result = rec,
                    rank = index + 1
                )
            }
        }

        item {
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}
