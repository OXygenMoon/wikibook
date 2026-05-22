export async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      Accept: 'application/json',
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.ok === false) {
    throw new Error(data.message || '请求失败，请稍后再试。');
  }
  return data;
}
