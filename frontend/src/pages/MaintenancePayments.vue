<template>
  <MaintenanceLayout :title="__('Payments')">
    <template #actions>
      <Button
        :label="__('Email reminders now')"
        :loading="sending"
        @click="emailNow"
      />
    </template>
    <p class="mb-4 max-w-3xl text-p-base text-ink-gray-5">
      {{
        __(
          "Who has to pay you. Monthly clients show up 7 days before their due date, annual clients 30 days before. Every day at 9:30 a reminder email goes to the admins, the head and each client's project manager. Nothing is ever sent to clients.",
        )
      }}
    </p>
    <div v-if="g" class="space-y-6">
      <div class="grid grid-cols-3 gap-4">
        <div class="rounded-lg border p-4">
          <div class="text-xs uppercase text-ink-gray-5">
            {{ __('Overdue') }}
          </div>
          <div class="text-2xl font-semibold text-red-600">
            {{ g.overdue.length }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ money(total(g.overdue)) }}
          </div>
        </div>
        <div class="rounded-lg border p-4">
          <div class="text-xs uppercase text-ink-gray-5">
            {{ __('Due soon') }}
          </div>
          <div class="text-2xl font-semibold text-amber-600">
            {{ g.due_soon.length }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ money(total(g.due_soon)) }}
          </div>
        </div>
        <div class="rounded-lg border p-4">
          <div class="text-xs uppercase text-ink-gray-5">
            {{ __('Paid up') }}
          </div>
          <div class="text-2xl font-semibold text-green-600">
            {{ g.ok.length }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('no action needed') }}
          </div>
        </div>
      </div>
      <section v-for="grp in groups" v-show="g[grp.key].length" :key="grp.key">
        <h3 class="mb-2 font-medium text-ink-gray-9">{{ grp.title }}</h3>
        <table class="w-full rounded-lg border text-p-base">
          <thead>
            <tr class="border-b text-left text-xs uppercase text-ink-gray-5">
              <th class="p-3">{{ __('Client') }}</th>
              <th>{{ __('Project manager') }}</th>
              <th>{{ __('Billing') }}</th>
              <th>{{ __('Payment due') }}</th>
              <th>{{ __('Status') }}</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in g[grp.key]"
              :key="r.name"
              class="border-b last:border-0"
            >
              <td class="p-3">
                <div class="font-medium text-ink-gray-9">
                  {{ r.client_name }}
                </div>
                <div class="text-p-sm text-ink-gray-5">
                  {{ r.agency_name }} · {{ r.plans.join(', ') }}
                </div>
              </td>
              <td>{{ r.pm_name || __('Not assigned') }}</td>
              <td>{{ r.billing_cycle }} {{ money(r.price) }}</td>
              <td>{{ fmtDate(r.next_payment_due) }}</td>
              <td :class="r.payment_state === 'overdue' ? 'text-red-600' : ''">
                {{ dueText(r) }}
                <div v-if="r.paid_till" class="text-p-sm text-ink-gray-5">
                  {{ __('Paid till') }} {{ r.paid_till.slice(0, 7) }}
                </div>
                <div v-else class="text-p-sm text-ink-gray-5">
                  {{ __('No payments yet') }}
                </div>
              </td>
              <td class="space-x-2 p-3 text-right">
                <Button
                  size="sm"
                  :label="__('Open')"
                  @click="
                    $router.push({
                      name: 'MaintenanceClient',
                      params: { clientId: r.name },
                    })
                  "
                />
                <Button
                  v-if="grp.key !== 'ok'"
                  size="sm"
                  variant="solid"
                  theme="green"
                  :label="__('Mark paid')"
                  @click="markPaid(r)"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </MaintenanceLayout>
</template>

<script setup>
import MaintenanceLayout from '@/components/Maintenance/MaintenanceLayout.vue'
import {
  api,
  dueText,
  fmtDate,
  loadCurrency,
  money,
} from '@/composables/maintenance'
import { Button, toast, usePageMeta } from 'frappe-ui'
import { onMounted, ref } from 'vue'

const g = ref(null)
const sending = ref(false)
const groups = [
  { key: 'overdue', title: __('Overdue') },
  { key: 'due_soon', title: __('Due soon') },
  { key: 'ok', title: __('Upcoming') },
]
const total = (rows) => rows.reduce((a, r) => a + (r.price || 0), 0)
const load = async () => (g.value = await api('get_payments'))
onMounted(() => {
  loadCurrency()
  load()
})
async function markPaid(r) {
  await api('record_payment', { client: r.name })
  toast.success(__('Marked paid'))
  load()
}
async function emailNow() {
  sending.value = true
  try {
    const n = await api('email_reminders_now')
    toast.success(`${__('Reminder email sent for')} ${n} ${__('client(s)')}`)
  } finally {
    sending.value = false
  }
}
usePageMeta(() => ({ title: __('Payments') }))
</script>
