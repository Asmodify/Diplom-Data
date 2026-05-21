import { useEffect, useMemo, useState, type ComponentType } from 'react';
import { supabase } from '../lib/supabase';
import { motion } from 'motion/react';
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
import { Activity, Database, Sparkles, TrendingUp, RefreshCw, Layers, CheckCircle } from 'lucide-react';
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
  Facebook: '#06b6d4', // Premium Cyan
  Twitter: '#3b82f6',  // Premium Blue
  Instagram: '#ec4899', // Premium Pink
};

export function Dashboard() {
  const [livePosts, setLivePosts] = useState<LiveAdminPost[]>([]);
  const [liveStats, setLiveStats] = useState<{ totalPosts: number; totalEngagement: number } | null>(null);
  const [backendStatus, setBackendStatus] = useState<'loading' | 'live' | 'demo'>('loading');
  const [refreshing, setRefreshing] = useState(false);

  const loadDashboard = async () => {
    setRefreshing(true);
    try {
      const [posts, stats] = await Promise.all([getBackendPosts(100), getBackendStats()]);

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
      setLivePosts([]);
      setLiveStats(null);
      setBackendStatus('demo');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    let mounted = true;

    const initLoad = async () => {
      if (mounted) {
        await loadDashboard();
      }
    };
    void initLoad();

    // Setup Supabase Realtime Subscription
    const channel = supabase
      .channel('schema-db-changes')
      .on(
        'postgres_changes',
        {
          event: '*', // Listen to INSERT, UPDATE, DELETE
          schema: 'public',
          table: 'facebook_posts',
        },
        () => {
          if (mounted) {
            void loadDashboard();
          }
        }
      )
      .subscribe();

    return () => {
      mounted = false;
      void supabase.removeChannel(channel);
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

  // Sort aggregated by date to ensure proper timeline charting
  aggregatedByDate.sort((a, b) => a.date.localeCompare(b.date));

  const totalPosts = liveStats?.totalPosts ?? mockSocialData.reduce((sum, item) => sum + item.posts, 0);
  const totalEngagement = liveStats?.totalEngagement ?? mockSocialData.reduce((sum, item) => sum + item.engagement, 0);
  const totalReach = mockSocialData.reduce((sum, item) => sum + item.reach, 0);
  const avgSentiment = mockSocialData.reduce((sum, item) => sum + item.sentiment, 0) / mockSocialData.length;
  
  const topSourceLabel = useMemo(
    () => (backendStatus === 'live' ? 'Бодит цагийн өгөгдөл' : 'Демо горим (Mock data)'),
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
  }))).slice(0, 5);

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 350, damping: 26 } },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* 4 Premium Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <motion.div variants={itemVariants}>
          <MetricCard 
            icon={Database} 
            label="Нийт цуглуулсан пост" 
            enLabel="Total Posts Ingested"
            value={totalPosts.toLocaleString()} 
            hint={topSourceLabel} 
            accent="purple" 
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard 
            icon={Activity} 
            label="Нийт харилцан үйлдэл" 
            enLabel="Total Engagement"
            value={totalEngagement.toLocaleString()} 
            hint="Пост идэвхжлийн нийлбэр" 
            accent="cyan" 
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard 
            icon={TrendingUp} 
            label="Нийт хүртээмж (Reach)" 
            enLabel="Total Reach"
            value={totalReach.toLocaleString()} 
            hint="+15.4% өмнөх долоо хоногоос" 
            accent="pink" 
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <MetricCard 
            icon={Sparkles} 
            label="Дундаж сэтгэл хөдлөл" 
            enLabel="Average Sentiment"
            value={`${(avgSentiment * 100).toFixed(1)}%`} 
            hint="Confidence confidence: High" 
            accent="indigo" 
          />
        </motion.div>
      </div>

      {/* Main Charts Area */}
      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        {/* Recharts Glass Card */}
        <motion.div variants={itemVariants} className="h-full">
          <Card className="h-full glass-card overflow-hidden shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between gap-4 border-b border-slate-200/50 pb-4">
              <div>
                <CardTitle className="text-lg font-bold text-slate-900">Идэвхжлийн өсөлтийн тренд</CardTitle>
                <CardDescription className="text-xs text-slate-400">Платформ тус бүрийн сүүлийн өдрүүдийн харилцан үйлдэл.</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => void loadDashboard()} 
                  disabled={refreshing}
                  className="bg-white/60 border-slate-200 text-slate-600 gap-1.5 h-8"
                >
                  <RefreshCw className={cn("h-3.5 w-3.5", refreshing && "animate-spin")} />
                  Шинэчлэх
                </Button>
                <Badge variant="secondary" className="bg-purple-100 text-purple-700 font-semibold border-purple-200 text-[10px]">
                  {backendStatus === 'live' ? 'Live backend' : 'Demo Mode'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="h-[360px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={aggregatedByDate} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.04)" />
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dy={8} />
                    <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dx={-8} />
                    <Tooltip
                      contentStyle={{
                        background: 'rgba(255, 255, 255, 0.88)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(168, 85, 247, 0.15)',
                        borderRadius: 16,
                        boxShadow: '0 12px 30px rgba(168, 85, 247, 0.05)',
                        color: '#1e293b',
                        fontSize: 12
                      }}
                    />
                    <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                    <Line type="monotone" dataKey="Facebook" name="Facebook" stroke={platformColors.Facebook} strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                    <Line type="monotone" dataKey="Twitter" name="Twitter / X" stroke={platformColors.Twitter} strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                    <Line type="monotone" dataKey="Instagram" name="Instagram" stroke={platformColors.Instagram} strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Snapshot Summary Columns */}
        <motion.div variants={itemVariants} className="space-y-6">
          {/* Diagnostic status */}
          <Card className="glass-card shadow-sm">
            <CardHeader className="border-b border-slate-200/50 pb-4">
              <CardTitle className="text-base font-bold text-slate-900">Шуурхай мэдээлэл</CardTitle>
              <CardDescription className="text-xs text-slate-400">Системийн өгөгдлийн статус болон хурд.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              <div className="rounded-2xl border border-slate-200 bg-white/40 p-4">
                <div className="flex items-center justify-between text-xs sm:text-sm font-semibold">
                  <span className="text-slate-600">Backend холболт</span>
                  <Badge variant={backendStatus === 'live' ? 'default' : 'secondary'} className={cn(
                    backendStatus === 'live' ? 'bg-emerald-100 text-emerald-700 border-emerald-200' : 'bg-amber-100 text-amber-700 border-amber-200'
                  )}>
                    {backendStatus === 'live' ? 'Хэвийн' : 'Демо горим'}
                  </Badge>
                </div>
                <div className="mt-3.5 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: backendStatus === 'live' ? '100%' : '50%' }}
                    transition={{ duration: 1 }}
                    className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full" 
                  />
                </div>
                <p className="mt-3 text-[11px] leading-relaxed text-slate-400">
                  Сошиал сувгуудын скрапинг болон мэдээллийн нэгтгэлийг тасралтгүй хийж, анализатор руу дамжуулж байна.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white/40 p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.1em] text-slate-400">Дундаж өгөгдлийн давтамж</p>
                <p className="mt-1 text-xl font-bold text-slate-800">{sourceData.length} Сорьц цугларсан</p>
                <p className="mt-1 text-xs text-slate-500">Сүүлийн идэвхжилүүд Instagram болон Twitter сувгууд дээр түлхүү төвлөрлөө.</p>
              </div>
            </CardContent>
          </Card>

          {/* Area Metric Chart Card */}
          <Card className="glass-card shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-200/50">
              <CardTitle className="text-sm font-bold text-slate-900">Идэвхжлийн өсөлтийн хурдац</CardTitle>
              <CardDescription className="text-xs text-slate-400">Долоо хоногийн харилцан үйлдэл.</CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="h-[140px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={aggregatedByDate} margin={{ top: 5, right: 0, left: -25, bottom: 0 }}>
                    <defs>
                      <linearGradient id="engagementFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.03)" />
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: 'rgba(255, 255, 255, 0.9)',
                        backdropFilter: 'blur(16px)',
                        border: '1px solid rgba(139, 92, 246, 0.15)',
                        borderRadius: 12,
                        boxShadow: '0 8px 24px rgba(139, 92, 246, 0.05)',
                        fontSize: 11
                      }}
                    />
                    <Area type="monotone" dataKey="totalEngagement" name="Нийт идэвх" stroke="#8b5cf6" fill="url(#engagementFill)" strokeWidth={2.5} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* BarChart & Live Post Signals Feed Grid */}
      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        {/* platform distribution bar chart */}
        <motion.div variants={itemVariants} className="h-full">
          <Card className="h-full glass-card shadow-sm">
            <CardHeader className="border-b border-slate-200/50 pb-4">
              <CardTitle className="text-lg font-bold text-slate-900">Платформын харьцуулалт</CardTitle>
              <CardDescription className="text-xs text-slate-400">Сүүлийн хугацааны нийт идэвхжилийн тоо хэмжээ.</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="h-[310px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={aggregatedByDate.slice(-6)} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.03)" />
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dy={5} />
                    <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dx={-5} />
                    <Tooltip
                      contentStyle={{
                        background: 'rgba(255, 255, 255, 0.9)',
                        backdropFilter: 'blur(16px)',
                        border: '1px solid rgba(139, 92, 246, 0.15)',
                        borderRadius: 12,
                        boxShadow: '0 8px 24px rgba(139, 92, 246, 0.05)'
                      }}
                    />
                    <Bar dataKey="totalEngagement" name="Нийт идэвх" fill="#6366f1" radius={[8, 8, 0, 0]} barSize={32} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Live signals scrolling panel */}
        <motion.div variants={itemVariants}>
          <Card className="h-full glass-card shadow-sm">
            <CardHeader className="border-b border-slate-200/50 pb-4 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg font-bold text-slate-900">Сүүлийн өгөгдлийн дохио (Signals)</CardTitle>
                <CardDescription className="text-xs text-slate-400">Системд хамгийн сүүлд бүртгэгдсэн сошиал постууд.</CardDescription>
              </div>
              <Badge variant="outline" className="bg-indigo-50 border-indigo-200 text-indigo-700 animate-pulse text-[10px] py-0.5 px-2">
                Live Feed Pulse
              </Badge>
            </CardHeader>
            <CardContent className="space-y-4 pt-4 max-h-[340px] overflow-y-auto pr-2">
              {recentPosts.map((post) => (
                <div 
                  key={post.id} 
                  className="rounded-2xl border border-slate-200 bg-white/40 p-4 transition-all duration-300 hover:border-purple-200 hover:bg-white/80 hover:shadow-sm"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-bold text-slate-800">{post.author}</p>
                      <div className="mt-1 flex items-center gap-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{post.platform}</span>
                        <span className="text-slate-300">•</span>
                        <span className="text-[10px] text-slate-400">{post.date}</span>
                      </div>
                    </div>
                    <Badge variant="outline" className="border-purple-200 bg-purple-50 text-purple-700 text-[10px] py-0.5 px-2.5">
                      {post.engagement.toLocaleString()} engagement
                    </Badge>
                  </div>
                  <p className="mt-2.5 text-xs sm:text-sm leading-relaxed text-slate-600 line-clamp-2">
                    {post.content || 'Постын үндсэн текст хоосон байна.'}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {post.keywords.slice(0, 4).map((keyword) => (
                      <span key={keyword} className="rounded-full bg-slate-100 border border-slate-200 px-2 py-0.5 text-[10px] font-semibold text-slate-500 hover:bg-slate-200 transition-colors">
                        #{keyword}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  );
}

interface MetricCardProps {
  icon: ComponentType<{ className?: string }>;
  label: string;
  enLabel: string;
  value: string;
  hint: string;
  accent: 'purple' | 'cyan' | 'pink' | 'indigo';
}

function MetricCard({
  icon: Icon,
  label,
  enLabel,
  value,
  hint,
  accent,
}: MetricCardProps) {
  const accentConfig = {
    purple: {
      card: 'bg-gradient-to-br from-purple-500/5 to-purple-500/0 border-purple-200/60 shadow-purple-500/5',
      badge: 'bg-purple-100 text-purple-600 border-purple-200/50',
      text: 'text-purple-600'
    },
    cyan: {
      card: 'bg-gradient-to-br from-cyan-500/5 to-cyan-500/0 border-cyan-200/60 shadow-cyan-500/5',
      badge: 'bg-cyan-100 text-cyan-600 border-cyan-200/50',
      text: 'text-cyan-600'
    },
    pink: {
      card: 'bg-gradient-to-br from-pink-500/5 to-pink-500/0 border-pink-200/60 shadow-pink-500/5',
      badge: 'bg-pink-100 text-pink-600 border-pink-200/50',
      text: 'text-pink-600'
    },
    indigo: {
      card: 'bg-gradient-to-br from-indigo-500/5 to-indigo-500/0 border-indigo-200/60 shadow-indigo-500/5',
      badge: 'bg-indigo-100 text-indigo-600 border-indigo-200/50',
      text: 'text-indigo-600'
    },
  };

  const style = accentConfig[accent];

  return (
    <Card className={cn("glass-card shadow-sm overflow-hidden border", style.card)}>
      <CardContent className="p-5">
        <div className="flex items-center justify-between gap-4">
          <div className="space-y-1">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">{label}</p>
            <p className="text-2xl font-bold text-slate-800 tracking-tight">{value}</p>
          </div>
          <div className={cn('flex h-11 w-11 items-center justify-center rounded-2xl border shadow-inner', style.badge)}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
        <div className="mt-3 flex items-center justify-between border-t border-slate-200/30 pt-2.5">
          <span className="text-[10px] font-semibold text-slate-400 tracking-wide line-clamp-1">{enLabel}</span>
          <span className="text-[10px] font-bold text-slate-500 line-clamp-1">{hint}</span>
        </div>
      </CardContent>
    </Card>
  );
}
