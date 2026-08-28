import { Message, Session } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_ORIGIN || process.env.BACKEND_ORIGIN || "http://localhost:8000";

export async function fetchSessions(): Promise<Session[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/sessions`);
    if (!res.ok) return [];
    const data = await res.json();
    return data || [];
  } catch (e) {
    console.error("Failed to fetch sessions", e);
    return [];
  }
}

export async function createSession(title: string = "New Chat"): Promise<Session> {
  const res = await fetch(`${API_BASE}/api/v1/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to create session");
  return await res.json();
}

export function parseMessageArtifact(msg: Message): Message {
  if (!msg || !msg.content || !msg.content.includes("<artifact")) {
    return msg;
  }

  // Check for complete <artifact ...> ... </artifact> match
  const match = msg.content.match(/<artifact type="([^"]+)" title="([^"]+)">([\s\S]*?)<\/artifact>/);
  if (match) {
    const type = match[1] as "markdown" | "html";
    const title = match[2];
    let cleanContent = match[3].trim();
    cleanContent = cleanContent.replace(/<artifact[^>]*>/gi, "").replace(/<\/artifact>/gi, "").trim();

    const artifactData = {
      type,
      title,
      content: cleanContent,
      subtitle: "Generated grounded document based on Lenny's Podcast transcripts.",
    };

    const displayContent = msg.content
      .replace(match[0], "*✨ Artifact created successfully. View the published document in the right panel.*")
      .replace(/<artifact[^>]*>/gi, "")
      .replace(/<\/artifact>/gi, "")
      .trim();

    return {
      ...msg,
      content: displayContent,
      artifactData,
    };
  }

  // Check for start tag <artifact type="..." title="...">
  const startMatch = msg.content.match(/<artifact type="([^"]+)" title="([^"]+)">/);
  if (startMatch) {
    const type = startMatch[1] as "markdown" | "html";
    const title = startMatch[2];
    const startIndex = startMatch.index! + startMatch[0].length;
    let rawContent = msg.content.substring(startIndex);
    rawContent = rawContent.replace(/<artifact[^>]*>/gi, "").replace(/<\/artifact>/gi, "").trim();

    const artifactData = {
      type,
      title,
      content: rawContent,
      subtitle: "Generated grounded document based on Lenny's Podcast transcripts.",
    };

    const displayContent =
      msg.content.substring(0, startMatch.index) +
      "*✨ Artifact created successfully. View the published document in the right panel.*";

    return {
      ...msg,
      content: displayContent.trim(),
      artifactData,
    };
  }

  return msg;
}

export async function fetchSessionMessages(sessionId: string): Promise<Message[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/messages`);
    if (!res.ok) return [];
    const data: Message[] = await res.json();
    return (data || []).map(parseMessageArtifact);
  } catch (e) {
    console.error("Failed to fetch messages", e);
    return [];
  }
}

export async function deleteSession(sessionId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}`, {
      method: "DELETE",
    });
    return res.ok;
  } catch (e) {
    console.error("Failed to delete session", e);
    return false;
  }
}
