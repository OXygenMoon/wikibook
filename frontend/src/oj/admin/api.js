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
    const message = data.message || '操作失败，请稍后再试。';
    throw Object.assign(new Error(message), { response, data });
  }
  return data;
}

export function postForm(url, formData) {
  return requestJson(url, {
    method: 'POST',
    body: formData,
  });
}
