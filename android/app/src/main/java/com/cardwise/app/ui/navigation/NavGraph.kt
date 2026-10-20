package com.cardwise.app.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.ui.graphics.vector.ImageVector

sealed class Screen(val route: String, val title: String, val icon: ImageVector) {
    object Home : Screen("home", "Home", Icons.Default.Home)
    object Wallet : Screen("wallet", "My Cards", Icons.Default.CreditCard)
    object Matcher : Screen("matcher", "Card Matcher", Icons.Default.AutoAwesome)
    object Payments : Screen("payments", "Payments", Icons.Default.AccountBalanceWallet)
    object Rewards : Screen("rewards", "Rewards", Icons.Default.CardGiftcard)
    object Settings : Screen("settings", "Settings", Icons.Default.Settings)
    object StatementReview : Screen("statement_review", "Import Statement", Icons.Default.Receipt)
}

val bottomNavScreens = listOf(
    Screen.Home,
    Screen.Wallet,
    Screen.Matcher,
    Screen.Payments,
    Screen.Rewards
)
