"use client";

import { useRef, useEffect } from "react";
import { Message, Artifact } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";
import { ChatComposer } from "./ChatComposer";
import { Sparkles, MessageSquare, Lightbulb, Rocket, Shield } from "lucide-react";

interface ChatPanelProps {
  messages: Message[];
  input: string;
  onInputChange: (text: string) => void;
  onSendMessage: (text: string) => void;
  isStreaming: boolean;
  selectedModel: string;
  onSelectModel: (model: string) => void;
  onSelectPrompt: (prompt: string) => void;
  onOpenArtifact?: (artifact: Artifact) => void;
}

const SUGGESTED_PROMPTS = [
  { icon: <Sparkles size={16} style={{ color: "#a855f7" }} />, text: "What did Brian Chesky say about product-market fit?" },
  { icon: <Lightbulb size={16} style={{ color: "#3b82f6" }} />, text: "What are the core growth frameworks shared by Lenny's guests?" },
  { icon: <Rocket size={16} style={{ color: "#ec4899" }} />, text: "Turn the PMF insights into a Ship 30 for 30 essay." },
  { icon: <Shield size={16} style={{ color: "#10b981" }} />, text: "How do top PMs handle hard prioritization trade-offs?" },
];

export function ChatPanel({
  messages,
  input,
  onInputChange,
  onSendMessage,
  isStreaming,
  selectedModel,
  onSelectModel,
  onSelectPrompt,
  onOpenArtifact,
}: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-panel">
      {/* Messages Scroll Area */}
      <div className="messages-scroll">
        {messages.length === 0 ? (
          <div className="chat-empty-state">
            <div className="empty-state-avatar">
              <Sparkles size={32} />
            </div>
            <div className="empty-state-title">Lenny Growth Assistant</div>
            <div className="empty-state-sub">
              Grounded AI assistant trained on 300+ episodes of Lenny's Podcast.
            </div>

            <div className="prompt-chips-grid">
              {SUGGESTED_PROMPTS.map((p, idx) => (
                <div
                  key={idx}
                  className="prompt-chip-card"
                  onClick={() => onSelectPrompt(p.text)}
                >
                  {p.icon}
                  <span>{p.text}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => (
            <MessageBubble
              key={m.id}
              msg={m}
              onOpenArtifact={onOpenArtifact}
            />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Integrated Composer at Bottom */}
      <ChatComposer
        input={input}
        onChange={onInputChange}
        onSend={onSendMessage}
        isStreaming={isStreaming}
        selectedModel={selectedModel}
        onSelectModel={onSelectModel}
      />
    </div>
  );
}
