<template>
  <MaintenanceLayout :title="__('Agencies')">
    <template #actions>
      <Button
        variant="solid"
        iconLeft="lucide-plus"
        :label="__('Add agency')"
        @click="edit(null)"
      />
    </template>
    <p class="mb-4 text-p-base text-ink-gray-5">
      {{ __('White-label partners who bring you maintenance clients') }}
    </p>
    <div class="grid gap-4 md:grid-cols-2">
      <div
        v-for="a in agencies"
        :key="a.name"
        class="cursor-pointer rounded-lg border p-4 hover:bg-surface-gray-2"
        @click="edit(a)"
      >
        <div class="flex items-start justify-between">
          <div>
            <div class="font-medium text-ink-gray-9">{{ a.agency_name }}</div>
            <div class="text-p-sm text-ink-gray-5">
              {{ a.contact_person }}{{ a.country ? ' · ' + a.country : '' }}
            </div>
          </div>
          <Badge v-if="a.branded" :label="__('Branded')" theme="blue" />
        </div>
        <div class="mt-3 grid grid-cols-2 gap-3">
          <div>
            <div class="text-xs uppercase text-ink-gray-5">
              {{ __('Clients') }}
            </div>
            <div class="text-xl font-semibold">{{ a.clients }}</div>
          </div>
          <div>
            <div class="text-xs uppercase text-ink-gray-5">
              {{ __('Monthly value') }}
            </div>
            <div class="text-xl font-semibold">
              {{ money(a.monthly_value) }}
            </div>
          </div>
        </div>
        <div class="mt-2 text-p-sm text-ink-gray-5">{{ a.email }}</div>
      </div>
    </div>
    <div v-if="!agencies.length" class="py-10 text-center text-ink-gray-5">
      {{ __('No agencies yet.') }}
    </div>
    <FormDialog
      v-model:open="show"
      :title="current ? __('Edit agency') : __('Add agency')"
      :fields="fields"
      :initial="current || {}"
      :onSubmit="save"
    />
  </MaintenanceLayout>
</template>

<script setup>
import FormDialog from '@/components/Maintenance/FormDialog.vue'
import MaintenanceLayout from '@/components/Maintenance/MaintenanceLayout.vue'
import {
  api,
  insertDoc,
  loadCurrency,
  money,
  saveDoc,
} from '@/composables/maintenance'
import { Badge, Button, usePageMeta } from 'frappe-ui'
import { onMounted, ref } from 'vue'

const agencies = ref([])
const show = ref(false)
const current = ref(null)
const fields = [
  { key: 'agency_name', label: 'Agency name', required: true },
  { key: 'contact_person', label: 'Contact person' },
  { key: 'email', label: 'Email', type: 'email' },
  { key: 'country', label: 'Country' },
  {
    key: 'branded',
    label: "Use the agency's name on its clients' reports",
    type: 'checkbox',
  },
]
const load = async () => (agencies.value = await api('get_agencies'))
onMounted(() => {
  loadCurrency()
  load()
})
const edit = (a) => {
  current.value = a ? { ...a, branded: !!a.branded } : null
  show.value = true
}
async function save(v) {
  const doc = {
    doctype: 'CRM Maintenance Agency',
    ...v,
    branded: v.branded ? 1 : 0,
  }
  await (current.value ? saveDoc({ ...current.value, ...doc }) : insertDoc(doc))
  load()
}
usePageMeta(() => ({ title: __('Agencies') }))
</script>
