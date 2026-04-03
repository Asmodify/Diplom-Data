export type BackendHealth = {
  status: string;
  version?: string;
  firebase: boolean;
  analyzer: boolean;
  advanced_analyzer: boolean;
  sheets: boolean;
};

export type BackendPost = {
  id: string;
  page_name: string;
  post_id: string;
  post_url?: string | null;
  content?: string | null;
  timestamp?: string | null;
  likes?: number;
  shares?: number;
  comment_count?: number;
  scraped_at?: string | null;
};

export type BackendStats = {
  total_posts: number;
  total_pages: number;
  total_comments: number;
  avg_likes: number;
  avg_shares: number;
  avg_comments: number;
  sentiment_distribution?: Record<string, number> | null;
};

export type LiveAdminPost = {
  id: string;
  platform: string;
  date: string;
  author: string;
  content: string;
  keywords: string[];
  engagement: number;
  likes: number;
  shares: number;
  commentCount: number;
};

const DEFAULT_BACKEND_BASE_URL = 'https://diplom-data-api.onrender.com';
const backendEnv = import.meta as ImportMeta & {
  env?: Record<string, string | undefined>;
};

export const backendBaseUrl = (
  backendEnv.env?.VITE_BACKEND_API_URL?.trim() || DEFAULT_BACKEND_BASE_URL
).replace(/\/+$/, '');

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 12000);

  try {
    const response = await fetch(`${backendBaseUrl}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(init?.headers ?? {}),
      },
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `Request failed with status ${response.status}`);
    }

    return (await response.json()) as T;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export async function getBackendHealth(): Promise<BackendHealth> {
  return requestJson<BackendHealth>('/health');
}

export async function getBackendStats(): Promise<BackendStats> {
  return requestJson<BackendStats>('/api/v1/stats');
}

export async function getBackendPosts(limit = 50): Promise<BackendPost[]> {
  return requestJson<BackendPost[]>(`/api/v1/posts?limit=${limit}`);
}

export function normalizeBackendPosts(posts: BackendPost[]): LiveAdminPost[] {
  return posts.map((post) => {
    const content = post.content?.trim() || 'No content available';
    const keywords = extractKeywords(content);
    const timestamp = post.timestamp || post.scraped_at || new Date().toISOString();

    return {
      id: post.id || post.post_id,
      platform: 'facebook',
      date: timestamp.slice(0, 10),
      author: post.page_name || 'Unknown page',
      content,
      keywords,
      engagement: (post.likes ?? 0) + (post.shares ?? 0) * 2 + (post.comment_count ?? 0),
      likes: post.likes ?? 0,
      shares: post.shares ?? 0,
      commentCount: post.comment_count ?? 0,
    };
  });
}

function extractKeywords(content: string): string[] {
  const tokens = content
    .toLowerCase()
    .match(/\b[a-zа-яөүё]{4,}\b/gi)
    ?.slice(0, 6) ?? [];

  return Array.from(new Set(tokens)).slice(0, 5);
}
