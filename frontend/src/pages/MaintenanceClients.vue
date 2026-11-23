<template>
  <MaintenanceLayout :title="__('Clients')">
    <template #actions>
      <Button
        variant="solid"
        iconLeft="lucide-plus"
        :label="__('Add client')"
        @click="openAdd"
      />
    </template>

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <div class="w-48">
        <FormControl v-model="pmFilter" type="select" :options="pmOptions" />
      </div>
      <div class="w-56">
        <FormControl
          v-model="planFilter"
          type="select"
          :options="planOptions"
        />
      </div>
      <div class="flex gap-1">
        <Button
          v-for="s in ['Active', 'Paused', 'Ended', 'All']"
          :key="s"
          size="sm"
          :variant="statusFilter === s ? 'subtle' : 'ghost'"
          :label="s"
          @click="statusFilter = s"
        />
      </div>
    </div>

    <table class="w-full text-p-base">
      <thead>
        <tr class="border-b text-left text-xs uppercase text-ink-gray-5">
          <th class="py-2">{{ __('Client') }}</th>
          <th>{{ __('Plan') }}</th>
          <th>{{ __('Project manager') }}</th>
          <th>{{ __('Hours') }} ({{ monthLabel }})</th>
          <th>{{ __('Next payment') }}</th>
          <th>{{ __('Score') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="c in filtered"
          :key="c.name"
          class="cursor-pointer border-b hover:bg-surface-gray-2"
          @click="
            $router.push({
              name: 'MaintenanceClient',
              params: { clientId: c.name },
            })
          "
        >
          <td class="py-3">
            <div class="font-medium text-ink-gray-9">{{ c.client_name }}</div>
            <div class="text-p-sm text-ink-gray-5">
              {{ c.agency_name }} · {{ c.website }}
            </div>
          </td>
          <td>
            <div v-for="p in c.plans" :key="p" class="text-p-sm">{{ p }}</div>
            <div class="text-p-sm text-ink-gray-5">
              {{ money(c.price)
              }}{{ c.billing_cycle === 'Annual' ? '/yr' : '/mo' }}
            </div>
          </td>
          <td>{{ c.pm_name || __('Not assigned') }}</td>
          <td class="w-44">
            <HoursBar :used="c.hours_used" :included="c.hours_included" />
          </td>
          <td>
            <div>{{ fmtDate(c.next_payment_due) }}</div>
            <div
              class="text-p-sm"
              :class="
                c.payment_state === 'overdue'
                  ? 'text-red-600'
                  : 'text-ink-gray-5'
              "
            >
              {{ dueText(c) }}
            </div>
          </td>
          <td class="font-semibold" :class="scoreColor(c.score)">
            {{ c.score ?? '–' }}
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!filtered.length" class="py-10 text-center text-ink-gray-5">
      {{ __('No clients match.') }}
    </div>

    <FormDialog
      v-model:open="showAdd"
      :title="__('Add client')"
      :fields="fields"
      :initial="{ start_date: today }"
      :onSubmit="create"
    />
  </MaintenanceLayout>
</template>

<script setup>
import FormDialog from '@/components/Maintenance/FormDialog.vue'
import HoursBar from '@/components/Maintenance/HoursBar.vue'
import MaintenanceLayout from '@/components/Maintenance/MaintenanceLayout.vue'
import {
  clientFields,
  loadClientChoices,
  toClientDoc,
} from '@/components/Maintenance/clientForm'
import {
  api,
  dueText,
  fmtDate,
  insertDoc,
  loadCurrency,
  money,
  month,
  monthLabel,
  scoreColor,
} from '@/composables/maintenance'
import { Button, FormControl, usePageMeta } from 'frappe-ui'
import { computed, onMounted, ref, watch } from 'vue'

const rows = ref([])
const pmFilter = ref('')
const planFilter = ref('')
const statusFilter = ref('Active')
const showAdd = ref(false)
const fields = ref([])
const today = new Date().toISOString().slice(0, 10)

const load = async () =>
  (rows.value = await api('get_clients', { month: month.value }))
onMounted(() => {
  loadCurrency()
  load()
})
watch(month, load)

const pmOptions = computed(() => [
  { label: __('All project managers'), value: '' },
  { label: __('Not assigned'), value: '__none' },
  ...[
    ...new Map(
      rows.value
        .filter((r) => r.project_manager)
        .map((r) => [r.project_manager, r.pm_name]),
    ).entries(),
  ].map(([value, label]) => ({ label, value })),
])
const planOptions = computed(() => [
  { label: __('All plans'), value: '' },
  ...[...new Set(rows.value.flatMap((r) => r.plans))].map((p) => ({
    label: p,
    value: p,
  })),
])
const filtered = computed(() =>
  rows.value.filter(
    (r) =>
      (statusFilter.value === 'All' || r.status === statusFilter.value) &&
      (!pmFilter.value ||
        (pmFilter.value === '__none'
          ? !r.project_manager
          : r.project_manager === pmFilter.value)) &&
      (!planFilter.value || r.plans.includes(planFilter.value)),
  ),
)

async function openAdd() {
  fields.value = clientFields(await loadClientChoices())
  showAdd.value = true
}
async function create(values) {
  await insertDoc(toClientDoc(values))
  load()
}
usePageMeta(() => ({ title: __('Clients') }))
</script>
