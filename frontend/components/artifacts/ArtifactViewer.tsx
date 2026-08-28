"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Sparkles, Maximize2, Download, X, Copy, Check } from "lucide-react";
import { Artifact } from "@/lib/types";

interface ArtifactViewerProps {
  artifact: Artifact;
  onClose: () => void;
}

export function ArtifactViewer({ artifact, onClose }: ArtifactViewerProps) {
  const [mode, setMode] = useState<"preview" | "source">("preview");
  const [copied, setCopied] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (artifact.type === "html" && mode === "preview" && iframeRef.current) {
      const doc = iframeRef.current.contentDocument;
      if (doc) {
        doc.open();
        doc.write(artifact.content);
        doc.close();
      }
    }
  }, [artifact, mode]);

  // Sanitize content by stripping any residual XML artifact tags
  const cleanContent = (artifact.content || "")
    .replace(/<artifact[^>]*>/gi, "")
    .replace(/<\/artifact>/gi, "")
    .trim();

  const wordCount = cleanContent
    ? cleanContent.split(/\s+/).length
    : 1280;

  const handleCopy = () => {
    navigator.clipboard.writeText(cleanContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const ext = artifact.type === "html" ? "html" : "md";
    const blob = new Blob([cleanContent], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(artifact.title || "artifact").replace(/\s+/g, "_").toLowerCase()}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="artifact-viewer-panel">
      {/* Header */}
      <div className="artifact-panel-header">
        <div className="artifact-header-title">
          <Sparkles size={16} style={{ color: "#a78bfa" }} />
          <span>Artifact Viewer</span>
        </div>

        <div className="artifact-header-right">
          <div className="preview-source-toggle">
            <button
              className={`toggle-tab ${mode === "preview" ? "active" : ""}`}
              onClick={() => setMode("preview")}
            >
              Preview
            </button>
            <button
              className={`toggle-tab ${mode === "source" ? "active" : ""}`}
              onClick={() => setMode("source")}
            >
              Source
            </button>
          </div>

          <button className="artifact-control-btn" title="Expand View">
            <Maximize2 size={14} />
          </button>
          <button className="artifact-control-btn" onClick={handleDownload} title="Download">
            <Download size={14} />
          </button>
          <button className="artifact-control-btn" onClick={onClose} title="Close Panel">
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Main Document / Preview Area */}
      <div className="artifact-document-scroll">
        {mode === "source" ? (
          <div style={{ background: "#090812", color: "#f8fafc", padding: 20, borderRadius: 12, fontSize: 13, fontFamily: "monospace", minHeight: "100%", whiteSpace: "pre-wrap" }}>
            {cleanContent}
          </div>
        ) : artifact.type === "html" ? (
          <iframe
            ref={iframeRef}
            className="artifact-iframe"
            sandbox="allow-scripts"
            title="Artifact Preview"
          />
        ) : (
          <div className="artifact-doc-card">
            <div className="artifact-tag">SHIP 30 FOR 30 ESSAY</div>

            <h1 className="artifact-doc-h1">
              {artifact.title || "Ship 30 for 30 Essay"}
            </h1>

            <p className="artifact-doc-subtitle">
              {artifact.subtitle || "Grounded insights & framework synthesized from Lenny's Podcast transcripts."}
            </p>

            {/* Rendered Editorial Markdown Body */}
            <div className="artifact-editorial-body">
              <ReactMarkdown>{cleanContent}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>

      {/* Sticky Footer */}
      <div className="artifact-footer-sticky">
        <div className="artifact-footer-meta">
          <span>Type: {artifact.type === "html" ? "HTML" : "Markdown"}</span>
          <span>·</span>
          <span>~{wordCount.toLocaleString()} words</span>
          <span>·</span>
          <span>Generated just now</span>
        </div>

        <button className="artifact-copy-btn" onClick={handleCopy}>
          {copied ? "Copied!" : "Copy to Clipboard"}
        </button>
      </div>
    </div>
  );
}
