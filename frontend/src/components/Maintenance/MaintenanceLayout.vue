<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="crumbs" />
    </template>
    <template #right-header>
      <slot name="actions" />
    </template>
  </LayoutHeader>
  <div class="flex h-full min-h-0 flex-col overflow-auto">
    <nav class="flex shrink-0 gap-5 overflow-x-auto border-b px-5">
      <router-link
        v-for="l in links"
        :key="l.name"
        :to="{ name: l.name }"
        class="flex items-center gap-1.5 whitespace-nowrap py-2.5 text-p-base text-ink-gray-5 hover:text-ink-gray-9"
        active-class="!text-ink-gray-9 border-b-2 border-ink-gray-9 -mb-px"
      >
        {{ __(l.label) }}
        <Badge
          v-if="l.count"
          :label="String(l.count)"
          :theme="l.theme || 'red'"
          size="sm"
        />
      </router-link>
    </nav>
    <div class="p-5"><slot /></div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { api } from '@/composables/maintenance'
import { Badge, Breadcrumbs } from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'

const props = defineProps({ title: String, crumbs: Array })
const counts = ref({})
onMounted(async () => {
  try {
    counts.value = await api('get_counts')
  } catch (e) {
    // badges are optional
  }
})
const crumbs = computed(
  () =>
    props.crumbs || [
      { label: __('Maintenance'), route: { name: 'Maintenance' } },
      { label: props.title },
    ],
)
const links = computed(() => [
  { name: 'Maintenance', label: 'Dashboard' },
  { name: 'MaintenanceClients', label: 'Clients' },
  { name: 'MaintenanceAgencies', label: 'Agencies' },
  {
    name: 'MaintenancePayments',
    label: 'Payments',
    count: counts.value.payments_due,
  },
  {
    name: 'MaintenanceTickets',
    label: 'Support tickets',
    count: counts.value.open_tickets,
    theme: 'orange',
  },
  { name: 'MaintenanceLogins', label: 'Client logins' },
  { name: 'MaintenanceReports', label: 'Monthly reports' },
  { name: 'MaintenanceHours', label: 'Hours log' },
  { name: 'MaintenancePlans', label: 'Plans' },
  { name: 'MaintenanceSettings', label: 'Settings' },
])
</script>
