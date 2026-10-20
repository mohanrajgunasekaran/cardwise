package com.cardwise.app.ui.screens.wallet

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.cardwise.app.data.repository.CardWiseRepository
import com.cardwise.app.domain.model.CreditCard
import com.cardwise.app.domain.model.NetworkType
import com.cardwise.app.domain.model.RewardType
import com.cardwise.app.ui.components.MaskedCardItem
import kotlinx.coroutines.launch
import java.math.BigDecimal
import java.util.UUID

@Composable
fun WalletScreen(
    repository: CardWiseRepository,
    modifier: Modifier = Modifier
) {
    val cards by repository.getActiveCards().collectAsState(initial = emptyList())
    val scope = rememberCoroutineScope()
    var showAddCardDialog by remember { mutableStateOf(false) }

    Scaffold(
        floatingActionButton = {
            FloatingActionButton(
                onClick = { showAddCardDialog = true },
                containerColor = MaterialTheme.colorScheme.primary
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add Card")
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "Card Wallet",
                            style = MaterialTheme.typography.headlineLarge,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "${cards.size} active cards registered",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                        )
                    }

                    if (cards.isEmpty()) {
                        FilledTonalButton(
                            onClick = {
                                scope.launch {
                                    repository.seedDemoData()
                                }
                            }
                        ) {
                            Text("Load 10 Demo Cards")
                        }
                    }
                }
            }

            if (cards.isEmpty()) {
                item {
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 32.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
                    ) {
                        Column(
                            modifier = Modifier.padding(24.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Icon(
                                Icons.Default.CreditCard,
                                contentDescription = null,
                                modifier = Modifier.size(48.dp),
                                tint = MaterialTheme.colorScheme.primary
                            )
                            Spacer(modifier = Modifier.height(12.dp))
                            Text(
                                text = "No Credit Cards Added",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = "Add your cards with masked numbers to enable intelligent reward calculations and bill tracking.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                                modifier = Modifier.padding(top = 4.dp, bottom = 16.dp)
                            )
                            Button(
                                onClick = {
                                    scope.launch {
                                        repository.seedDemoData()
                                    }
                                }
                            ) {
                                Text("Populate 10 Reference Cards")
                            }
                        }
                    }
                }
            } else {
                items(cards, key = { it.id }) { card ->
                    MaskedCardItem(
                        card = card,
                        onClick = {
                            // View details or archive option
                        }
                    )
                }
            }

            item {
                Spacer(modifier = Modifier.height(48.dp))
            }
        }
    }

    if (showAddCardDialog) {
        AddCardDialog(
            onDismiss = { showAddCardDialog = false },
            onAddCard = { newCard ->
                scope.launch {
                    repository.insertCard(newCard)
                    showAddCardDialog = false
                }
            }
        )
    }
}

@Composable
fun AddCardDialog(
    onDismiss: () -> Unit,
    onAddCard: (CreditCard) -> Unit
) {
    var issuer by remember { mutableStateOf("") }
    var variant by remember { mutableStateOf("") }
    var nickname by remember { mutableStateOf("") }
    var last4 by remember { mutableStateOf("") }
    var creditLimitStr by remember { mutableStateOf("") }
    var billingDayStr by remember { mutableStateOf("15") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Credit Card") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = issuer,
                    onValueChange = { issuer = it },
                    label = { Text("Bank / Issuer (e.g. HDFC)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = variant,
                    onValueChange = { variant = it },
                    label = { Text("Card Variant (e.g. Coral, Regalia)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = last4,
                    onValueChange = { if (it.length <= 4) last4 = it },
                    label = { Text("Last 4 digits only") },
                    placeholder = { Text("e.g. 7207") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = creditLimitStr,
                    onValueChange = { creditLimitStr = it },
                    label = { Text("Credit Limit (₹)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = billingDayStr,
                    onValueChange = { billingDayStr = it },
                    label = { Text("Billing Cycle Day (1-31)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    if (issuer.isNotBlank() && variant.isNotBlank() && last4.length == 4) {
                        val card = CreditCard(
                            id = UUID.randomUUID().toString(),
                            issuer = issuer.trim(),
                            variant = variant.trim(),
                            nickname = if (nickname.isNotBlank()) nickname.trim() else null,
                            maskedNumber = "XXXX-XXXX-XXXX-$last4",
                            network = NetworkType.VISA,
                            creditLimit = creditLimitStr.toBigDecimalOrNull(),
                            availableLimit = creditLimitStr.toBigDecimalOrNull(),
                            billingCycleDay = billingDayStr.toIntOrNull() ?: 15,
                            isVerified = true
                        )
                        onAddCard(card)
                    }
                }
            ) {
                Text("Save Card")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
