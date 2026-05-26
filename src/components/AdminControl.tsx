import { useEffect, useMemo, useState, type ComponentType } from 'react';
import { Activity, Database, RefreshCw, Search, ServerCog, ShieldCheck } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { mockCollectedPosts } from '../lib/mockData';
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
  const [backendStatus, setBackendStatus] = useState('Connecting to backend...');
  const [backendBusy, setBackendBusy] = useState(true);

  const loadBackendSnapshot = async () => {
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
      setBackendStatus(`Connected. Loaded ${posts.length} recent posts from the backend.`);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setLivePosts([]);
      setBackendStatus(`Backend unavailable. Showing demo records. ${message}`);
    } finally {
      setBackendBusy(false);
    }
  };

  useEffect(() => {
    void loadBackendSnapshot();
  }, []);

  const visiblePosts = useMemo(
    () =>
      livePosts.length > 0
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
          })),
    [livePosts],
  );

  const toggleControl = (key: keyof typeof controls) => {
    setControls((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const runCollectionQuery = () => {
    const keywordList = collectionQuery.keywords
      .split(',')
      .map((item) => item.trim().toLowerCase())
      .filter(Boolean);

    const filtered = visiblePosts.filter((post) => {
      const platformOk =
        !collectionQuery.platform ||
        collectionQuery.platform.toLowerCase() === 'all' ||
        post.platform === collectionQuery.platform.toLowerCase();
      const startOk = !collectionQuery.startDate || post.date >= collectionQuery.startDate;
      const endOk = !collectionQuery.endDate || post.date <= collectionQuery.endDate;
      const searchText = `${post.author} ${post.content} ${post.keywords.join(' ')}`.toLowerCase();
      const keywordOk = keywordList.length === 0 || keywordList.some((keyword) => searchText.includes(keyword));
      return platformOk && startOk && endOk && keywordOk;
    });

    setQueryResults(filtered);
    setCollectionQuery((prev) => ({
      ...prev,
      lastRunSummary: `${filtered.length} posts matched / platform ${prev.platform || 'any'} / keywords ${keywordList.join(', ') || 'none'}`,
    }));
  };

  const visibleSummary = [
    { title: 'Backend төлөв', value: backendHealth?.status ?? (backendBusy ? 'checking' : 'offline'), hint: backendHealth?.version ? `v${backendHealth.version}` : 'Render API', icon: ServerCog },
    { title: 'Бодит постууд', value: String(backendStats?.total_posts ?? visiblePosts.length), hint: 'Scraper баазын бичлэгүүд', icon: Database },
    { title: 'Хадгалалт', value: backendHealth?.firebase ? 'Connected' : 'Нөөц', hint: 'Firebase/Supabase нэгтгэл', icon: ShieldCheck },
    { title: 'Фронтенд', value: 'Ready', hint: backendBusy ? 'Төлөвийг шинэчилж байна' : 'Статик Vite хувилбар', icon: Activity },
  ] as const;

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {visibleSummary.map((item) => (
          <SummaryCard key={item.title} title={item.title} value={item.value} hint={item.hint} icon={item.icon} />
        ))}
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="flex flex-wrap gap-2 rounded-lg border border-slate-200 bg-white p-1">
          <TabsTrigger value="overview">Тойм</TabsTrigger>
          <TabsTrigger value="limits">Хязгаарууд</TabsTrigger>
          <TabsTrigger value="collect">Хайлт</TabsTrigger>
          <TabsTrigger value="ops">Журмууд</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-5 xl:grid-cols-[1fr_0.95fr]">
            <Card>
              <CardHeader className="border-b border-slate-200 pb-4">
                <CardTitle>Удирдлагын тохируулга</CardTitle>
                <CardDescription>Гол системийн модулиудын хөтөч дээрх удирдлага.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-2">
                <ToggleRow label="Цуглуулах" description="Автоматжуулсан цуглуулах ажлуудыг ажиллахыг зөвшөөрөх." enabled={controls.scrapingEnabled} onToggle={() => toggleControl('scrapingEnabled')} />
                <ToggleRow label="AI Шинжилгээ" description="Урьдчилан таамаглах болон текст шинжилгээний функцуудыг идэвхжүүлэх." enabled={controls.aiAnalysisEnabled} onToggle={() => toggleControl('aiAnalysisEnabled')} />
                <ToggleRow label="API хандалт" description="Хамгаалагдсан REST цэгүүдийг нээлттэй байлгах." enabled={controls.apiAccessEnabled} onToggle={() => toggleControl('apiAccessEnabled')} />
                <ToggleRow label="Автомат синхрончлол" description="Цуглуулсан өгөгдлийг үүлэн хадгалалттай синхрончлох." enabled={controls.autoSyncEnabled} onToggle={() => toggleControl('autoSyncEnabled')} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="border-b border-slate-200 pb-4">
                <CardTitle>Backend синхрончлол</CardTitle>
                <CardDescription>Холбогдсон API-н эрүүл мэнд болон өгөгдлийн төлөв.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-700">
                  {backendStatus}
                </div>
                <Button onClick={loadBackendSnapshot} disabled={backendBusy} variant="outline">
                  <RefreshCw className={cn('h-4 w-4', backendBusy && 'animate-spin')} />
                  Refresh backend
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="limits">
          <Card>
            <CardHeader className="border-b border-slate-200 pb-4">
              <CardTitle>Цуглуулах хязгаар</CardTitle>
              <CardDescription>Цуглуулах болон API ачааллыг хянахын тулд ашиглагддаг үйл ажиллагааны хязгаар.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-3">
              <LimitField label="Нэг удаагийн гүйлт дэх пост" value={limits.maxPostsPerRun} onChange={(value) => setLimits((prev) => ({ ...prev, maxPostsPerRun: value }))} />
              <LimitField label="Пост тус бүрийн сэтгэгдэл" value={limits.maxCommentsPerPost} onChange={(value) => setLimits((prev) => ({ ...prev, maxCommentsPerPost: value }))} />
              <LimitField label="Завсарлах хугацаа (минут)" value={limits.scrapeIntervalMinutes} onChange={(value) => setLimits((prev) => ({ ...prev, scrapeIntervalMinutes: value }))} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="collect">
          <Card>
            <CardHeader className="border-b border-slate-200 pb-4">
              <CardTitle>Түлхүүр үг болон огнооны хайлт</CardTitle>
              <CardDescription>Одоо ачаалагдсан постуудыг платформ, үг болон огноогоор шүүх.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <Field label="Платформ" value={collectionQuery.platform} placeholder="facebook / twitter / instagram / all" onChange={(value) => setCollectionQuery((prev) => ({ ...prev, platform: value }))} />
                <Field label="Түлхүүр үгс" value={collectionQuery.keywords} placeholder="AI, election, policy" onChange={(value) => setCollectionQuery((prev) => ({ ...prev, keywords: value }))} />
                <Field label="Эхлэх огноо" type="date" value={collectionQuery.startDate} onChange={(value) => setCollectionQuery((prev) => ({ ...prev, startDate: value }))} />
                <Field label="Дуусах огноо" type="date" value={collectionQuery.endDate} onChange={(value) => setCollectionQuery((prev) => ({ ...prev, endDate: value }))} />
              </div>

              <Button onClick={runCollectionQuery}>
                <Search className="h-4 w-4" />
                Run query
              </Button>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                {collectionQuery.lastRunSummary || 'Одоогоор ямар нэг хайлт хийгдээгүй байна.'}
              </div>

              <div className="grid gap-3 lg:grid-cols-2">
                {queryResults.slice(0, 6).map((post) => (
                  <article key={post.id} className="rounded-lg border border-slate-200 bg-white p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-slate-950">{post.author}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">{post.platform} / {post.date}</p>
                      </div>
                      <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-700">{post.engagement} engagement</Badge>
                    </div>
                    <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-700">{post.content}</p>
                  </article>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ops">
          <Card>
            <CardHeader className="border-b border-slate-200 pb-4">
              <CardTitle>Backend эрүүл мэнд</CardTitle>
              <CardDescription>Backend эрүүл мэндийн цэгээс буцаагдсан одоогийн төлөвүүд.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <MiniInfo label="Status" value={backendHealth?.status ?? 'Тодорхойгүй'} />
                <MiniInfo label="Хувилбар" value={backendHealth?.version ?? 'n/a'} />
                <MiniInfo label="Firebase" value={backendHealth?.firebase ? 'Connected' : 'Offline'} />
                <MiniInfo label="Analyzer" value={backendHealth?.analyzer ? 'Идэвхжсэн' : 'Хаагдсан'} />
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-700">
                {backendStatus}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ToggleRow({ label, description, enabled, onToggle }: { label: string; description: string; enabled: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={cn('w-full rounded-lg border p-4 text-left transition-colors', enabled ? 'border-blue-200 bg-blue-50' : 'border-slate-200 bg-slate-50 hover:bg-white')}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-950">{label}</p>
          <p className="mt-1 text-sm leading-6 text-slate-600">{description}</p>
        </div>
        <Badge variant="outline" className={enabled ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-white text-slate-500'}>
          {enabled ? 'On' : 'Off'}
        </Badge>
      </div>
    </button>
  );
}

function Field({ label, value, onChange, placeholder, type = 'text' }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string; type?: string }) {
  return (
    <label className="space-y-2">
      <span className="block text-sm font-medium text-slate-700">{label}</span>
      <Input type={type} value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function LimitField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <p className="text-sm font-medium text-slate-700">{label}</p>
      <Input value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function MiniInfo({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function SummaryCard({ title, value, hint, icon: Icon }: { key?: string; title: string; value: string; hint: string; icon: ComponentType<{ className?: string }> }) {
  return (
    <div className="metric-card">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{title}</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
          <p className="mt-2 line-clamp-2 text-sm text-slate-600">{hint}</p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}
