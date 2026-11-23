<template>
  <MaintenanceLayout :title="__('Plans')">
    <template #actions>
      <Button :label="__('Add service')" @click="showService = true" />
      <Button
        variant="solid"
        iconLeft="lucide-plus"
        :label="__('Add plan')"
        @click="editPlan(null)"
      />
    </template>
    <p class="mb-4 max-w-3xl text-p-base text-ink-gray-5">
      {{
        __(
          'Group your packages by service. When you create a client and pick a plan, its price, hours, deliverables and monthly checks fill in by themselves.',
        )
      }}
    </p>
    <div class="mb-5 flex flex-wrap gap-2">
      <Button
        v-for="s in services"
        :key="s.name"
        size="sm"
        :variant="selected === s.name ? 'subtle' : 'outline'"
        :label="`${s.name} (${count(s.name)})`"
        @click="selected = s.name"
      />
    </div>
    <div class="grid gap-4 md:grid-cols-3">
      <div
        v-for="p in shown"
        :key="p.name"
        class="flex flex-col rounded-lg border p-4"
      >
        <div class="text-xs uppercase text-ink-gray-5">
          {{ __('Tier') }} {{ p.tier_order || '' }}
        </div>
        <div class="text-lg font-semibold text-ink-gray-9">
          {{ p.tier_name }}
        </div>
        <div class="text-2xl font-semibold">
          {{ money(p.monthly_price)
          }}<span class="text-p-sm font-normal text-ink-gray-5"
            >/{{ __('month') }}</span
          >
        </div>
        <div class="text-p-sm text-ink-gray-5">
          {{ __('or') }} {{ money(p.annual_price) }}/{{ __('year') }} ·
          {{ p.hours_per_month }}h {{ __('a month') }}
        </div>
        <ul
          class="my-3 flex-1 list-disc space-y-1 pl-5 text-p-sm text-ink-gray-7"
        >
          <li v-for="(d, i) in p.deliverables" :key="i">{{ d.text }}</li>
        </ul>
        <div class="flex items-center justify-between">
          <span class="text-p-sm text-ink-gray-5"
            >{{ p.clients }} {{ __('active client(s)') }}</span
          >
          <Button size="sm" :label="__('Edit')" @click="editPlan(p)" />
        </div>
      </div>
    </div>
    <div v-if="!shown.length" class="py-10 text-center text-ink-gray-5">
      {{ __('No plans for this service yet.') }}
    </div>
    <p class="mt-6 text-p-sm text-ink-gray-5">
      {{
        __(
          "Need something outside these packages? Tick Custom on the client plan and type that client's own price, hours and deliverables.",
        )
      }}
    </p>

    <FormDialog
      v-model:open="showService"
      :title="__('Add service')"
      :fields="[{ key: 'service_name', label: 'Service name', required: true }]"
      :onSubmit="addService"
    />
    <FormDialog
      v-model:open="showPlan"
      :title="current ? __('Edit plan') : __('Add plan')"
      :fields="planFields"
      :initial="planInitial"
      :onSubmit="savePlan"
    />
  </MaintenanceLayout>
</template>

<script setup>
import FormDialog from '@/components/Maintenance/FormDialog.vue'
import MaintenanceLayout from '@/components/Maintenance/MaintenanceLayout.vue'
import {
  getDoc,
  getList,
  insertDoc,
  loadCurrency,
  money,
  saveDoc,
} from '@/composables/maintenance'
import { Button, usePageMeta } from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'

const services = ref([])
const plans = ref([])
const usage = ref({})
const selected = ref('')
const showService = ref(false)
const showPlan = ref(false)
const current = ref(null)

const load = async () => {
  services.value = await getList('CRM Maintenance Service Type', ['name'])
  selected.value ||= services.value[0]?.name
  const list = await getList('CRM Maintenance Plan', ['name'], {
    order_by: 'tier_order asc',
  })
  plans.value = await Promise.all(
    list.map((p) => getDoc('CRM Maintenance Plan', p.name)),
  )
  const rows = await getList(
    'CRM Maintenance Client Plan',
    ['plan', 'parent'],
    { parent: 'CRM Maintenance Client' },
  )
  const active = new Set(
    (
      await getList('CRM Maintenance Client', ['name'], {
        filters: { status: 'Active' },
      })
    ).map((c) => c.name),
  )
  usage.value = rows
    .filter((r) => active.has(r.parent))
    .reduce((a, r) => ((a[r.plan] = (a[r.plan] || 0) + 1), a), {})
}
onMounted(() => {
  loadCurrency()
  load()
})
const shown = computed(() =>
  plans.value
    .filter((p) => p.service === selected.value)
    .map((p) => ({ ...p, clients: usage.value[p.name] || 0 })),
)
const count = (s) => plans.value.filter((p) => p.service === s).length

const planFields = computed(() => [
  {
    key: 'service',
    label: 'Service',
    type: 'select',
    required: true,
    options: services.value.map((s) => ({ label: s.name, value: s.name })),
  },
  { key: 'tier_name', label: 'Tier name (e.g. Basic)', required: true },
  { key: 'tier_order', label: 'Tier order', type: 'number' },
  { key: 'monthly_price', label: 'Price per month', type: 'number' },
  { key: 'annual_price', label: 'Price per year', type: 'number' },
  { key: 'hours_per_month', label: 'Hours per month', type: 'number' },
  {
    key: 'deliverables',
    label: 'Deliverables (one per line)',
    type: 'textarea',
    rows: 6,
  },
])
const planInitial = computed(() =>
  current.value
    ? {
        ...current.value,
        deliverables: current.value.deliverables.map((d) => d.text).join('\n'),
      }
    : { service: selected.value },
)
const editPlan = (p) => {
  current.value = p
  showPlan.value = true
}
async function savePlan(v) {
  const doc = {
    doctype: 'CRM Maintenance Plan',
    ...(current.value || {}),
    ...v,
    deliverables: v.deliverables
      .split('\n')
      .map((t) => t.trim())
      .filter(Boolean)
      .map((text) => ({ text })),
  }
  await (current.value ? saveDoc(doc) : insertDoc(doc))
  await load()
}
async function addService(v) {
  await insertDoc({ doctype: 'CRM Maintenance Service Type', ...v })
  selected.value = v.service_name
  await load()
}
usePageMeta(() => ({ title: __('Plans') }))
</script>
