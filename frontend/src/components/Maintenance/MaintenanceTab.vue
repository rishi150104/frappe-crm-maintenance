<template>
  <div class="p-5">
    <div
      v-for="c in clients.data"
      :key="c.name"
      class="flex cursor-pointer justify-between border-b py-2 hover:bg-surface-gray-2"
      @click="
        $router.push({
          name: 'MaintenanceClient',
          params: { clientId: c.name },
        })
      "
    >
      <span class="text-ink-gray-9">{{ c.plan_name || c.name }}</span>
      <Badge
        :label="c.status"
        :theme="c.status === 'Active' ? 'green' : 'gray'"
      />
    </div>
    <div v-if="clients.data && !clients.data.length" class="text-ink-gray-5">
      {{ __('No maintenance plan for this organization.') }}
      <a
        class="underline"
        :href="`/app/crm-maintenance-client/new?organization=${encodeURIComponent(organization)}`"
        target="_blank"
        >{{ __('Create one') }}</a
      >
    </div>
  </div>
</template>

<script setup>
import { Badge, createListResource } from 'frappe-ui'

const props = defineProps({ organization: String })
const clients = createListResource({
  doctype: 'CRM Maintenance Client',
  fields: ['name', 'plan_name', 'status'],
  filters: { organization: props.organization },
  auto: true,
})
</script>
