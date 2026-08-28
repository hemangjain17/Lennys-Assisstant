"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

interface ArtifactPanelProps {
  content: string;
  type: "html" | "markdown";
  title: string;
  onClose: () => void;
}

export function ArtifactPanel({ content, type, title, onClose }: ArtifactPanelProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [activeTab, setActiveTab] = useState<"preview" | "code">("preview");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (type === "html" && activeTab === "preview" && iframeRef.current) {
      const doc = iframeRef.current.contentDocument;
      if (doc) {
        doc.open();
        doc.write(content);
        doc.close();
      }
    }
  }, [content, type, activeTab]);

  // Calculate statistics
  const wordCount = content ? content.trim().split(/\s+/).length : 0;
  const readTimeMin = Math.max(1, Math.ceil(wordCount / 225));

  // Extract headings for Table of Contents / Navigator
  const headings = (content || "")
    .split("\n")
    .filter((line) => line.startsWith("#"))
    .map((line) => {
      const match = line.match(/^(#{1,3})\s+(.*)$/);
      if (match) {
        return {
          level: match[1].length,
          text: match[2].replace(/\*/g, "").trim(),
          id: match[2].toLowerCase().replace(/[^\w\s-]/g, "").replace(/\s+/g, "-"),
        };
      }
      return null;
    })
    .filter(Boolean) as Array<{ level: number; text: string; id: string }>;

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const ext = type === "html" ? "html" : "md";
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(title || "artifact").replace(/\s+/g, "_").toLowerCase()}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="artifact-panel">
      {/* Header */}
      <div className="artifact-header">
        <div className="artifact-header-left">
          <span className="artifact-title">{title || "Generated Artifact"}</span>
          <span className={`artifact-type-badge ${type}`}>{type}</span>
        </div>

        <div className="artifact-header-actions">
          {/* Tab buttons */}
          <div className="artifact-tabs">
            <button
              className={`artifact-tab ${activeTab === "preview" ? "active" : ""}`}
              onClick={() => setActiveTab("preview")}
            >
              👁️ Preview
            </button>
            <button
              className={`artifact-tab ${activeTab === "code" ? "active" : ""}`}
              onClick={() => setActiveTab("code")}
            >
              💻 Code
            </button>
          </div>

          <button className="artifact-icon-btn" onClick={handleCopy} title="Copy Content">
            {copied ? "✅ Copied" : "📋 Copy"}
          </button>
          <button className="artifact-icon-btn" onClick={handleDownload} title="Download File">
            📥 Export
          </button>
          <button className="close-artifact-btn" onClick={onClose} title="Close Panel">
            ✕
          </button>
        </div>
      </div>

      {/* Meta Subbar */}
      <div className="artifact-meta-bar">
        <span>📊 {wordCount} words</span>
        <span>⏱️ {readTimeMin} min read</span>
        <span>✨ Grounded Podcast Artifact</span>
      </div>

      {/* Body Area */}
      <div className="artifact-body">
        {activeTab === "code" ? (
          <div className="artifact-code-view">
            <pre><code>{content}</code></pre>
          </div>
        ) : type === "html" ? (
          <iframe
            ref={iframeRef}
            className="artifact-iframe"
            sandbox="allow-scripts allow-same-origin"
            title="Artifact Preview"
          />
        ) : (
          <div className="artifact-markdown-container">
            {/* Table of Contents Section Navigator */}
            {headings.length > 1 && (
              <div className="artifact-toc">
                <div className="artifact-toc-title">📍 Section Navigation</div>
                <div className="artifact-toc-list">
                  {headings.map((h, i) => (
                    <a
                      key={i}
                      href={`#${h.id}`}
                      className={`artifact-toc-item level-${h.level}`}
                    >
                      {h.text}
                    </a>
                  ))}
                </div>
              </div>
            )}

            <div className="artifact-markdown">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
