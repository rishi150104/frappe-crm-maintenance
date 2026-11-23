import { api, getList } from '@/composables/maintenance'

// Loads the choices the client form needs (agencies, team, plans) once per call.
export async function loadClientChoices() {
  const [agencies, team, plans] = await Promise.all([
    getList('CRM Maintenance Agency', ['name', 'agency_name']),
    api('get_team'),
    getList('CRM Maintenance Plan', [
      'name',
      'service',
      'tier_name',
      'monthly_price',
    ]),
  ])
  return { agencies, team, plans }
}

const opt = (rows, label, value = 'name') =>
  rows.map((r) => ({ label: r[label], value: r[value] }))

export function clientFields({ agencies, team, plans }) {
  return [
    { key: 'client_name', label: 'Client / business name', required: true },
    { key: 'website', label: 'Website' },
    { key: 'platform', label: 'Platform', placeholder: 'WordPress, Shopify…' },
    {
      key: 'agency',
      label: 'Agency',
      type: 'select',
      options: [
        { label: 'Direct client', value: '' },
        ...opt(agencies, 'agency_name'),
      ],
    },
    {
      key: 'project_manager',
      label: 'Project manager',
      type: 'select',
      options: [
        { label: 'Not assigned', value: '' },
        ...opt(team, 'full_name'),
      ],
    },
    { key: 'contact_name', label: 'Contact name' },
    { key: 'contact_email', label: 'Report recipient email', type: 'email' },
    {
      key: 'report_to',
      label: 'Send reports to',
      type: 'select',
      default: 'Client',
      options: ['Client', 'Agency'].map((v) => ({ label: v, value: v })),
    },
    {
      key: 'billing_cycle',
      label: 'Billing',
      type: 'select',
      default: 'Monthly',
      options: ['Monthly', 'Annual'].map((v) => ({ label: v, value: v })),
    },
    { key: 'start_date', label: 'Start date', type: 'date', required: true },
    { key: 'contract_end', label: 'Contract end (optional)', type: 'date' },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      default: 'Active',
      options: ['Active', 'Paused', 'Ended'].map((v) => ({
        label: v,
        value: v,
      })),
    },
    {
      key: 'extra_hours_rate',
      label: 'Extra hours rate (blank = default)',
      type: 'number',
    },
    {
      key: 'plans',
      label: 'Plans',
      type: 'multiselect',
      options: plans.map((p) => ({
        label: `${p.service} · ${p.tier_name}`,
        value: p.name,
      })),
    },
  ]
}

// form values -> doc (keeps existing plan rows so custom prices are not lost)
export function toClientDoc(values, existing = {}) {
  const keep = (existing.plans || []).filter((r) =>
    values.plans.includes(r.plan),
  )
  const have = new Set(keep.map((r) => r.plan))
  return {
    doctype: 'CRM Maintenance Client',
    ...existing,
    ...values,
    agency: values.agency || null,
    project_manager: values.project_manager || null,
    contract_end: values.contract_end || null,
    extra_hours_rate: values.extra_hours_rate || null,
    plans: [
      ...keep,
      ...values.plans.filter((p) => !have.has(p)).map((plan) => ({ plan })),
    ],
  }
}

export const clientInitial = (doc) => ({
  ...doc,
  plans: (doc.plans || []).map((r) => r.plan),
})
