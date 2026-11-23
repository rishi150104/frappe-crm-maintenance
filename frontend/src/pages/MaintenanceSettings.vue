<template>
  <MaintenanceLayout :title="__('Settings')">
    <p class="mb-4 text-p-base text-ink-gray-5">
      {{ __('Branding, email, the monthly checklist and your team') }}
    </p>
    <div class="mb-5 flex gap-1">
      <Button
        v-for="t in tabs"
        :key="t"
        size="sm"
        :variant="tab === t ? 'subtle' : 'ghost'"
        :label="t"
        @click="tab = t"
      />
    </div>

    <section v-if="tab === 'Company & email' && s" class="max-w-2xl space-y-3">
      <p class="text-p-sm text-ink-gray-5">
        {{ __('Used on the PDF report and when emailing clients') }}
      </p>
      <FormControl
        v-model="s.company_name"
        :label="__('Company name (shown on reports)')"
      />
      <FormControl v-model="s.company_website" :label="__('Company website')" />
      <div>
        <div class="mb-1.5 text-sm text-ink-gray-5">
          {{ __('Brand color (report header and accents)') }}
        </div>
        <input
          v-model="s.brand_color"
          type="color"
          class="h-9 w-16 rounded border"
        />
      </div>
      <FormControl
        v-model="s.default_currency"
        type="select"
        :label="__('Default currency')"
        :options="currencies"
      />
      <FormControl
        v-model="s.send_from"
        :label="__('Send emails from')"
        :description="
          __(
            'e.g. Reports <reports@yourdomain.com> - the domain must be verified in your email service',
          )
        "
      />
      <FormControl v-model="s.reply_to" :label="__('Reply-to email')" />
      <FormControl
        v-model="s.report_footer"
        :label="__('Report footer line')"
      />
      <h4 class="pt-3 font-medium text-ink-gray-9">
        {{ __('Extra hours & renewals') }}
      </h4>
      <FormControl
        v-model="s.extra_hours_rate"
        type="number"
        :label="__('Hourly rate for extra hours')"
      />
      <FormControl
        v-model="s.renewal_alert_days"
        type="number"
        :label="__('Contract renewal alert (days before a contract ends)')"
      />
      <FormControl
        v-model="s.head_emails"
        type="textarea"
        :rows="2"
        :label="
          __(
            'Head / management emails (comma separated, on top of the admin users)',
          )
        "
      />
      <p class="rounded border bg-surface-gray-1 p-3 text-p-sm text-ink-gray-7">
        {{
          __(
            'Emails are sent through the CRM\'s outgoing email account. To send with Resend, set the site\'s outgoing email server to smtp.resend.com, port 587, user "resend", and your Resend API key as the password, then use a verified domain in "Send emails from".',
          )
        }}
      </p>
      <Button
        variant="solid"
        :label="__('Save settings')"
        :loading="saving"
        @click="saveSettings"
      />
    </section>

    <section v-if="tab === 'Checklist'" class="max-w-3xl">
      <div class="mb-3 flex items-center justify-between">
        <p class="text-p-sm text-ink-gray-5">
          {{
            __(
              'These checks are copied into every monthly report. A check tied to a service only appears for clients on a plan in that service.',
            )
          }}
        </p>
        <Button
          variant="solid"
          iconLeft="lucide-plus"
          :label="__('Add check')"
          @click="editCheck(null)"
        />
      </div>
      <div v-for="cat in categories" :key="cat" class="mb-4 rounded-lg border">
        <div class="border-b p-3 text-xs font-medium uppercase text-ink-gray-5">
          {{ cat }}
        </div>
        <div
          v-for="c in checks.filter((x) => x.category === cat)"
          :key="c.name"
          class="flex items-center justify-between border-b px-3 py-2 last:border-0"
        >
          <span
            >{{ c.label
            }}<span v-if="c.service" class="ml-2 text-p-sm text-ink-gray-5"
              >· {{ c.service }}</span
            ><span v-if="c.weight > 1" class="ml-2 text-p-sm text-ink-gray-5"
              >×{{ c.weight }}</span
            ></span
          >
          <span class="space-x-1"
            ><Button
              size="sm"
              variant="ghost"
              :label="__('Edit')"
              @click="editCheck(c)" /><Button
              size="sm"
              variant="ghost"
              theme="red"
              icon="lucide-trash-2"
              @click="removeCheck(c)"
          /></span>
        </div>
      </div>
    </section>

    <section v-if="tab === 'Team'" class="max-w-2xl">
      <p class="mb-3 text-p-sm text-ink-gray-5">
        {{
          __(
            "Team members are the CRM's own users (they sign in to the CRM). Project managers are picked from this list. Add or remove people in CRM Settings → Users.",
          )
        }}
      </p>
      <div class="rounded-lg border">
        <div
          v-for="u in team"
          :key="u.name"
          class="border-b px-4 py-2.5 last:border-0"
        >
          <div class="text-ink-gray-9">{{ u.full_name }}</div>
          <div class="text-p-sm text-ink-gray-5">{{ u.name }}</div>
        </div>
      </div>
    </section>

    <FormDialog
      v-model:open="showCheck"
      :title="currentCheck ? __('Edit check') : __('Add check')"
      :fields="checkFields"
      :initial="currentCheck || { category: 'Updates', weight: 1 }"
      :onSubmit="saveCheck"
    />
  </MaintenanceLayout>
</template>

<script setup>
import FormDialog from '@/components/Maintenance/FormDialog.vue'
import MaintenanceLayout from '@/components/Maintenance/MaintenanceLayout.vue'
import {
  api,
  deleteDoc,
  getDoc,
  getList,
  insertDoc,
  saveDoc,
} from '@/composables/maintenance'
import { Button, FormControl, toast, usePageMeta } from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'

const DT = 'CRM Maintenance Settings'
const tabs = ['Company & email', 'Checklist', 'Team']
const tab = ref('Company & email')
const s = ref(null)
const saving = ref(false)
const checks = ref([])
const services = ref([])
const team = ref([])
const showCheck = ref(false)
const currentCheck = ref(null)
const categories = [
  'Updates',
  'Security',
  'Performance',
  'Functionality',
  'Technical SEO',
  'Other',
]
const currencies = ['USD', 'GBP', 'EUR', 'AUD', 'CAD', 'INR', 'AED'].map(
  (v) => ({ label: v, value: v }),
)

const loadChecks = async () =>
  (checks.value = await getList(
    'CRM Maintenance Check',
    ['name', 'category', 'label', 'service', 'weight'],
    { order_by: 'sort asc, creation asc' },
  ))
onMounted(async () => {
  s.value = await getDoc(DT, DT)
  services.value = await getList('CRM Maintenance Service Type', ['name'])
  team.value = await api('get_team')
  loadChecks()
})
async function saveSettings() {
  saving.value = true
  try {
    await saveDoc({ ...s.value, doctype: DT })
    toast.success(__('Saved'))
  } finally {
    saving.value = false
  }
}
const checkFields = computed(() => [
  {
    key: 'category',
    label: 'Category',
    type: 'select',
    options: categories.map((v) => ({ label: v, value: v })),
  },
  { key: 'label', label: 'Check', required: true },
  {
    key: 'service',
    label: 'Only for service (optional)',
    type: 'select',
    options: [
      { label: 'All clients', value: '' },
      ...services.value.map((x) => ({ label: x.name, value: x.name })),
    ],
  },
  { key: 'weight', label: 'Weight', type: 'number' },
])
const editCheck = (c) => {
  currentCheck.value = c
  showCheck.value = true
}
async function saveCheck(v) {
  const doc = {
    doctype: 'CRM Maintenance Check',
    ...(currentCheck.value || {}),
    ...v,
    service: v.service || null,
    weight: Number(v.weight) || 1,
  }
  await (currentCheck.value ? saveDoc(doc) : insertDoc(doc))
  loadChecks()
}
async function removeCheck(c) {
  await deleteDoc('CRM Maintenance Check', c.name)
  loadChecks()
}
usePageMeta(() => ({ title: __('Settings') }))
</script>
