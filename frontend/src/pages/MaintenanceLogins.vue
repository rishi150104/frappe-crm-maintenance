<template>
  <MaintenanceLayout :title="__('Client logins')">
    <template #actions>
      <Button
        variant="solid"
        iconLeft="lucide-plus"
        :label="__('Add client login')"
        @click="edit(null)"
      />
    </template>
    <p class="mb-4 max-w-3xl text-p-base text-ink-gray-5">
      {{
        __(
          "Logins for your clients' support portal, where they raise tickets and see their reports. These are separate from your team users and can only see their own projects.",
        )
      }}
      <a class="underline" href="/portal" target="_blank">/portal</a>
    </p>
    <table class="w-full text-p-base">
      <thead>
        <tr class="border-b text-left text-xs uppercase text-ink-gray-5">
          <th class="py-2">{{ __('Client user') }}</th>
          <th>{{ __('Email (username)') }}</th>
          <th>{{ __('Projects') }}</th>
          <th>{{ __('Last login') }}</th>
          <th>{{ __('Status') }}</th>
          <th />
        </tr>
      </thead>
      <tbody>
        <tr v-for="l in logins" :key="l.name" class="border-b">
          <td class="py-3">
            <div class="font-medium text-ink-gray-9">{{ l.full_name }}</div>
            <div class="text-p-sm text-ink-gray-5">{{ l.company }}</div>
          </td>
          <td>{{ l.user }}</td>
          <td>{{ l.clients.map(name).join(', ') }}</td>
          <td>{{ fmtDate(l.last_login) || '–' }}</td>
          <td>
            <Badge
              :label="l.active ? 'Active' : 'Disabled'"
              :theme="l.active ? 'green' : 'gray'"
            />
          </td>
          <td class="text-right">
            <Button size="sm" :label="__('Edit')" @click="edit(l)" />
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!logins.length" class="py-10 text-center text-ink-gray-5">
      {{ __('No client logins yet.') }}
    </div>
    <FormDialog
      v-model:open="show"
      :title="current ? __('Edit client login') : __('Add client login')"
      :fields="fields"
      :initial="initial"
      :onSubmit="save"
    />
  </MaintenanceLayout>
</template>

<script setup>
import FormDialog from '@/components/Maintenance/FormDialog.vue'
import MaintenanceLayout from '@/components/Maintenance/MaintenanceLayout.vue'
import { loginFields, saveLogin } from '@/components/Maintenance/loginForm'
import { api, fmtDate, getList } from '@/composables/maintenance'
import { Badge, Button, usePageMeta } from 'frappe-ui'
import { onMounted, ref } from 'vue'

const logins = ref([])
const clients = ref({})
const show = ref(false)
const current = ref(null)
const fields = ref([])
const initial = ref({})
const name = (c) => clients.value[c] || c

const load = async () => {
  logins.value = await api('get_logins')
  clients.value = Object.fromEntries(
    (await getList('CRM Maintenance Client', ['name', 'client_name'])).map(
      (c) => [c.name, c.client_name],
    ),
  )
}
onMounted(load)
async function edit(l) {
  current.value = l
  fields.value = await loginFields(!l)
  initial.value = l
    ? {
        email: l.user,
        full_name: l.full_name,
        company: l.company,
        clients: l.clients,
        active: !!l.active,
      }
    : { active: true, clients: [] }
  show.value = true
}
async function save(v) {
  await saveLogin(v)
  load()
}
usePageMeta(() => ({ title: __('Client logins') }))
</script>
