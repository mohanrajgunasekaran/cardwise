package com.cardwise.app.ui.screens.statements

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.cardwise.app.data.repository.CardWiseRepository
import com.cardwise.app.domain.model.CreditCard
import com.cardwise.app.domain.model.Statement
import com.cardwise.app.ui.components.MinimumDueWarningBanner
import kotlinx.coroutines.launch
import java.math.BigDecimal
import java.time.LocalDate
import java.util.UUID

@Composable
fun StatementReviewScreen(
    repository: CardWiseRepository,
    navController: NavController,
    modifier: Modifier = Modifier
) {
    val cards by repository.getActiveCards().collectAsState(initial = emptyList())
    val scope = rememberCoroutineScope()

    var selectedCardId by remember { mutableStateOf("") }
    var totalBalanceStr by remember { mutableStateOf("12500.00") }
    var minimumDueStr by remember { mutableStateOf("650.00") }
    var statementDateStr by remember { mutableStateOf(LocalDate.now().minusDays(5).toString()) }
    var dueDateStr by remember { mutableStateOf(LocalDate.now().plusDays(15).toString()) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var successMessage by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(cards) {
        if (cards.isNotEmpty() && selectedCardId.isEmpty()) {
            selectedCardId = cards.first().id
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
                text = "Statement Import & Review",
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "Review extracted statement values before committing to local persistence. Duplicate cycles and conflicting dates are detected automatically.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
            )
        }

        item {
            MinimumDueWarningBanner()
        }

        item {
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = "1. Associate with Registered Card",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.SemiBold
                    )

                    if (cards.isEmpty()) {
                        Text(
                            text = "No cards available. Please add a card first.",
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodySmall
                        )
                    } else {
                        Column {
                            cards.forEach { card ->
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    RadioButton(
                                        selected = selectedCardId == card.id,
                                        onClick = { selectedCardId = card.id }
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        text = "${card.issuer} ${card.variant} (${card.maskedNumber})",
                                        style = MaterialTheme.typography.bodyMedium
                                    )
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "2. Review Financial Balances",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.SemiBold
                    )

                    OutlinedTextField(
                        value = totalBalanceStr,
                        onValueChange = { totalBalanceStr = it },
                        label = { Text("Total Statement Balance (₹)") },
                        leadingIcon = { Text("₹") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )

                    OutlinedTextField(
                        value = minimumDueStr,
                        onValueChange = { minimumDueStr = it },
                        label = { Text("Minimum Amount Due (₹)") },
                        leadingIcon = { Text("₹") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "3. Review Dates (YYYY-MM-DD)",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.SemiBold
                    )

                    OutlinedTextField(
                        value = statementDateStr,
                        onValueChange = { statementDateStr = it },
                        label = { Text("Statement Date") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )

                    OutlinedTextField(
                        value = dueDateStr,
                        onValueChange = { dueDateStr = it },
                        label = { Text("Payment Due Date") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }

        if (errorMessage != null) {
            item {
                Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)) {
                    Row(modifier = Modifier.padding(12.dp)) {
                        Icon(Icons.Default.Error, contentDescription = null, tint = MaterialTheme.colorScheme.error)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(text = errorMessage!!, color = MaterialTheme.colorScheme.onErrorContainer)
                    }
                }
            }
        }

        if (successMessage != null) {
            item {
                Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
                    Row(modifier = Modifier.padding(12.dp)) {
                        Icon(Icons.Default.CheckCircle, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(text = successMessage!!, color = MaterialTheme.colorScheme.onPrimaryContainer)
                    }
                }
            }
        }

        item {
            Button(
                onClick = {
                    errorMessage = null
                    successMessage = null
                    val bal = totalBalanceStr.toBigDecimalOrNull()
                    val minDue = minimumDueStr.toBigDecimalOrNull()
                    val stmtDate = try { LocalDate.parse(statementDateStr) } catch (e: Exception) { null }
                    val dueDate = try { LocalDate.parse(dueDateStr) } catch (e: Exception) { null }

                    if (selectedCardId.isEmpty()) {
                        errorMessage = "Please select an associated card."
                    } else if (bal == null || bal < BigDecimal.ZERO) {
                        errorMessage = "Invalid statement balance entered."
                    } else if (minDue == null || minDue < BigDecimal.ZERO || minDue > bal) {
                        errorMessage = "Minimum due cannot exceed total statement balance."
                    } else if (stmtDate == null || dueDate == null || dueDate.isBefore(stmtDate)) {
                        errorMessage = "Payment due date must be on or after statement date."
                    } else {
                        scope.launch {
                            val statement = Statement(
                                id = UUID.randomUUID().toString(),
                                cardId = selectedCardId,
                                statementDate = stmtDate,
                                paymentDueDate = dueDate,
                                periodStart = stmtDate.minusDays(30),
                                periodEnd = stmtDate,
                                totalBalance = bal,
                                minimumDue = minDue,
                                source = "EXTRACTED_REVIEW"
                            )
                            val added = repository.addStatement(statement)
                            if (added) {
                                successMessage = "Statement saved successfully! No duplicates detected."
                            } else {
                                errorMessage = "Duplicate rejected: A statement already exists for this card on this date."
                            }
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Default.Save, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text("Confirm & Save Verified Statement")
            }
        }

        item {
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}
