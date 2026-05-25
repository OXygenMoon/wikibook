export const DIFFICULTY_OPTIONS = [
  { value: 'easy', label: '简单' },
  { value: 'medium', label: '中等' },
  { value: 'hard', label: '困难' },
  { value: 'extreme', label: '极度困难' },
  { value: 'glitch', label: '乱码滚动' },
];

export function difficultyLabel(difficulty) {
  return DIFFICULTY_OPTIONS.find((item) => item.value === difficulty)?.label || difficulty || '-';
}

