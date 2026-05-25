export const DIFFICULTY_OPTIONS = [
  { value: 'easy', label: '简单' },
  { value: 'medium', label: '中等' },
  { value: 'hard', label: '困难' },
  { value: 'extreme', label: '特难' },
  { value: 'glitch', label: '???' },
];

export function difficultyLabel(difficulty) {
  return DIFFICULTY_OPTIONS.find((item) => item.value === difficulty)?.label || difficulty || '-';
}
