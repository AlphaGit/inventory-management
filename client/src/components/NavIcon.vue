<template>
  <svg
    class="nav-icon"
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <!-- Overview: 2x2 grid -->
    <template v-if="name === 'overview'">
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </template>
    <!-- Inventory: box -->
    <template v-else-if="name === 'inventory'">
      <path d="M21 8l-9-5-9 5 9 5 9-5z" />
      <path d="M3 8v8l9 5 9-5V8" />
      <path d="M12 13v8" />
    </template>
    <!-- Orders: receipt -->
    <template v-else-if="name === 'orders'">
      <path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3z" />
      <path d="M9 8h6" />
      <path d="M9 12h6" />
    </template>
    <!-- Finance: wallet -->
    <template v-else-if="name === 'finance'">
      <rect x="3" y="6" width="18" height="14" rx="2" />
      <path d="M3 10h18" />
      <path d="M16 15h2" />
      <path d="M6 6V5a2 2 0 012-2h9" />
    </template>
    <!-- Demand forecast: trending-up line -->
    <template v-else-if="name === 'demand'">
      <path d="M3 17l6-6 4 4 8-8" />
      <path d="M15 7h6v6" />
    </template>
    <!-- Restocking: refresh-cw (two circular arrows) -->
    <template v-else-if="name === 'restocking'">
      <path d="M21 12a9 9 0 00-15.5-6.2L3 8" />
      <path d="M3 3v5h5" />
      <path d="M3 12a9 9 0 0015.5 6.2L21 16" />
      <path d="M21 21v-5h-5" />
    </template>
    <!-- Reports: bar chart -->
    <template v-else-if="name === 'reports'">
      <path d="M4 20V10" />
      <path d="M10 20V4" />
      <path d="M16 20v-7" />
      <path d="M22 20H2" />
    </template>
    <!-- Menu: three lines (drawer toggle) -->
    <template v-else-if="name === 'menu'">
      <path d="M4 6h16" />
      <path d="M4 12h16" />
      <path d="M4 18h16" />
    </template>
  </svg>
</template>

<script setup>
defineProps({
  name: {
    type: String,
    required: true
  }
})
</script>

<style scoped>
.nav-icon {
  flex-shrink: 0;
}
</style>
