"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { ArtifactViewer } from "@/components/artifacts/ArtifactViewer";
import { Message, Artifact, Session } from "@/lib/types";
import { fetchSessions, createSession, fetchSessionMessages } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_ORIGIN || process.env.BACKEND_ORIGIN || "http://localhost:8000";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedModel, setSelectedModel] = useState("gemini-3-flash-preview");

  const loadSessionsList = async () => {
    const list = await fetchSessions();
    setSessions(list);
  };

  useEffect(() => {
    loadSessionsList();
  }, []);

  const handleSelectSession = async (id: string) => {
    setSessionId(id);
    setArtifact(null);
    const history = await fetchSessionMessages(id);
    setMessages(history);    // Find the latest assistant message that has an artifact and auto-open it in the side panel
    const lastMsgWithArtifact = [...history].reverse().find((m) => m.artifactData);
    if (lastMsgWithArtifact?.artifactData) {
      setArtifact(lastMsgWithArtifact.artifactData);
    }  };

  const handleNewChat = () => {
    setSessionId(null);
    setMessages([]);
    setArtifact(null);
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isStreaming) return;

    let currentSid = sessionId;
    if (!currentSid) {
      try {
        const newSess = await createSession(text.slice(0, 30));
        currentSid = newSess.id;
        setSessionId(newSess.id);
        setSessions((prev) => [newSess, ...prev]);
      } catch (e) {
        console.error("Could not create session", e);
        return;
      }
    }

    const timeLabel = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: timeLabel,
    };

    const assistantMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: "",
      streaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput("");
    setIsStreaming(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSid,
          message: text,
          model: selectedModel,
        }),
      });

      if (!res.ok) throw new Error("Chat API error");

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data:")) continue;
          try {
            const data = JSON.parse(line.slice(5).trim());

            if (data.type === "status") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.streaming) {
                    const existing = m.statusSteps || [];
                    return {
                      ...m,
                      statusSteps: [
                        ...existing,
                        { stage: data.stage, label: data.label, results: data.results },
                      ],
                    };
                  }
                  return m;
                })
              );
            } else if (data.type === "token") {
              accumulated += data.text;

              // Live building artifact detection
              if (accumulated.includes("<artifact")) {
                const startMatch = accumulated.match(/<artifact type="([^"]+)" title="([^"]+)">/);
                if (startMatch) {
                  const type = startMatch[1] as "markdown" | "html";
                  const title = startMatch[2];
                  const startIndex = startMatch.index! + startMatch[0].length;
                  const endIndex = accumulated.indexOf("</artifact>");
                  let rawContent =
                    endIndex !== -1
                      ? accumulated.substring(startIndex, endIndex)
                      : accumulated.substring(startIndex);

                  // Strip any internal/nested <artifact...> or </artifact> tags
                  rawContent = rawContent.replace(/<artifact[^>]*>/gi, "").replace(/<\/artifact>/gi, "").trim();

                  const artObj: Artifact = {
                    content: rawContent,
                    type,
                    title,
                    subtitle: "Generated grounded document based on Lenny's Podcast transcripts.",
                  };
                  setArtifact(artObj);

                  // Display clean status in chat bubble while streaming artifact into side panel
                  let chatBubbleText = accumulated.substring(0, startMatch.index);
                  if (endIndex !== -1) {
                    chatBubbleText += "*✨ Artifact created successfully. View the published document in the right panel.*";
                  } else {
                    chatBubbleText += "*✨ Generating artifact in side panel...*";
                  }

                  setMessages((prev) =>
                    prev.map((m) => (m.streaming ? { ...m, content: chatBubbleText, artifactData: artObj } : m))
                  );
                  continue;
                }
              }

              setMessages((prev) =>
                prev.map((m) => (m.streaming ? { ...m, content: accumulated } : m))
              );
            } else if (data.type === "done") {
              if (data.title) {
                setSessions((prev) =>
                  prev.map((s) => (s.id === currentSid ? { ...s, title: data.title } : s))
                );
              }
              setMessages((prev) =>
                prev.map((m) => (m.streaming ? { ...m, streaming: false } : m))
              );
            }
          } catch {
            /* ignore malformed JSON */
          }
        }
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) =>
        prev.map((m) =>
          m.streaming
            ? { ...m, content: "⚠️ Something went wrong connecting to the assistant. Please try again.", streaming: false }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
      setTimeout(loadSessionsList, 1000);
    }
  };

  return (
    <div className="app-shell">
      {/* 1. Left Sidebar */}
      <Sidebar
        sessions={sessions}
        currentSessionId={sessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
      />

      {/* 2. Center Chat Workspace */}
      <ChatPanel
        messages={messages}
        input={input}
        onInputChange={setInput}
        onSendMessage={handleSendMessage}
        isStreaming={isStreaming}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        onSelectPrompt={handleSendMessage}
        onOpenArtifact={(art) => setArtifact(art)}
      />

      {/* 3. Right Artifact Viewer Panel */}
      {artifact && (
        <ArtifactViewer
          artifact={artifact}
          onClose={() => setArtifact(null)}
        />
      )}
    </div>
  );
}
