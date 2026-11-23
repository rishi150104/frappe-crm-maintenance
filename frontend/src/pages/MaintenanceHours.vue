<template>
  <MaintenanceLayout :title="__('Hours log')">
    <template #actions>
      <div class="w-48">
        <FormControl
          v-model="clientFilter"
          type="select"
          :options="clientOptions"
        />
      </div>
      <MonthSwitch />
      <Button
        variant="solid"
        iconLeft="lucide-plus"
        :label="__('Log hours')"
        @click="show = true"
      />
    </template>
    <p class="mb-4 text-p-base text-ink-gray-5">
      {{ __('Time spent on each client, against the hours in their plan') }}
    </p>
    <div v-if="d" class="grid gap-5 lg:grid-cols-3">
      <section class="rounded-lg border">
        <div class="border-b p-4">
          <div class="font-medium text-ink-gray-9">
            {{ __('Usage by client') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ fmtHours(total) }} {{ __('logged this month') }}
          </div>
        </div>
        <div
          v-for="u in d.usage"
          :key="u.name"
          class="border-b px-4 py-3 last:border-0"
        >
          <div class="mb-1 text-ink-gray-9">{{ u.client_name }}</div>
          <HoursBar :used="u.hours_used" :included="u.hours_included" />
          <div
            class="mt-0.5 text-p-sm"
            :class="
              u.hours_used > u.hours_included
                ? 'text-red-600'
                : 'text-ink-gray-5'
            "
          >
            {{
              u.hours_used > u.hours_included
                ? fmtHours(u.hours_used - u.hours_included) +
                  ' ' +
                  __('over plan')
                : fmtHours(u.hours_included - u.hours_used) + ' ' + __('left')
            }}
          </div>
        </div>
      </section>
      <section class="rounded-lg border lg:col-span-2">
        <div class="border-b p-4 font-medium text-ink-gray-9">
          {{ __('Entries') }} · {{ d.entries.length }}
        </div>
        <table class="w-full text-p-base">
          <thead>
            <tr class="text-left text-xs uppercase text-ink-gray-5">
              <th class="px-4 py-2">{{ __('Date') }}</th>
              <th>{{ __('Client') }}</th>
              <th>{{ __('Work') }}</th>
              <th>{{ __('By') }}</th>
              <th class="pr-4 text-right">{{ __('Hours') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in d.entries" :key="e.name" class="border-t">
              <td class="px-4 py-2.5">{{ fmtDate(e.date) }}</td>
              <td>{{ e.client_name }}</td>
              <td>
                <span class="text-ink-gray-5">{{ e.work_type }}</span>
                {{ e.description }}
              </td>
              <td>{{ e.logged_by }}</td>
              <td class="pr-4 text-right font-medium">
                {{ fmtHours(e.hours) }}
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="!d.entries.length" class="p-6 text-center text-ink-gray-5">
          {{ __('No hours logged this month.') }}
        </div>
      </section>
    </div>
    <FormDialog
      v-model:open="show"
      :title="__('Log hours')"
      :fields="fields"
      :initial="{ date: today, work_type: 'Support', client: clientFilter }"
      :onSubmit="save"
    />
  </MaintenanceLayout>
</template>

<script setup>
import FormDialog from '@/components/Maintenance/FormDialog.vue'
import HoursBar from '@/components/Maintenance/HoursBar.vue'
import MaintenanceLayout from '@/components/Maintenance/MaintenanceLayout.vue'
import MonthSwitch from '@/components/Maintenance/MonthSwitch.vue'
import { api, fmtDate, fmtHours, month } from '@/composables/maintenance'
import { Button, FormControl, usePageMeta } from 'frappe-ui'
import { computed, onMounted, ref, watch } from 'vue'

const d = ref(null)
const clientFilter = ref('')
const show = ref(false)
const today = new Date().toISOString().slice(0, 10)
const load = async () =>
  (d.value = await api('get_hours', {
    month: month.value,
    client: clientFilter.value,
  }))
onMounted(load)
watch([month, clientFilter], load)

const total = computed(() =>
  d.value.usage.reduce((a, u) => a + u.hours_used, 0),
)
const clientOptions = computed(() => [
  { label: __('All clients'), value: '' },
  ...(d.value?.usage || []).map((u) => ({
    label: u.client_name,
    value: u.name,
  })),
])
const fields = computed(() => [
  {
    key: 'client',
    label: 'Client',
    type: 'select',
    required: true,
    options: clientOptions.value.filter((o) => o.value),
  },
  { key: 'hours', label: 'Hours (e.g. 1.5)', type: 'number', required: true },
  { key: 'date', label: 'Date', type: 'date', required: true },
  {
    key: 'work_type',
    label: 'Type',
    type: 'select',
    options: [
      'Support',
      'Updates',
      'Bug fix',
      'Development',
      'SEO',
      'Other',
    ].map((v) => ({ label: v, value: v })),
  },
  { key: 'description', label: 'What was done', type: 'textarea', rows: 2 },
])
async function save(v) {
  await api('log_hours', v)
  await load()
}
usePageMeta(() => ({ title: __('Hours log') }))
</script>
