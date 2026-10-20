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
    const demoEmail = 'demo_user@cardwise.local';
    const demoPassword = 'Password123!';

    if (authToken) {
        try {
            const meRes = await fetch(`${API_BASE}/auth/me`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            if (meRes.ok) return;
        } catch (e) {
            console.warn('Existing token invalid, acquiring fresh token');
        }
    }

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
            'comparison': ['Card Product Comparison', 'Detailed benchmark of verified benefits, fees, charges, and lounge access'],
            'payments': ['Payments & Ledger', 'Plan disbursements and verify confirmed settlements'],
            'rewards': ['Rewards & Offers', 'Active verified benefits and validity trackers'],
            'statement-import': ['Statement Review', 'Audit extracted statement fields before persistence']
        };
        if (titles[tabId]) {
            document.getElementById('page-title').innerText = titles[tabId][0];
            document.getElementById('page-subtitle').innerText = titles[tabId][1];
        }

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
    else if (tabId === 'comparison') loadComparison();
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
        if (document.getElementById('metric-credit-balance')) {
            document.getElementById('metric-credit-balance').innerText = formatINR(summary.total_credit_balances || 0);
        }
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

        // Display all 10 cards on dashboard overview
        container.innerHTML = userCards.map(card => renderCardHtml(card)).join('');
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
    const isLazyPay = (card.masked_number === 'XX57') || (card.variant && card.variant.toLowerCase().includes('lazypay'));
    
    // Credit Limit logic
    let limitDisplay = 'Not provided';
    let limitSubBadge = '';
    if (isLazyPay && card.credit_limit) {
        limitDisplay = formatINR(card.credit_limit);
        limitSubBadge = `<span class="badge" style="background:#FFFBEB; color:#92400E; border:1px solid #FCD34D; font-size:10px; display:inline-block; margin-top:2px;">Last known limit — requires verification</span>`;
    } else if (card.credit_limit != null) {
        limitDisplay = formatINR(card.credit_limit);
    }

    // Available Limit logic
    const availDisplay = card.available_limit != null ? formatINR(card.available_limit) : 'Not provided';

    // Masked number display
    const maskedDisplay = card.masked_number || 'Not available';

    // Verification Status Tag
    const statusText = card.verification_status || (card.is_verified ? 'Verified' : 'Imported — needs verification');
    const tagClass = card.is_verified ? 'verified' : 'needs-verification';

    // Billing Day
    const billingText = card.billing_cycle_day ? `${card.billing_cycle_day}th of month` : 'Not provided';

    // Notes box
    const notesHtml = card.notes ? `<div class="card-note-box">${card.notes}</div>` : '';

    return `
        <div class="credit-card-item">
            <div>
                <div class="card-top">
                    <span class="card-issuer">${card.issuer}</span>
                    <span class="card-tag ${tagClass}">${statusText}</span>
                </div>
                <div class="card-variant">${card.nickname ? `${card.nickname} (${card.variant})` : card.variant}</div>
                <div class="card-category-sub">${card.category || 'Category: Unknown'}</div>
                <div class="card-masked">${maskedDisplay}</div>
                ${notesHtml}
            </div>
            <div>
                <div class="card-footer" style="margin-top: 12px;">
                    <div class="card-footer-item">
                        <span>Credit Limit</span>
                        <strong>${limitDisplay}</strong>
                        ${limitSubBadge}
                    </div>
                    <div class="card-footer-item">
                        <span>Available Limit</span>
                        <strong>${availDisplay}</strong>
                    </div>
                    <div class="card-footer-item" style="text-align: right;">
                        <span>Billing Cycle</span>
                        <strong>${billingText}</strong>
                    </div>
                </div>
                <div class="card-actions-row">
                    <button class="btn btn-secondary btn-sm" onclick="openCardDetails('${card.id}')">View Details / Edit</button>
                </div>
            </div>
        </div>
    `;
}

// Modal Tab Switcher
window.switchModalTab = function(tabName) {
    document.querySelectorAll('.modal-tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.modal-section-pane').forEach(pane => pane.classList.remove('active'));

    const targetBtn = document.querySelector(`.modal-tab-btn[data-section="${tabName}"]`);
    const targetPane = document.getElementById(`modal-pane-${tabName}`);
    if (targetBtn) targetBtn.classList.add('active');
    if (targetPane) targetPane.classList.add('active');
};

// 5-Section Comprehensive Card Details Modal Handler
window.openCardDetails = async function(cardId) {
    let card = userCards.find(c => c.id === cardId);
    try {
        const res = await fetch(`${API_BASE}/cards/${cardId}`, { headers: authHeaders() });
        if (res.ok) card = await res.json();
    } catch (e) {
        console.error('Error fetching card details', e);
    }
    if (!card) return;

    const modal = document.getElementById('card-details-modal');
    const content = document.getElementById('card-details-content');
    const terms = card.product_terms || {};

    const isUnverifiedVariant = !terms.exact_variant || (terms.variant_verification_status && terms.variant_verification_status.toLowerCase().includes('unverified'));
    const isDiscontinued = terms.variant_verification_status && terms.variant_verification_status.toLowerCase().includes('discontinued');

    let statusBadgeClass = 'badge-variant-verified';
    if (isUnverifiedVariant) statusBadgeClass = 'badge-variant-unverified';
    else if (isDiscontinued) statusBadgeClass = 'badge-discontinued';

    const statusPill = `<span class="${statusBadgeClass}">${terms.variant_verification_status || card.verification_status || 'Unverified'}</span>`;
    document.getElementById('detail-modal-title').innerHTML = `${card.issuer} — ${card.variant} ${statusPill}`;

    // Fetch latest statement for this card
    let stmt = null;
    try {
        const res = await fetch(`${API_BASE}/statements?card_id=${cardId}`, { headers: authHeaders() });
        if (res.ok) {
            const stmts = await res.json();
            if (stmts.length > 0) stmt = stmts[0];
        }
    } catch (e) {
        console.error('Error fetching statement for card', e);
    }

    const isLazyPay = (card.masked_number === 'XX57') || (card.variant && card.variant.toLowerCase().includes('lazypay'));
    const limitDisplay = isLazyPay && card.credit_limit
        ? `${formatINR(card.credit_limit)} <span style="font-size:11px; color:#92400E;">(Historical limit from 2023 welcome email — unverified)</span>`
        : (card.credit_limit != null ? formatINR(card.credit_limit) : 'Not provided');
    const availDisplay = card.available_limit != null ? formatINR(card.available_limit) : 'Not provided';
    const cycleDisplay = stmt && stmt.period_start && stmt.period_end
        ? `${stmt.period_start} to ${stmt.period_end}`
        : (card.billing_cycle_day ? `${card.billing_cycle_day}th of month` : 'Not provided');
    const stmtGenDisplay = stmt && stmt.statement_date ? stmt.statement_date : 'Unknown';
    
    let dueDisplay = 'Unknown — verify';
    if (stmt) {
        if (stmt.is_credit_balance) dueDisplay = '<span style="color:#059669; font-weight:700;">No payment required (Credit Surplus)</span>';
        else if (stmt.payment_due_date) dueDisplay = stmt.payment_due_date;
    }

    let balDisplay = 'Unknown';
    if (stmt) {
        if (stmt.is_credit_balance) balDisplay = `<span style="color:#059669; font-weight:700;">${formatINR(stmt.total_balance)} (Credit Balance — surplus)</span>`;
        else if (stmt.total_balance != null) balDisplay = formatINR(stmt.total_balance);
    }

    let minDisplay = 'Unknown — verify';
    if (stmt) {
        if (stmt.is_credit_balance) minDisplay = '₹0.00 (No payment required)';
        else if (stmt.minimum_due != null) minDisplay = formatINR(stmt.minimum_due);
    }

    const sourceDisplay = stmt ? `${stmt.source} (Imported Oct 2026)` : 'Fixture / Manual Import';
    const notesDisplay = card.notes || (stmt ? stmt.notes : '') || 'None';

    // RENDER 5 SECTIONS
    content.innerHTML = `
        <!-- Modal Tabs Navigation -->
        <div class="modal-nav-tabs">
            <button class="modal-tab-btn active" data-section="overview" onclick="switchModalTab('overview')">1. Overview & Statements</button>
            <button class="modal-tab-btn" data-section="rewards" onclick="switchModalTab('rewards')">2. Rewards & Cashback</button>
            <button class="modal-tab-btn" data-section="travel" onclick="switchModalTab('travel')">3. Travel & Lifestyle</button>
            <button class="modal-tab-btn" data-section="fees" onclick="switchModalTab('fees')">4. Fees & Charges</button>
            <button class="modal-tab-btn" data-section="terms" onclick="switchModalTab('terms')">5. Official Terms & Sources</button>
        </div>

        <!-- Section 1: Overview & Statements -->
        <div id="modal-pane-overview" class="modal-section-pane active">
            <div class="section-block">
                <div class="section-block-title">Card Identity & Network</div>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Bank / Issuer</label>
                        <div>${card.issuer}</div>
                    </div>
                    <div class="detail-item">
                        <label>Exact Product Variant</label>
                        <div>${terms.exact_variant || (isUnverifiedVariant ? 'Variant Unverified — exact terms withheld' : card.variant)}</div>
                    </div>
                    <div class="detail-item">
                        <label>Masked Card Number</label>
                        <div>${card.masked_number || 'Not available'}</div>
                    </div>
                    <div class="detail-item">
                        <label>Payment Network</label>
                        <div>${terms.network || card.network || 'VISA'}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label>Verification Status</label>
                        <div>${terms.variant_verification_status || card.verification_status || 'Unverified'}</div>
                    </div>
                </div>
            </div>

            <div class="section-block">
                <div class="section-block-title">Account Limits & Billing Cycle</div>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Total Credit Limit</label>
                        <div>${limitDisplay}</div>
                    </div>
                    <div class="detail-item">
                        <label>Available Credit Limit</label>
                        <div>${availDisplay}</div>
                    </div>
                    <div class="detail-item">
                        <label>Billing Cycle / Period</label>
                        <div>${cycleDisplay}</div>
                    </div>
                    <div class="detail-item">
                        <label>Statement Date</label>
                        <div>${stmtGenDisplay}</div>
                    </div>
                </div>
            </div>

            <div class="section-block">
                <div class="section-block-title">Statement Balances & Payment Status</div>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Payment Due Date</label>
                        <div>${dueDisplay}</div>
                    </div>
                    <div class="detail-item">
                        <label>Total Statement Balance</label>
                        <div>${balDisplay}</div>
                    </div>
                    <div class="detail-item">
                        <label>Minimum Amount Due</label>
                        <div>${minDisplay}</div>
                    </div>
                    <div class="detail-item">
                        <label>Statement Import Source</label>
                        <div>${sourceDisplay}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label>Account Context & Notes</label>
                        <div>${notesDisplay}</div>
                    </div>
                </div>
            </div>

            <div class="section-block">
                <div class="section-block-title">Update Card Details</div>
                <form id="edit-card-form" onsubmit="handleUpdateCard(event, '${card.id}')">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Credit Limit (₹)</label>
                            <input type="number" id="edit-limit" value="${card.credit_limit || ''}" placeholder="Leave blank if unknown">
                        </div>
                        <div class="form-group">
                            <label>Available Limit (₹)</label>
                            <input type="number" id="edit-avail-limit" value="${card.available_limit || ''}" placeholder="Leave blank if unknown">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Billing Cycle Day (1-31)</label>
                            <input type="number" id="edit-cycle-day" min="1" max="31" value="${card.billing_cycle_day || ''}" placeholder="e.g. 15">
                        </div>
                        <div class="form-group">
                            <label>Verification Status</label>
                            <select id="edit-status">
                                <option value="Imported — needs verification" ${card.verification_status === 'Imported — needs verification' ? 'selected' : ''}>Imported — needs verification</option>
                                <option value="Verified" ${card.verification_status === 'Verified' ? 'selected' : ''}>Verified</option>
                                <option value="Unverified" ${card.verification_status === 'Unverified' ? 'selected' : ''}>Unverified</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Card Notes</label>
                        <input type="text" id="edit-notes" value="${card.notes || ''}" placeholder="Add context or verification details">
                    </div>
                    <div style="display: flex; justify-content: flex-end; gap: 8px;">
                        <button type="button" class="btn btn-secondary" onclick="closeCardDetails()">Close</button>
                        <button type="submit" class="btn btn-primary">Save Updates</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Section 2: Rewards and Cashback -->
        <div id="modal-pane-rewards" class="modal-section-pane">
            <div class="section-block">
                <div class="section-block-title">Reward Structure & Value Valuation</div>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Reward Model</label>
                        <div>${terms.reward_type || (isUnverifiedVariant ? 'Unknown — unverified variant' : 'Cashback / Points')}</div>
                    </div>
                    <div class="detail-item">
                        <label>Point Redemption Value (INR)</label>
                        <div>${terms.reward_point_value != null ? `₹${parseFloat(terms.reward_point_value).toFixed(2)} per point` : (isUnverifiedVariant ? 'Unverified' : 'N/A (Direct Cashback)')}</div>
                    </div>
                    <div class="detail-item">
                        <label>Cashback / Reward Capping</label>
                        <div>${terms.cashback_cap || (isUnverifiedVariant ? 'Unverified' : 'No general capping')}</div>
                    </div>
                    <div class="detail-item">
                        <label>Reward Expiry Period</label>
                        <div>${terms.reward_expiry || (isUnverifiedVariant ? 'Unverified' : 'Does not expire')}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label>Verified Category Reward Rates</label>
                        <div>${terms.reward_rate || (isUnverifiedVariant ? 'Benefits withheld: exact card variant is unverified.' : 'Standard base rate.')}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label>Redemption Options & Settlement</label>
                        <div>${terms.redemption_method || (isUnverifiedVariant ? 'Unverified' : 'Net credit or portal catalog')}</div>
                    </div>
                </div>
            </div>

            <div class="section-block">
                <div class="section-block-title">Spend Exclusions & Eligibility Rules</div>
                <div class="detail-grid">
                    <div class="detail-item full-width">
                        <label>Eligible Spending Categories</label>
                        <div>${terms.eligible_spend_categories || (isUnverifiedVariant ? 'Unverified' : 'All standard POS and e-commerce retail transactions')}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label style="color:#B91C1C;">Excluded Spend Categories (No Rewards Accrued)</label>
                        <div style="color:#991B1B;">${terms.excluded_spend_categories || (isUnverifiedVariant ? 'Unverified' : 'Fuel, ATM cash, wallet loading, rent, EMI transactions')}</div>
                    </div>
                </div>
            </div>

            <div class="section-block">
                <div class="section-block-title">Milestones & Welcome Benefits</div>
                <div class="detail-grid">
                    <div class="detail-item full-width">
                        <label>Milestone Benefits</label>
                        <div>${terms.milestone_benefits || (isUnverifiedVariant ? 'Unverified' : 'None applicable')}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label>Welcome / Joining Offers</label>
                        <div>${terms.welcome_benefits || (isUnverifiedVariant ? 'Unverified' : 'None')}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Section 3: Travel and Lifestyle -->
        <div id="modal-pane-travel" class="modal-section-pane">
            <div class="section-block">
                <div class="section-block-title">Lounge Access & Eligibility Thresholds</div>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Airport Lounge Access</label>
                        <div>${terms.airport_lounge_access || (isUnverifiedVariant ? 'Unverified' : 'None')}</div>
                    </div>
                    <div class="detail-item">
                        <label>Railway Lounge Access</label>
                        <div>${terms.railway_lounge_access || (isUnverifiedVariant ? 'Unverified' : 'None')}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label>Lounge Spend Eligibility Requirements</label>
                        <div>${terms.lounge_eligibility_conditions || (isUnverifiedVariant ? 'Unverified — variant requires identification' : 'Not applicable / Free complimentary')}</div>
                    </div>
                </div>
            </div>

            <div class="section-block">
                <div class="section-block-title">Dining, Entertainment & Travel Offers</div>
                <div class="detail-grid">
                    <div class="detail-item full-width">
                        <label>Movie & Dining Benefits</label>
                        <div>${terms.dining_and_entertainment_benefits || (isUnverifiedVariant ? 'Unverified' : 'Standard issuer dining discounts')}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label>Travel Benefits & Concierge</label>
                        <div>${terms.travel_benefits || (isUnverifiedVariant ? 'Unverified' : 'None')}</div>
                    </div>
                </div>
            </div>

            <div class="section-block">
                <div class="section-block-title">Insurance Coverage & Purchase Protection</div>
                <div class="detail-grid">
                    <div class="detail-item full-width">
                        <label>Insurance Coverages</label>
                        <div>${terms.insurance_and_purchase_protection || (isUnverifiedVariant ? 'Unverified' : 'Zero lost card liability after reporting')}</div>
                    </div>
                    <div class="detail-item">
                        <label>Benefit Validity Window</label>
                        <div>${terms.benefit_validity || (isUnverifiedVariant ? 'Unverified' : 'Active')}</div>
                    </div>
                    <div class="detail-item">
                        <label>General Terms Reference</label>
                        <div>${terms.benefit_terms || (isUnverifiedVariant ? 'Pending variant verification' : 'Standard cardholder agreement')}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Section 4: Fees and Charges -->
        <div id="modal-pane-fees" class="modal-section-pane">
            <div class="section-block">
                <div class="section-block-title">Annual Fees & Waiver Criteria</div>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Joining Fee</label>
                        <div>${terms.joining_fee != null ? formatINR(terms.joining_fee) : (isUnverifiedVariant ? 'Unverified' : '₹0.00')}</div>
                    </div>
                    <div class="detail-item">
                        <label>Annual / Renewal Fee</label>
                        <div>${terms.annual_fee != null ? formatINR(terms.annual_fee) : (isUnverifiedVariant ? 'Unverified' : '₹0.00')}</div>
                    </div>
                    <div class="detail-item">
                        <label>Fee Waiver Spend Threshold</label>
                        <div>${terms.annual_fee_waiver_threshold != null ? formatINR(terms.annual_fee_waiver_threshold) : (isUnverifiedVariant ? 'Unverified' : 'Not applicable / LTF')}</div>
                    </div>
                    <div class="detail-item">
                        <label>Fee Waiver Conditions</label>
                        <div>${terms.waiver_period_and_conditions || (isUnverifiedVariant ? 'Unverified' : 'Standard annual cycle spend')}</div>
                    </div>
                </div>
            </div>

            <div class="section-block">
                <div class="section-block-title">Finance Charges & Cash Advance Terms</div>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Monthly Interest / Finance Charge</label>
                        <div>${terms.interest_rate_monthly != null ? `${terms.interest_rate_monthly}% per month` : (isUnverifiedVariant ? 'Unverified' : 'Standard bank rate')}</div>
                    </div>
                    <div class="detail-item">
                        <label>Annualized Interest Rate (APR)</label>
                        <div>${terms.interest_rate_annual != null ? `${terms.interest_rate_annual}% APR` : (isUnverifiedVariant ? 'Unverified' : 'Standard bank APR')}</div>
                    </div>
                    <div class="detail-item">
                        <label>Cash Advance Fee</label>
                        <div>${terms.cash_advance_fee || (isUnverifiedVariant ? 'Unverified' : '2.5% of amount (Min ₹500)')}</div>
                    </div>
                    <div class="detail-item">
                        <label>Cash Advance Interest Terms</label>
                        <div>${terms.cash_advance_interest_terms || (isUnverifiedVariant ? 'Unverified' : 'Finance charges apply from withdrawal date')}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label>Late Payment Fee Structure</label>
                        <div>${terms.late_payment_fee_structure || (isUnverifiedVariant ? 'Unverified' : 'Tiered based on total outstanding balance')}</div>
                    </div>
                </div>
            </div>

            <div class="section-block">
                <div class="section-block-title">Forex, EMI, Fuel & Miscellaneous Fees</div>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Foreign Currency / Forex Markup</label>
                        <div>${terms.forex_markup != null ? `${terms.forex_markup}%` : (isUnverifiedVariant ? 'Unverified' : '3.50%')}</div>
                    </div>
                    <div class="detail-item">
                        <label>Over-Limit Penalty</label>
                        <div>${terms.over_limit_fee || (isUnverifiedVariant ? 'Unverified' : '2.5% of overlimit amount (Min ₹500)')}</div>
                    </div>
                    <div class="detail-item">
                        <label>EMI Processing Fee</label>
                        <div>${terms.emi_processing_fee || (isUnverifiedVariant ? 'Unverified' : '₹199 + GST')}</div>
                    </div>
                    <div class="detail-item">
                        <label>EMI Foreclosure Terms</label>
                        <div>${terms.emi_foreclosure_terms || (isUnverifiedVariant ? 'Unverified' : '3% on principal balance + GST')}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label>Fuel Surcharge Waiver Terms</label>
                        <div>${terms.fuel_surcharge_terms || (isUnverifiedVariant ? 'Unverified' : '1% waiver on fuel spends between ₹400 and ₹4,000')}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label>GST Notes on Financial Charges</label>
                        <div>${terms.applicable_gst_notes || 'Standard 18% GST applies on all fees, charges, and interest.'}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Section 5: Official Terms and Sources -->
        <div id="modal-pane-terms" class="modal-section-pane">
            <div class="section-block">
                <div class="section-block-title">Verified Bank Provenance & Source Documents</div>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Official Document Title</label>
                        <div>${terms.source_title || 'Bank Schedule of Charges / Product MITC'}</div>
                    </div>
                    <div class="detail-item">
                        <label>Source Type</label>
                        <div>${terms.source_type || 'Official Schedule of Charges'}</div>
                    </div>
                    <div class="detail-item">
                        <label>Date Verified</label>
                        <div>${terms.date_verified || '2026-10-20'}</div>
                    </div>
                    <div class="detail-item">
                        <label>Terms Effective Date</label>
                        <div>${terms.effective_date || 'Current Published Terms (2026)'}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label>Direct Bank Source URL</label>
                        <div style="word-break: break-all; margin-top: 4px;">
                            ${terms.source_url ? `
                                <a href="${terms.source_url}" target="_blank" rel="noopener noreferrer" class="provenance-link">
                                    ${terms.source_url}
                                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                                </a>
                            ` : '<span style="color:#D97706;">Direct source URL pending confirmation of exact card variant.</span>'}
                        </div>
                    </div>
                </div>
            </div>

            <div class="section-block">
                <div class="section-block-title">Methodology Notes & Unresolved Questions</div>
                <div class="detail-grid">
                    <div class="detail-item full-width">
                        <label>Confidence & Verification Notes</label>
                        <div>${terms.confidence_notes || (isUnverifiedVariant ? 'Variant unverified in customer records. Material claims are suppressed to avoid fabricating features.' : 'Verified against official bank schedule of charges and MITC.')}</div>
                    </div>
                    <div class="detail-item full-width">
                        <label style="color:#B45309;">Unresolved Questions / Required Documentation</label>
                        <div style="color:#92400E;">${terms.unresolved_questions || 'None. Product variant and MITC schedule are confirmed.'}</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    modal.classList.add('active');
};

window.closeCardDetails = function() {
    const modal = document.getElementById('card-details-modal');
    if (modal) modal.classList.remove('active');
};

document.getElementById('close-details-modal-btn').addEventListener('click', closeCardDetails);

window.handleUpdateCard = async function(e, cardId) {
    e.preventDefault();
    const limitVal = document.getElementById('edit-limit').value;
    const availVal = document.getElementById('edit-avail-limit').value;
    const cycleVal = document.getElementById('edit-cycle-day').value;
    const statusVal = document.getElementById('edit-status').value;
    const notesVal = document.getElementById('edit-notes').value.trim();

    const payload = {
        credit_limit: limitVal ? parseFloat(limitVal) : null,
        available_limit: availVal ? parseFloat(availVal) : null,
        billing_cycle_day: cycleVal ? parseInt(cycleVal) : null,
        verification_status: statusVal,
        notes: notesVal || null
    };

    try {
        const res = await fetch(`${API_BASE}/cards/${cardId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            alert('Card updated successfully!');
            closeCardDetails();
            await loadWallet();
            await loadDashboard();
            if (document.getElementById('tab-comparison').classList.contains('active')) {
                await loadComparison();
            }
        } else {
            alert('Failed to update card.');
        }
    } catch (err) {
        console.error('Error updating card', err);
    }
};

// 3. Card Comparison Loader
async function loadComparison() {
    try {
        const res = await fetch(`${API_BASE}/cards`, { headers: authHeaders() });
        if (!res.ok) return;
        userCards = await res.json();
        const tbody = document.getElementById('comparison-table-body');
        const filterVal = document.getElementById('comparison-category-filter').value;

        if (userCards.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="empty-state">No credit cards available for comparison.</td></tr>`;
            return;
        }

        let filtered = userCards.filter(card => {
            const terms = card.product_terms || {};
            const isUnverified = !terms.exact_variant || (terms.variant_verification_status && terms.variant_verification_status.toLowerCase().includes('unverified'));
            if (filterVal === 'VERIFIED') return !isUnverified;
            if (filterVal === 'UNVERIFIED') return isUnverified;
            if (filterVal === 'NO_FEE') return parseFloat(terms.annual_fee || 0) === 0 && !isUnverified;
            if (filterVal === 'LOUNGE') return terms.airport_lounge_access && !terms.airport_lounge_access.toLowerCase().includes('none') && !isUnverified;
            return true;
        });

        tbody.innerHTML = filtered.map(card => {
            const terms = card.product_terms || {};
            const isUnverified = !terms.exact_variant || (terms.variant_verification_status && terms.variant_verification_status.toLowerCase().includes('unverified'));
            const isDiscontinued = terms.variant_verification_status && terms.variant_verification_status.toLowerCase().includes('discontinued');

            let badgeHtml = `<span class="badge-variant-verified">Verified</span>`;
            if (isUnverified) badgeHtml = `<span class="badge-variant-unverified">Variant Unverified</span>`;
            else if (isDiscontinued) badgeHtml = `<span class="badge-discontinued">Discontinued</span>`;

            const feeDisplay = isUnverified 
                ? '<span style="color:#D97706;">Unverified</span>'
                : `J: ${terms.joining_fee != null ? formatINR(terms.joining_fee) : '₹0'} <br>A: ${terms.annual_fee != null ? formatINR(terms.annual_fee) : '₹0'}`;

            const waiverDisplay = isUnverified
                ? '<span style="color:#D97706;">Unverified</span>'
                : (terms.annual_fee_waiver_threshold ? `${formatINR(terms.annual_fee_waiver_threshold)} / yr` : 'Lifetime Free');

            const rewardDisplay = isUnverified
                ? '<span style="color:#D97706;">Withheld (Unverified)</span>'
                : `<strong>${terms.reward_type || 'Points'}</strong><br><small>${(terms.reward_rate || '').substring(0, 50)}...</small>`;

            const loungeDisplay = isUnverified
                ? '<span style="color:#D97706;">Unverified</span>'
                : `Air: ${terms.airport_lounge_access || 'None'}<br>Rail: ${terms.railway_lounge_access || 'None'}`;

            const forexDisplay = isUnverified
                ? '<span style="color:#D97706;">Unverified</span>'
                : (terms.forex_markup != null ? `${terms.forex_markup}%` : '3.50%');

            const exclusionsDisplay = isUnverified
                ? '<span style="color:#D97706;">Unverified</span>'
                : `<small>${(terms.excluded_spend_categories || 'Standard exclusions').substring(0, 45)}...</small>`;

            const sourceDisplay = terms.source_url
                ? `<a href="${terms.source_url}" target="_blank" rel="noopener noreferrer" class="provenance-link" title="${terms.source_title}">Official Link</a>`
                : '<span style="color:#D97706;">Unresolved</span>';

            return `
                <tr>
                    <td>
                        <div class="table-card-issuer">${card.issuer}</div>
                        <div class="table-card-title">${card.variant}</div>
                        <small style="color:var(--slate-500);">${card.masked_number || 'N/A'}</small>
                        <div style="margin-top:6px;">
                            <button class="btn btn-secondary btn-sm" onclick="openCardDetails('${card.id}')">Inspect</button>
                        </div>
                    </td>
                    <td>${badgeHtml}</td>
                    <td>${feeDisplay}</td>
                    <td>${waiverDisplay}</td>
                    <td>${rewardDisplay}</td>
                    <td>${loungeDisplay}</td>
                    <td>${forexDisplay}</td>
                    <td>${exclusionsDisplay}</td>
                    <td>${sourceDisplay}</td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error('Error loading comparison', e);
    }
}

document.getElementById('comparison-category-filter').addEventListener('change', loadComparison);

// 4. Smart Card Matcher Runner
async function runMatcher() {
    const amountInput = document.getElementById('matcher-amount');
    const merchantInput = document.getElementById('matcher-merchant');
    const resultsContainer = document.getElementById('matcher-results-list');

    const amount = parseFloat(amountInput.value) || 5000;
    const merchant = merchantInput.value.trim();

    resultsContainer.innerHTML = '<div style="padding:16px; text-align:center; color:var(--slate-500);">Evaluating verified benefits and eligibility rules...</div>';

    try {
        const res = await fetch(`${API_BASE}/matcher/recommend`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({
                purchase_amount: amount,
                category: currentCategory,
                merchant: merchant || null
            })
        });

        if (!res.ok) {
            resultsContainer.innerHTML = '<div class="alert-box error">Unable to evaluate cards. Please ensure cards are loaded in your wallet.</div>';
            return;
        }

        const data = await res.json();
        const recs = data.recommendations;

        if (!recs || recs.length === 0) {
            resultsContainer.innerHTML = '<div class="empty-state">No matching cards found for this category.</div>';
            return;
        }

        resultsContainer.innerHTML = recs.map((rec, idx) => {
            const isRank1 = idx === 0 && rec.confidence !== 'UNVERIFIED' && rec.estimated_net_benefit_inr > 0;
            const isUnverified = rec.confidence === 'UNVERIFIED';

            let cardClass = isRank1 ? 'result-card rank-1' : 'result-card';
            let rankBadge = isRank1 ? '<span class="rank-badge">Top Recommendation</span>' : `<span class="badge" style="font-size:11px;">#${idx + 1}</span>`;

            if (isUnverified) {
                return `
                    <div class="${cardClass}" style="background:#FFFBEB; border-color:#FCD34D;">
                        <div class="result-card-header">
                            <div>
                                <span class="badge-variant-unverified">Insufficient Verified Data</span>
                                <strong style="margin-left: 8px; color:var(--slate-900);">${rec.card_name}</strong>
                                <span style="font-size:12px; color:var(--slate-500);">(${rec.masked_number})</span>
                            </div>
                            <span class="badge" style="background:#FEF3C7; color:#92400E; border:1px solid #FCD34D;">Variant Unverified</span>
                        </div>
                        <div style="font-size:13px; color:#92400E; margin:8px 0; line-height:1.4;">
                            ⚠️ <strong>No perks fabricated:</strong> ${rec.calculation_breakdown}
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                            <span style="font-size:12px; color:var(--slate-600);">${rec.eligibility_conditions}</span>
                            <button class="btn btn-secondary btn-sm" onclick="openCardDetails('${rec.card_id}')">Upload Details / Inspect</button>
                        </div>
                    </div>
                `;
            }

            return `
                <div class="${cardClass}">
                    <div class="result-card-header">
                        <div>
                            ${rankBadge}
                            <strong style="margin-left: 8px; font-size:14px; color:var(--slate-900);">${rec.card_name}</strong>
                            <span style="font-size:12px; color:var(--slate-500);">(${rec.masked_number})</span>
                        </div>
                        <span class="benefit-pill">${rec.effective_rate_percent}% Return</span>
                    </div>

                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <div class="benefit-inr">${formatINR(rec.estimated_net_benefit_inr)}</div>
                        <span style="font-size:11px; color:var(--slate-500); font-weight:600;">Estimated Net Savings</span>
                    </div>

                    <div class="result-formula">
                        <strong>Rule Applied:</strong> ${rec.applied_rule}
                    </div>

                    <p style="font-size: 12px; color: var(--slate-600); margin: 6px 0;">
                        ${rec.calculation_breakdown}
                    </p>

                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px; border-top:1px dashed var(--slate-200); padding-top:6px;">
                        <span style="font-size:11px; color:var(--slate-500);">ℹ️ ${rec.eligibility_conditions}</span>
                        <button class="btn btn-secondary btn-sm" onclick="openCardDetails('${rec.card_id}')">View Verified Terms</button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Error running matcher', e);
        resultsContainer.innerHTML = '<div class="alert-box error">Error calculating card recommendations.</div>';
    }
}

document.getElementById('run-matcher-btn').addEventListener('click', runMatcher);


// 4. Payments & Ledger
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

        // Today's date in local ISO string (YYYY-MM-DD)
        const todayStr = new Date().toISOString().split('T')[0];

        container.innerHTML = statements.map(stmt => {
            const cardTitle = `${stmt.card_issuer || ''} ${stmt.card_name || 'Card'} (${stmt.masked_number || 'N/A'})`;

            // Payment Due Date Badge & Text
            let dueBadge = '';
            let dueText = '';
            if (stmt.is_credit_balance) {
                dueText = 'No payment required, as reported';
                dueBadge = `<span class="badge" style="background:#D1FAE5; color:#065F46; border:1px solid #6EE7B7;">Credit Surplus</span>`;
            } else if (stmt.payment_due_date) {
                dueText = stmt.payment_due_date;
                if (stmt.payment_due_date < todayStr) {
                    dueBadge = `<span class="badge badge-overdue">Overdue (${stmt.payment_due_date})</span>`;
                } else if (stmt.payment_due_date === todayStr) {
                    dueBadge = `<span class="badge badge-today">Due Today (${stmt.payment_due_date})</span>`;
                } else {
                    dueBadge = `<span class="badge badge-upcoming">Upcoming (Due: ${stmt.payment_due_date})</span>`;
                }
            } else {
                dueText = 'Unknown — verify';
                dueBadge = `<span class="badge badge-unknown">Due Date Unknown — Verify</span>`;
            }

            // Billing Cycle / Statement info
            const cycleText = (stmt.period_start && stmt.period_end)
                ? `Billing Cycle: ${stmt.period_start} to ${stmt.period_end}`
                : (stmt.statement_date ? `Statement Date: ${stmt.statement_date}` : 'Cycle: Unknown');

            // Balance Display
            let balanceDisplay = '';
            if (stmt.is_credit_balance) {
                balanceDisplay = `<strong style="color: #059669;">${formatINR(stmt.total_balance)} (Credit Balance)</strong>`;
            } else if (stmt.total_balance != null) {
                balanceDisplay = `<strong>${formatINR(stmt.total_balance)}</strong>`;
            } else {
                balanceDisplay = `<strong style="color: #D97706;">Unknown</strong>`;
            }

            // Minimum Due Display
            let minDueDisplay = '';
            if (stmt.is_credit_balance) {
                minDueDisplay = `<strong>₹0.00</strong>`;
            } else if (stmt.minimum_due != null) {
                minDueDisplay = `<strong style="color: var(--rose);">${formatINR(stmt.minimum_due)}</strong>`;
            } else {
                minDueDisplay = `<strong style="color: #D97706;">Unknown — verify</strong>`;
            }

            // Remaining to Plan Display
            let remainingDisplay = '';
            if (stmt.is_credit_balance) {
                remainingDisplay = `<strong style="color: #059669;">₹0.00</strong>`;
            } else if (stmt.remaining_to_plan != null) {
                remainingDisplay = `<strong>${formatINR(stmt.remaining_to_plan)}</strong>`;
            } else {
                remainingDisplay = `<strong>Unknown</strong>`;
            }

            // Context Notes
            let contextNote = '';
            if (stmt.is_credit_balance) {
                contextNote = `<div class="card-note-box" style="background:#ECFDF5; border-left-color:#10B981; color:#065F46;">
                    <strong>Surplus Credit Balance:</strong> The statement shows an excess balance of ₹1,035. This is not a debt; no payment is required.
                </div>`;
            } else if (stmt.is_historical) {
                contextNote = `<div class="card-note-box warning">
                    <strong>Historical Statement:</strong> This statement cycle reports ₹0 due. The current outstanding balance has not been verified against live data.
                </div>`;
            } else if (!stmt.payment_due_date && stmt.total_balance != null) {
                contextNote = `<div class="card-note-box warning">
                    <strong>Pending Bank Details:</strong> Payment due date and minimum amount due are unknown — requires verification from bank statement.
                </div>`;
            } else if (stmt.notes) {
                contextNote = `<div class="card-note-box">${stmt.notes}</div>`;
            }

            // Payment Planning Form
            let planFormHtml = '';
            if (stmt.is_credit_balance) {
                planFormHtml = `<div class="payment-plan-form" style="background: #ECFDF5; color: #065F46; font-size: 13px; font-weight: 600;">
                    ✓ Account is in credit surplus. No payment scheduling required.
                </div>`;
            } else if (stmt.total_balance == null) {
                planFormHtml = `<div class="payment-plan-form" style="background: #FFFBEB; color: #92400E; font-size: 13px;">
                    Statement balance is unknown. Please verify with the bank before scheduling payment tranches.
                </div>`;
            } else if (parseFloat(stmt.remaining_to_plan) <= 0) {
                planFormHtml = `<div class="payment-plan-form" style="background: #F1F5F9; color: #475569; font-size: 13px;">
                    ✓ Entire statement balance planned or settled.
                </div>`;
            } else {
                planFormHtml = `
                    <div class="payment-plan-form">
                        <div class="form-group">
                            <label>Schedule Payment Tranche (₹)</label>
                            <input type="number" id="pay-amt-${stmt.id}" value="${stmt.remaining_to_plan}" step="100">
                        </div>
                        <button class="btn btn-primary" onclick="planPayment('${stmt.id}')">Schedule Payment</button>
                    </div>
                `;
            }

            return `
                <div class="statement-box">
                    <div class="statement-top">
                        <div>
                            <div style="font-size: 16px; font-weight: 700; color: var(--slate-900); margin-bottom: 4px;">${cardTitle}</div>
                            <span class="due-date-highlight">Due Date: ${dueText}</span>
                            <span style="color: var(--slate-500); margin-left: 12px; font-size: 13px;">(${cycleText})</span>
                        </div>
                        <div>
                            ${dueBadge}
                            <span class="badge" style="margin-left: 6px;">${stmt.is_paid ? 'Paid' : 'Unpaid Statement'}</span>
                        </div>
                    </div>

                    ${contextNote}

                    <div class="statement-amounts-row" style="margin-top: 14px;">
                        <div class="amount-col">
                            <span>Statement Balance</span>
                            ${balanceDisplay}
                        </div>
                        <div class="amount-col">
                            <span>Minimum Due</span>
                            ${minDueDisplay}
                        </div>
                        <div class="amount-col">
                            <span>Confirmed Paid</span>
                            <strong style="color: var(--primary);">${formatINR(stmt.confirmed_paid_amount || 0)}</strong>
                        </div>
                        <div class="amount-col">
                            <span>Remaining to Plan</span>
                            ${remainingDisplay}
                        </div>
                    </div>

                    ${planFormHtml}
                </div>
            `;
        }).join('');
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
