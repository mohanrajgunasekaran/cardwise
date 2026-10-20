package com.cardwise.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Receipt
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.*
import com.cardwise.app.ui.navigation.Screen
import com.cardwise.app.ui.navigation.bottomNavScreens
import com.cardwise.app.ui.screens.home.HomeScreen
import com.cardwise.app.ui.screens.matcher.MatcherScreen
import com.cardwise.app.ui.screens.payments.PaymentsScreen
import com.cardwise.app.ui.screens.rewards.RewardsScreen
import com.cardwise.app.ui.screens.settings.SettingsScreen
import com.cardwise.app.ui.screens.statements.StatementReviewScreen
import com.cardwise.app.ui.screens.wallet.WalletScreen
import com.cardwise.app.ui.theme.CardWiseTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val app = application as CardWiseApplication
        val repository = app.repository

        setContent {
            CardWiseTheme {
                CardWiseAppRoot(repository = repository)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CardWiseAppRoot(repository: com.cardwise.app.data.repository.CardWiseRepository) {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = navBackStackEntry?.destination

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "CardWise",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                },
                actions = {
                    IconButton(onClick = { navController.navigate(Screen.StatementReview.route) }) {
                        Icon(Icons.Default.Receipt, contentDescription = "Import Statement")
                    }
                    IconButton(onClick = { navController.navigate(Screen.Settings.route) }) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        bottomBar = {
            NavigationBar(
                containerColor = MaterialTheme.colorScheme.surface
            ) {
                bottomNavScreens.forEach { screen ->
                    val isSelected = currentDestination?.route == screen.route
                    NavigationBarItem(
                        icon = { Icon(screen.icon, contentDescription = screen.title) },
                        label = { Text(screen.title) },
                        selected = isSelected,
                        onClick = {
                            navController.navigate(screen.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = MaterialTheme.colorScheme.primary,
                            selectedTextColor = MaterialTheme.colorScheme.primary,
                            indicatorColor = MaterialTheme.colorScheme.primaryContainer
                        )
                    )
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Screen.Home.route,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Screen.Home.route) {
                HomeScreen(repository = repository, navController = navController)
            }
            composable(Screen.Wallet.route) {
                WalletScreen(repository = repository)
            }
            composable(Screen.Matcher.route) {
                MatcherScreen(repository = repository)
            }
            composable(Screen.Payments.route) {
                PaymentsScreen(repository = repository)
            }
            composable(Screen.Rewards.route) {
                RewardsScreen(repository = repository)
            }
            composable(Screen.Settings.route) {
                SettingsScreen(repository = repository)
            }
            composable(Screen.StatementReview.route) {
                StatementReviewScreen(repository = repository, navController = navController)
            }
        }
    }
}
