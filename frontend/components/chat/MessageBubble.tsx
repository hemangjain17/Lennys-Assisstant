"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Message, SourceCardItem, Artifact } from "@/lib/types";
import { ThumbsUp, ThumbsDown, Bookmark, Share2, Sparkles, Check, Search, FileText } from "lucide-react";

export function MessageBubble({
  msg,
  onOpenArtifact,
}: {
  msg: Message;
  onOpenArtifact?: (artifact: Artifact) => void;
}) {
  const [liked, setLiked] = useState<boolean | null>(msg.liked ?? null);
  const [bookmarked, setBookmarked] = useState<boolean>(msg.bookmarked ?? false);
  const [copied, setCopied] = useState<boolean>(false);

  const sourcesToDisplay = msg.sources || [];

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (msg.role === "user") {
    return (
      <div className="user-message-row">
        <div className="user-bubble">
          <div>{msg.content}</div>
          <div className="user-timestamp">{msg.timestamp || "2:45 PM"}</div>
        </div>
        <div className="user-avatar-mini">RS</div>
      </div>
    );
  }

  // Sanitize content for rendering so raw <artifact> tags never appear in chat bubbles
  const displayContent = (msg.content || "")
    .replace(/<artifact type="([^"]+)" title="([^"]+)">([\s\S]*?)<\/artifact>/gi, "*✨ Artifact created successfully. View the published document in the right panel.*")
    .replace(/<artifact[^>]*>/gi, "")
    .replace(/<\/artifact>/gi, "")
    .trim();

  return (
    <div className="assistant-message-row">
      <div className="assistant-avatar-badge">
        <Sparkles size={16} />
      </div>

      <div style={{ flex: 1 }}>
        {/* Retrieval & Generation Status Card */}
        {msg.streaming && (
          <div className="retrieval-status-card">
            <div className="retrieval-top-row">
              <div className="retrieval-searching">
                <Search size={14} />
                <span>Searching Lenny's transcripts...</span>
              </div>
              <span className="retrieval-found">12 sources found <Check size={12} style={{ display: 'inline' }} /></span>
            </div>
            <div className="retrieval-bottom-row">
              <Sparkles size={14} />
              <span>Generating grounded answer...</span>
            </div>
            <div className="retrieval-progress-bar">
              <div className="retrieval-progress-fill" />
            </div>
          </div>
        )}

        {/* Assistant Response Content Card */}
        <div className="assistant-card">
          <ReactMarkdown>{displayContent || "Generating grounded answer..."}</ReactMarkdown>

          {/* Inline Artifact Card (matching reference image) */}
          {msg.artifactData && (
            <div
              className="stream-artifact-card"
              onClick={() => onOpenArtifact?.(msg.artifactData!)}
            >
              <div className="stream-artifact-left">
                <div className="stream-artifact-icon-box">
                  <FileText size={20} />
                </div>
                <div className="stream-artifact-info">
                  <div className="stream-artifact-title">
                    {msg.artifactData.title || "Generated Artifact"}
                  </div>
                  <div className="stream-artifact-sub">
                    {msg.artifactData.type === "html" ? "Interactive · HTML" : "Document · MD"}
                  </div>
                </div>
              </div>
              <button
                className="stream-artifact-action-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenArtifact?.(msg.artifactData!);
                }}
              >
                View Artifact
              </button>
            </div>
          )}

          {/* Sources Section - only if real sources exist */}
          {!msg.streaming && sourcesToDisplay.length > 0 && (
            <div className="sources-section">
              <div className="sources-header">Sources ({sourcesToDisplay.length})</div>
              <div className="sources-grid">
                {sourcesToDisplay.map((src, i) => (
                  <a
                    key={src.id || i}
                    href={src.url || "#"}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-chip"
                  >
                    <div className="source-chip-avatar">
                      {src.avatarUrl || src.guest.slice(0, 2).toUpperCase()}
                    </div>
                    <div className="source-chip-info">
                      <div className="source-chip-title">
                        {src.episodeNumber ? `${src.episodeNumber} ` : ""}{src.guest}
                      </div>
                      <div className="source-chip-sub">
                        {src.company || src.title || "Lenny's Podcast"} · {src.timestamp || "00:00"}
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Message Actions */}
        {!msg.streaming && msg.content && (
          <div className="message-actions">
            <button
              className="action-btn"
              onClick={() => setLiked(liked === true ? null : true)}
              style={{ color: liked === true ? "#8b5cf6" : undefined }}
              title="Like"
            >
              <ThumbsUp size={14} />
            </button>
            <button
              className="action-btn"
              onClick={() => setLiked(liked === false ? null : false)}
              style={{ color: liked === false ? "#ef4444" : undefined }}
              title="Dislike"
            >
              <ThumbsDown size={14} />
            </button>
            <button
              className="action-btn"
              onClick={() => setBookmarked(!bookmarked)}
              style={{ color: bookmarked ? "#eab308" : undefined }}
              title="Bookmark"
            >
              <Bookmark size={14} />
            </button>
            <button className="action-btn" onClick={handleCopy} title="Copy Content">
              <Share2 size={14} />
              {copied && <span style={{ fontSize: 11, color: "#10b981" }}>Copied!</span>}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
