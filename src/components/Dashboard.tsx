import { useEffect, useMemo, useState, type ComponentType } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  AreaChart,
  Area,
} from 'recharts';
import { Activity, Database, Sparkles, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { mockCollectedPosts, mockSocialData } from '../lib/mockData';
import { getBackendPosts, getBackendStats, normalizeBackendPosts, type LiveAdminPost } from '../lib/backend';
import { cn } from '../lib/utils';

type DashboardPoint = {
  date: string;
  Facebook?: number;
  Twitter?: number;
  Instagram?: number;
  totalEngagement: number;
};

const platformColors: Record<string, string> = {
  Facebook: '#22d3ee',
  Twitter: '#60a5fa',
  Instagram: '#f472b6',
};

export function Dashboard() {
  const [livePosts, setLivePosts] = useState<LiveAdminPost[]>([]);
  const [liveStats, setLiveStats] = useState<{ totalPosts: number; totalEngagement: number } | null>(null);
  const [backendStatus, setBackendStatus] = useState<'loading' | 'live' | 'demo'>('loading');

  useEffect(() => {
    let mounted = true;

    const loadDashboard = async () => {
      try {
        const [posts, stats] = await Promise.all([getBackendPosts(100), getBackendStats()]);

        if (!mounted) {
          return;
        }

        setLivePosts(normalizeBackendPosts(posts));
        setLiveStats({
          totalPosts: stats.total_posts,
          totalEngagement: posts.reduce(
            (sum, post) => sum + (post.likes ?? 0) + (post.shares ?? 0) * 2 + (post.comment_count ?? 0),
            0,
          ),
        });
        setBackendStatus('live');
      } catch {
        if (mounted) {
          setLivePosts([]);
          setLiveStats(null);
          setBackendStatus('demo');
        }
      }
    };

    void loadDashboard();

    return () => {
      mounted = false;
    };
  }, []);

  const sourceData: LiveAdminPost[] = livePosts.length > 0
    ? livePosts
    : mockSocialData.map((item) => ({
        id: `${item.platform}-${item.date}`,
        platform: item.platform.toLowerCase(),
        date: item.date,
        author: item.platform,
        content: '',
        keywords: [],
        engagement: item.engagement,
        likes: item.engagement,
        shares: 0,
        commentCount: 0,
      }));

  const aggregatedByDate = sourceData.reduce((acc, curr) => {
    const existing = acc.find((item) => item.date === curr.date);
    const platformKey = curr.platform.toLowerCase();

    if (existing) {
      if (platformKey === 'facebook') {
        existing.Facebook = (existing.Facebook ?? 0) + curr.engagement;
      }
      if (platformKey === 'twitter') {
        existing.Twitter = (existing.Twitter ?? 0) + curr.engagement;
      }
      if (platformKey === 'instagram') {
        existing.Instagram = (existing.Instagram ?? 0) + curr.engagement;
      }
      existing.totalEngagement += curr.engagement;
    } else {
      acc.push({
        date: curr.date,
        ...(platformKey === 'facebook' ? { Facebook: curr.engagement } : {}),
        ...(platformKey === 'twitter' ? { Twitter: curr.engagement } : {}),
        ...(platformKey === 'instagram' ? { Instagram: curr.engagement } : {}),
        totalEngagement: curr.engagement,
      });
    }

    return acc;
  }, [] as DashboardPoint[]);

  const totalPosts = liveStats?.totalPosts ?? mockSocialData.reduce((sum, item) => sum + item.posts, 0);
  const totalEngagement = liveStats?.totalEngagement ?? mockSocialData.reduce((sum, item) => sum + item.engagement, 0);
  const totalReach = mockSocialData.reduce((sum, item) => sum + item.reach, 0);
  const avgSentiment = mockSocialData.reduce((sum, item) => sum + item.sentiment, 0) / mockSocialData.length;
  const topSourceLabel = useMemo(
    () => (backendStatus === 'live' ? 'Live Render feed' : 'Local demo feed'),
    [backendStatus],
  );

  const recentPosts = (livePosts.length > 0 ? livePosts : mockCollectedPosts.map((post) => ({
    id: post.id,
    platform: post.platform,
    date: post.date,
    author: post.author,
    content: post.content,
    keywords: post.keywords,
    engagement: post.engagement,
    likes: post.engagement,
    shares: 0,
    commentCount: 0,
  }))).slice(0, 4);

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={Database} label="Нийт пост" value={totalPosts.toLocaleString()} hint={topSourceLabel} accent="cyan" />
        <MetricCard icon={Activity} label="Нийт идэвх" value={totalEngagement.toLocaleString()} hint="Backend synced metrics" accent="emerald" />
        <MetricCard icon={TrendingUp} label="Нийт хүртээмж" value={totalReach.toLocaleString()} hint="+15% өмнөх 7 хоногоос" accent="amber" />
        <MetricCard icon={Sparkles} label="Дундаж sentiment" value={`${(avgSentiment * 100).toFixed(1)}%`} hint="Trend confidence rising" accent="rose" />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.4fr_0.9fr]">
        <Card className="overflow-hidden border-cyan-400/15 bg-gradient-to-br from-slate-950/90 to-slate-900/60">
          <CardHeader className="flex flex-row items-center justify-between gap-4">
            <div>
              <CardTitle className="text-lg text-white">Trend line</CardTitle>
              <CardDescription>Платформ бүрийн идэвхжил ба нийлбэр trend.</CardDescription>
            </div>
            <Badge variant="default" className="bg-cyan-400/15 text-cyan-100 ring-cyan-400/30">{topSourceLabel}</Badge>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="h-[340px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={aggregatedByDate}>
                  <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="rgba(148,163,184,0.14)" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: '#020617', border: '1px solid rgba(148,163,184,0.18)', borderRadius: 16 }} />
                  <Legend />
                  <Line type="monotone" dataKey="Facebook" stroke={platformColors.Facebook} strokeWidth={2.5} dot={false} />
                  <Line type="monotone" dataKey="Twitter" stroke={platformColors.Twitter} strokeWidth={2.5} dot={false} />
                  <Line type="monotone" dataKey="Instagram" stroke={platformColors.Instagram} strokeWidth={2.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-5">
          <Card className="border-white/10 bg-white/[0.03]">
            <CardHeader>
              <CardTitle className="text-lg text-white">Operational snapshot</CardTitle>
              <CardDescription>Backend health and engagement pulse.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-300">Runtime mode</span>
                  <Badge variant={backendStatus === 'live' ? 'default' : 'secondary'}>
                    {backendStatus === 'live' ? 'Live' : 'Demo fallback'}
                  </Badge>
                </div>
                <div className="mt-3 h-2 rounded-full bg-slate-800">
                  <div className="h-2 w-[82%] rounded-full bg-gradient-to-r from-cyan-400 to-emerald-400" />
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-400">
                  Collecting, normalizing, and summarizing cross-platform posts in a single view.
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                <p className="text-sm text-slate-400">Average post velocity</p>
                <p className="mt-2 text-2xl font-semibold text-white">{mockSocialData.length} samples</p>
                <p className="mt-2 text-sm text-slate-500">Recent activity is concentrated on Instagram and Twitter.</p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                <p className="text-sm text-slate-400">Actionable readout</p>
                <p className="mt-2 text-sm leading-6 text-slate-200">
                  The current signal favors high engagement around civic and data-focused content, especially where sentiment is positive and visual material is present.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-white/[0.03]">
            <CardHeader>
              <CardTitle className="text-lg text-white">Momentum pulse</CardTitle>
              <CardDescription>Weekly total engagement trend.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[170px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={aggregatedByDate}>
                    <defs>
                      <linearGradient id="engagementFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.45} />
                        <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="rgba(148,163,184,0.14)" />
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: '#020617', border: '1px solid rgba(148,163,184,0.18)', borderRadius: 16 }} />
                    <Area type="monotone" dataKey="totalEngagement" stroke="#22d3ee" fill="url(#engagementFill)" strokeWidth={2.5} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="border-white/10 bg-white/[0.03]">
          <CardHeader>
            <CardTitle className="text-lg text-white">Platform mix</CardTitle>
            <CardDescription>Aggregated engagement per source.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={aggregatedByDate.slice(-5)}>
                  <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="rgba(148,163,184,0.14)" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: '#020617', border: '1px solid rgba(148,163,184,0.18)', borderRadius: 16 }} />
                  <Bar dataKey="totalEngagement" fill="#8b5cf6" radius={[14, 14, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/10 bg-white/[0.03]">
          <CardHeader>
            <CardTitle className="text-lg text-white">Recent signals</CardTitle>
            <CardDescription>High-value posts currently in the workspace.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {recentPosts.map((post) => (
              <div key={post.id} className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 transition-colors hover:border-cyan-400/30 hover:bg-slate-900/90">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-white">{post.author}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.28em] text-slate-500">{post.platform}</p>
                  </div>
                  <Badge variant="outline" className="border-cyan-400/20 text-cyan-100">
                    {post.engagement} engagement
                  </Badge>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{post.content || 'No content available'}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {post.keywords.slice(0, 4).map((keyword) => (
                    <span key={keyword} className="rounded-full bg-white/[0.05] px-3 py-1 text-xs text-slate-300">
                      #{keyword}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  hint,
  accent,
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: string;
  hint: string;
  accent: 'cyan' | 'emerald' | 'amber' | 'rose';
}) {
  const accentClasses = {
    cyan: 'from-cyan-400/20 to-cyan-400/5 text-cyan-200 ring-cyan-400/20',
    emerald: 'from-emerald-400/20 to-emerald-400/5 text-emerald-200 ring-emerald-400/20',
    amber: 'from-amber-400/20 to-amber-400/5 text-amber-200 ring-amber-400/20',
    rose: 'from-rose-400/20 to-rose-400/5 text-rose-200 ring-rose-400/20',
  } as const;

  return (
    <Card className="border-white/10 bg-white/[0.03]">
      <CardContent className="p-4">
        <div className={cn('rounded-2xl border bg-gradient-to-br p-4', accentClasses[accent])}>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] opacity-70">{label}</p>
              <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
            </div>
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-950/60 text-current ring-1 ring-inset ring-white/10">
              <Icon className="h-5 w-5" />
            </div>
          </div>
          <p className="mt-3 text-sm leading-6 opacity-80">{hint}</p>
        </div>
      </CardContent>
    </Card>
  );
}
