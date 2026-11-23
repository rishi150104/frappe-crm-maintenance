<template>
  <MaintenanceLayout
    v-if="r"
    :crumbs="[
      { label: __('Maintenance'), route: { name: 'Maintenance' } },
      { label: __('Monthly reports'), route: { name: 'MaintenanceReports' } },
      { label: r.client.client_name },
    ]"
  >
    <template #actions>
      <span class="text-p-sm text-ink-gray-5">{{
        saved ? __('All changes saved') : __('Saving…')
      }}</span>
      <Button
        :label="__('Preview PDF')"
        :loading="busy === 'pdf'"
        @click="pdf(false)"
      />
      <Button
        :label="__('Download')"
        :loading="busy === 'dl'"
        @click="pdf(true)"
      />
      <Button :label="__('WhatsApp')" @click="whatsapp" />
      <Button
        variant="solid"
        :label="
          r.doc.status === 'Sent' ? __('Resend email') : __('Email report')
        "
        @click="showSend = true"
      />
    </template>

    <div class="mb-4">
      <div class="flex items-center gap-2">
        <h2 class="text-xl font-semibold text-ink-gray-9">
          {{ r.client.client_name }}
        </h2>
        <Badge
          :label="r.doc.status"
          :theme="
            r.doc.status === 'Sent'
              ? 'green'
              : r.doc.status === 'Ready'
                ? 'blue'
                : 'gray'
          "
        />
      </div>
      <div class="text-p-base text-ink-gray-5">
        {{ monthText }} · {{ r.client.website }}
      </div>
    </div>

    <div class="grid gap-5 lg:grid-cols-3">
      <div class="space-y-5 lg:col-span-2">
        <section class="rounded-lg border">
          <div class="flex items-center justify-between border-b p-4">
            <div>
              <div class="font-medium text-ink-gray-9">
                {{ __('Monthly checklist') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{ counts.Done }} {{ __('done') }} · {{ counts.Issue }}
                {{ __('issues') }} · {{ counts.none }} {{ __('not checked') }}
              </div>
            </div>
            <Button size="sm" :label="__('Mark rest done')" @click="markRest" />
          </div>
          <template v-for="(items, cat) in byCategory" :key="cat">
            <div
              class="border-b bg-surface-gray-1 px-4 py-1.5 text-xs font-medium uppercase text-ink-gray-5"
            >
              {{ cat }}
            </div>
            <div
              v-for="i in items"
              :key="i.name"
              class="border-b px-4 py-2.5 last:border-0"
            >
              <div class="flex items-center justify-between gap-3">
                <span class="text-ink-gray-9">{{ i.item }}</span>
                <div
                  class="flex shrink-0 overflow-hidden rounded border text-p-sm"
                >
                  <button
                    v-for="s in ['Done', 'Issue', 'N/A']"
                    :key="s"
                    class="px-2.5 py-1"
                    :class="
                      i.status === s
                        ? s === 'Done'
                          ? 'bg-green-600 text-white'
                          : s === 'Issue'
                            ? 'bg-red-600 text-white'
                            : 'bg-gray-600 text-white'
                        : 'hover:bg-surface-gray-2'
                    "
                    @click="i.status = i.status === s ? '' : s"
                  >
                    {{ s }}
                  </button>
                </div>
              </div>
              <input
                v-if="i.status === 'Issue' || i.note"
                v-model="i.note"
                class="mt-2 w-full rounded border px-2 py-1 text-p-sm"
                :placeholder="__('Note for this check')"
              />
            </div>
          </template>
        </section>

        <section class="rounded-lg border p-4">
          <div class="mb-3 font-medium text-ink-gray-9">
            {{ __('Notes for the client') }}
            <span class="text-p-sm font-normal text-ink-gray-5">{{
              __('These appear in the PDF')
            }}</span>
          </div>
          <FormControl
            v-model="r.doc.summary"
            type="textarea"
            :rows="3"
            :label="__('Summary of the month')"
          />
          <FormControl
            v-model="r.doc.recommendations"
            class="mt-3"
            type="textarea"
            :rows="3"
            :label="__('Recommendations / next steps')"
          />
          <div class="mt-4">
            <div class="mb-2 text-sm text-ink-gray-5">
              {{ __('Screenshots for the client') }}
            </div>
            <div
              v-for="(s, idx) in r.doc.screenshots"
              :key="idx"
              class="mb-2 flex items-center gap-3"
            >
              <img
                :src="s.image"
                class="h-16 w-24 rounded border object-cover"
              />
              <input
                v-model="s.caption"
                class="flex-1 rounded border px-2 py-1 text-p-sm"
                :placeholder="__('Caption')"
              />
              <Button
                size="sm"
                variant="ghost"
                theme="red"
                icon="lucide-trash-2"
                @click="r.doc.screenshots.splice(idx, 1)"
              />
            </div>
            <FileUploader
              :fileTypes="['image/*']"
              @success="
                (f) =>
                  r.doc.screenshots.push({ image: f.file_url, caption: '' })
              "
            >
              <template #default="{ openFileSelector, uploading }">
                <Button
                  size="sm"
                  :loading="uploading"
                  :label="__('Add screenshot')"
                  @click="openFileSelector"
                />
              </template>
            </FileUploader>
          </div>
        </section>
      </div>

      <div class="space-y-5">
        <section class="rounded-lg border p-4">
          <div class="text-xs uppercase text-ink-gray-5">
            {{ __('Health score') }}
          </div>
          <div class="text-4xl font-semibold" :class="scoreColor(liveScore)">
            {{ liveScore }}<span class="text-lg text-ink-gray-4">/100</span>
          </div>
          <div class="text-p-base text-ink-gray-7">{{ label(liveScore) }}</div>
        </section>
        <section class="rounded-lg border p-4">
          <div class="mb-1 text-xs uppercase text-ink-gray-5">
            {{ __('Hours used') }}
          </div>
          <HoursBar :used="r.doc.hours_used" :included="r.doc.hours_included" />
        </section>
        <section class="rounded-lg border">
          <div class="flex items-center justify-between border-b p-4">
            <div>
              <div class="font-medium text-ink-gray-9">
                {{ __('Work logged') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{ r.work.length }} {{ __('entries · goes into the report') }}
              </div>
            </div>
            <Button
              size="sm"
              :label="__('Log hours')"
              @click="showHours = true"
            />
          </div>
          <div
            v-for="w in r.work"
            :key="w.name"
            class="flex justify-between border-b px-4 py-2.5 last:border-0"
          >
            <div>
              <div>{{ w.description }}</div>
              <div class="text-p-sm text-ink-gray-5">
                {{ fmtDate(w.date) }} · {{ w.work_type }}
              </div>
            </div>
            <span class="font-medium">{{ fmtHours(w.hours) }}</span>
          </div>
        </section>
        <Button
          theme="red"
          variant="subtle"
          :label="__('Delete report')"
          @click="remove"
        />
      </div>
    </div>

    <FormDialog
      v-model:open="showHours"
      :title="__('Log hours')"
      :fields="hourFields"
      :initial="{ date: today, work_type: 'Support' }"
      :onSubmit="logHours"
    />
    <FormDialog
      v-model:open="showSend"
      :title="__('Email report to client')"
      :fields="[
        { key: 'to', label: 'Send to (comma separated)', required: true },
      ]"
      :initial="{ to: defaultTo }"
      :submitLabel="__('Send PDF')"
      :onSubmit="send"
    />
  </MaintenanceLayout>
</template>

<script setup>
import FormDialog from '@/components/Maintenance/FormDialog.vue'
import HoursBar from '@/components/Maintenance/HoursBar.vue'
import MaintenanceLayout from '@/components/Maintenance/MaintenanceLayout.vue'
import {
  api,
  deleteDoc,
  fmtDate,
  fmtHours,
  saveDoc,
  scoreColor,
} from '@/composables/maintenance'
import {
  Badge,
  Button,
  FileUploader,
  FormControl,
  toast,
  usePageMeta,
} from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({ reportId: String })
const router = useRouter()
const r = ref(null)
const saved = ref(true)
const busy = ref('')
const showHours = ref(false)
const showSend = ref(false)
const today = new Date().toISOString().slice(0, 10)

const load = async () =>
  (r.value = await api('get_report', { name: props.reportId }))
onMounted(load)

const monthText = computed(() =>
  new Date(r.value.doc.month + 'T00:00:00').toLocaleString('en', {
    month: 'long',
    year: 'numeric',
  }),
)
const byCategory = computed(() =>
  r.value.doc.items.reduce(
    (a, i) => ((a[i.category || 'Other'] ||= []).push(i), a),
    {},
  ),
)
const counts = computed(() => {
  const it = r.value.doc.items
  return {
    Done: it.filter((i) => i.status === 'Done').length,
    Issue: it.filter((i) => i.status === 'Issue').length,
    none: it.filter((i) => !i.status).length,
  }
})
// same rule as the server (N/A excluded; Issue and unchecked count against); the server value is authoritative on save
const liveScore = computed(() => {
  const it = r.value.doc.items.filter((i) => i.status !== 'N/A')
  const total = it.reduce((a, i) => a + (i.weight || 1), 0)
  return total
    ? Math.round(
        (it
          .filter((i) => i.status === 'Done')
          .reduce((a, i) => a + (i.weight || 1), 0) *
          100) /
          total,
      )
    : 0
})
const label = (s) =>
  s >= 90
    ? 'Excellent'
    : s >= 75
      ? 'Good'
      : s >= 50
        ? 'Needs some work'
        : 'Poor'
const defaultTo = computed(() => r.value.client.contact_email || '')

// ---- autosave (debounced); only the editable parts are watched so server echoes don't loop
const editable = computed(
  () =>
    r.value &&
    JSON.stringify([
      r.value.doc.items.map((i) => [i.status, i.note]),
      r.value.doc.summary,
      r.value.doc.recommendations,
      r.value.doc.screenshots,
    ]),
)
let timer
watch(editable, (now, before) => {
  if (!before) return
  saved.value = false
  clearTimeout(timer)
  timer = setTimeout(save, 800)
})
async function save() {
  try {
    const d = await saveDoc(r.value.doc)
    Object.assign(r.value.doc, {
      modified: d.modified,
      score: d.score,
      score_label: d.score_label,
      status: d.status,
      hours_used: d.hours_used,
    })
    saved.value = true
  } catch (e) {
    toast.error(__('Could not save: ') + (e.messages?.[0] || e.message))
  }
}
onBeforeUnmount(() => {
  clearTimeout(timer)
  if (r.value && !saved.value) save()
})

const markRest = () =>
  r.value.doc.items.forEach((i) => !i.status && (i.status = 'Done'))

async function pdf(download) {
  busy.value = download ? 'dl' : 'pdf'
  try {
    await save()
    const url = await api('generate_pdf', { report: props.reportId })
    const a = document.createElement('a')
    a.href = url
    a.target = '_blank'
    if (download) a.download = `${props.reportId}.pdf`
    a.click()
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not create the PDF'))
  } finally {
    busy.value = ''
  }
}
function whatsapp() {
  const c = r.value.client
  const text = `Hi, your website care report for ${monthText.value} (${c.client_name}) is ready. Health score: ${liveScore.value}/100. ${r.value.doc.summary || ''}`
  window.open('https://wa.me/?text=' + encodeURIComponent(text), '_blank')
}
async function send(v) {
  await save()
  await api('send_report', { report: props.reportId, recipients: v.to })
  toast.success(__('Report sent'))
  await load()
}
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
async function logHours(v) {
  await api('log_hours', { client: r.value.client.name, ...v })
  await save()
  await load()
}
async function remove() {
  if (!confirm(__('Delete this report? This cannot be undone.'))) return
  await deleteDoc('CRM Maintenance Report', props.reportId)
  router.push({ name: 'MaintenanceReports' })
}
usePageMeta(() => ({ title: __('Maintenance report') }))
</script>
