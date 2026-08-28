"use client";

import { Session, UserProfile } from "@/lib/types";
import { MessageSquare, Rocket, Box, Settings, Plus } from "lucide-react";

interface SidebarProps {
  sessions: Session[];
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  userProfile?: UserProfile;
}

export function Sidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  userProfile = {
    name: "Rishabh Sharma",
    plan: "Pro Plan",
    status: "Online",
  },
}: SidebarProps) {
  // Helper to group sessions into Today, Yesterday, Earlier
  const getGroupedSessions = () => {
    const today: Session[] = [];
    const yesterday: Session[] = [];
    const earlier: Session[] = [];

    const now = new Date();
    const todayStr = now.toDateString();

    const yest = new Date(now);
    yest.setDate(yest.getDate() - 1);
    const yestStr = yest.toDateString();

    if (sessions.length === 0) {
      // Mock defaults for reference UI match if no sessions exist yet
      return {
        Today: [
          { id: "mock-1", title: "What did Brian Chesky say...", timeLabel: "2:45 PM" },
          { id: "mock-2", title: "PMF lessons from Lenny...", timeLabel: "1:30 PM" },
          { id: "mock-3", title: "Growth strategy insights", timeLabel: "11:20 AM" },
        ],
        Yesterday: [
          { id: "mock-4", title: "Product decision frameworks", timeLabel: "4:10 PM" },
          { id: "mock-5", title: "Founder mindset", timeLabel: "2:30 PM" },
        ],
        Earlier: [
          { id: "mock-6", title: "Pricing strategies", timeLabel: "Mon" },
          { id: "mock-7", title: "User interviews learnings", timeLabel: "Sun" },
        ],
      };
    }

    sessions.forEach((s) => {
      if (!s.created_at) {
        today.push({ ...s, timeLabel: s.timeLabel || "Today" });
        return;
      }
      const d = new Date(s.created_at);
      const dStr = d.toDateString();
      const timeLabel = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      if (dStr === todayStr) {
        today.push({ ...s, timeLabel });
      } else if (dStr === yestStr) {
        yesterday.push({ ...s, timeLabel });
      } else {
        const dayLabel = d.toLocaleDateString([], { weekday: "short" });
        earlier.push({ ...s, timeLabel: dayLabel });
      }
    });

    return { Today: today, Yesterday: yesterday, Earlier: earlier };
  };

  const grouped = getGroupedSessions();

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="brand-avatar">
          🎙️
        </div>
        <div className="brand-title">
          <span className="brand-name">Lenny Growth</span>
          <span className="brand-subtitle">
            Assistant <span style={{ fontSize: 13 }}>✨</span>
          </span>
        </div>
      </div>

      {/* New Chat Button */}
      <button className="new-chat-btn" onClick={onNewChat}>
        <Plus size={16} />
        <span>New Chat</span>
      </button>

      {/* Navigation Links */}
      <div className="sidebar-nav">
        <div className="nav-item active">
          <MessageSquare size={16} className="nav-icon" />
          <span>Chat</span>
        </div>
        <div className="nav-item">
          <Rocket size={16} className="nav-icon" />
          <span>Ship 30 for 30</span>
        </div>
        <div className="nav-item">
          <Box size={16} className="nav-icon" />
          <span>Artifacts</span>
        </div>
      </div>

      {/* Conversations Section */}
      <div className="conversations-container">
        <div className="group-label">Conversations</div>

        {grouped.Today.length > 0 && (
          <div className="conversation-group">
            <div className="group-label" style={{ fontSize: 10, color: '#475569' }}>Today</div>
            {grouped.Today.map((s) => (
              <div
                key={s.id}
                className={`conversation-item ${s.id === currentSessionId ? "active" : ""}`}
                onClick={() => onSelectSession(s.id)}
              >
                <span className="conversation-title">{s.title || "Untitled Chat"}</span>
                <span className="conversation-time">{s.timeLabel || "2:45 PM"}</span>
              </div>
            ))}
          </div>
        )}

        {grouped.Yesterday.length > 0 && (
          <div className="conversation-group">
            <div className="group-label" style={{ fontSize: 10, color: '#475569' }}>Yesterday</div>
            {grouped.Yesterday.map((s) => (
              <div
                key={s.id}
                className={`conversation-item ${s.id === currentSessionId ? "active" : ""}`}
                onClick={() => onSelectSession(s.id)}
              >
                <span className="conversation-title">{s.title || "Untitled Chat"}</span>
                <span className="conversation-time">{s.timeLabel || "Yesterday"}</span>
              </div>
            ))}
          </div>
        )}

        {grouped.Earlier.length > 0 && (
          <div className="conversation-group">
            <div className="group-label" style={{ fontSize: 10, color: '#475569' }}>Earlier</div>
            {grouped.Earlier.map((s) => (
              <div
                key={s.id}
                className={`conversation-item ${s.id === currentSessionId ? "active" : ""}`}
                onClick={() => onSelectSession(s.id)}
              >
                <span className="conversation-title">{s.title || "Untitled Chat"}</span>
                <span className="conversation-time">{s.timeLabel || "Mon"}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* User Profile Card at Sidebar Bottom */}
      <div className="sidebar-profile">
        <div className="profile-info">
          <div className="profile-avatar">
            RS
            <span className="status-dot" />
          </div>
          <div className="profile-text">
            <span className="profile-name">{userProfile.name}</span>
            <span className="profile-plan">
              👑 {userProfile.plan}
            </span>
          </div>
        </div>
        <button className="settings-btn" title="Settings">
          <Settings size={16} />
        </button>
      </div>
    </aside>
  );
}
