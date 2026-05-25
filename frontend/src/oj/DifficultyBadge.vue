<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { difficultyLabel } from './difficulty.js';

const props = defineProps({
  difficulty: {
    type: String,
    default: '',
  },
});

const label = computed(() => difficultyLabel(props.difficulty));
const isGlitch = computed(() => props.difficulty === 'glitch');
const glitchText = ref('0000');
const isShaking = ref(false);
const isFlashing = ref(false);
let rollTimer = 0;
let shakeTimer = 0;
let flashTimer = 0;

const GLITCH_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ@$#%&*+=?<>█▓▒░';
const GLITCH_LENGTH = 4;

const classes = computed(() => [
  'difficulty-badge',
  props.difficulty ? `difficulty-badge--${props.difficulty}` : '',
  {
    'difficulty-badge--glitch': isGlitch.value,
    'difficulty-badge--shake': isShaking.value,
    'difficulty-badge--flash': isFlashing.value,
  },
]);

function randomChar() {
  return GLITCH_CHARS[Math.floor(Math.random() * GLITCH_CHARS.length)];
}

function randomCode() {
  let text = '';
  for (let index = 0; index < GLITCH_LENGTH; index += 1) {
    text += randomChar();
  }
  return text;
}

function triggerShake() {
  window.clearTimeout(shakeTimer);
  isShaking.value = false;
  window.requestAnimationFrame(() => {
    isShaking.value = true;
    shakeTimer = window.setTimeout(() => {
      isShaking.value = false;
    }, 90);
  });
}

function triggerFlash() {
  window.clearTimeout(flashTimer);
  isFlashing.value = false;
  window.requestAnimationFrame(() => {
    isFlashing.value = true;
    flashTimer = window.setTimeout(() => {
      isFlashing.value = false;
    }, 120);
  });
}

function roll() {
  glitchText.value = randomCode();
  if (Math.random() > 0.76) triggerShake();
  if (Math.random() > 0.86) triggerFlash();
}

function stopGlitch() {
  window.clearInterval(rollTimer);
  window.clearTimeout(shakeTimer);
  window.clearTimeout(flashTimer);
  rollTimer = 0;
  isShaking.value = false;
  isFlashing.value = false;
}

function startGlitch() {
  stopGlitch();
  glitchText.value = randomCode();
  rollTimer = window.setInterval(roll, 180);
}

watch(isGlitch, (enabled) => {
  if (enabled) startGlitch();
  else stopGlitch();
});

onMounted(() => {
  if (isGlitch.value) startGlitch();
});

onBeforeUnmount(stopGlitch);
</script>

<template>
  <span :class="classes" :title="label" :aria-label="label" :data-text="isGlitch ? glitchText : null">
    <span v-if="isGlitch" class="difficulty-glitch-code" aria-hidden="true">{{ glitchText }}</span>
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
  width: 6ch;
  max-width: none;
  min-height: 1.9rem;
  border-color: rgba(0, 255, 240, 0.72);
  background:
    linear-gradient(90deg, rgba(255, 0, 90, 0.08), transparent 18%, transparent 82%, rgba(0, 255, 240, 0.08)),
    rgba(0, 20, 28, 0.76);
  color: #7dfff7;
  font-family: Consolas, Monaco, "Courier New", monospace;
  font-size: 0.78rem;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-align: center;
  text-shadow:
    0 0 8px rgba(0, 255, 240, 0.95),
    1px 0 0 rgba(255, 0, 100, 0.7),
    -1px 0 0 rgba(0, 120, 255, 0.7);
  box-shadow:
    0 0 16px rgba(0, 255, 240, 0.22),
    0 0 28px rgba(255, 0, 100, 0.12),
    inset 0 0 14px rgba(0, 255, 240, 0.14);
  isolation: isolate;
  text-transform: none;
  animation: difficulty-cyber-pulse 2.4s infinite steps(2);
}

.difficulty-badge--glitch::before {
  content: attr(data-text);
  position: absolute;
  inset: 0.25rem 0.75rem;
  z-index: 2;
  color: #ff2b8a;
  text-shadow:
    -2px 0 0 rgba(255, 0, 100, 0.95),
    2px 0 0 rgba(0, 255, 240, 0.8);
  opacity: 0;
  pointer-events: none;
  animation: difficulty-error-slice 2.1s infinite steps(1);
}

.difficulty-badge--glitch::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 3;
  background:
    linear-gradient(90deg, transparent 0%, rgba(255, 0, 100, 0.22) 48%, transparent 52%),
    repeating-linear-gradient(
      to bottom,
      rgba(255, 255, 255, 0.08) 0,
      rgba(255, 255, 255, 0.08) 1px,
      transparent 1px,
      transparent 5px
    );
  background-size: 180% 100%, 100% 100%;
  opacity: 0.38;
  pointer-events: none;
  animation: difficulty-scan-move 1.6s linear infinite;
}

.difficulty-badge--shake {
  animation: difficulty-shake 0.08s steps(2) 1, difficulty-cyber-pulse 2.4s infinite steps(2);
}

.difficulty-badge--flash {
  border-color: rgba(255, 0, 100, 0.95);
  color: #ffffff;
  box-shadow:
    0 0 18px rgba(255, 0, 100, 0.8),
    0 0 34px rgba(0, 255, 240, 0.28),
    inset 0 0 18px rgba(255, 0, 100, 0.28);
}

.difficulty-glitch-code {
  position: relative;
  z-index: 1;
}

@keyframes difficulty-shake {
  0% {
    transform: translate(0, 0) skewX(0deg);
  }
  40% {
    transform: translate(-2px, 1px) skewX(-4deg);
  }
  80% {
    transform: translate(2px, -1px) skewX(4deg);
  }
  100% {
    transform: translate(0, 0) skewX(0deg);
  }
}

@keyframes difficulty-cyber-pulse {
  0%,
  100% {
    filter: brightness(1);
  }
  47% {
    filter: brightness(1);
  }
  48% {
    filter: brightness(1.35) contrast(1.35);
  }
  50% {
    filter: brightness(0.9);
  }
  52% {
    filter: brightness(1.2);
  }
}

@keyframes difficulty-scan-move {
  from {
    background-position: -120% 0, 0 0;
  }

  to {
    background-position: 120% 0, 0 0;
  }
}

@keyframes difficulty-error-slice {
  0%,
  78%,
  100% {
    opacity: 0;
    clip-path: inset(0 0 0 0);
    transform: translateX(0);
  }
  80% {
    opacity: 0.95;
    clip-path: inset(0 0 68% 0);
    transform: translateX(-4px);
  }
  82% {
    opacity: 0.75;
    clip-path: inset(36% 0 42% 0);
    transform: translateX(5px);
  }
  84% {
    opacity: 0.9;
    clip-path: inset(70% 0 0 0);
    transform: translateX(-3px);
  }
  86% {
    opacity: 0;
    clip-path: inset(0 0 0 0);
    transform: translateX(0);
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
