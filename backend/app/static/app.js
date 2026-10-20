// CardWise Frontend Client Controller
const API_BASE = '/api/v1';
let authToken = localStorage.getItem('cardwise_token');
let currentCategory = 'SHOPPING';
let userCards = [];

// Currency formatter for Indian Rupees
function formatINR(val) {
    const num = parseFloat(val) || 0;
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 2
    }).format(num);
}

// Ensure session exists
async function initSession() {
    if (!authToken) {
        const demoEmail = 'demo_user@cardwise.local';
        const demoPassword = 'Password123!';

        // Try login
        let res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: demoEmail, password: demoPassword })
        });

        if (!res.ok) {
            // Register first
            await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: demoEmail, password: demoPassword, full_name: 'CardWise Explorer' })
            });

            res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: demoEmail, password: demoPassword })
            });
        }

        if (res.ok) {
            const data = await res.json();
            authToken = data.access_token;
            localStorage.setItem('cardwise_token', authToken);
        }
    }
}

function authHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
    };
}

// Tab navigation
document.querySelectorAll('.nav-item').forEach(button => {
    button.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));

        button.classList.add('active');
        const tabId = button.getAttribute('data-tab');
        document.getElementById(`tab-${tabId}`).classList.add('active');

        // Update titles
        const titles = {
            'home': ['Financial Overview', 'Track balances, upcoming due dates, and payment planning'],
            'wallet': ['My Cards Wallet', 'Manage credit cards, sanctioned limits, and billing dates'],
            'matcher': ['Smart Card Matcher', 'Find the most beneficial card for planned purchases'],
            'payments': ['Payments & Ledger', 'Plan disbursements and verify confirmed settlements'],
            'rewards': ['Rewards & Offers', 'Active verified benefits and validity trackers'],
            'statement-import': ['Statement Review', 'Audit extracted statement fields before persistence']
        };
        document.getElementById('page-title').innerText = titles[tabId][0];
        document.getElementById('page-subtitle').innerText = titles[tabId][1];

        refreshCurrentTab(tabId);
    });
});

// Category chip selection
document.querySelectorAll('.category-chips .chip').forEach(chip => {
    chip.addEventListener('click', () => {
        document.querySelectorAll('.category-chips .chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        currentCategory = chip.getAttribute('data-cat');
        runMatcher();
    });
});

async function refreshCurrentTab(tabId) {
    if (tabId === 'home') loadDashboard();
    else if (tabId === 'wallet') loadWallet();
    else if (tabId === 'matcher') runMatcher();
    else if (tabId === 'payments') loadPayments();
    else if (tabId === 'rewards') loadOffers();
    else if (tabId === 'statement-import') populateStatementCardDropdown();
}

// 1. Dashboard Loader
async function loadDashboard() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/summary`, { headers: authHeaders() });
        if (!res.ok) return;
        const summary = await res.json();

        document.getElementById('metric-statement-balance').innerText = formatINR(summary.total_statement_balances);
        document.getElementById('metric-minimum-due').innerText = formatINR(summary.total_minimum_due);
        document.getElementById('metric-remaining-plan').innerText = formatINR(summary.remaining_unplanned_total);
        document.getElementById('metric-planned-confirmed').innerText =
            `${formatINR(summary.planned_payment_total)} / ${formatINR(summary.confirmed_payment_total)}`;
        document.getElementById('card-count-badge').innerText = `${summary.total_cards_count} Cards`;

        await loadWalletPreview();
    } catch (e) {
        console.error('Error loading dashboard summary', e);
    }
}

async function loadWalletPreview() {
    try {
        const res = await fetch(`${API_BASE}/cards`, { headers: authHeaders() });
        if (!res.ok) return;
        userCards = await res.json();
        const container = document.getElementById('home-cards-preview');

        if (userCards.length === 0) {
            container.innerHTML = `<div class="empty-state">No cards added yet. Click "Load 10 Reference Cards" above to populate synthetic data.</div>`;
            return;
        }

        container.innerHTML = userCards.slice(0, 4).map(card => renderCardHtml(card)).join('');
    } catch (e) {
        console.error('Error loading cards', e);
    }
}

// 2. Wallet Loader
async function loadWallet() {
    try {
        const res = await fetch(`${API_BASE}/cards`, { headers: authHeaders() });
        if (!res.ok) return;
        userCards = await res.json();
        const container = document.getElementById('wallet-cards-list');

        if (userCards.length === 0) {
            container.innerHTML = `<div class="empty-state">No credit cards added. Click "Load 10 Reference Cards" to view sample cards.</div>`;
            return;
        }

        container.innerHTML = userCards.map(card => renderCardHtml(card)).join('');
    } catch (e) {
        console.error('Error loading wallet', e);
    }
}

function renderCardHtml(card) {
    const verifiedClass = card.is_verified ? 'verified' : '';
    const verifiedText = card.is_verified ? 'Verified' : 'Unverified';
    const limitDisplay = card.available_limit ? formatINR(card.available_limit) : 'Unknown';

    return `
        <div class="credit-card-item">
            <div>
                <div class="card-top">
                    <span class="card-issuer">${card.issuer}</span>
                    <span class="card-tag ${verifiedClass}">${verifiedText}</span>
                </div>
                <div class="card-variant">${card.nickname ? `${card.nickname} (${card.variant})` : card.variant}</div>
                <div class="card-masked">${card.masked_number}</div>
            </div>
            <div class="card-footer">
                <div class="card-footer-item">
                    <span>Available Limit</span>
                    <strong>${limitDisplay}</strong>
                </div>
                <div class="card-footer-item" style="text-align: right;">
                    <span>Billing Day</span>
                    <strong>${card.billing_cycle_day}th of month</strong>
                </div>
            </div>
        </div>
    `;
}

// 3. Smart Card Matcher
async function runMatcher() {
    const amountVal = parseFloat(document.getElementById('matcher-amount').value) || 0;
    const merchantVal = document.getElementById('matcher-merchant').value.trim();
    const container = document.getElementById('matcher-results-list');

    if (amountVal <= 0) {
        container.innerHTML = `<div class="empty-state">Please enter a valid purchase amount greater than 0.</div>`;
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/matcher/recommend`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                purchase_amount: amountVal,
                category: currentCategory,
                merchant: merchantVal || null
            })
        });

        if (!res.ok) {
            const err = await res.json();
            container.innerHTML = `<div class="empty-state">${err.detail || 'Could not evaluate recommendations.'}</div>`;
            return;
        }

        const data = await res.json();
        const recs = data.recommendations;

        if (!recs || recs.length === 0) {
            container.innerHTML = `<div class="empty-state">No eligible cards found for this category.</div>`;
            return;
        }

        container.innerHTML = recs.map((rec, index) => `
            <div class="result-card ${index === 0 ? 'rank-1' : ''}">
                <div class="result-card-header">
                    <div>
                        <span class="rank-badge">#${index + 1} Best Card</span>
                        <strong style="margin-left: 8px; font-size: 15px;">${rec.card_name}</strong>
                    </div>
                    <span class="benefit-pill">${rec.effective_rate_percent}% Return</span>
                </div>
                <div class="benefit-inr">${formatINR(rec.estimated_net_benefit_inr)} Net Benefit</div>
                <div class="result-formula"><strong>Calculation:</strong> ${rec.calculation_breakdown}</div>
                <div class="result-formula" style="color: var(--slate-600); margin-top: 4px;"><strong>Conditions:</strong> ${rec.eligibility_conditions}</div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Error running matcher', e);
    }
}

document.getElementById('run-matcher-btn').addEventListener('click', runMatcher);
document.getElementById('matcher-amount').addEventListener('input', runMatcher);
document.getElementById('matcher-merchant').addEventListener('input', runMatcher);

// 4. Payments
async function loadPayments() {
    try {
        const res = await fetch(`${API_BASE}/statements`, { headers: authHeaders() });
        if (!res.ok) return;
        const statements = await res.json();
        const container = document.getElementById('statements-list');

        if (statements.length === 0) {
            container.innerHTML = `<div class="empty-state">No statements recorded. Add a card and generate statements or load sample data.</div>`;
            return;
        }

        container.innerHTML = statements.map(stmt => `
            <div class="statement-box">
                <div class="statement-top">
                    <div>
                        <span class="due-date-highlight">Payment Due Date: ${stmt.payment_due_date}</span>
                        <span style="color: var(--slate-600); margin-left: 12px; font-size: 13px;">(Statement: ${stmt.statement_date})</span>
                    </div>
                    <span class="badge">${stmt.is_paid ? 'Paid' : 'Unpaid Statement'}</span>
                </div>
                <div class="statement-amounts-row">
                    <div class="amount-col">
                        <span>Statement Balance</span>
                        <strong>${formatINR(stmt.total_balance)}</strong>
                    </div>
                    <div class="amount-col">
                        <span>Minimum Due</span>
                        <strong style="color: var(--rose);">${formatINR(stmt.minimum_due)}</strong>
                    </div>
                    <div class="amount-col">
                        <span>Confirmed Paid</span>
                        <strong style="color: var(--primary);">${formatINR(stmt.confirmed_paid_amount)}</strong>
                    </div>
                    <div class="amount-col">
                        <span>Remaining to Plan</span>
                        <strong>${formatINR(stmt.remaining_to_plan)}</strong>
                    </div>
                </div>

                <div class="payment-plan-form">
                    <div class="form-group">
                        <label>Schedule Payment Tranche (₹)</label>
                        <input type="number" id="pay-amt-${stmt.id}" value="${stmt.remaining_to_plan}" step="100">
                    </div>
                    <button class="btn btn-primary" onclick="planPayment('${stmt.id}')">Schedule Payment</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Error loading payments', e);
    }
}

window.planPayment = async function(statementId) {
    const input = document.getElementById(`pay-amt-${statementId}`);
    const amount = parseFloat(input.value);
    if (!amount || amount <= 0) {
        alert('Please enter a valid amount');
        return;
    }

    try {
        const today = new Date().toISOString().split('T')[0];
        const res = await fetch(`${API_BASE}/payments`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                statement_id: statementId,
                amount: amount,
                planned_date: today,
                notes: 'Browser scheduled tranche'
            })
        });

        if (res.ok) {
            alert('Payment planned successfully!');
            loadPayments();
            loadDashboard();
        }
    } catch (e) {
        console.error('Error planning payment', e);
    }
};

// 5. Offers Catalog
async function loadOffers() {
    try {
        const res = await fetch(`${API_BASE}/offers`, { headers: authHeaders() });
        if (!res.ok) return;
        const offers = await res.json();
        const container = document.getElementById('offers-grid');

        if (offers.length === 0) {
            container.innerHTML = `<div class="empty-state">No offers available in catalog.</div>`;
            return;
        }

        container.innerHTML = offers.map(off => `
            <div class="credit-card-item">
                <div class="card-top">
                    <span class="card-issuer">${off.issuer}</span>
                    <span class="card-tag verified">${off.category}</span>
                </div>
                <div class="card-variant">${off.title}</div>
                <p style="font-size: 13px; color: var(--slate-600); margin: 8px 0;">${off.exclusion_details || 'Standard terms apply.'}</p>
                <div class="card-footer">
                    <div class="card-footer-item">
                        <span>Validity</span>
                        <strong>Until ${off.valid_to}</strong>
                    </div>
                    <div class="card-footer-item" style="text-align: right;">
                        <span>Confidence</span>
                        <strong>${off.confidence}</strong>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Error loading offers', e);
    }
}

// 6. Statement Import Review
async function populateStatementCardDropdown() {
    const select = document.getElementById('stmt-card-select');
    if (userCards.length === 0) {
        const res = await fetch(`${API_BASE}/cards`, { headers: authHeaders() });
        if (res.ok) userCards = await res.json();
    }
    select.innerHTML = '<option value="">-- Choose Card --</option>' +
        userCards.map(c => `<option value="${c.id}">${c.issuer} ${c.variant} (${c.masked_number})</option>`).join('');

    // Default dates
    const today = new Date();
    document.getElementById('stmt-date').value = today.toISOString().split('T')[0];
    const dueDate = new Date();
    dueDate.setDate(today.getDate() + 20);
    document.getElementById('stmt-due-date').value = dueDate.toISOString().split('T')[0];
}

document.getElementById('statement-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const cardId = document.getElementById('stmt-card-select').value;
    const balance = parseFloat(document.getElementById('stmt-balance').value);
    const minDue = parseFloat(document.getElementById('stmt-min-due').value);
    const stmtDate = document.getElementById('stmt-date').value;
    const dueDate = document.getElementById('stmt-due-date').value;
    const alertBox = document.getElementById('statement-alert');

    alertBox.style.display = 'none';

    try {
        const res = await fetch(`${API_BASE}/statements`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                card_id: cardId,
                statement_date: stmtDate,
                payment_due_date: dueDate,
                period_start: stmtDate,
                period_end: dueDate,
                total_balance: balance,
                minimum_due: minDue,
                source: 'BROWSER_REVIEW'
            })
        });

        if (res.status === 409) {
            alertBox.className = 'alert-box error';
            alertBox.innerText = 'Duplicate rejected: A statement already exists for this card on this date.';
            alertBox.style.display = 'block';
        } else if (res.ok) {
            alertBox.className = 'alert-box success';
            alertBox.innerText = 'Statement validated and saved successfully!';
            alertBox.style.display = 'block';
            loadDashboard();
        } else {
            const err = await res.json();
            alertBox.className = 'alert-box error';
            alertBox.innerText = err.detail || 'Failed to save statement.';
            alertBox.style.display = 'block';
        }
    } catch (e) {
        console.error('Error saving statement', e);
    }
});

// Seed Button
document.getElementById('seed-demo-btn').addEventListener('click', async () => {
    try {
        const res = await fetch(`${API_BASE}/auth/seed-demo-data`, {
            method: 'POST',
            headers: authHeaders()
        });
        if (res.ok) {
            const data = await res.json();
            alert(data.message || '10 Reference Cards Loaded!');
            await loadDashboard();
            await loadWallet();
        }
    } catch (e) {
        console.error('Error seeding data', e);
    }
});

// Add Card Modal
const modal = document.getElementById('add-card-modal');
document.getElementById('open-add-card-modal').addEventListener('click', () => modal.classList.add('active'));
document.getElementById('close-modal-btn').addEventListener('click', () => modal.classList.remove('active'));

document.getElementById('add-card-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const issuer = document.getElementById('card-issuer').value.trim();
    const variant = document.getElementById('card-variant').value.trim();
    const last4 = document.getElementById('card-last4').value.trim();
    const limit = parseFloat(document.getElementById('card-limit').value) || null;
    const cycleDay = parseInt(document.getElementById('card-billing-day').value) || 15;

    try {
        const res = await fetch(`${API_BASE}/cards`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                issuer: issuer,
                variant: variant,
                masked_number: `XXXX-XXXX-XXXX-${last4}`,
                credit_limit: limit,
                available_limit: limit,
                billing_cycle_day: cycleDay,
                is_verified: true
            })
        });

        if (res.ok) {
            modal.classList.remove('active');
            document.getElementById('add-card-form').reset();
            loadWallet();
            loadDashboard();
        }
    } catch (e) {
        console.error('Error saving card', e);
    }
});

// Bootstrapping
window.addEventListener('DOMContentLoaded', async () => {
    await initSession();
    await loadDashboard();
    await runMatcher();
});
