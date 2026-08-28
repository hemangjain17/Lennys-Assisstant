"use client";

import { useState, useRef } from "react";
import { Paperclip, Mic, Send, Square, ChevronUp, Sparkles, Check, Cpu } from "lucide-react";

interface ChatComposerProps {
  input: string;
  onChange: (text: string) => void;
  onSend: (text: string) => void;
  isStreaming: boolean;
  onStop?: () => void;
  selectedModel: string;
  onSelectModel: (model: string) => void;
}

const MODEL_OPTIONS = [
  { id: "gemini-3.5-flash", name: "Gemini 3.5 Flash", provider: "gemini" },
  { id: "gemini-3.1-flash-lite", name: "Gemini 3.1 Flash Lite", provider: "gemini" },
  { id: "gemini-3-flash-preview", name: "Gemini 3 Flash Preview", provider: "gemini" },
  { id: "llama3.1-local", name: "Llama 3.1 (Local)", provider: "ollama" },
  { id: "gemma4:31b", name: "Gemma 4 (31B)", provider: "ollama" },
  { id: "minimax-m3:cloud", name: "Minimax M3 (Cloud)", provider: "ollama" },
];

export function ChatComposer({
  input,
  onChange,
  onSend,
  isStreaming,
  onStop,
  selectedModel,
  onSelectModel,
}: ChatComposerProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const activeModelObj = MODEL_OPTIONS.find((m) => m.id === selectedModel) || MODEL_OPTIONS[2];

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isStreaming) {
        onSend(input);
      }
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
  };

  return (
    <div className="composer-wrapper">
      <div className="composer-card">
        {/* Top Input Row */}
        <div className="composer-top-row">
          <button className="attachment-btn" title="Attach file or context">
            <Paperclip size={18} />
          </button>

          <textarea
            ref={textareaRef}
            className="composer-textarea"
            placeholder="Ask anything about Lenny's podcasts..."
            value={input}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            rows={1}
          />
        </div>

        {/* Bottom Bar: Model Selector Dropdown + Controls */}
        <div className="composer-bottom-row">
          {/* Integrated Model Selector */}
          <div className="model-dropdown-container">
            <button
              className="model-dropdown-trigger"
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              type="button"
            >
              {activeModelObj.provider === "gemini" ? (
                <Sparkles size={14} style={{ color: "#8b5cf6" }} />
              ) : (
                <Cpu size={14} style={{ color: "#ec4899" }} />
              )}
              <span>{activeModelObj.name}</span>
              <ChevronUp size={12} style={{ transform: isDropdownOpen ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
            </button>

            {isDropdownOpen && (
              <div className="model-dropdown-menu">
                {MODEL_OPTIONS.map((m) => (
                  <div
                    key={m.id}
                    className={`model-option ${m.id === selectedModel ? "selected" : ""}`}
                    onClick={() => {
                      onSelectModel(m.id);
                      setIsDropdownOpen(false);
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      {m.provider === "gemini" ? (
                        <Sparkles size={13} style={{ color: "#8b5cf6" }} />
                      ) : (
                        <Cpu size={13} style={{ color: "#ec4899" }} />
                      )}
                      <span>{m.name}</span>
                    </div>
                    {m.id === selectedModel && <Check size={14} style={{ color: "#8b5cf6" }} />}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right Controls */}
          <div className="composer-right-controls">
            <button className="mic-btn" title="Voice Input">
              <Mic size={16} />
            </button>

            {isStreaming ? (
              <button className="send-btn-gradient" onClick={onStop} title="Stop generation">
                <Square size={13} fill="currentColor" />
              </button>
            ) : (
              <button
                className="send-btn-gradient"
                onClick={() => onSend(input)}
                disabled={!input.trim()}
                title="Send message (Enter)"
              >
                <Send size={14} style={{ marginLeft: 1 }} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
