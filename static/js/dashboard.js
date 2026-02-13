const CHART_IDS = {
  revenue: 'revenueChart',
  expenses: 'expensesChart',
  operational: 'operationalChart',
  geographic: 'geographicChart'
};

const KPI_IDS = {
  totalRevenue: 'totalRevenue',
  totalOrders: 'totalOrders',
  totalExpenses: 'totalExpenses',
  netProfit: 'netProfit',
  reconciliationRate: 'reconciliationRate',
  profitMargin: 'profitMargin',
  reconciliationStatus: 'reconciliationStatus',
  lastUpdate: 'lastUpdate',
  criticalInsights: 'criticalInsights'
};

const FILTER_IDS = {
  client: 'clientFilter',
  restaurant: 'restaurantFilter',
  dateFrom: 'dateFrom',
  dateTo: 'dateTo',
  apply: 'applyFilter',
  clear: 'clearFilter'
};

const state = {
  rawData: null,
  dailyRows: [],
  filteredRows: [],
  charts: {},
  listenersBound: false
};

const currencyFormatter = new Intl.NumberFormat('en-GB', {
  style: 'currency',
  currency: 'GBP',
  maximumFractionDigits: 0
});

const compactCurrencyFormatter = new Intl.NumberFormat('en-GB', {
  style: 'currency',
  currency: 'GBP',
  notation: 'compact',
  maximumFractionDigits: 1
});

function getEl(id) {
  return document.getElementById(id);
}

function safeNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function sanitizeDateString(value) {
  if (!value) return '';
  const text = String(value);
  return text.length >= 10 ? text.slice(0, 10) : '';
}

function formatCurrency(value) {
  const amount = safeNumber(value);
  if (Math.abs(amount) >= 1000) {
    return compactCurrencyFormatter.format(amount);
  }
  return currencyFormatter.format(amount);
}

function formatInteger(value) {
  return Math.round(safeNumber(value)).toLocaleString('en-GB');
}

function formatPercent(value) {
  return `${safeNumber(value).toFixed(1)}%`;
}

function setText(id, value) {
  const el = getEl(id);
  if (el) {
    el.textContent = value;
  }
}

async function loadDashboardData() {
  const response = await fetch('/api/data', {
    method: 'GET',
    headers: { Accept: 'application/json' }
  });

  if (!response.ok) {
    throw new Error(`Dashboard API error: ${response.status}`);
  }

  const payload = await response.json();
  if (!payload || typeof payload !== 'object') {
    throw new Error('Invalid API response payload');
  }

  return payload;
}

function normalizeDailyRow(row) {
  return {
    restaurant_id: safeNumber(row?.restaurant_id),
    name: String(row?.name || ''),
    country: String(row?.country || 'Other'),
    date: sanitizeDateString(row?.date),
    client_id: safeNumber(row?.client_id),
    client_name: String(row?.client_name || ''),
    orders: safeNumber(row?.orders),
    revenue: safeNumber(row?.revenue),
    expenses: safeNumber(row?.expenses),
    profit: safeNumber(row?.profit),
    food_payment: safeNumber(row?.food_payment),
    drinks_payment: safeNumber(row?.drinks_payment),
    other_payment: safeNumber(row?.other_payment),
    service_charges: safeNumber(row?.service_charges),
    delivery_charges: safeNumber(row?.delivery_charges),
    bills: safeNumber(row?.bills),
    vendors: safeNumber(row?.vendors),
    wage_advance: safeNumber(row?.wage_advance),
    repairs: safeNumber(row?.repairs),
    sundries: safeNumber(row?.sundries)
  };
}

function getFilters() {
  const clientFilter = getEl(FILTER_IDS.client);
  const restaurantFilter = getEl(FILTER_IDS.restaurant);
  const dateFrom = getEl(FILTER_IDS.dateFrom);
  const dateTo = getEl(FILTER_IDS.dateTo);

  return {
    clientId: clientFilter?.value ? Number(clientFilter.value) : null,
    restaurantId: restaurantFilter?.value ? Number(restaurantFilter.value) : null,
    dateFrom: dateFrom?.value || null,
    dateTo: dateTo?.value || null
  };
}

function computeFilteredRows(rows, filters) {
  const fromDate = filters.dateFrom || null;
  const toDate = filters.dateTo || null;

  return rows.filter((row) => {
    if (filters.clientId !== null && row.client_id !== filters.clientId) {
      return false;
    }

    if (filters.restaurantId !== null && row.restaurant_id !== filters.restaurantId) {
      return false;
    }

    if (fromDate && row.date && row.date < fromDate) {
      return false;
    }

    if (toDate && row.date && row.date > toDate) {
      return false;
    }

    return true;
  });
}

function computeAggregates(rows) {
  const revenueBreakdown = {
    food: 0,
    drinks: 0,
    other: 0,
    service: 0,
    delivery: 0
  };

  const expenseBreakdown = {
    bills: 0,
    vendors: 0,
    wageAdvance: 0,
    repairs: 0,
    sundries: 0
  };

  const restaurantMap = new Map();
  const countryRestaurants = new Map();

  let totalRevenue = 0;
  let totalExpenses = 0;
  let totalOrders = 0;
  let totalProfit = 0;
  let reconciledRows = 0;

  rows.forEach((row) => {
    totalRevenue += row.revenue;
    totalExpenses += row.expenses;
    totalOrders += row.orders;
    totalProfit += row.profit;

    revenueBreakdown.food += row.food_payment;
    revenueBreakdown.drinks += row.drinks_payment;
    revenueBreakdown.other += row.other_payment;
    revenueBreakdown.service += row.service_charges;
    revenueBreakdown.delivery += row.delivery_charges;

    expenseBreakdown.bills += row.bills;
    expenseBreakdown.vendors += row.vendors;
    expenseBreakdown.wageAdvance += row.wage_advance;
    expenseBreakdown.repairs += row.repairs;
    expenseBreakdown.sundries += row.sundries;

    const expectedProfit = row.revenue - row.expenses;
    if (Math.abs(expectedProfit - row.profit) <= 0.01) {
      reconciledRows += 1;
    }

    const restaurantKey = row.restaurant_id;
    const previous = restaurantMap.get(restaurantKey) || {
      restaurant_id: row.restaurant_id,
      name: row.name || `Restaurant ${row.restaurant_id}`,
      orders: 0,
      revenue: 0,
      expenses: 0,
      profit: 0
    };

    previous.orders += row.orders;
    previous.revenue += row.revenue;
    previous.expenses += row.expenses;
    previous.profit += row.profit;
    restaurantMap.set(restaurantKey, previous);

    const countryKey = (row.country || 'Other').toUpperCase();
    const existingSet = countryRestaurants.get(countryKey) || new Set();
    existingSet.add(restaurantKey);
    countryRestaurants.set(countryKey, existingSet);
  });

  const topRestaurants = Array.from(restaurantMap.values())
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 10);

  const ukRestaurants = countryRestaurants.get('UK')?.size || 0;
  const indiaRestaurants = countryRestaurants.get('INDIA')?.size || 0;
  const otherRestaurants = Array.from(countryRestaurants.entries())
    .filter(([country]) => country !== 'UK' && country !== 'INDIA')
    .reduce((sum, [, set]) => sum + set.size, 0);

  const totalRows = rows.length;
  const reconciliationRate = totalRows > 0 ? (reconciledRows / totalRows) * 100 : 0;
  const netProfit = totalProfit;
  const profitMargin = totalRevenue > 0 ? (netProfit / totalRevenue) * 100 : 0;

  return {
    rowsCount: totalRows,
    totalRevenue,
    totalExpenses,
    totalOrders,
    netProfit,
    reconciliationRate,
    profitMargin,
    revenueBreakdown,
    expenseBreakdown,
    topRestaurants,
    geo: {
      uk: ukRestaurants,
      india: indiaRestaurants,
      other: otherRestaurants
    }
  };
}

function updateMetrics(aggregates) {
  setText(KPI_IDS.totalRevenue, formatCurrency(aggregates.totalRevenue));
  setText(KPI_IDS.totalOrders, formatInteger(aggregates.totalOrders));
  setText(KPI_IDS.totalExpenses, formatCurrency(aggregates.totalExpenses));
  setText(KPI_IDS.netProfit, formatCurrency(aggregates.netProfit));
  setText(KPI_IDS.reconciliationRate, formatPercent(aggregates.reconciliationRate));
  setText(KPI_IDS.profitMargin, `${formatPercent(aggregates.profitMargin)} margin`);

  const reconciliationStatus = getEl(KPI_IDS.reconciliationStatus);
  if (reconciliationStatus) {
    if (aggregates.rowsCount === 0) {
      reconciliationStatus.textContent = 'No data for selected filters';
      reconciliationStatus.className = 'metric-change neutral';
    } else if (aggregates.reconciliationRate < 95) {
      reconciliationStatus.textContent = 'Below 95% target';
      reconciliationStatus.className = 'metric-change critical';
    } else {
      reconciliationStatus.textContent = 'Healthy';
      reconciliationStatus.className = 'metric-change positive';
    }
  }
}

function destroyChart(key) {
  if (state.charts[key]) {
    state.charts[key].destroy();
    state.charts[key] = null;
  }
}

function buildChart(key, config) {
  const canvasId = CHART_IDS[key];
  const canvas = getEl(canvasId);
  if (!canvas) {
    return;
  }

  destroyChart(key);
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    return;
  }

  state.charts[key] = new Chart(ctx, config);
}

function updateCharts(aggregates) {
  buildChart('revenue', {
    type: 'doughnut',
    data: {
      labels: ['Food', 'Drinks', 'Other', 'Service', 'Delivery'],
      datasets: [
        {
          data: [
            aggregates.revenueBreakdown.food,
            aggregates.revenueBreakdown.drinks,
            aggregates.revenueBreakdown.other,
            aggregates.revenueBreakdown.service,
            aggregates.revenueBreakdown.delivery
          ],
          backgroundColor: ['#ff6b6b', '#4ecdc4', '#ffe66d', '#1a535c', '#5c7cfa'],
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  });

  buildChart('expenses', {
    type: 'bar',
    data: {
      labels: ['Bills', 'Vendors', 'Wage Advance', 'Repairs', 'Sundries'],
      datasets: [
        {
          label: 'Amount',
          data: [
            aggregates.expenseBreakdown.bills,
            aggregates.expenseBreakdown.vendors,
            aggregates.expenseBreakdown.wageAdvance,
            aggregates.expenseBreakdown.repairs,
            aggregates.expenseBreakdown.sundries
          ],
          backgroundColor: ['#f4a261', '#e76f51', '#2a9d8f', '#e9c46a', '#264653']
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });

  buildChart('operational', {
    type: 'bar',
    data: {
      labels: aggregates.topRestaurants.map((item) => item.name),
      datasets: [
        {
          label: 'Revenue',
          data: aggregates.topRestaurants.map((item) => item.revenue),
          backgroundColor: '#118ab2'
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          beginAtZero: true
        }
      }
    }
  });

  buildChart('geographic', {
    type: 'pie',
    data: {
      labels: ['UK', 'India', 'Other'],
      datasets: [
        {
          data: [aggregates.geo.uk, aggregates.geo.india, aggregates.geo.other],
          backgroundColor: ['#43aa8b', '#f94144', '#577590'],
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  });
}

function updateInsights(aggregates) {
  const insightsEl = getEl(KPI_IDS.criticalInsights);
  if (!insightsEl) {
    return;
  }

  if (aggregates.rowsCount === 0) {
    insightsEl.innerHTML = `
      <div class="insights-empty-state">
        <h3>No insight data yet</h3>
        <p>Try widening date filters or selecting a different client/restaurant.</p>
      </div>
    `;
    return;
  }

  const topRestaurant = aggregates.topRestaurants[0];
  const avgOrderValue = aggregates.totalOrders > 0 ? aggregates.totalRevenue / aggregates.totalOrders : 0;
  const expenseRatio = aggregates.totalRevenue > 0
    ? (aggregates.totalExpenses / aggregates.totalRevenue) * 100
    : 0;
  const topRestaurantShare = topRestaurant && aggregates.totalRevenue > 0
    ? (topRestaurant.revenue / aggregates.totalRevenue) * 100
    : 0;

  const recommendations = [];

  if (aggregates.reconciliationRate < 95) {
    recommendations.push({
      tone: 'warning',
      title: 'Improve reconciliation discipline',
      detail: `Rate is ${formatPercent(aggregates.reconciliationRate)}. Target unresolved cash-up mismatches and enforce day-end checks to get above 95%.`
    });
  } else {
    recommendations.push({
      tone: 'positive',
      title: 'Reconciliation quality is stable',
      detail: `Current rate is ${formatPercent(aggregates.reconciliationRate)}. Keep existing closing controls and weekly exception reviews.`
    });
  }

  if (expenseRatio > 65) {
    recommendations.push({
      tone: 'warning',
      title: 'Expenses are pressuring margins',
      detail: `Expense ratio is ${formatPercent(expenseRatio)}. Audit vendors, repairs, and wage-advance trends for cost containment.`
    });
  } else {
    recommendations.push({
      tone: 'positive',
      title: 'Cost profile is healthy',
      detail: `Expense ratio is ${formatPercent(expenseRatio)}. Maintain procurement discipline and monitor outlier days.`
    });
  }

  if (topRestaurantShare > 35) {
    recommendations.push({
      tone: 'info',
      title: 'Revenue concentration risk',
      detail: `${escapeHtml(topRestaurant?.name || 'Top unit')} contributes ${formatPercent(topRestaurantShare)} of revenue. Lift mid-tier restaurants with focused campaigns.`
    });
  } else {
    recommendations.push({
      tone: 'info',
      title: 'Revenue spread is balanced',
      detail: `Top unit share is ${formatPercent(topRestaurantShare)}. Continue growth experiments across multiple branches.`
    });
  }

  if (aggregates.profitMargin < 20) {
    recommendations.push({
      tone: 'warning',
      title: 'Margin needs intervention',
      detail: `Profit margin is ${formatPercent(aggregates.profitMargin)}. Review menu engineering, promo leakage, and labor scheduling.`
    });
  } else if (aggregates.profitMargin > 40) {
    recommendations.push({
      tone: 'positive',
      title: 'Strong profitability window',
      detail: `Margin is ${formatPercent(aggregates.profitMargin)}. Reinvest part of gains into retention and repeat-order campaigns.`
    });
  } else {
    recommendations.push({
      tone: 'info',
      title: 'Margins are moderate',
      detail: `Margin is ${formatPercent(aggregates.profitMargin)}. Prioritize high-margin items and reduce low-yield discounts.`
    });
  }

  insightsEl.innerHTML = `
    <div class="insights-layout">
      <div class="insights-kpis">
        <article class="insight-kpi-card">
          <p class="insight-kpi-label">Filtered Records</p>
          <p class="insight-kpi-value">${formatInteger(aggregates.rowsCount)}</p>
        </article>
        <article class="insight-kpi-card">
          <p class="insight-kpi-label">Top Restaurant</p>
          <p class="insight-kpi-value insight-kpi-name">${escapeHtml(topRestaurant ? topRestaurant.name : 'N/A')}</p>
          <p class="insight-kpi-sub">${topRestaurant ? formatCurrency(topRestaurant.revenue) : formatCurrency(0)} revenue</p>
        </article>
        <article class="insight-kpi-card">
          <p class="insight-kpi-label">Average Order Value</p>
          <p class="insight-kpi-value">${formatCurrency(avgOrderValue)}</p>
        </article>
        <article class="insight-kpi-card">
          <p class="insight-kpi-label">Profit Margin</p>
          <p class="insight-kpi-value">${formatPercent(aggregates.profitMargin)}</p>
        </article>
      </div>

      <div class="insights-recommendations">
        <h3>Actionable Suggestions</h3>
        <div class="insight-pill-row">
          <span class="insight-pill">Expense Ratio: ${formatPercent(expenseRatio)}</span>
          <span class="insight-pill">Top Revenue Share: ${formatPercent(topRestaurantShare)}</span>
          <span class="insight-pill">Reconciliation: ${formatPercent(aggregates.reconciliationRate)}</span>
        </div>
        ${recommendations
          .map((item) => `
            <article class="suggestion-card ${item.tone}">
              <p class="suggestion-title">${escapeHtml(item.title)}</p>
              <p class="suggestion-detail">${escapeHtml(item.detail)}</p>
            </article>
          `)
          .join('')}
      </div>
    </div>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function sortByName(a, b) {
  return String(a).localeCompare(String(b), 'en', { sensitivity: 'base' });
}

function setSelectOptions(selectEl, options, selectedValue = '') {
  if (!selectEl) {
    return;
  }

  selectEl.innerHTML = '';
  options.forEach((opt) => {
    const optionEl = document.createElement('option');
    optionEl.value = String(opt.value);
    optionEl.textContent = opt.label;
    if (String(opt.value) === String(selectedValue)) {
      optionEl.selected = true;
    }
    selectEl.appendChild(optionEl);
  });
}

function populateRestaurantFilter(selectedClientId = null, selectedRestaurantId = null) {
  const restaurantFilter = getEl(FILTER_IDS.restaurant);
  if (!restaurantFilter) {
    return;
  }

  const restaurants = Array.isArray(state.rawData?.restaurants_list)
    ? state.rawData.restaurants_list
    : [];

  const filteredRestaurants = selectedClientId === null
    ? restaurants
    : restaurants.filter((r) => safeNumber(r?.client_id) === selectedClientId);

  const restaurantOptions = [
    { value: '', label: 'All Restaurants' },
    ...filteredRestaurants
      .map((r) => ({
        value: safeNumber(r?.restaurant_id),
        label: String(r?.name || r?.restaurant_name || `Restaurant ${safeNumber(r?.restaurant_id)}`)
      }))
      .sort((a, b) => sortByName(a.label, b.label))
  ];

  const stillValid = restaurantOptions.some((opt) => String(opt.value) === String(selectedRestaurantId));
  setSelectOptions(restaurantFilter, restaurantOptions, stillValid ? selectedRestaurantId : '');
}

function populateFilters() {
  const clientFilter = getEl(FILTER_IDS.client);
  if (!clientFilter) {
    return;
  }

  const clients = Array.isArray(state.rawData?.clients_list) ? state.rawData.clients_list : [];
  const selectedClientValue = clientFilter.value;

  const clientOptions = [
    { value: '', label: 'All Clients' },
    ...clients
      .map((c) => ({
        value: safeNumber(c?.client_id),
        label: String(c?.client_name || `Client ${safeNumber(c?.client_id)}`)
      }))
      .sort((a, b) => sortByName(a.label, b.label))
  ];

  const selectedClientStillExists = clientOptions.some((opt) => String(opt.value) === String(selectedClientValue));
  const selectedClient = selectedClientStillExists && selectedClientValue !== '' ? Number(selectedClientValue) : null;

  setSelectOptions(clientFilter, clientOptions, selectedClientStillExists ? selectedClientValue : '');

  const restaurantFilter = getEl(FILTER_IDS.restaurant);
  const selectedRestaurantValue = restaurantFilter?.value || '';
  populateRestaurantFilter(selectedClient, selectedRestaurantValue);
}

function getDateBounds() {
  const minDate = state.dailyRows.reduce((min, row) => (min && min < row.date ? min : row.date), '');
  const maxDate = state.dailyRows.reduce((max, row) => (max && max > row.date ? max : row.date), '');
  return { minDate, maxDate };
}

function initializeDateInputs() {
  const fromInput = getEl(FILTER_IDS.dateFrom);
  const toInput = getEl(FILTER_IDS.dateTo);

  if (!fromInput && !toInput) {
    return;
  }

  const { minDate, maxDate } = getDateBounds();

  if (fromInput) {
    if (minDate) {
      fromInput.min = minDate;
      fromInput.max = maxDate || '';
    }
  }

  if (toInput) {
    if (maxDate) {
      toInput.min = minDate || '';
      toInput.max = maxDate;
    }
  }
}

function refreshDashboard() {
  if (!state.rawData) {
    return;
  }

  const filters = getFilters();

  if (
    filters.clientId !== null &&
    filters.restaurantId !== null &&
    Array.isArray(state.rawData?.restaurants_list)
  ) {
    const restaurant = state.rawData.restaurants_list.find(
      (r) => safeNumber(r?.restaurant_id) === filters.restaurantId
    );

    if (restaurant && safeNumber(restaurant.client_id) !== filters.clientId) {
      filters.restaurantId = null;
      const restaurantFilter = getEl(FILTER_IDS.restaurant);
      if (restaurantFilter) {
        restaurantFilter.value = '';
      }
    }
  }

  if (filters.dateFrom && filters.dateTo && filters.dateFrom > filters.dateTo) {
    const temp = filters.dateFrom;
    filters.dateFrom = filters.dateTo;
    filters.dateTo = temp;

    const fromInput = getEl(FILTER_IDS.dateFrom);
    const toInput = getEl(FILTER_IDS.dateTo);
    if (fromInput) fromInput.value = filters.dateFrom;
    if (toInput) toInput.value = filters.dateTo;
  }

  state.filteredRows = computeFilteredRows(state.dailyRows, filters);
  const aggregates = computeAggregates(state.filteredRows);

  updateMetrics(aggregates);
  updateCharts(aggregates);
  updateInsights(aggregates);

  if (state.rawData.last_updated) {
    const dt = new Date(state.rawData.last_updated);
    const lastUpdatedText = Number.isNaN(dt.getTime())
      ? String(state.rawData.last_updated)
      : dt.toLocaleString();
    setText(KPI_IDS.lastUpdate, lastUpdatedText);
  }
}

function clearFilters() {
  const clientFilter = getEl(FILTER_IDS.client);
  const restaurantFilter = getEl(FILTER_IDS.restaurant);
  const dateFrom = getEl(FILTER_IDS.dateFrom);
  const dateTo = getEl(FILTER_IDS.dateTo);

  if (clientFilter) clientFilter.value = '';
  if (restaurantFilter) restaurantFilter.value = '';
  if (dateFrom) dateFrom.value = '';
  if (dateTo) dateTo.value = '';

  populateRestaurantFilter(null, null);
  refreshDashboard();
}

function bindEventListeners() {
  if (state.listenersBound) {
    return;
  }

  const clientFilter = getEl(FILTER_IDS.client);
  const restaurantFilter = getEl(FILTER_IDS.restaurant);
  const dateFrom = getEl(FILTER_IDS.dateFrom);
  const dateTo = getEl(FILTER_IDS.dateTo);
  const applyButton = getEl(FILTER_IDS.apply);
  const clearButton = getEl(FILTER_IDS.clear);

  if (clientFilter) {
    clientFilter.addEventListener('change', () => {
      const clientId = clientFilter.value ? Number(clientFilter.value) : null;
      const restaurantValue = restaurantFilter?.value || null;
      populateRestaurantFilter(clientId, restaurantValue);
      refreshDashboard();
    });
  }

  if (restaurantFilter) {
    restaurantFilter.addEventListener('change', refreshDashboard);
  }

  if (dateFrom) {
    dateFrom.addEventListener('change', refreshDashboard);
  }

  if (dateTo) {
    dateTo.addEventListener('change', refreshDashboard);
  }

  if (applyButton) {
    applyButton.addEventListener('click', refreshDashboard);
  }

  if (clearButton) {
    clearButton.addEventListener('click', clearFilters);
  }

  state.listenersBound = true;
}

function showLoadingState() {
  const loading = getEl('loading');
  const error = getEl('error');
  const content = getEl('dashboard-content');

  if (loading) loading.style.display = 'block';
  if (error) error.style.display = 'none';
  if (content) content.style.display = 'none';
}

function showErrorState(message) {
  const loading = getEl('loading');
  const error = getEl('error');
  const content = getEl('dashboard-content');

  if (loading) loading.style.display = 'none';
  if (content) content.style.display = 'none';

  if (error) {
    error.style.display = 'block';
    if (message) {
      error.textContent = message;
    }
  }
}

function showDashboardState() {
  const loading = getEl('loading');
  const error = getEl('error');
  const content = getEl('dashboard-content');

  if (loading) loading.style.display = 'none';
  if (error) error.style.display = 'none';
  if (content) content.style.display = 'block';
}

async function initializeDashboard() {
  showLoadingState();

  try {
    state.rawData = await loadDashboardData();
    const daily = Array.isArray(state.rawData?.per_restaurant_daily)
      ? state.rawData.per_restaurant_daily
      : [];

    state.dailyRows = daily
      .map(normalizeDailyRow)
      .filter((row) => row.date);

    populateFilters();
    initializeDateInputs();
    bindEventListeners();
    refreshDashboard();
    showDashboardState();
  } catch (error) {
    console.error('Dashboard initialization error:', error);
    showErrorState('Failed to load dashboard data from backend API.');
  }
}

document.addEventListener('DOMContentLoaded', initializeDashboard);

window.populateFilters = populateFilters;
window.refreshDashboard = refreshDashboard;
window.initializeDashboard = initializeDashboard;
window.computeFilteredRows = computeFilteredRows;
window.computeAggregates = computeAggregates;
