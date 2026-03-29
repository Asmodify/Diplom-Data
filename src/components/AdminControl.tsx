import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { mockCollectedPosts, type MockCollectedPost } from '../lib/mockData';

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
  const [queryResults, setQueryResults] = useState<MockCollectedPost[]>([]);

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

    const filtered = mockCollectedPosts.filter((post) => {
      const platformOk =
        !collectionQuery.platform ||
        collectionQuery.platform.toLowerCase() === 'all' ||
        post.platform === collectionQuery.platform.toLowerCase();

      const startOk = !collectionQuery.startDate || post.date >= collectionQuery.startDate;
      const endOk = !collectionQuery.endDate || post.date <= collectionQuery.endDate;

      const postSearchText = `${post.content} ${post.keywords.join(' ')}`.toLowerCase();
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Админ хяналтын хуудас</h2>
          <p className="text-muted-foreground">
            Системийн урсгал, API эрх, AI анализ, өгөгдөл цуглуулалтын хязгааруудыг удирдана.
          </p>
        </div>
        <Badge variant="default" className="bg-emerald-600 hover:bg-emerald-700">
          Control Page
        </Badge>
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

              {collectionQuery.lastRunSummary && (
                <div className="rounded-md border bg-muted/30 p-3 text-sm text-muted-foreground">
                  {collectionQuery.lastRunSummary}
                </div>
              )}

              {queryResults.length > 0 && (
                <div className="space-y-2 rounded-md border p-3">
                  <p className="text-sm font-medium">Mock Query Results</p>
                  <div className="space-y-2">
                    {queryResults.slice(0, 6).map((post) => (
                      <div key={post.id} className="rounded border p-2 text-sm">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium">{post.author}</span>
                          <Badge variant="secondary">{post.platform}</Badge>
                        </div>
                        <p className="mt-1 text-muted-foreground">{post.content}</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {post.date} | Engagement: {post.engagement}
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
