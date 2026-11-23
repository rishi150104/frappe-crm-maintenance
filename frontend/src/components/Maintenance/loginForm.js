import { api, getList } from '@/composables/maintenance'

export async function loginFields(isNew) {
  const clients = await getList('CRM Maintenance Client', [
    'name',
    'client_name',
  ])
  return [
    {
      key: 'email',
      label: 'Email (username)',
      type: 'email',
      required: true,
      disabled: !isNew,
    },
    { key: 'full_name', label: 'Full name', required: true },
    { key: 'company', label: 'Company' },
    {
      key: 'password',
      label: isNew ? 'Password' : 'New password (leave blank to keep)',
      type: 'password',
      required: isNew,
    },
    {
      key: 'clients',
      label: 'Projects this login can see',
      type: 'multiselect',
      options: clients.map((c) => ({ label: c.client_name, value: c.name })),
    },
    { key: 'active', label: 'Active', type: 'checkbox', default: true },
  ]
}

export const saveLogin = (v) =>
  api('save_client_login', {
    email: v.email,
    full_name: v.full_name,
    company: v.company,
    password: v.password || null,
    clients: v.clients,
    active: v.active ? 1 : 0,
  })
