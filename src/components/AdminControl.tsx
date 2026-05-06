import { useEffect, useMemo, useState, type ComponentType } from 'react';
import {
  Activity,
  Database,
  RefreshCw,
  Search,
  ServerCog,
  ShieldCheck,
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { mockCollectedPosts, type MockCollectedPost } from '../lib/mockData';
import { cn } from '../lib/utils';
import {
  getBackendHealth,
  getBackendPosts,
  getBackendStats,
  normalizeBackendPosts,
  type BackendHealth,
  type BackendStats,
  type LiveAdminPost,
} from '../lib/backend';

export function AdminControl() {
  const [controls, setControls] = useState({
    scrapingEnabled: true,
    aiAnalysisEnabled: true,
    apiAccessEnabled: true,
    autoSyncEnabled: false,
  });

  const [limits, setLimits] = useState({
    maxPostsPerRun: '100',
    maxCommentsPerPost: '50',
    scrapeIntervalMinutes: '30',
  });

  const [collectionQuery, setCollectionQuery] = useState({
    platform: 'facebook',
    keywords: '',
    startDate: '',
    endDate: '',
    lastRunSummary: '',
  });

  const [queryResults, setQueryResults] = useState<LiveAdminPost[]>([]);
  const [backendHealth, setBackendHealth] = useState<BackendHealth | null>(null);
  const [backendStats, setBackendStats] = useState<BackendStats | null>(null);
  const [livePosts, setLivePosts] = useState<LiveAdminPost[]>([]);
  const [backendStatus, setBackendStatus] = useState('Connecting to Render backend...');
  const [backendBusy, setBackendBusy] = useState(true);
  const [backendBusy, setBackendBusy] = useState(true);

  useEffect(() => {
    let mounted = true;

    const loadBackendSnapshot = async () => {
      setBackendBusy(true);
      try {
        const [healthResult, statsResult, postsResult] = await Promise.allSettled([
          getBackendHealth(),
          getBackendStats(),
          getBackendPosts(50),
        ]);

        if (!mounted) {
          return;
        }

        if (healthResult.status === 'fulfilled') {
          setBackendHealth(healthResult.value);
        }

        if (statsResult.status === 'fulfilled') {
          setBackendStats(statsResult.value);
        }

        if (postsResult.status === 'fulfilled') {
          setLivePosts(normalizeBackendPosts(postsResult.value));
          setBackendStatus(`Connected to Render backend: ${postsResult.value.length} live posts loaded.`);
        } else {
          setLivePosts([]);
          setBackendStatus('Render backend is unreachable. Check VITE_BACKEND_API_URL and Render logs.');
        }

        if (healthResult.status === 'rejected' && statsResult.status === 'rejected') {
          setBackendStatus(`Backend sync degraded: ${String(healthResult.status === 'rejected' ? healthResult.reason : statsResult.reason)}`);
        }
      } finally {
        if (mounted) {
          setBackendBusy(false);
        }
      }
    };

    void loadBackendSnapshot();

    return () => {
      mounted = false;
    };
  }, []);

  const visiblePosts = useMemo(() => {
    return livePosts.length > 0
      ? livePosts
      : mockCollectedPosts.map((post) => ({
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
        }));
  }, [livePosts]);

  const toggleControl = (key: keyof typeof controls) => {
    setControls((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const runCollectionQuery = () => {
    const keywordList = collectionQuery.keywords
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
      .map((item) => item.toLowerCase());

    const filtered = visiblePosts.filter((post) => {
      const platformOk =
        !collectionQuery.platform ||
        collectionQuery.platform.toLowerCase() === 'all' ||
        post.platform === collectionQuery.platform.toLowerCase();

      const startOk = !collectionQuery.startDate || post.date >= collectionQuery.startDate;
      const endOk = !collectionQuery.endDate || post.date <= collectionQuery.endDate;

      const postSearchText = `${post.author} ${post.content} ${post.keywords.join(' ')}`.toLowerCase();
      const keywordOk = keywordList.length === 0 || keywordList.some((keyword) => postSearchText.includes(keyword));

      return platformOk && startOk && endOk && keywordOk;
    });

    const summary = [
      `Platform: ${collectionQuery.platform || 'not set'}`,
      `Keywords: ${keywordList.length > 0 ? keywordList.join(', ') : 'none'}`,
      `Date range: ${collectionQuery.startDate || 'any'} -> ${collectionQuery.endDate || 'any'}`,
      `Matched posts: ${filtered.length}`,
    ].join(' | ');

    setQueryResults(filtered);
    setCollectionQuery((prev) => ({
      ...prev,
      lastRunSummary: summary,
    }));
  };

  const refreshBackendSnapshot = async () => {
    setBackendBusy(true);
    try {
      const [health, stats, posts] = await Promise.all([
        getBackendHealth(),
        getBackendStats(),
        getBackendPosts(50),
      ]);

      setBackendHealth(health);
      setBackendStats(stats);
      setLivePosts(normalizeBackendPosts(posts));
      setBackendStatus(`Connected to Render backend: ${posts.length} live posts loaded.`);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setBackendStatus(`Backend refresh failed: ${message}`);
    } finally {
      setBackendBusy(false);
    }
  };

  const visibleSummary = [
    { title: 'Backend status', value: backendHealth?.status ?? 'unknown', hint: backendHealth?.version ? `v${backendHealth.version}` : 'Render API', icon: ServerCog },
    { title: 'Live posts', value: String(backendStats?.total_posts ?? visiblePosts.length), hint: 'Pulled from scraper database', icon: Database },
    { title: 'Firebase', value: backendHealth?.firebase ? 'Connected' : 'Offline', hint: 'Admin logs via Firestore', icon: ShieldCheck },
    { title: 'Frontend API', value: 'Vercel-ready', hint: backendStatus, icon: Activity },
  ] as const;

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/70">Admin</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Админ хяналтын хуудас</h2>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-300">
            Системийн урсгал, API эрх, AI анализ, өгөгдөл цуглуулалтын хязгааруудыг нэг төвөөс удирдана.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant={backendHealth?.firebase ? 'default' : 'secondary'} className={backendHealth?.firebase ? 'bg-emerald-400/15 text-emerald-100 ring-emerald-400/20' : ''}>
            {backendHealth?.firebase ? 'Render + Firebase live' : 'Backend syncing'}
          </Badge>
          <Badge variant="outline">{backendBusy ? 'Refreshing' : 'Ready'}</Badge>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {visibleSummary.map((item) => (
          <SummaryCard title={item.title} value={item.value} hint={item.hint} icon={item.icon} />
        ))}
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="flex flex-wrap gap-2 bg-transparent p-0">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="limits">Хязгаар</TabsTrigger>
          <TabsTrigger value="collect">Түлхүүр үг хайлт</TabsTrigger>
          <TabsTrigger value="ops">Үйл ажиллагаа</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-5 xl:grid-cols-[1fr_0.95fr]">
            <Card className="border-white/10 bg-white/[0.03]">
              <CardHeader>
                <CardTitle className="text-lg text-white">Core control switches</CardTitle>
                <CardDescription>Гол модуль бүрийн идэвхийг шууд удирдах хэсэг.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-2">
                <ToggleRow
                  label="Скрапинг ажиллуулах"
                  description="Scraper модулийг ажиллуулах/зогсоох"
                  enabled={controls.scrapingEnabled}
                  onToggle={() => toggleControl('scrapingEnabled')}
                />
                <ToggleRow
                  label="AI анализ"
                  description="Predictive, emotion, topic, network анализ"
                  enabled={controls.aiAnalysisEnabled}
                  onToggle={() => toggleControl('aiAnalysisEnabled')}
                />
                <ToggleRow
                  label="API хандалт"
                  description="REST endpoint-уудыг нээх/хаах"
                  enabled={controls.apiAccessEnabled}
                  onToggle={() => toggleControl('apiAccessEnabled')}
                />
                <ToggleRow
                  label="Auto Cloud Sync"
                  description="Firebase sync урсгал"
                  enabled={controls.autoSyncEnabled}
                  onToggle={() => toggleControl('autoSyncEnabled')}
                />
              </CardContent>
            </Card>

            <Card className="border-cyan-400/15 bg-gradient-to-br from-cyan-400/10 to-slate-900/70">
              <CardHeader>
                <CardTitle className="text-lg text-white">Live backend sync</CardTitle>
                <CardDescription>Render дээрх scraper API болон Firebase холболтыг шалгана.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4 text-sm text-slate-300">
                  {backendStatus}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button onClick={refreshBackendSnapshot} disabled={backendBusy} className="gap-2">
                    <RefreshCw className="h-4 w-4" />
                    Refresh live backend
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="limits" className="space-y-4">
          <Card className="border-white/10 bg-white/[0.03]">
            <CardHeader>
              <CardTitle className="text-lg text-white">Data collection limits</CardTitle>
              <CardDescription>Системийн нөөц болон API тогтвортой ажиллагаанд зориулсан хязгаарууд.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-3">
              <LimitField
                label="Run бүрийн пост"
                value={limits.maxPostsPerRun}
                onChange={(value) => setLimits((prev) => ({ ...prev, maxPostsPerRun: value }))}
              />
              <LimitField
                label="Пост бүрийн сэтгэгдэл"
                value={limits.maxCommentsPerPost}
                onChange={(value) => setLimits((prev) => ({ ...prev, maxCommentsPerPost: value }))}
              />
              <LimitField
                label="Скрап интервал (минут)"
                value={limits.scrapeIntervalMinutes}
                onChange={(value) => setLimits((prev) => ({ ...prev, scrapeIntervalMinutes: value }))}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="collect" className="space-y-4">
          <Card className="border-white/10 bg-white/[0.03]">
            <CardHeader>
              <CardTitle className="text-lg text-white">Keyword + date collection query</CardTitle>
              <CardDescription>Платформ, түлхүүр үг болон хугацааны муж оруулж query бэлдэнэ.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <p className="text-sm font-medium text-slate-200">Platform</p>
                  <Input
                    placeholder="facebook / twitter / instagram"
                    value={collectionQuery.platform}
                    onChange={(event) =>
                      setCollectionQuery((prev) => ({ ...prev, platform: event.target.value }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-medium text-slate-200">Keywords</p>
                  <Input
                    placeholder="AI, data science, election"
                    value={collectionQuery.keywords}
                    onChange={(event) =>
                      setCollectionQuery((prev) => ({ ...prev, keywords: event.target.value }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-medium text-slate-200">Start Date</p>
                  <Input
                    type="date"
                    value={collectionQuery.startDate}
                    onChange={(event) =>
                      setCollectionQuery((prev) => ({ ...prev, startDate: event.target.value }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-medium text-slate-200">End Date</p>
                  <Input
                    type="date"
                    value={collectionQuery.endDate}
                    onChange={(event) =>
                      setCollectionQuery((prev) => ({ ...prev, endDate: event.target.value }))
                    }
                  />
                </div>
              </div>

              <Button onClick={runCollectionQuery} className="gap-2">
                <Search className="h-4 w-4" />
                Run query
              </Button>

              <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-sm text-slate-300">
                <p>{collectionQuery.lastRunSummary || 'No query has been executed yet.'}</p>
              </div>

              <div className="grid gap-3 lg:grid-cols-2">
                {queryResults.slice(0, 4).map((post) => (
                  <div key={post.id} className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-white">{post.author}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.28em] text-slate-500">{post.platform}</p>
                      </div>
                      <Badge variant="outline" className="border-cyan-400/20 text-cyan-100">
                        {post.engagement} engagement
                      </Badge>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slate-300">{post.content}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ops" className="space-y-4">
          <div className="grid gap-5 xl:grid-cols-1">
            <Card className="border-white/10 bg-white/[0.03]">
              <CardHeader>
                <CardTitle className="text-lg text-white">Backend health</CardTitle>
                <CardDescription>Live status snapshot from Render and local fallback.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <MiniInfo label="Status" value={backendHealth?.status ?? 'unknown'} />
                  <MiniInfo label="Version" value={backendHealth?.version ?? 'n/a'} />
                  <MiniInfo label="Firebase" value={backendHealth?.firebase ? 'Connected' : 'Offline'} />
                  <MiniInfo label="Analyzer" value={backendHealth?.analyzer ? 'Enabled' : 'Disabled'} />
                </div>
                <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4 text-sm text-slate-300">
                  {backendStatus}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ToggleRow({
  label,
  description,
  enabled,
  onToggle,
}: {
  label: string;
  description: string;
  enabled: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={cn(
        'w-full rounded-2xl border p-4 text-left transition-colors',
        enabled ? 'border-cyan-400/30 bg-cyan-400/10' : 'border-white/10 bg-slate-950/40 hover:border-white/20',
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-white">{label}</p>
          <p className="mt-1 text-sm leading-6 text-slate-400">{description}</p>
        </div>
        <Badge variant={enabled ? 'default' : 'outline'} className={enabled ? 'bg-emerald-400/15 text-emerald-100 ring-emerald-400/20' : ''}>
          {enabled ? 'On' : 'Off'}
        </Badge>
      </div>
    </button>
  );
}

function LimitField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-2 rounded-2xl border border-white/10 bg-slate-950/50 p-4">
      <p className="text-sm font-medium text-slate-100">{label}</p>
      <Input value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function MiniInfo({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
      <p className="text-xs uppercase tracking-[0.25em] text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-medium text-white">{value}</p>
    </div>
  );
}

interface SummaryCardProps {
  title: string;
  value: string;
  hint: string;
  icon: ComponentType<{ className?: string }>;
}

function SummaryCard({
  title,
  value,
  hint,
  icon: Icon,
}: SummaryCardProps) {
  return (
    <Card className="border-white/10 bg-white/[0.03]">
      <CardContent className="flex items-center justify-between gap-4 p-5">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{title}</p>
          <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
          <p className="mt-2 text-sm text-slate-400">{hint}</p>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-400/12 text-cyan-200 ring-1 ring-inset ring-cyan-400/20">
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}
