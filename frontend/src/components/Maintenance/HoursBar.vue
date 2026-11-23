<template>
  <div>
    <div class="flex items-baseline gap-1 text-p-sm">
      <span class="font-medium text-ink-gray-9">{{ fmtHours(used) }}</span>
      <span class="text-ink-gray-5">/ {{ fmtHours(included) }}</span>
    </div>
    <div class="mt-1 h-1.5 w-full overflow-hidden rounded bg-surface-gray-3">
      <div
        class="h-full rounded"
        :class="
          pct > 100
            ? 'bg-surface-red-5'
            : pct > 80
              ? 'bg-surface-amber-3'
              : 'bg-surface-green-3'
        "
        :style="{ width: Math.min(pct, 100) + '%' }"
      />
    </div>
  </div>
</template>

<script setup>
import { fmtHours } from '@/composables/maintenance'
import { computed } from 'vue'

const props = defineProps({ used: Number, included: Number })
const pct = computed(() =>
  props.included ? (props.used / props.included) * 100 : 0,
)
</script>
