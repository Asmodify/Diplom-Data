import { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { mockCollectedPosts, type MockCollectedPost } from '../lib/mockData';
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

  const [maintenanceMessage, setMaintenanceMessage] = useState('');
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
          const fallbackMessage =
            healthResult.status === 'rejected' ? healthResult.reason : statsResult.reason;
          setBackendStatus(`Backend sync degraded: ${String(fallbackMessage)}`);
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
      const keywordOk =
        keywordList.length === 0 || keywordList.some((keyword) => postSearchText.includes(keyword));

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Админ хяналтын хуудас</h2>
          <p className="text-muted-foreground">
            Системийн урсгал, API эрх, AI анализ, өгөгдөл цуглуулалтын хязгааруудыг удирдана.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={backendHealth?.firebase ? 'default' : 'secondary'} className="bg-emerald-600 hover:bg-emerald-700">
            {backendHealth?.firebase ? 'Render + Firebase live' : 'Backend syncing'}
          </Badge>
          <Badge variant="outline">{backendBusy ? 'Refreshing' : 'Ready'}</Badge>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Backend status</CardDescription>
            <CardTitle className="text-base">{backendHealth?.status ?? 'unknown'}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {backendHealth?.version ? `v${backendHealth.version}` : 'Render API'}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Live posts</CardDescription>
            <CardTitle className="text-base">{backendStats?.total_posts ?? visiblePosts.length}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Pulled from scraper database
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Firebase</CardDescription>
            <CardTitle className="text-base">{backendHealth?.firebase ? 'Connected' : 'Offline'}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Admin logs via Firestore
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Frontend API</CardDescription>
            <CardTitle className="text-base">Vercel-ready</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {backendStatus}
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="system" className="space-y-4">
        <TabsList>
          <TabsTrigger value="system">Систем</TabsTrigger>
          <TabsTrigger value="limits">Хязгаар</TabsTrigger>
          <TabsTrigger value="collect">Түлхүүр үг хайлт</TabsTrigger>
          <TabsTrigger value="ops">Үйл ажиллагаа</TabsTrigger>
        </TabsList>

        <TabsContent value="system" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Core Control Switches</CardTitle>
              <CardDescription>
                Гол модуль бүрийн идэвхийг шууд удирдах хэсэг.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              <ControlRow
                label="Скрапинг ажиллуулах"
                description="Scraper модулийг ажиллуулах/зогсоох"
                enabled={controls.scrapingEnabled}
                onToggle={() => toggleControl('scrapingEnabled')}
              />
              <ControlRow
                label="AI анализ"
                description="Predictive, emotion, topic, network анализ"
                enabled={controls.aiAnalysisEnabled}
                onToggle={() => toggleControl('aiAnalysisEnabled')}
              />
              <ControlRow
                label="API хандалт"
                description="REST endpoint-уудыг нээх/хаах"
                enabled={controls.apiAccessEnabled}
                onToggle={() => toggleControl('apiAccessEnabled')}
              />
              <ControlRow
                label="Auto Cloud Sync"
                description="Firebase sync урсгал"
                enabled={controls.autoSyncEnabled}
                onToggle={() => toggleControl('autoSyncEnabled')}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Live backend sync</CardTitle>
              <CardDescription>
                Энэ хэсэг Render дээрх scraper API болон Firebase холболтыг шалгана.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-md border bg-muted/30 p-3 text-sm text-muted-foreground">
                {backendStatus}
              </div>
              <div className="flex flex-wrap gap-2">
                <Button onClick={refreshBackendSnapshot} disabled={backendBusy}>
                  Refresh live backend
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="limits" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Data Collection Limits</CardTitle>
              <CardDescription>
                Системийн нөөц болон API тогтвортой ажиллагаанд зориулсан хязгаарууд.
              </CardDescription>
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
          <Card>
            <CardHeader>
              <CardTitle>Keyword + Date Collection Query</CardTitle>
              <CardDescription>
                Платформ, түлхүүр үг болон хугацааны муж оруулж data collection query бэлдэнэ.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <p className="text-sm font-medium">Platform</p>
                  <Input
                    placeholder="facebook / twitter / instagram"
                    value={collectionQuery.platform}
                    onChange={(event) =>
                      setCollectionQuery((prev) => ({ ...prev, platform: event.target.value }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-medium">Keywords</p>
                  <Input
                    placeholder="AI, data science, election"
                    value={collectionQuery.keywords}
                    onChange={(event) =>
                      setCollectionQuery((prev) => ({ ...prev, keywords: event.target.value }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-medium">Start Date</p>
                  <Input
                    type="date"
                    value={collectionQuery.startDate}
                    onChange={(event) =>
                      setCollectionQuery((prev) => ({ ...prev, startDate: event.target.value }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-medium">End Date</p>
                  <Input
                    type="date"
                    value={collectionQuery.endDate}
                    onChange={(event) =>
                      setCollectionQuery((prev) => ({ ...prev, endDate: event.target.value }))
                    }
                  />
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button onClick={runCollectionQuery}>Query ажиллуулах</Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setCollectionQuery((prev) => ({
                      ...prev,
                      keywords: '',
                      startDate: '',
                      endDate: '',
                      lastRunSummary: '',
                    }));
                    setQueryResults([]);
                  }}
                >
                  Query цэвэрлэх
                </Button>
              </div>

              <div className="rounded-md border bg-muted/20 p-3 text-sm text-muted-foreground">
                Showing {visiblePosts.length} live-capable posts from the backend or fallback demo set.
              </div>

              {collectionQuery.lastRunSummary && (
                <div className="rounded-md border bg-muted/30 p-3 text-sm text-muted-foreground">
                  {collectionQuery.lastRunSummary}
                </div>
              )}

              {queryResults.length > 0 && (
                <div className="space-y-2 rounded-md border p-3">
                  <p className="text-sm font-medium">Live Query Results</p>
                  <div className="space-y-2">
                    {queryResults.slice(0, 6).map((post) => (
                      <div key={post.id} className="rounded border p-2 text-sm">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium">{post.author}</span>
                          <Badge variant="secondary">{post.platform}</Badge>
                        </div>
                        <p className="mt-1 text-muted-foreground">{post.content}</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {post.date} | Engagement: {post.engagement} | Likes: {post.likes}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ops" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Operational Actions</CardTitle>
              <CardDescription>
                Засвар үйлчилгээ болон хяналтын мессежүүд.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm font-medium">Maintenance Message</p>
                <Input
                  placeholder="Системд түр засвар үйлчилгээ явагдаж байна..."
                  value={maintenanceMessage}
                  onChange={(event) => setMaintenanceMessage(event.target.value)}
                />
              </div>

              <div className="flex flex-wrap gap-2">
                <Button>Хяналтын өөрчлөлт хадгалах</Button>
                <Button variant="outline">Системийн төлөв дахин ачаалах</Button>
                <Button variant="destructive">Emergency Stop</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

type ControlRowProps = {
  label: string;
  description: string;
  enabled: boolean;
  onToggle: () => void;
};

function ControlRow({ label, description, enabled, onToggle }: ControlRowProps) {
  return (
    <div className="rounded-md border p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="font-medium">{label}</p>
        <Badge variant={enabled ? 'default' : 'secondary'}>
          {enabled ? 'ON' : 'OFF'}
        </Badge>
      </div>
      <p className="mb-3 text-sm text-muted-foreground">{description}</p>
      <Button variant={enabled ? 'outline' : 'default'} size="sm" onClick={onToggle}>
        {enabled ? 'Disable' : 'Enable'}
      </Button>
    </div>
  );
}

type LimitFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
};

function LimitField({ label, value, onChange }: LimitFieldProps) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{label}</p>
      <Input value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}
