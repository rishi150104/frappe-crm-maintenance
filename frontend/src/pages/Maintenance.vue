<template>
  <MaintenanceLayout :title="__('Dashboard')">
    <template #actions>
      <MonthSwitch />
      <Button
        variant="solid"
        :label="__('Monthly reports')"
        @click="$router.push({ name: 'MaintenanceReports' })"
      />
    </template>

    <div v-if="d" class="space-y-5">
      <div class="grid grid-cols-2 divide-x rounded-lg border md:grid-cols-5">
        <div v-for="k in kpis" :key="k.label" class="p-4">
          <div class="text-xs uppercase tracking-wide text-ink-gray-5">
            {{ k.label }}
          </div>
          <div
            class="mt-1 text-2xl font-semibold"
            :class="k.class || 'text-ink-gray-9'"
          >
            {{ k.value }}
            <span v-if="k.of" class="text-base font-normal text-ink-gray-4"
              >/ {{ k.of }}</span
            >
          </div>
          <div class="mt-0.5 text-p-sm text-ink-gray-5">{{ k.sub }}</div>
        </div>
      </div>

      <section v-if="d.reminders.length" class="rounded-lg border">
        <div class="border-b p-4">
          <div class="font-medium text-ink-gray-9">
            {{ __('Payment reminders') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Due within 7 days (monthly) or 30 days (annual), or already overdue.',
              )
            }}
          </div>
        </div>
        <div
          v-for="r in d.reminders"
          :key="r.name"
          class="flex items-center justify-between border-b px-4 py-3 last:border-0"
        >
          <div>
            <router-link
              class="font-medium text-ink-gray-9 hover:underline"
              :to="{ name: 'MaintenanceClient', params: { clientId: r.name } }"
              >{{ r.client_name }}</router-link
            >
            <div class="text-p-sm text-ink-gray-5">
              {{ r.agency_name }} · {{ r.billing_cycle }} · PM:
              {{ r.pm_name || __('not assigned') }}
            </div>
          </div>
          <div class="flex items-center gap-4">
            <span class="font-medium">{{ money(r.price) }}</span>
            <span
              :class="
                r.payment_state === 'overdue'
                  ? 'text-red-600'
                  : 'text-amber-600'
              "
              class="text-p-sm"
              >{{ dueText(r) }}</span
            >
            <Button
              size="sm"
              variant="solid"
              theme="green"
              :label="__('Mark paid')"
              @click="markPaid(r)"
            />
          </div>
        </div>
      </section>

      <div class="grid gap-5 lg:grid-cols-3">
        <div class="rounded-lg border p-4 lg:col-span-2">
          <div class="font-medium text-ink-gray-9">
            {{ __('Health score trend') }}
          </div>
          <div class="mb-2 text-p-sm text-ink-gray-5">
            {{ __('Average checklist score, last 6 months') }}
          </div>
          <div class="h-56">
            <LineChart :data="d.trend" x="month" :y="['score']" />
          </div>
        </div>
        <div class="rounded-lg border">
          <div class="border-b p-4 font-medium text-ink-gray-9">
            {{ __('Needs attention') }}
          </div>
          <router-link
            :to="{ name: 'MaintenanceReports' }"
            class="flex justify-between border-b px-4 py-3 hover:bg-surface-gray-2"
          >
            <span
              >{{ d.attention.reports_unsent }}
              {{ __('report(s) not sent yet') }}</span
            ><span>›</span>
          </router-link>
          <router-link
            :to="{ name: 'MaintenancePayments' }"
            class="flex justify-between border-b px-4 py-3 hover:bg-surface-gray-2"
          >
            <span
              >{{ d.attention.payments_due }}
              {{ __('payment(s) due or overdue') }}</span
            ><span>›</span>
          </router-link>
          <router-link
            :to="{ name: 'MaintenanceTickets' }"
            class="flex justify-between px-4 py-3 hover:bg-surface-gray-2"
          >
            <span
              >{{ d.attention.open_tickets }} {{ __('open ticket(s)') }}</span
            ><span>›</span>
          </router-link>
        </div>
      </div>

      <section class="rounded-lg border">
        <div class="flex items-center justify-between border-b p-4">
          <div>
            <div class="font-medium text-ink-gray-9">
              {{ __('Clients this month') }}
            </div>
            <div class="text-p-sm text-ink-gray-5">
              {{ __('Hours, score and report at a glance') }}
            </div>
          </div>
          <router-link
            class="text-p-sm text-ink-gray-7 underline"
            :to="{ name: 'MaintenanceClients' }"
            >{{ __('All clients') }}</router-link
          >
        </div>
        <table class="w-full text-p-base">
          <thead>
            <tr class="text-left text-xs uppercase text-ink-gray-5">
              <th class="px-4 py-2">{{ __('Client') }}</th>
              <th>{{ __('Hours') }}</th>
              <th>{{ __('Score') }}</th>
              <th>{{ __('Report') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="c in d.clients"
              :key="c.name"
              class="cursor-pointer border-t hover:bg-surface-gray-2"
              @click="
                $router.push({
                  name: 'MaintenanceClient',
                  params: { clientId: c.name },
                })
              "
            >
              <td class="px-4 py-2.5">
                <div class="font-medium text-ink-gray-9">
                  {{ c.client_name }}
                </div>
                <div class="text-p-sm text-ink-gray-5">{{ c.agency_name }}</div>
              </td>
              <td class="w-64">
                <HoursBar :used="c.hours_used" :included="c.hours_included" />
              </td>
              <td class="font-semibold" :class="scoreColor(c.score)">
                {{ c.score ?? '–' }}
              </td>
              <td>
                <Badge
                  v-if="c.report_status"
                  :label="c.report_status"
                  :theme="
                    c.report_status === 'Sent'
                      ? 'green'
                      : c.report_status === 'Ready'
                        ? 'blue'
                        : 'gray'
                  "
                />
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <div class="grid gap-5 lg:grid-cols-3">
        <div class="rounded-lg border p-4 lg:col-span-2">
          <div class="font-medium text-ink-gray-9">
            {{ __('Hours logged') }}
          </div>
          <div class="mb-2 text-p-sm text-ink-gray-5">
            {{ __('All clients, last 6 months') }}
          </div>
          <div class="h-56">
            <BarChart :data="d.trend" x="month" :y="['hours']" />
          </div>
        </div>
        <div class="rounded-lg border">
          <div class="flex items-center justify-between border-b p-4">
            <span class="font-medium text-ink-gray-9">{{
              __('Recent work')
            }}</span>
            <router-link
              class="text-p-sm underline"
              :to="{ name: 'MaintenanceHours' }"
              >{{ __('Hours log') }}</router-link
            >
          </div>
          <div
            v-for="(w, i) in d.recent"
            :key="i"
            class="flex justify-between border-b px-4 py-2.5 last:border-0"
          >
            <div>
              <div class="text-ink-gray-9">{{ w.client_name }}</div>
              <div class="text-p-sm text-ink-gray-5">
                {{ w.description }} · {{ fmtDate(w.date) }}
              </div>
            </div>
            <span class="font-medium">{{ fmtHours(w.hours) }}</span>
          </div>
        </div>
      </div>
    </div>
  </MaintenanceLayout>
</template>

<script setup>
import HoursBar from '@/components/Maintenance/HoursBar.vue'
import MaintenanceLayout from '@/components/Maintenance/MaintenanceLayout.vue'
import MonthSwitch from '@/components/Maintenance/MonthSwitch.vue'
import {
  api,
  dueText,
  fmtDate,
  fmtHours,
  loadCurrency,
  money,
  month,
  scoreColor,
} from '@/composables/maintenance'
import { Badge, Button, toast, usePageMeta } from 'frappe-ui'
import { BarChart, LineChart } from 'frappe-ui/charts'
import { computed, onMounted, ref, watch } from 'vue'

const d = ref(null)
const load = async () =>
  (d.value = await api('get_dashboard', { month: month.value }))
onMounted(() => {
  loadCurrency()
  load()
})
watch(month, load)

const kpis = computed(() => {
  const k = d.value.kpis
  return [
    {
      label: __('Active clients'),
      value: k.active,
      sub: `${k.total} ${__('total')}`,
    },
    {
      label: __('Monthly revenue'),
      value: money(k.revenue),
      sub: __('from active plans'),
    },
    {
      label: __('Hours used'),
      value: fmtHours(k.hours_used),
      of: fmtHours(k.hours_included),
      sub: '',
    },
    {
      label: __('Avg health score'),
      value: k.avg_score,
      class: scoreColor(k.avg_score),
      sub: `${k.reports_sent} ${__('of')} ${k.active} ${__('reports sent')}`,
    },
    {
      label: __('Payments due'),
      value: k.payments_due,
      class: k.payments_due ? 'text-red-600' : '',
      sub: __('see Payments'),
    },
  ]
})
async function markPaid(r) {
  await api('record_payment', { client: r.name })
  toast.success(__('Marked paid'))
  load()
}
usePageMeta(() => ({ title: __('Maintenance') }))
</script>
