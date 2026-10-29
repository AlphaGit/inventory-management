<template>
  <div class="app" :class="{ 'is-collapsed': sidebarCollapsed }">
    <!-- Sidebar: full width on desktop, icon rail on tablet, off-canvas drawer on mobile -->
    <aside
      id="app-sidebar"
      class="sidebar"
      :class="{ open: sidebarOpen }"
    >
      <div class="sidebar-brand">
        <span class="brand-mark" aria-hidden="true">{{ brandInitial }}</span>
        <div class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>
      <nav class="sidebar-nav" :aria-label="t('nav.mainNavigation')">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: isActive(item.to) }"
          :aria-current="isActive(item.to) ? 'page' : null"
          :aria-label="item.label"
          :title="item.label"
        >
          <NavIcon :name="item.icon" />
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
      <!-- Desktop-only toggle (hidden below 1024px, where the layout is already a rail or a drawer) -->
      <div class="sidebar-footer">
        <button
          type="button"
          class="collapse-button"
          aria-controls="app-sidebar"
          :aria-expanded="sidebarCollapsed ? 'false' : 'true'"
          :aria-label="collapseLabel"
          :title="collapseLabel"
          @click="toggleCollapsed"
        >
          <svg class="collapse-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
            <rect x="3" y="4" width="18" height="16" rx="2" />
            <path d="M9 4v16" />
            <path d="M15 10l-2 2 2 2" />
          </svg>
          <span class="nav-label">{{ collapseLabel }}</span>
        </button>
      </div>
    </aside>

    <div
      v-if="sidebarOpen"
      class="sidebar-backdrop"
      aria-hidden="true"
      @click="sidebarOpen = false"
    ></div>

    <div class="main-column">
      <header class="content-header">
        <button
          type="button"
          class="menu-button"
          aria-controls="app-sidebar"
          :aria-expanded="sidebarOpen ? 'true' : 'false'"
          :aria-label="t('nav.toggleMenu')"
          @click="sidebarOpen = !sidebarOpen"
        >
          <NavIcon name="menu" />
        </button>
        <div class="breadcrumb">
          <span class="breadcrumb-root">{{ t('nav.companyName') }}</span>
          <svg class="breadcrumb-sep" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="breadcrumb-current">{{ currentPageLabel }}</span>
        </div>
        <div class="header-actions">
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import NavIcon from './components/NavIcon.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    NavIcon
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const route = useRoute()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Shell UI state: the mobile navigation drawer (presentation only)
    const sidebarOpen = ref(false)

    // Desktop collapsed state (>=1024px only; CSS ignores it on tablet/mobile).
    // localStorage can throw (private mode, blocked storage), so every access is guarded.
    const STORAGE_KEY = 'sidebar-collapsed'
    const readCollapsed = () => {
      try {
        return localStorage.getItem(STORAGE_KEY) === '1'
      } catch (err) {
        return false
      }
    }
    const sidebarCollapsed = ref(readCollapsed())
    const collapseLabel = computed(() =>
      sidebarCollapsed.value ? t('nav.expandSidebar') : t('nav.collapseSidebar')
    )
    const toggleCollapsed = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
      try {
        localStorage.setItem(STORAGE_KEY, sidebarCollapsed.value ? '1' : '0')
      } catch (err) {
        // Storage unavailable: the choice just lasts for this session
      }
    }

    // Same links, order and labels as the old top nav. "Reports" had no
    // translation key in the old nav, so it stays a literal here.
    const navItems = computed(() => [
      { to: '/', icon: 'overview', label: t('nav.overview') },
      { to: '/inventory', icon: 'inventory', label: t('nav.inventory') },
      { to: '/orders', icon: 'orders', label: t('nav.orders') },
      { to: '/spending', icon: 'finance', label: t('nav.finance') },
      { to: '/demand', icon: 'demand', label: t('nav.demandForecast') },
      { to: '/restocking', icon: 'restocking', label: t('nav.restocking') },
      { to: '/reports', icon: 'reports', label: 'Reports' }
    ])

    // Root matches exactly; other items also match nested paths (e.g. /orders/123)
    const isActive = (path) => {
      if (path === '/') return route.path === '/'
      return route.path === path || route.path.startsWith(path + '/')
    }

    // Content header title is the label of the nav item that matches the route
    const currentPageLabel = computed(() => {
      const match = navItems.value.find(item => isActive(item.to))
      return match ? match.label : ''
    })

    const brandInitial = computed(() => t('nav.companyName').charAt(0))

    // Close the drawer after navigating and when Escape is pressed
    watch(() => route.path, () => {
      sidebarOpen.value = false
    })

    const handleKeydown = (event) => {
      if (event.key === 'Escape' && sidebarOpen.value) {
        sidebarOpen.value = false
        return
      }
      // Ctrl/Cmd+B toggles the sidebar, unless the user is typing in a field
      if ((event.ctrlKey || event.metaKey) && !event.altKey && !event.shiftKey && event.key.toLowerCase() === 'b') {
        const el = document.activeElement
        const tag = el ? el.tagName : ''
        if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA' || (el && el.isContentEditable)) return
        event.preventDefault()
        toggleCollapsed()
      }
    }

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(() => {
      loadTasks()
      window.addEventListener('keydown', handleKeydown)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('keydown', handleKeydown)
    })

    return {
      t,
      sidebarOpen,
      sidebarCollapsed,
      collapseLabel,
      toggleCollapsed,
      navItems,
      isActive,
      currentPageLabel,
      brandInitial,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
/* ---------- Design tokens (the app's own slate + blue palette) ---------- */
:root {
  /* Color roles */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-muted: #f1f5f9;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-text: #0f172a;
  --color-text-secondary: #334155;
  --color-text-muted: #64748b;
  --color-text-subtle: #94a3b8;
  --color-accent: #2563eb;
  --color-accent-hover: #1d4ed8;
  --color-accent-strong: #1e40af;
  --color-accent-soft: #eff6ff;
  --color-success: #059669;
  --color-success-soft: #d1fae5;
  --color-info: #2563eb;
  --color-info-soft: #dbeafe;
  --color-warning: #b45309;
  --color-warning-soft: #fef3c7;
  --color-danger: #dc2626;
  --color-danger-soft: #fee2e2;

  /* Chart series colors (kept from the existing charts) */
  --chart-blue: #3b82f6;
  --chart-green: #10b981;
  --chart-amber: #f59e0b;
  --chart-red: #ef4444;

  /* Spacing (4px base) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;

  /* Type scale */
  --text-xs: 12px;
  --text-sm: 13px;
  --text-base: 14px;
  --text-lg: 16px;
  --text-xl: 20px;
  --text-2xl: 24px;
  --text-3xl: 30px;

  /* Radius and elevation */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 12px rgb(0 0 0 / 0.08);
  --shadow-lg: 0 12px 32px rgb(15 23 42 / 0.16);

  /* Layout */
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 64px;
  --header-height: 56px;
  --content-max-width: 1440px;
  /* Horizontal page padding, shared by the header, the filter bar and the content */
  --content-padding-x: var(--space-8);
}

@media (max-width: 1279px) {
  :root {
    --content-padding-x: var(--space-6);
  }
}

@media (max-width: 767px) {
  :root {
    --content-padding-x: var(--space-4);
  }
}

/* ---------- Base ---------- */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  font-size: var(--text-base);
  line-height: 1.5;
  background: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    transition-duration: 0ms !important;
    animation-duration: 0ms !important;
  }
}

/* ---------- Shell ---------- */
.app {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
}

.sidebar {
  grid-column: 1;
  grid-row: 1;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--header-height);
  padding: 0 var(--space-5);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: var(--color-accent);
  color: #ffffff;
  font-size: var(--text-base);
  font-weight: 600;
  flex-shrink: 0;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.25;
}

.brand-name {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-3) 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 36px;
  padding: 0 var(--space-3);
  margin: 0 var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
  transition: background-color 150ms ease, color 150ms ease;
}

.nav-item:hover {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.nav-item.active {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-footer {
  margin-top: auto;
  padding: var(--space-3) 0;
  border-top: 1px solid var(--color-border);
}

/* Hidden by default; only shown at >=1024px (see the desktop media query below) */
.collapse-button {
  display: none;
  align-items: center;
  gap: var(--space-3);
  width: calc(100% - var(--space-3) * 2);
  height: 36px;
  padding: 0 var(--space-3);
  margin: 0 var(--space-3);
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color 150ms ease, color 150ms ease;
}

.collapse-button:hover {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.sidebar-backdrop {
  display: none;
}

.main-column {
  grid-column: 2;
  grid-row: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.content-header {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--header-height);
  padding: 0 var(--content-padding-x);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.menu-button {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  margin-left: calc(var(--space-2) * -1);
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}

.menu-button:hover {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  font-size: var(--text-base);
}

.breadcrumb-root {
  color: var(--color-text-muted);
  white-space: nowrap;
}

.breadcrumb-sep {
  color: var(--color-border-strong);
  flex-shrink: 0;
}

.breadcrumb-current {
  color: var(--color-text);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-left: auto;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-8) var(--content-padding-x);
}

/* Desktop: the collapse toggle is available. The collapsed state reuses the
   tablet rail styles below. It is scoped to >=1024px so the stored preference
   never affects the tablet rail (always collapsed) or the mobile drawer. */
@media (min-width: 1024px) {
  .app {
    transition: grid-template-columns 180ms ease;
  }

  .collapse-button {
    display: flex;
  }

  .app.is-collapsed {
    grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr);
  }

  .app.is-collapsed .sidebar-brand {
    justify-content: center;
    padding: 0;
  }

  .app.is-collapsed .brand-text,
  .app.is-collapsed .nav-label {
    display: none;
  }

  .app.is-collapsed .nav-item,
  .app.is-collapsed .collapse-button {
    justify-content: center;
    padding: 0;
  }

  .app.is-collapsed .collapse-icon {
    transform: scaleX(-1);
  }
}

/* Tablet: icon rail */
@media (min-width: 768px) and (max-width: 1023px) {
  .app {
    grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr);
  }

  .sidebar-brand {
    justify-content: center;
    padding: 0;
  }

  .brand-text,
  .nav-label {
    display: none;
  }

  .nav-item {
    justify-content: center;
    padding: 0;
  }
}

/* Mobile: off-canvas drawer */
@media (max-width: 767px) {
  .app {
    grid-template-columns: minmax(0, 1fr);
  }

  .main-column {
    grid-column: 1;
  }

  .sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 300;
    width: var(--sidebar-width);
    height: 100%;
    transform: translateX(-100%);
    visibility: hidden;
    transition: transform 180ms ease, visibility 180ms ease;
  }

  .sidebar.open {
    transform: none;
    visibility: visible;
    box-shadow: var(--shadow-lg);
  }

  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 250;
    background: rgb(15 23 42 / 0.4);
  }

  .menu-button {
    display: inline-flex;
  }

  .breadcrumb-root,
  .breadcrumb-sep {
    display: none;
  }

  .main-content {
    padding: var(--space-6) var(--content-padding-x);
  }
}

/* ---------- Shared page classes (used by every view) ---------- */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-2xl);
  line-height: 32px;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.02em;
  margin-bottom: var(--space-1);
}

.page-header p {
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-6);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 500;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-3xl);
  line-height: 36px;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.stat-card.warning .stat-value {
  color: var(--color-warning);
}

.stat-card.success .stat-value {
  color: var(--color-success);
}

.stat-card.danger .stat-value {
  color: var(--color-danger);
}

.stat-card.info .stat-value {
  color: var(--color-info);
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-6);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.card-title {
  font-size: var(--text-lg);
  line-height: 24px;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

/* Flush card: the table runs edge to edge; the header keeps the card padding */
.card--flush {
  padding: 0;
  overflow: hidden;
}

.card--flush .card-header {
  margin-bottom: 0;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.card--flush .table-container {
  border: none;
  border-radius: 0;
}

.card--flush th:first-child,
.card--flush td:first-child {
  padding-left: var(--space-6);
}

.card--flush th:last-child,
.card--flush td:last-child {
  padding-right: var(--space-6);
}

@media (max-width: 767px) {
  .card--flush .card-header {
    padding: var(--space-3) var(--space-4);
  }

  .card--flush th:first-child,
  .card--flush td:first-child {
    padding-left: var(--space-4);
  }

  .card--flush th:last-child,
  .card--flush td:last-child {
    padding-right: var(--space-4);
  }
}

/* ---------- Tables ---------- */
.table-container {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

thead {
  background: var(--color-surface-muted);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-weight: 500;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  line-height: 16px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  vertical-align: bottom;
  border-bottom: 1px solid var(--color-border);
}

td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  line-height: 20px;
  font-variant-numeric: tabular-nums;
}

tbody tr:last-child td {
  border-bottom: none;
}

tbody tr {
  transition: background-color 150ms ease;
}

tbody tr:hover {
  background: var(--color-surface-muted);
}

/* Numeric and currency columns */
th.num,
td.num {
  text-align: right;
}

/* ---------- Badges ---------- */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px var(--space-2);
  border-radius: 999px;
  font-size: var(--text-xs);
  line-height: 16px;
  font-weight: 500;
  white-space: nowrap;
}

.badge.success,
.badge.increasing {
  background: var(--color-success-soft);
  color: #065f46;
}

.badge.warning,
.badge.medium {
  background: var(--color-warning-soft);
  color: #92400e;
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--color-danger-soft);
  color: #991b1b;
}

.badge.info,
.badge.low {
  background: var(--color-info-soft);
  color: #1e40af;
}

.badge.stable {
  background: var(--color-surface-muted);
  color: var(--color-text-secondary);
}

/* ---------- States ---------- */
.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}
</style>
