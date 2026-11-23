<template>
  <MaintenanceLayout :title="__('Support tickets')">
    <template #actions>
      <Button
        variant="solid"
        iconLeft="lucide-plus"
        :label="__('New ticket')"
        @click="openNew"
      />
    </template>
    <p class="mb-4 max-w-3xl text-p-base text-ink-gray-5">
      {{
        __(
          "Requests your maintenance clients raise from their support portal. New tickets and client replies are emailed to the admins, the head and the client's project manager.",
        )
      }}
    </p>
    <div class="mb-4 grid grid-cols-2 gap-4 md:grid-cols-5">
      <div v-for="k in kpis" :key="k.label" class="rounded-lg border p-3">
        <div class="text-xs uppercase text-ink-gray-5">{{ k.label }}</div>
        <div class="text-xl font-semibold" :class="k.class">{{ k.value }}</div>
      </div>
    </div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <div class="flex gap-1">
        <Button
          v-for="s in tabs"
          :key="s"
          size="sm"
          :variant="tab === s ? 'subtle' : 'ghost'"
          :label="s"
          @click="tab = s"
        />
      </div>
      <div class="w-48">
        <FormControl v-model="pmFilter" type="select" :options="pmOptions" />
      </div>
    </div>
    <table class="w-full text-p-base">
      <thead>
        <tr class="border-b text-left text-xs uppercase text-ink-gray-5">
          <th class="py-2">{{ __('Ticket') }}</th>
          <th>{{ __('Client') }}</th>
          <th>{{ __('Priority') }}</th>
          <th>{{ __('Status') }}</th>
          <th>{{ __('PM') }}</th>
          <th>{{ __('Updated') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="t in shown"
          :key="t.name"
          class="cursor-pointer border-b hover:bg-surface-gray-2"
          @click="open(t)"
        >
          <td class="py-3">
            <div class="font-medium text-ink-gray-9">{{ t.subject }}</div>
            <div class="text-p-sm text-ink-gray-5">
              #{{ t.name }} · {{ t.ticket_type
              }}<span v-if="t.client_replied" class="text-amber-600">
                · {{ __('client replied') }}</span
              >
            </div>
          </td>
          <td>{{ t.client_name }}</td>
          <td>
            <Badge
              :label="t.priority"
              :theme="
                t.priority === 'Urgent'
                  ? 'red'
                  : t.priority === 'High'
                    ? 'orange'
                    : 'gray'
              "
            />
          </td>
          <td>{{ t.status }}</td>
          <td>{{ t.pm_name || '–' }}</td>
          <td>{{ fmtDate(t.modified) }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="!shown.length" class="py-10 text-center text-ink-gray-5">
      {{ __('No tickets here.') }}
    </div>

    <Dialog v-model:open="showDetail" :title="detail?.subject || ''">
      <template #default>
        <div v-if="detail" class="flex flex-col gap-3">
          <div class="text-p-sm text-ink-gray-5">
            #{{ detail.name }} · {{ detail.client }} · {{ detail.priority }}
          </div>
          <div class="whitespace-pre-wrap rounded border p-3 text-p-base">
            {{ detail.description }}
          </div>
          <div
            v-for="(r, i) in detail.replies"
            :key="i"
            class="whitespace-pre-wrap rounded border p-3 text-p-base"
            :class="r.is_client ? 'bg-surface-green-1' : ''"
          >
            <div class="mb-1 text-p-sm text-ink-gray-5">
              {{ r.by_name }} · {{ fmtDate(r.creation) }}
            </div>
            {{ r.message }}
          </div>
          <FormControl
            v-model="reply"
            type="textarea"
            :rows="3"
            :placeholder="__('Write a reply')"
          />
          <div class="flex items-center gap-2">
            <div class="w-48">
              <FormControl
                v-model="newStatus"
                type="select"
                :options="statusOptions"
              />
            </div>
            <Button
              variant="solid"
              :label="__('Send reply')"
              :loading="sending"
              @click="sendReply"
            />
            <Button :label="__('Update status')" @click="setStatus" />
          </div>
        </div>
      </template>
    </Dialog>

    <FormDialog
      v-model:open="showNew"
      :title="__('New ticket')"
      :fields="newFields"
      :onSubmit="createTicket"
    />
  </MaintenanceLayout>
</template>

<script setup>
import FormDialog from '@/components/Maintenance/FormDialog.vue'
import MaintenanceLayout from '@/components/Maintenance/MaintenanceLayout.vue'
import { api, fmtDate, getList, insertDoc } from '@/composables/maintenance'
import { Badge, Button, Dialog, FormControl, usePageMeta } from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'

const rows = ref([])
const tab = ref('Open')
const pmFilter = ref('')
const showDetail = ref(false)
const showNew = ref(false)
const detail = ref(null)
const reply = ref('')
const newStatus = ref('Open')
const sending = ref(false)
const newFields = ref([])
const tabs = ['Open', 'In progress', 'Waiting', 'Resolved', 'All']
const statusOptions = [
  'Open',
  'In progress',
  'Waiting on client',
  'Resolved',
].map((v) => ({ label: v, value: v }))
const map = {
  Open: 'Open',
  'In progress': 'In progress',
  Waiting: 'Waiting on client',
  Resolved: 'Resolved',
}

const load = async () => (rows.value = await api('get_tickets'))
onMounted(load)

const count = (s) => rows.value.filter((r) => r.status === s).length
const kpis = computed(() => [
  { label: __('Open'), value: count('Open') },
  { label: __('In progress'), value: count('In progress') },
  { label: __('Waiting on client'), value: count('Waiting on client') },
  {
    label: __('Urgent / high'),
    value: rows.value.filter(
      (r) => r.status !== 'Resolved' && ['Urgent', 'High'].includes(r.priority),
    ).length,
    class: 'text-red-600',
  },
  { label: __('Resolved'), value: count('Resolved') },
])
const pmOptions = computed(() => [
  { label: __('All project managers'), value: '' },
  ...[
    ...new Map(
      rows.value
        .filter((r) => r.assigned_to)
        .map((r) => [r.assigned_to, r.pm_name]),
    ).entries(),
  ].map(([value, label]) => ({ label, value })),
])
const shown = computed(() =>
  rows.value.filter(
    (r) =>
      (tab.value === 'All' || r.status === map[tab.value]) &&
      (!pmFilter.value || r.assigned_to === pmFilter.value),
  ),
)

async function open(t) {
  detail.value = await api('get_ticket', { name: t.name })
  newStatus.value = detail.value.status
  reply.value = ''
  showDetail.value = true
}
async function sendReply() {
  if (!reply.value.trim()) return
  sending.value = true
  try {
    await api('reply_ticket', {
      ticket: detail.value.name,
      message: reply.value,
      status: newStatus.value,
    })
    await open({ name: detail.value.name })
    load()
  } finally {
    sending.value = false
  }
}
async function setStatus() {
  await api('update_ticket', {
    ticket: detail.value.name,
    status: newStatus.value,
  })
  load()
}
async function openNew() {
  const clients = await getList('CRM Maintenance Client', [
    'name',
    'client_name',
  ])
  newFields.value = [
    {
      key: 'client',
      label: 'Client',
      type: 'select',
      required: true,
      options: clients.map((c) => ({ label: c.client_name, value: c.name })),
    },
    { key: 'subject', label: 'Subject', required: true },
    {
      key: 'ticket_type',
      label: 'Type',
      type: 'select',
      default: 'Other',
      options: [
        'Bug / something broken',
        'Content change',
        'New feature',
        'Question',
        'Other',
      ].map((v) => ({ label: v, value: v })),
    },
    {
      key: 'priority',
      label: 'Priority',
      type: 'select',
      default: 'Normal',
      options: ['Low', 'Normal', 'High', 'Urgent'].map((v) => ({
        label: v,
        value: v,
      })),
    },
    { key: 'description', label: 'Details', type: 'textarea', rows: 4 },
  ]
  showNew.value = true
}
async function createTicket(v) {
  await insertDoc({ doctype: 'CRM Maintenance Ticket', ...v })
  load()
}
usePageMeta(() => ({ title: __('Support tickets') }))
</script>
