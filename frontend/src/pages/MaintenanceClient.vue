<template>
  <MaintenanceLayout
    v-if="c"
    :crumbs="[
      { label: __('Maintenance'), route: { name: 'Maintenance' } },
      { label: __('Clients'), route: { name: 'MaintenanceClients' } },
      { label: c.doc.client_name },
    ]"
  >
    <template #actions>
      <Button :label="__('Log hours')" @click="showHours = true" />
      <Button :label="__('Edit')" @click="openEdit" />
      <Button
        variant="solid"
        :label="__('Open this month\'s report')"
        :loading="creating"
        @click="openReport"
      />
    </template>

    <div class="mb-5">
      <div class="flex items-center gap-2">
        <h2 class="text-xl font-semibold text-ink-gray-9">
          {{ c.doc.client_name }}
        </h2>
        <Badge
          :label="c.doc.status"
          :theme="c.doc.status === 'Active' ? 'green' : 'gray'"
        />
      </div>
      <div class="text-p-base text-ink-gray-5">
        {{ c.row?.agency_name }} · {{ __('PM') }}:
        {{ c.row?.pm_name || __('not assigned') }} ·
        <a
          v-if="c.doc.website"
          class="underline"
          :href="url(c.doc.website)"
          target="_blank"
          >{{ c.doc.website }}</a
        >
      </div>
    </div>

    <div
      class="mb-5 grid grid-cols-2 divide-x rounded-lg border md:grid-cols-4"
    >
      <div class="p-4">
        <div class="text-xs uppercase text-ink-gray-5">
          {{ __('Hours this month') }}
        </div>
        <HoursBar
          class="mt-1"
          :used="c.row?.hours_used || 0"
          :included="c.doc.hours_included"
        />
      </div>
      <div class="p-4">
        <div class="text-xs uppercase text-ink-gray-5">
          {{ __('Next payment') }}
        </div>
        <div class="text-lg font-semibold">
          {{ fmtDate(c.doc.next_payment_due) }}
        </div>
        <div
          class="text-p-sm"
          :class="
            c.row?.payment_state === 'overdue'
              ? 'text-red-600'
              : 'text-ink-gray-5'
          "
        >
          {{ c.row && dueText(c.row) }}
        </div>
      </div>
      <div class="p-4">
        <div class="text-xs uppercase text-ink-gray-5">
          {{ c.doc.plans.length }} {{ __('plan(s)') }} ·
          {{ c.doc.billing_cycle }}
        </div>
        <div class="text-lg font-semibold">
          {{ money(c.doc.price)
          }}<span class="text-p-sm font-normal text-ink-gray-5">{{
            c.doc.billing_cycle === 'Annual' ? '/yr' : '/mo'
          }}</span>
        </div>
      </div>
      <div class="p-4">
        <div class="text-xs uppercase text-ink-gray-5">
          {{ __("This month's score") }}
        </div>
        <div class="text-lg font-semibold" :class="scoreColor(c.row?.score)">
          {{ c.row?.score ?? '–' }}
        </div>
        <div class="text-p-sm text-ink-gray-5">{{ c.row?.report_status }}</div>
      </div>
    </div>

    <div class="grid gap-5 lg:grid-cols-3">
      <div class="space-y-5 lg:col-span-2">
        <section class="rounded-lg border">
          <div class="border-b p-4 font-medium text-ink-gray-9">
            {{ __('Services & deliverables') }}
          </div>
          <div
            v-for="p in c.doc.plans"
            :key="p.name"
            class="border-b p-4 last:border-0"
          >
            <div class="flex justify-between">
              <span class="font-medium"
                >{{ p.service }} · {{ p.tier || p.plan }}</span
              >
              <span class="text-p-sm text-ink-gray-5"
                >{{ money(p.monthly_price) }}/mo ·
                {{ p.hours_per_month }}h</span
              >
            </div>
            <ul
              class="mt-2 list-disc space-y-0.5 pl-5 text-p-sm text-ink-gray-7"
            >
              <li
                v-for="(line, i) in (p.deliverables || '')
                  .split('\n')
                  .filter(Boolean)"
                :key="i"
              >
                {{ line }}
              </li>
            </ul>
          </div>
          <div v-if="!c.doc.plans.length" class="p-4 text-ink-gray-5">
            {{ __('No plans yet. Edit the client to add plans.') }}
          </div>
        </section>

        <section class="rounded-lg border">
          <div class="flex items-center justify-between border-b p-4">
            <div>
              <div class="font-medium text-ink-gray-9">
                {{ __('Payments') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{ c.doc.months_paid }} {{ __('cycle(s) paid in total') }} ·
                {{ money(c.doc.total_received) }} {{ __('received') }}
              </div>
            </div>
            <div class="flex gap-2">
              <Button
                size="sm"
                variant="solid"
                theme="green"
                :label="__('Mark next paid')"
                @click="markPaid"
              />
              <Button
                size="sm"
                :label="__('Record payment')"
                @click="showPay = true"
              />
            </div>
          </div>
          <div
            v-for="p in [...c.doc.payments].reverse()"
            :key="p.name"
            class="flex justify-between border-b px-4 py-2.5 last:border-0"
          >
            <span
              >{{ (p.month || '').slice(0, 7) }}
              <span class="text-p-sm text-ink-gray-5">{{ p.note }}</span></span
            >
            <span>{{ money(p.amount) }} · {{ fmtDate(p.paid_on) }}</span>
          </div>
          <div
            v-if="!c.doc.payments.length"
            class="p-4 text-p-sm text-ink-gray-5"
          >
            {{ __('No payments recorded.') }}
          </div>
        </section>

        <section class="rounded-lg border">
          <div class="border-b p-4 font-medium text-ink-gray-9">
            {{ __('Monthly reports') }}
          </div>
          <div
            v-for="r in c.reports"
            :key="r.name"
            class="flex cursor-pointer items-center justify-between border-b px-4 py-2.5 last:border-0 hover:bg-surface-gray-2"
            @click="
              $router.push({
                name: 'MaintenanceReport',
                params: { reportId: r.name },
              })
            "
          >
            <span>{{ (r.month || '').slice(0, 7) }}</span>
            <span class="flex items-center gap-3"
              ><b :class="scoreColor(r.score)">{{ r.score }}</b
              ><Badge :label="r.status"
            /></span>
          </div>
        </section>
      </div>

      <div class="space-y-5">
        <section class="rounded-lg border p-4 text-p-base">
          <div class="mb-2 font-medium text-ink-gray-9">
            {{ __('Details') }}
          </div>
          <dl class="space-y-1.5">
            <div
              v-for="[k, v] in details"
              :key="k"
              class="flex justify-between gap-3"
            >
              <dt class="text-ink-gray-5">{{ k }}</dt>
              <dd class="text-right">{{ v || '–' }}</dd>
            </div>
          </dl>
        </section>

        <section class="rounded-lg border">
          <div class="flex items-center justify-between border-b p-4">
            <span class="font-medium text-ink-gray-9">{{
              __('Client portal logins')
            }}</span>
            <Button size="sm" :label="__('Add login')" @click="openLogin" />
          </div>
          <div
            v-for="l in c.logins"
            :key="l.name"
            class="border-b px-4 py-2.5 last:border-0"
          >
            <div>{{ l.full_name }}</div>
            <div class="text-p-sm text-ink-gray-5">{{ l.user }}</div>
          </div>
          <div class="p-4 text-p-sm text-ink-gray-5">
            {{ __('Portal') }}:
            <a class="underline" href="/portal" target="_blank">/portal</a>
          </div>
        </section>

        <section class="rounded-lg border">
          <div class="border-b p-4 font-medium text-ink-gray-9">
            {{ __('Support tickets') }}
          </div>
          <div
            v-for="t in c.tickets"
            :key="t.name"
            class="flex justify-between border-b px-4 py-2.5 last:border-0"
          >
            <span>{{ t.subject }}</span><Badge :label="t.status" />
          </div>
          <div v-if="!c.tickets.length" class="p-4 text-p-sm text-ink-gray-5">
            {{ __('No tickets.') }}
          </div>
        </section>

        <section class="rounded-lg border">
          <div class="border-b p-4 font-medium text-ink-gray-9">
            {{ __('Hours by month') }}
          </div>
          <div
            v-for="h in c.hours_by_month"
            :key="h.month"
            class="flex justify-between border-b px-4 py-2 last:border-0"
          >
            <span>{{ h.month.slice(0, 7) }}</span><span>{{
              fmtHours(h.hours)
            }}</span>
          </div>
        </section>
      </div>
    </div>

    <FormDialog
      v-model:open="showEdit"
      :title="__('Edit client')"
      :fields="fields"
      :initial="initial"
      :onSubmit="saveEdit"
    />
    <FormDialog
      v-model:open="showPay"
      :title="__('Record payment')"
      :fields="payFields"
      :initial="{ amount: c.doc.price, paid_on: today }"
      :onSubmit="recordPayment"
    />
    <FormDialog
      v-model:open="showHours"
      :title="__('Log hours')"
      :fields="hourFields"
      :initial="{ date: today, work_type: 'Support' }"
      :onSubmit="logHours"
    />
    <FormDialog
      v-model:open="showLogin"
      :title="__('Add client login')"
      :fields="lfields"
      :initial="{ clients: [clientId], active: true }"
      :onSubmit="addLogin"
    />
  </MaintenanceLayout>
</template>

<script setup>
import FormDialog from '@/components/Maintenance/FormDialog.vue'
import HoursBar from '@/components/Maintenance/HoursBar.vue'
import MaintenanceLayout from '@/components/Maintenance/MaintenanceLayout.vue'
import {
  clientFields,
  clientInitial,
  loadClientChoices,
  toClientDoc,
} from '@/components/Maintenance/clientForm'
import { loginFields, saveLogin } from '@/components/Maintenance/loginForm'
import {
  api,
  dueText,
  fmtDate,
  fmtHours,
  loadCurrency,
  money,
  month,
  saveDoc,
  scoreColor,
} from '@/composables/maintenance'
import { Badge, Button, toast, usePageMeta } from 'frappe-ui'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({ clientId: String })
const router = useRouter()
const c = ref(null)
const fields = ref([])
const lfields = ref([])
const showEdit = ref(false)
const showPay = ref(false)
const showHours = ref(false)
const showLogin = ref(false)
const creating = ref(false)
const today = new Date().toISOString().slice(0, 10)

const load = async () =>
  (c.value = await api('get_client', {
    name: props.clientId,
    month: month.value,
  }))
onMounted(() => {
  loadCurrency()
  load()
})
watch(month, load)

const url = (w) => (/^https?:/.test(w) ? w : 'https://' + w)
const initial = computed(() => (c.value ? clientInitial(c.value.doc) : {}))
const details = computed(() => {
  const d = c.value.doc
  return [
    [__('Started'), fmtDate(d.start_date)],
    [__('Contract end'), fmtDate(d.contract_end)],
    [__('Platform'), d.platform],
    [__('Months active'), d.months_paid],
    [
      __('Hours included'),
      d.hours_included ? d.hours_included + 'h / month' : '',
    ],
    [
      __('Extra hours rate'),
      d.extra_hours_rate ? money(d.extra_hours_rate) : __('Default'),
    ],
    [__('Report sent to'), d.report_to],
    [__('Recipient'), d.contact_email],
  ]
})

const payFields = [
  { key: 'amount', label: 'Amount', type: 'number', required: true },
  { key: 'paid_on', label: 'Paid on', type: 'date' },
  { key: 'note', label: 'Note' },
]
const hourFields = [
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
]

async function openEdit() {
  fields.value = clientFields(await loadClientChoices())
  showEdit.value = true
}
async function saveEdit(v) {
  await saveDoc(toClientDoc(v, c.value.doc))
  await load()
}
async function recordPayment(v) {
  await api('record_payment', {
    client: props.clientId,
    amount: v.amount,
    paid_on: v.paid_on,
    note: v.note,
  })
  await load()
}
async function markPaid() {
  await api('record_payment', { client: props.clientId })
  toast.success(__('Marked paid'))
  load()
}
async function logHours(v) {
  await api('log_hours', {
    client: props.clientId,
    hours: v.hours,
    date: v.date,
    work_type: v.work_type,
    description: v.description,
  })
  await load()
}
async function openLogin() {
  lfields.value = await loginFields(true)
  showLogin.value = true
}
async function addLogin(v) {
  await saveLogin(v)
  await load()
}
async function openReport() {
  creating.value = true
  try {
    const name = await api('create_month_report', {
      client: props.clientId,
      month: month.value,
    })
    router.push({ name: 'MaintenanceReport', params: { reportId: name } })
  } finally {
    creating.value = false
  }
}
usePageMeta(() => ({ title: c.value?.doc.client_name || __('Client') }))
</script>
