export interface StatusStep {
  stage: string;
  label: string;
  results?: Array<{ guest: string; title: string; url?: string; timestamp?: string }>;
}

export interface SourceCardItem {
  id?: string;
  guest: string;
  title?: string;
  company?: string;
  episodeNumber?: string;
  timestamp?: string;
  url?: string;
  avatarUrl?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  streaming?: boolean;
  statusSteps?: StatusStep[];
  sources?: SourceCardItem[];
  artifactData?: Artifact;
  liked?: boolean | null;
  bookmarked?: boolean;
}

export interface Artifact {
  content: string;
  type: "html" | "markdown";
  title: string;
  subtitle?: string;
  wordCount?: number;
  readTime?: number;
  heroImage?: string;
}

export interface Session {
  id: string;
  title: string;
  created_at?: string;
  timeLabel?: string;
  group?: "Today" | "Yesterday" | "Earlier";
}

export interface UserProfile {
  name: string;
  plan: string;
  status: "Online" | "Offline";
  avatarUrl?: string;
}
