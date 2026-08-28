"use client";

import { Session } from "@/lib/types";

export function SessionSidebar({
  sessions,
  currentSessionId,
  onSelect,
  onNewChat,
}: {
  sessions: Session[];
  currentSessionId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
}) {
  const getTopicIcon = (title: string, index: number) => {
    const t = (title || "").toLowerCase();
    if (t.includes("apple") || t.includes("b2b")) return "🍏";
    if (t.includes("growth") || t.includes("viral")) return "📈";
    if (t.includes("ai") || t.includes("devin") || t.includes("prompt")) return "🤖";
    if (t.includes("product") || t.includes("pm")) return "💡";
    if (t.includes("strategy") || t.includes("leadership")) return "⚡";
    const icons = ["🎙️", "💬", "📌", "✨", "🚀", "🎯"];
    return icons[index % icons.length];
  };

  return (
    <aside className="traders-sidebar">
      {/* Brand Header */}
      <div className="traders-logo">
        <div className="traders-logo-icon">🧠</div>
        <div className="traders-logo-text">LennyGPT</div>
      </div>

      {/* New Chat Button */}
      <button className="traders-new-chat-btn" onClick={onNewChat}>
        <span>New Chat</span>
        <span style={{ fontSize: 12, opacity: 0.8 }}>✏️</span>
      </button>

      {/* Navigation Tabs */}
      <div className="traders-tab-group">
        <button className="traders-tab">
          <span>📁 Topics</span>
        </button>
        <button className="traders-tab active">
          <span>💬 Chats</span>
        </button>
      </div>

      {/* Search Input */}
      <div className="traders-search-chats">
        <span>🔍</span>
        <input placeholder="Search Chats" />
      </div>

      {/* Sidebar Links Scroll Area */}
      <div className="traders-sessions-scroll">
        {/* Favorites */}
        <div className="traders-section-header">
          <span>Favorites</span>
          <span>▼</span>
        </div>
        <div className="traders-favorite-item">
          <span className="fav-icon">🍏</span>
          <span className="fav-title">Apple Business Strategy</span>
          <span className="fav-star">★</span>
        </div>
        <div className="traders-favorite-item">
          <span className="fav-icon">₿</span>
          <span className="fav-title">Bitcoin's Current Plan</span>
          <span className="fav-star">★</span>
        </div>

        {/* Chats */}
        <div className="traders-section-header" style={{ marginTop: 16 }}>
          <span>Chats</span>
          <span>▼</span>
        </div>
        {sessions.length === 0 ? (
          <div style={{ padding: '8px 12px', fontSize: 12, color: 'var(--text-muted)' }}>
            No previous chats
          </div>
        ) : (
          sessions.map((s, idx) => (
            <div
              key={s.id}
              className={`traders-chat-item ${s.id === currentSessionId ? "active" : ""}`}
              onClick={() => onSelect(s.id)}
            >
              <span className="chat-icon">{getTopicIcon(s.title, idx)}</span>
              <span className="chat-title">{s.title || "Untitled Chat"}</span>
            </div>
          ))
        )}
      </div>

      {/* Sidebar Footer */}
      <div className="traders-sidebar-footer">
        <button className="traders-history-btn">
          <span>Question History</span>
          <span>🕒</span>
        </button>
      </div>
    </aside>
  );
}
