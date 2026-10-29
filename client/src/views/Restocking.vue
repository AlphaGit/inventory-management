<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="filters-note">{{ t('restocking.filtersNote') }}</div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="successOrder" class="banner banner-success">
        <span>{{ t('restocking.orderPlaced', { number: successOrder.order_number, date: formatDate(successOrder.expected_delivery) }) }}</span>
        <router-link to="/orders" class="banner-link">{{ t('restocking.viewInOrders') }}</router-link>
      </div>
      <div v-if="submitError" class="banner banner-error">{{ submitError }}</div>

      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <span class="budget-hint">
            {{ t('restocking.maxBudget', { amount: formatCurrency(maxBudget, currentCurrency) }) }}
            <span v-if="refreshing"> - {{ t('restocking.updating') }}</span>
          </span>
        </div>
        <div class="budget-controls">
          <input
            type="range"
            class="budget-slider"
            min="0"
            :max="maxBudget"
            step="500"
            :value="budget"
            :aria-label="t('restocking.budgetSlider')"
            @input="onBudgetInput($event.target.value)"
          />
          <label class="budget-number">
            <span>$</span>
            <input
              type="number"
              min="0"
              :max="maxBudget"
              step="500"
              :value="budget"
              :aria-label="t('restocking.budgetInput')"
              @input="onBudgetInput($event.target.value)"
            />
          </label>
          <div class="budget-display">{{ formatCurrency(budget, currentCurrency) }}</div>
        </div>
      </div>

      <div class="card card--flush">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ lines.length }})</h3>
          <button type="button" class="btn btn-secondary btn-sm" :disabled="!hasEdits" @click="resetQuantities">
            {{ t('restocking.reset') }}
          </button>
        </div>
        <div v-if="lines.length === 0" class="empty">{{ t('restocking.noLines') }}</div>
        <div v-else class="table-container">
          <table class="lines-table">
            <thead>
              <tr>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.forecast') }}</th>
                <th class="num">{{ t('restocking.table.onHand') }}</th>
                <th class="num">{{ t('restocking.table.need') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="line in lines" :key="line.sku" :class="{ 'row-edited': isEdited(line) }">
                <td>
                  <strong>{{ translateProductName(line.name) }}</strong>
                  <div class="sku">{{ line.sku }}</div>
                </td>
                <td>
                  <span :class="['badge', line.trend]">{{ t(`trends.${line.trend}`) }}</span>
                </td>
                <td class="num">{{ line.forecasted_demand }}</td>
                <td class="num">{{ line.on_hand }}</td>
                <td class="num">{{ line.need }}</td>
                <td class="num">{{ formatCurrencyWithDecimals(line.unit_cost, currentCurrency, 2) }}</td>
                <td class="num">
                  <template v-if="line.lead_time_days !== null && line.lead_time_days !== undefined">
                    {{ t('restocking.days', { count: line.lead_time_days }) }}
                  </template>
                  <template v-else>
                    {{ t('restocking.days', { count: DEFAULT_LEAD_TIME_DAYS }) }}
                    <span class="sku">({{ t('restocking.defaultLeadTime') }})</span>
                  </template>
                </td>
                <td class="num">
                  <input
                    type="number"
                    min="0"
                    step="1"
                    class="qty-input"
                    :value="quantities[line.sku]"
                    :aria-label="`${t('restocking.table.quantity')} ${line.sku}`"
                    @input="onQuantityInput(line.sku, $event)"
                  />
                  <div v-if="isEdited(line)" class="edited-marker">{{ t('restocking.edited') }}</div>
                </td>
                <td class="num"><strong>{{ formatCurrencyWithDecimals(lineTotalCents(line) / 100, currentCurrency, 2) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="summary">
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.summary.budget') }}</span>
            <span class="summary-value">{{ formatCurrency(budget, currentCurrency) }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.summary.orderTotal') }}</span>
            <span :class="['summary-value', { 'over-budget': overBudget }]">{{ formatCurrencyWithDecimals(totalCents / 100, currentCurrency, 2) }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('restocking.summary.remaining') }}</span>
            <span :class="['summary-value', { 'over-budget': overBudget }]">{{ formatSignedCents(remainingCents) }}</span>
          </div>
          <button type="button" class="btn btn-primary" :disabled="!canPlaceOrder" @click="placeOrder">
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>
        <div v-if="overBudget" class="over-budget-warning">
          {{ t('restocking.overBudget', { amount: formatCurrencyWithDecimals(-remainingCents / 100, currentCurrency, 2) }) }}
        </div>
      </div>

      <div v-if="unpriced.length > 0" class="card card--flush">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.needsPricing.title') }} ({{ unpriced.length }})</h3>
        </div>
        <p class="section-note">{{ t('restocking.needsPricing.description') }}</p>
        <div class="table-container">
          <table class="pricing-table">
            <thead>
              <tr>
                <th>{{ t('restocking.table.item') }}</th>
                <th class="num">{{ t('restocking.needsPricing.forecast') }}</th>
                <th class="num">{{ t('restocking.needsPricing.need') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in unpriced" :key="item.sku">
                <td>
                  <strong>{{ translateProductName(item.name) }}</strong>
                  <div class="sku">{{ item.sku }}</div>
                </td>
                <td class="num">{{ item.forecasted_demand }}</td>
                <td class="num">{{ item.need }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const DEBOUNCE_MS = 250
// The server treats a missing lead time as 14 days
const DEFAULT_LEAD_TIME_DAYS = 14

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const loading = ref(true)
    const refreshing = ref(false)
    const error = ref(null)
    const submitting = ref(false)
    const submitError = ref(null)
    const successOrder = ref(null)

    const budget = ref(0)
    const maxBudget = ref(0)
    const lines = ref([])
    const unpriced = ref([])
    const quantities = ref({})

    let debounceTimer = null
    let requestId = 0

    const seedQuantities = () => {
      const seeded = {}
      for (const line of lines.value) seeded[line.sku] = line.recommended_qty
      quantities.value = seeded
    }

    // initialBudget undefined lets the server choose its default
    const loadRecommendations = async (initialBudget) => {
      // Ignore out-of-order responses when the budget changes quickly
      const myRequest = ++requestId
      try {
        refreshing.value = true
        const data = await api.getRestockRecommendations(initialBudget)
        if (myRequest !== requestId) return
        maxBudget.value = data.max_budget
        if (initialBudget === undefined) budget.value = data.budget
        lines.value = data.lines
        unpriced.value = data.unpriced
        // A new recommendation intentionally overwrites any manual edits
        seedQuantities()
        error.value = null
      } catch (err) {
        if (myRequest !== requestId) return
        console.error('Restock load error:', err)
        // Keep the last good data on screen if a refetch fails
        if (loading.value) error.value = t('restocking.loadFailed') + ': ' + err.message
        else submitError.value = t('restocking.loadFailed')
      } finally {
        if (myRequest === requestId) {
          loading.value = false
          refreshing.value = false
        }
      }
    }

    const onBudgetInput = (raw) => {
      let value = Math.floor(Number(raw))
      if (!Number.isFinite(value) || value < 0) value = 0
      if (value > maxBudget.value) value = maxBudget.value
      budget.value = value
      successOrder.value = null
      submitError.value = null
      // Debounce so dragging the slider does not fire a request per tick
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => loadRecommendations(value), DEBOUNCE_MS)
    }

    const onQuantityInput = (sku, event) => {
      let value = Math.floor(Number(event.target.value))
      if (!Number.isFinite(value) || value < 0) value = 0
      quantities.value[sku] = value
      // Write back so the field never shows a fractional or negative value
      if (String(value) !== event.target.value) event.target.value = value
    }

    const isEdited = (line) => quantities.value[line.sku] !== line.recommended_qty

    const hasEdits = computed(() => lines.value.some(isEdited))

    // Money is summed in integer cents to avoid floating point drift
    const toCents = (amount) => Math.round(amount * 100)
    const lineTotalCents = (line) => toCents(line.unit_cost) * (quantities.value[line.sku] || 0)
    const totalCents = computed(() => lines.value.reduce((sum, line) => sum + lineTotalCents(line), 0))
    // Remaining can be negative; put the sign before the currency symbol
    const formatSignedCents = (cents) =>
      (cents < 0 ? '-' : '') + formatCurrencyWithDecimals(Math.abs(cents) / 100, currentCurrency.value, 2)
    const remainingCents = computed(() => toCents(budget.value) - totalCents.value)
    const overBudget = computed(() => remainingCents.value < 0)

    const canPlaceOrder = computed(() =>
      !submitting.value && totalCents.value > 0 && !overBudget.value
    )

    const resetQuantities = () => seedQuantities()

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return '-'
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      submitting.value = true
      submitError.value = null
      successOrder.value = null
      try {
        const orderLines = lines.value
          .filter(line => quantities.value[line.sku] > 0)
          .map(line => ({ sku: line.sku, quantity: quantities.value[line.sku] }))
        successOrder.value = await api.createRestockOrder({ budget: budget.value, lines: orderLines })
        seedQuantities()
      } catch (err) {
        const detail = err.response?.data?.detail
        submitError.value = typeof detail === 'string' ? detail : t('restocking.placeFailed')
      } finally {
        submitting.value = false
      }
    }

    onMounted(() => loadRecommendations())
    onBeforeUnmount(() => clearTimeout(debounceTimer))

    return {
      t,
      currentCurrency,
      translateProductName,
      formatCurrency,
      formatCurrencyWithDecimals,
      DEFAULT_LEAD_TIME_DAYS,
      loading,
      refreshing,
      error,
      submitting,
      submitError,
      successOrder,
      budget,
      maxBudget,
      lines,
      unpriced,
      quantities,
      onBudgetInput,
      onQuantityInput,
      isEdited,
      hasEdits,
      lineTotalCents,
      totalCents,
      remainingCents,
      formatSignedCents,
      overBudget,
      canPlaceOrder,
      resetQuantities,
      placeOrder,
      formatDate
    }
  }
}
</script>

<style scoped>
.filters-note {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-6);
}

.banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-6);
  font-size: var(--text-sm);
  font-weight: 500;
}

.banner-success {
  background: var(--color-success-soft);
  color: #065f46;
  border: 1px solid var(--color-success);
}

.banner-error {
  background: var(--color-danger-soft);
  color: #991b1b;
  border: 1px solid var(--color-danger);
}

.banner-link {
  color: inherit;
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
}

.budget-hint {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.budget-controls {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  flex-wrap: wrap;
}

.budget-slider {
  flex: 1;
  min-width: 160px;
  accent-color: var(--color-accent);
}

.budget-number {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-muted);
}

/* Form controls: 36px high, 1px border, accent ring on focus */
.budget-number input,
.qty-input {
  height: 36px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  padding: 0 var(--space-3);
  font-family: inherit;
  font-size: var(--text-base);
  font-variant-numeric: tabular-nums;
  color: var(--color-text);
  background: var(--color-surface);
  text-align: right;
  transition: border-color 150ms ease, box-shadow 150ms ease;
}

.budget-number input:focus,
.qty-input:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-info-soft);
}

.budget-number input {
  width: 120px;
}

/* Table inputs are one step smaller so rows stay compact */
.qty-input {
  width: 84px;
  height: 32px;
}

.budget-display {
  font-size: var(--text-2xl);
  line-height: 32px;
  font-weight: 600;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
  min-width: 120px;
  text-align: right;
}

.lines-table {
  min-width: 900px;
}

.pricing-table {
  min-width: 360px;
}

.lines-table td strong,
.pricing-table td strong {
  font-weight: 500;
  color: var(--color-text);
}

.sku {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

/* Edited rows keep a warning tint, including on hover */
.row-edited,
.row-edited:hover {
  background: var(--color-warning-soft);
}

.edited-marker {
  color: var(--color-warning);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  margin-top: var(--space-1);
}

.empty,
.section-note {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  padding: var(--space-4) var(--space-6);
}

.section-note {
  border-bottom: 1px solid var(--color-border);
}

/* Buttons: 36px (32px small), 6px radius, visible focus from the global :focus-visible rule */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 0 var(--space-4);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  white-space: nowrap;
  transition: background-color 150ms ease, border-color 150ms ease;
}

.btn-sm {
  height: 32px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-accent);
  color: #ffffff;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-hover);
}

.btn-secondary {
  background: var(--color-surface);
  color: var(--color-text);
  border-color: var(--color-border-strong);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-surface-muted);
}

.summary {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-6) var(--space-8);
  flex-wrap: wrap;
  border-top: 1px solid var(--color-border);
  padding: var(--space-4) var(--space-6);
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.summary-label {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  line-height: 16px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.summary-value {
  font-size: var(--text-xl);
  line-height: 28px;
  font-weight: 600;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.summary-value.over-budget {
  color: var(--color-danger);
}

.over-budget-warning {
  margin: 0 var(--space-6) var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--color-danger-soft);
  border: 1px solid var(--color-danger);
  border-radius: var(--radius-md);
  color: #991b1b;
  font-size: var(--text-sm);
  font-weight: 500;
  text-align: right;
}

@media (max-width: 767px) {
  .budget-display {
    text-align: left;
  }

  /* Stack the totals as label/value rows so wrapped items never misalign */
  .summary {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-2);
    padding: var(--space-4);
  }

  .summary-item {
    flex-direction: row;
    justify-content: space-between;
    align-items: baseline;
  }

  .summary .btn {
    margin-top: var(--space-2);
  }

  .summary .btn {
    width: 100%;
  }

  .over-budget-warning {
    margin: 0 var(--space-4) var(--space-4);
    text-align: left;
  }

  .empty,
  .section-note {
    padding: var(--space-3) var(--space-4);
  }
}
</style>
