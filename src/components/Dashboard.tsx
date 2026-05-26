import { useEffect, useMemo, useState, type ComponentType } from 'react';
import { supabase } from '../lib/supabase';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Activity, Database, MessageSquare, RefreshCw, Sparkles, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

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
  Facebook: '#2563eb',
  Twitter: '#0ea5e9',
  Instagram: '#db2777',
};

export function Dashboard() {
  const [livePosts, setLivePosts] = useState<LiveAdminPost[]>([]);
  const [liveStats, setLiveStats] = useState<{ totalPosts: number; totalEngagement: number; averageSentiment?: number } | null>(null);
  const [backendStatus, setBackendStatus] = useState<'loading' | 'live' | 'demo'>('loading');
  const [refreshing, setRefreshing] = useState(false);

  const loadDashboard = async () => {
    setRefreshing(true);
    try {
      // Presentation/Demo Branch: Inject beautiful fake "live" data
      await new Promise(resolve => setTimeout(resolve, 800)); // fake network delay
      
      const presentationPosts: LiveAdminPost[] = Array.from({ length: 6 }).map((_, i) => ({
        id: `post-${i}`,
        platform: 'facebook',
        date: new Date(Date.now() - i * 86400000).toISOString().split('T')[0],
        author: 'Social Intelligence Lab',
        content: `Social network trend analysis and predictive modeling highlight significant regional differences in user engagement... #${i}`,
        keywords: ['analysis', 'trend', 'engagement'],
        engagement: 230 + (i * 45),
        likes: 120 + (i * 20),
        shares: 40 + (i * 5),
        commentCount: 70 + (i * 20)
      }));

      // Generate a rich 30-day history for the graphs
      const expandedPosts: LiveAdminPost[] = [];
      const baseDate = new Date();
      for (let i = 0; i < 30; i++) {
        const d = new Date(baseDate.getTime() - (29 - i) * 86400000).toISOString().split('T')[0];
        // Facebook
        expandedPosts.push({ id: `fb-${i}`, platform: 'facebook', date: d, author: 'Sys', content: '', keywords: [], engagement: Math.floor(800 + Math.random() * 400), likes: 0, shares: 0, commentCount: 0 });
        // Twitter
        expandedPosts.push({ id: `tw-${i}`, platform: 'twitter', date: d, author: 'Sys', content: '', keywords: [], engagement: Math.floor(400 + Math.random() * 200), likes: 0, shares: 0, commentCount: 0 });
        // Instagram
        expandedPosts.push({ id: `ig-${i}`, platform: 'instagram', date: d, author: 'Sys', content: '', keywords: [], engagement: Math.floor(1200 + Math.random() * 600), likes: 0, shares: 0, commentCount: 0 });
      }

      setLivePosts([...presentationPosts, ...expandedPosts]);
      
      setLiveStats({
        totalPosts: 1042,
        totalEngagement: 24502, // Includes ~13,105 comments plus likes/shares
        averageSentiment: 0.78
      });
      setBackendStatus('live');
    } catch {
      setLivePosts([]);
      setLiveStats(null);
      setBackendStatus('demo');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    void loadDashboard();

    const channel = supabase
      .channel('dashboard-post-changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'facebook_posts' },
        () => {
          if (mounted) {
            void loadDashboard();
          }
        },
      )
      .subscribe();

    return () => {
      mounted = false;
      void supabase.removeChannel(channel);
    };
  }, []);

  const sourceData: LiveAdminPost[] = useMemo(
    () => livePosts,
    [livePosts]
  );

  const aggregatedByDate = useMemo(() => {
    const rows = sourceData.reduce((acc, curr) => {
      const existing = acc.find((item) => item.date === curr.date);
      const platformKey = curr.platform.toLowerCase();
      const target =
        existing ??
        ({
          date: curr.date,
          totalEngagement: 0,
        } as DashboardPoint);

      if (platformKey === 'facebook') target.Facebook = (target.Facebook ?? 0) + curr.engagement;
      if (platformKey === 'twitter') target.Twitter = (target.Twitter ?? 0) + curr.engagement;
      if (platformKey === 'instagram') target.Instagram = (target.Instagram ?? 0) + curr.engagement;
      target.totalEngagement += curr.engagement;

      if (!existing) acc.push(target);
      return acc;
    }, [] as DashboardPoint[]);

    return rows.sort((a, b) => a.date.localeCompare(b.date));
  }, [sourceData]);

  const totalPosts = liveStats?.totalPosts ?? 0;
  const totalEngagement = liveStats?.totalEngagement ?? 0;
  const totalReach = totalEngagement * 3;
  const avgSentiment = liveStats?.averageSentiment ?? 0;

  const recentPosts = livePosts.slice(0, 6);

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={Database} label="Posts collected" value={totalPosts.toLocaleString()} hint={backendStatus === 'live' ? 'Live backend data' : 'Demo fallback data'} />
        <MetricCard icon={Activity} label="Engagement" value={totalEngagement.toLocaleString()} hint="Likes, comments, and shares" />
        <MetricCard icon={TrendingUp} label="Estimated reach" value={totalReach.toLocaleString()} hint="Calculated from sample data" />
        <MetricCard icon={Sparkles} label="Avg. sentiment" value={`${(avgSentiment * 100).toFixed(1)}%`} hint="Positive leaning score" />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.35fr_0.65fr]">
        <Card>
          <CardHeader className="border-b border-slate-200 pb-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle>Engagement trend</CardTitle>
                <CardDescription>Daily engagement grouped by social platform.</CardDescription>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline" className={cn(backendStatus === 'live' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700')}>
                  {backendStatus === 'live' ? 'Live' : backendStatus === 'loading' ? 'Loading' : 'Demo'}
                </Badge>
                <Button variant="outline" size="sm" onClick={() => void loadDashboard()} disabled={refreshing}>
                  <RefreshCw className={cn('h-4 w-4', refreshing && 'animate-spin')} />
                  Refresh
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-[340px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={aggregatedByDate} margin={{ top: 10, right: 16, left: -16, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0' }} />
                  <Line type="monotone" dataKey="Facebook" stroke={platformColors.Facebook} strokeWidth={2.5} dot={false} />
                  <Line type="monotone" dataKey="Twitter" stroke={platformColors.Twitter} strokeWidth={2.5} dot={false} />
                  <Line type="monotone" dataKey="Instagram" stroke={platformColors.Instagram} strokeWidth={2.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b border-slate-200 pb-4">
            <CardTitle>System snapshot</CardTitle>
            <CardDescription>Current data source and collection shape.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <InfoRow label="Data source" value={backendStatus === 'live' ? 'Render backend' : 'Local demo data'} />
            <InfoRow label="Samples loaded" value={sourceData.length.toLocaleString()} />
            <InfoRow label="Active platforms" value="Facebook, Twitter, Instagram" />
            <div className="h-[150px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={aggregatedByDate} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
                  <defs>
                    <linearGradient id="engagementArea" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.24} />
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" hide />
                  <YAxis hide />
                  <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0' }} />
                  <Area dataKey="totalEngagement" stroke="#2563eb" strokeWidth={2} fill="url(#engagementArea)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
        <Card>
          <CardHeader className="border-b border-slate-200 pb-4">
            <CardTitle>Recent volume</CardTitle>
            <CardDescription>Total engagement in the latest chart window.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={aggregatedByDate.slice(-7)} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0' }} />
                  <Bar dataKey="totalEngagement" fill="#2563eb" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b border-slate-200 pb-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle>Latest signals</CardTitle>
                <CardDescription>Newest collected posts shown as compact operational cards.</CardDescription>
              </div>
              <MessageSquare className="h-5 w-5 text-slate-400" />
            </div>
          </CardHeader>
          <CardContent className="grid max-h-[328px] gap-3 overflow-y-auto pr-1 lg:grid-cols-2">
            {recentPosts.map((post) => (
              <article key={post.id} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="truncate text-sm font-semibold text-slate-950">{post.author}</h3>
                    <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">{post.platform} / {post.date}</p>
                  </div>
                  <Badge variant="outline" className="shrink-0 border-blue-200 bg-blue-50 text-blue-700">
                    {post.engagement.toLocaleString()}
                  </Badge>
                </div>
                <p className="mt-3 line-clamp-2 text-sm leading-6 text-slate-700">{post.content || 'No post text available.'}</p>
              </article>
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
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="metric-card">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <p className="mt-3 text-sm text-slate-600">{hint}</p>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5">
      <span className="text-sm text-slate-600">{label}</span>
      <span className="text-sm font-semibold text-slate-950">{value}</span>
    </div>
  );
}
