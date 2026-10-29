<template>
  <div class="filters-bar">
    <div class="filters-container">
      <div class="filters-grid">
        <div class="filter-group">
          <label>{{ t('filters.timePeriod') }}</label>
          <select v-model="selectedPeriod" class="filter-select">
            <option value="all">{{ t('filters.allMonths') }}</option>
            <option value="2025-01">{{ t('months.january') }}</option>
            <option value="2025-02">{{ t('months.february') }}</option>
            <option value="2025-03">{{ t('months.march') }}</option>
            <option value="2025-04">{{ t('months.april') }}</option>
            <option value="2025-05">{{ t('months.may') }}</option>
            <option value="2025-06">{{ t('months.june') }}</option>
            <option value="2025-07">{{ t('months.july') }}</option>
            <option value="2025-08">{{ t('months.august') }}</option>
            <option value="2025-09">{{ t('months.september') }}</option>
            <option value="2025-10">{{ t('months.october') }}</option>
            <option value="2025-11">{{ t('months.november') }}</option>
            <option value="2025-12">{{ t('months.december') }}</option>
          </select>
        </div>

        <div class="filter-group">
          <label>{{ t('filters.location') }}</label>
          <select v-model="selectedLocation" class="filter-select">
            <option value="all">{{ t('filters.all') }}</option>
            <option value="San Francisco">{{ t('warehouses.sanFrancisco') }}</option>
            <option value="London">{{ t('warehouses.london') }}</option>
            <option value="Tokyo">{{ t('warehouses.tokyo') }}</option>
          </select>
        </div>

        <div class="filter-group">
          <label>{{ t('filters.category') }}</label>
          <select v-model="selectedCategory" class="filter-select">
            <option value="all">{{ t('filters.all') }}</option>
            <option value="circuit boards">{{ t('categories.circuitBoards') }}</option>
            <option value="sensors">{{ t('categories.sensors') }}</option>
            <option value="actuators">{{ t('categories.actuators') }}</option>
            <option value="controllers">{{ t('categories.controllers') }}</option>
            <option value="power supplies">{{ t('categories.powerSupplies') }}</option>
          </select>
        </div>

        <div class="filter-group">
          <label>{{ t('filters.orderStatus') }}</label>
          <select v-model="selectedStatus" class="filter-select">
            <option value="all">{{ t('filters.all') }}</option>
            <option value="delivered">{{ t('status.delivered') }}</option>
            <option value="shipped">{{ t('status.shipped') }}</option>
            <option value="processing">{{ t('status.processing') }}</option>
            <option value="backordered">{{ t('status.backordered') }}</option>
          </select>
        </div>
      </div>

      <button
        class="reset-filters-btn"
        @click="resetFilters"
        :disabled="!hasActiveFilters"
        title="Reset all filters"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script>
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'FilterBar',
  setup() {
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      hasActiveFilters,
      resetFilters
    } = useFilters()

    const { t } = useI18n()

    return {
      t,
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      hasActiveFilters,
      resetFilters
    }
  }
}
</script>

<style scoped>
/* Toolbar row under the content header; tokens come from App.vue */
.filters-bar {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  padding: var(--space-2) 0;
  position: sticky;
  top: var(--header-height);
  z-index: 90;
}

.filters-container {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: 0 var(--content-padding-x);
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.filters-grid {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2) var(--space-5);
  flex: 1;
  min-width: 0;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.filter-group label {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.filter-select {
  height: 32px;
  padding: 0 var(--space-8) 0 var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text);
  /* Native arrow replaced by an inline chevron so all selects look the same */
  appearance: none;
  -webkit-appearance: none;
  background: var(--color-surface) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Cpath d='M4 6l4 4 4-4' stroke='%2364748b' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") no-repeat right var(--space-2) center;
  cursor: pointer;
  transition: border-color 150ms ease, box-shadow 150ms ease;
  min-width: 140px;
}

.filter-select:hover {
  border-color: var(--color-border-strong);
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgb(37 99 235 / 0.15);
}

.reset-filters-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background-color 150ms ease, color 150ms ease;
  flex-shrink: 0;
}

.reset-filters-btn:hover:not(:disabled) {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.reset-filters-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.reset-filters-btn svg {
  width: 16px;
  height: 16px;
}

/* Mobile: two-column grid with labels above, and not sticky (saves vertical space) */
@media (max-width: 767px) {
  .filters-bar {
    position: static;
    padding: var(--space-3) 0;
  }

  .filters-container {
    align-items: flex-end;
  }

  .filters-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--space-3);
  }

  .filter-group {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-1);
  }

  .filter-select {
    width: 100%;
    min-width: 0;
  }
}
</style>
