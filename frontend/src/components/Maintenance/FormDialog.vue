<template>
  <Dialog v-model:open="open" :title="title">
    <template #default>
      <div class="flex flex-col gap-3">
        <template v-for="f in fields" :key="f.key">
          <div v-if="f.type === 'multiselect'">
            <div class="mb-1.5 text-sm text-ink-gray-5">{{ f.label }}</div>
            <div
              class="flex max-h-40 flex-col gap-1.5 overflow-auto rounded border p-2"
            >
              <label
                v-for="o in f.options"
                :key="o.value"
                class="flex items-center gap-2 text-p-base"
              >
                <input
                  v-model="values[f.key]"
                  type="checkbox"
                  :value="o.value"
                />
                {{ o.label }}
              </label>
              <div v-if="!f.options.length" class="text-p-sm text-ink-gray-5">
                {{ __('Nothing to choose from yet.') }}
              </div>
            </div>
          </div>
          <FormControl
            v-else
            v-model="values[f.key]"
            :type="f.type || 'text'"
            :label="f.label + (f.required ? ' *' : '')"
            :options="f.options"
            :placeholder="f.placeholder"
            :rows="f.rows"
            :disabled="f.disabled"
            :description="f.description"
          />
        </template>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="open = false" />
        <Button
          variant="solid"
          :label="submitLabel || __('Save')"
          :loading="saving"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { errorText } from '@/composables/maintenance'
import { Button, Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import { reactive, ref, watch } from 'vue'

// fields: [{ key, label, type: text|number|date|select|textarea|email|password|checkbox|multiselect,
//            options: [{label,value}], required, placeholder }]
const props = defineProps({
  title: String,
  fields: { type: Array, default: () => [] },
  initial: { type: Object, default: () => ({}) },
  submitLabel: String,
  onSubmit: Function, // async (values) => void; throw to show an error
})
const open = defineModel('open', { default: false })
const values = reactive({})
const error = ref('')
const saving = ref(false)

watch(open, (o) => {
  if (!o) return
  error.value = ''
  for (const f of props.fields) {
    values[f.key] =
      props.initial[f.key] ??
      (f.type === 'multiselect' ? [] : (f.default ?? ''))
  }
})

async function submit() {
  const missing = props.fields.find(
    (f) => f.required && (values[f.key] === '' || values[f.key] == null),
  )
  if (missing) {
    error.value = `${missing.label} is required`
    return
  }
  saving.value = true
  try {
    await props.onSubmit({ ...values })
    open.value = false
  } catch (e) {
    error.value = errorText(e)
  } finally {
    saving.value = false
  }
}
</script>
