import { call } from 'frappe-ui'
import { computed, ref } from 'vue'

const API = 'crm.api.maintenance.'
export const api = (method, args = {}) => call(API + method, args)
export const getDoc = (doctype, name) =>
  call('frappe.client.get', { doctype, name })
export const insertDoc = (doc) => call('frappe.client.insert', { doc })
export const saveDoc = (doc) => call('frappe.client.save', { doc })
export const deleteDoc = (doctype, name) =>
  call('frappe.client.delete', { doctype, name })
export const getList = (doctype, fields = ['name'], extra = {}) =>
  call('frappe.client.get_list', {
    doctype,
    fields,
    limit_page_length: 500,
    ...extra,
  })

// ---- shared month selector (YYYY-MM-01), kept across maintenance pages
const d = new Date()
export const month = ref(
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`,
)
export const monthLabel = computed(() =>
  new Date(month.value + 'T00:00:00').toLocaleString('en', {
    month: 'long',
    year: 'numeric',
  }),
)
export function shiftMonth(n) {
  const x = new Date(month.value + 'T00:00:00')
  x.setMonth(x.getMonth() + n)
  month.value = `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}-01`
}

// ---- formatting
export const currency = ref('USD')
let settingsLoaded = false
export async function loadCurrency() {
  if (settingsLoaded) return
  settingsLoaded = true
  try {
    const s = await getDoc(
      'CRM Maintenance Settings',
      'CRM Maintenance Settings',
    )
    if (s.default_currency) currency.value = s.default_currency
  } catch (e) {
    // settings not saved yet: keep USD
  }
}
export const money = (v) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.value,
    maximumFractionDigits: 0,
  }).format(v || 0)

export function fmtHours(h) {
  h = Number(h || 0)
  const hh = Math.floor(h)
  const mm = Math.round((h - hh) * 60)
  if (!hh && !mm) return '0m'
  return mm ? (hh ? `${hh}h ${mm}m` : `${mm}m`) : `${hh}h`
}

export function fmtDate(v) {
  if (!v) return ''
  return new Date(String(v).slice(0, 10) + 'T00:00:00').toLocaleDateString(
    'en-GB',
    { day: 'numeric', month: 'short', year: 'numeric' },
  )
}

export const dueText = (r) =>
  r.days < 0
    ? `${-r.days} day${r.days === -1 ? '' : 's'} overdue`
    : r.days === 0
      ? 'Due today'
      : `Due in ${r.days} days`

export const scoreColor = (s) =>
  s == null
    ? 'text-ink-gray-4'
    : s >= 75
      ? 'text-green-600'
      : s >= 50
        ? 'text-amber-600'
        : 'text-red-600'

export const errorText = (e) =>
  (e?.messages && e.messages[0]) || e?.message || 'Something went wrong'
