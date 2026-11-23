<template>
  <div class="flex items-center rounded border">
    <Button
      variant="ghost"
      icon="lucide-chevron-left"
      @click="shiftMonth(-1)"
    />
    <span class="min-w-32 text-center text-p-base">{{ monthLabel }}</span>
    <Button
      variant="ghost"
      icon="lucide-chevron-right"
      @click="shiftMonth(1)"
    />
  </div>
</template>

<script setup>
import { monthLabel, shiftMonth } from '@/composables/maintenance'
import { Button } from 'frappe-ui'
</script>
