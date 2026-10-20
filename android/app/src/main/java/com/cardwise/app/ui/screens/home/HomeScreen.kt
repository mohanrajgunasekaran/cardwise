package com.cardwise.app.ui.screens.home

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.cardwise.app.data.repository.CardWiseRepository
import com.cardwise.app.domain.model.HomeMetrics
import com.cardwise.app.ui.components.MetricCard
import com.cardwise.app.ui.components.MinimumDueWarningBanner
import com.cardwise.app.ui.navigation.Screen

@Composable
fun HomeScreen(
    repository: CardWiseRepository,
    navController: NavController,
    modifier: Modifier = Modifier
) {
    val metrics by repository.getHomeMetrics().collectAsState(initial = HomeMetrics())

    LazyColumn(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Financial Overview",
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "Track balances, upcoming due dates, and payment schedules",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
            )
        }

        item {
            MetricCard(
                title = "Total Statement Balances",
                amount = metrics.totalStatementBalances,
                subtitle = "Sum of active, non-duplicated monthly statements",
                icon = Icons.Default.AccountBalance
            )
        }

        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                MetricCard(
                    title = "Minimum Due",
                    amount = metrics.totalMinimumDue,
                    icon = Icons.Default.WarningAmber,
                    modifier = Modifier.weight(1f)
                )
                MetricCard(
                    title = "Remaining to Plan",
                    amount = metrics.remainingUnplannedTotal,
                    icon = Icons.Default.Schedule,
                    modifier = Modifier.weight(1f)
                )
            }
        }

        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                MetricCard(
                    title = "Planned Payments",
                    amount = metrics.plannedPaymentTotal,
                    subtitle = "Scheduled",
                    icon = Icons.Default.Event,
                    modifier = Modifier.weight(1f)
                )
                MetricCard(
                    title = "Confirmed Paid",
                    amount = metrics.confirmedPaymentTotal,
                    subtitle = "Reconciled",
                    icon = Icons.Default.CheckCircle,
                    modifier = Modifier.weight(1f)
                )
            }
        }

        if (metrics.overdueCount > 0) {
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Icon(Icons.Default.Error, contentDescription = null, tint = MaterialTheme.colorScheme.error)
                        Text(
                            text = "${metrics.overdueCount} statement(s) are past due date! Please review immediately.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onErrorContainer
                        )
                    }
                }
            }
        }

        item {
            MinimumDueWarningBanner()
        }

        item {
            Text(
                text = "Quick Actions",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = { navController.navigate(Screen.Matcher.route) },
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                ) {
                    Icon(Icons.Default.AutoAwesome, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Match Card")
                }
                OutlinedButton(
                    onClick = { navController.navigate(Screen.Payments.route) },
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(Icons.Default.Payment, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Plan Pay")
                }
            }
        }

        item {
            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}
