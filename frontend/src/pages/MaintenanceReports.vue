<template>
  <MaintenanceLayout :title="__('Monthly reports')">
    <template #actions><MonthSwitch /></template>
    <p class="mb-4 text-p-base text-ink-gray-5">
      {{ __('Tick the checklist for each website, then send the PDF report.') }}
      {{ sent }} {{ __('of') }} {{ rows.length }} {{ __('sent for') }}
      {{ monthLabel }}.
    </p>
    <div class="rounded-lg border">
      <div
        v-for="r in rows"
        :key="r.name"
        class="flex cursor-pointer items-center justify-between gap-4 border-b px-4 py-3 last:border-0 hover:bg-surface-gray-2"
        @click="
          $router.push({
            name: 'MaintenanceReport',
            params: { reportId: r.report },
          })
        "
      >
        <div class="flex items-center gap-4">
          <div
            class="w-10 text-center text-xl font-semibold"
            :class="scoreColor(r.score)"
          >
            {{ r.score }}
          </div>
          <div>
            <div class="font-medium text-ink-gray-9">{{ r.client_name }}</div>
            <div class="text-p-sm text-ink-gray-5">
              {{ r.agency_name }} · {{ r.website }}
            </div>
          </div>
        </div>
        <div class="flex items-center gap-3 text-p-sm">
          <span v-if="r.unchecked" class="text-ink-gray-5"
            >{{ r.unchecked }} {{ __('unchecked') }}</span
          >
          <span v-if="r.issues" class="text-red-600"
            >{{ r.issues }}
            {{ r.issues === 1 ? __('issue') : __('issues') }}</span
          >
          <Badge
            :label="r.report_status"
            :theme="
              r.report_status === 'Sent'
                ? 'green'
                : r.report_status === 'Ready'
                  ? 'blue'
                  : 'gray'
            "
          />
          <Button size="sm" :label="__('Open')" />
        </div>
      </div>
      <div v-if="!rows.length" class="p-8 text-center text-ink-gray-5">
        {{ __('No active clients.') }}
      </div>
    </div>
  </MaintenanceLayout>
</template>

<script setup>
import MaintenanceLayout from '@/components/Maintenance/MaintenanceLayout.vue'
import MonthSwitch from '@/components/Maintenance/MonthSwitch.vue'
import { api, month, monthLabel, scoreColor } from '@/composables/maintenance'
import { Badge, Button, usePageMeta } from 'frappe-ui'
import { computed, onMounted, ref, watch } from 'vue'

const rows = ref([])
const sent = computed(
  () => rows.value.filter((r) => r.report_status === 'Sent').length,
)
const load = async () =>
  (rows.value = await api('get_reports', { month: month.value }))
onMounted(load)
watch(month, load)
usePageMeta(() => ({ title: __('Monthly reports') }))
</script>
