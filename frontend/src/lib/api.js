const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function postJson(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.detail || data.message || "요청 처리 중 오류가 발생했습니다.";
    throw new Error(message);
  }

  return data;
}

export async function postChatTurn(payload) {
  return postJson("/chat/turn", payload);
}

export async function streamChatTurn(payload, { onEvent } = {}) {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "스트리밍 요청 처리 중 오류가 발생했습니다.");
  }

  if (!response.body) {
    throw new Error("스트리밍 응답 본문이 없습니다.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    buffer = consumeEvents(buffer, onEvent);
  }

  consumeEvents(buffer, onEvent);
}

function consumeEvents(buffer, onEvent) {
  let remaining = buffer;
  let boundary = remaining.indexOf("\n\n");

  while (boundary !== -1) {
    const rawEvent = remaining.slice(0, boundary);
    remaining = remaining.slice(boundary + 2);
    boundary = remaining.indexOf("\n\n");

    const data = rawEvent
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart())
      .join("\n");

    if (!data) {
      continue;
    }

    const parsed = JSON.parse(data);
    onEvent?.(parsed);
  }

  return remaining;
}
