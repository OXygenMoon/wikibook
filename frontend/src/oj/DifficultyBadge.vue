<script setup>
import { computed } from 'vue';
import { difficultyLabel } from './difficulty.js';

const props = defineProps({
  difficulty: {
    type: String,
    default: '',
  },
});

const label = computed(() => difficultyLabel(props.difficulty));
const isGlitch = computed(() => props.difficulty === 'glitch');
const classes = computed(() => [
  'difficulty-badge',
  props.difficulty ? `difficulty-badge--${props.difficulty}` : '',
  { 'difficulty-badge--glitch': isGlitch.value },
]);
</script>

<template>
  <span :class="classes" :title="label" :aria-label="label">
    <span v-if="isGlitch" class="difficulty-glitch-track" aria-hidden="true">
      <span>10?&amp;#@</span>
      <span>∑0!7?%</span>
      <span>乱码滚动</span>
      <span>4#?9∞</span>
      <span>10?&amp;#@</span>
    </span>
    <span :class="{ 'sr-only': isGlitch }">{{ label }}</span>
  </span>
</template>

<style>
.difficulty-badge {
  position: relative;
  display: inline-flex;
  min-height: 1.8rem;
  max-width: 10rem;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 900;
  line-height: 1;
  white-space: nowrap;
  text-transform: uppercase;
}

.difficulty-badge--easy {
  border-color: rgb(167 243 208);
  background: rgb(209 250 229);
  color: rgb(4 120 87);
}

.difficulty-badge--medium {
  border-color: rgb(253 230 138);
  background: rgb(254 243 199);
  color: rgb(180 83 9);
}

.difficulty-badge--hard {
  border-color: rgb(254 205 211);
  background: rgb(255 228 230);
  color: rgb(190 18 60);
}

.difficulty-badge--extreme {
  border-color: rgb(185 28 28);
  background: linear-gradient(135deg, rgb(127 29 29), rgb(17 24 39) 58%, rgb(88 28 135));
  color: rgb(254 242 242);
  box-shadow: 0 0 0 1px rgba(248, 113, 113, 0.28), 0 8px 22px rgba(127, 29, 29, 0.18);
}

.difficulty-badge--glitch {
  width: 6.8rem;
  border-color: rgba(34, 211, 238, 0.62);
  background:
    linear-gradient(90deg, rgba(8, 145, 178, 0.28), rgba(244, 63, 94, 0.20)),
    rgb(15 23 42);
  color: rgb(236 254 255);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  letter-spacing: 0;
  text-shadow: 1px 0 rgb(244 63 94), -1px 0 rgb(34 211 238);
}

.difficulty-glitch-track {
  display: flex;
  height: 1em;
  flex-direction: column;
  animation: difficulty-glitch-roll 1.15s steps(4, end) infinite;
}

.difficulty-glitch-track span {
  height: 1em;
  line-height: 1;
}

@keyframes difficulty-glitch-roll {
  from {
    transform: translateY(0);
  }
  to {
    transform: translateY(-4em);
  }
}

html.dark .difficulty-badge--easy {
  border-color: rgb(6 95 70);
  background: rgb(6 78 59);
  color: rgb(209 250 229);
}

html.dark .difficulty-badge--medium {
  border-color: rgb(146 64 14);
  background: rgb(120 53 15);
  color: rgb(254 243 199);
}

html.dark .difficulty-badge--hard {
  border-color: rgb(159 18 57);
  background: rgb(136 19 55);
  color: rgb(255 228 230);
}
</style>
