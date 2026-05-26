import { useEffect, useRef, useState, type ComponentType } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { CheckCircle2, Loader2, Play, Plus, RefreshCw, Save, Server, Trash2 } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { dataSources } from '../lib/mockData';
import { apiClient } from '../lib/api';
import { cn } from '../lib/utils';

export function DataSources() {
  const [pages, setPages] = useState<string[]>([]);
  const [newPage, setNewPage] = useState('');
  const [scraperActive, setScraperActive] = useState(false);
  const [scraperLogs, setScraperLogs] = useState('Консол эхэллээ. Мэдээлэл цуглуулахын тулд автоматжуулалтыг эхлүүлнэ үү.');
  const [loadingPages, setLoadingPages] = useState(true);
  const [savingPages, setSavingPages] = useState(false);
  const [runningScraper, setRunningScraper] = useState(false);
  const logTerminalRef = useRef<HTMLPreElement>(null);

  const connectedCount = dataSources.filter((source) => source.connected).length;

  const loadConfiguration = async () => {
    try {
      setLoadingPages(true);
      const [pagesRes, statusRes, logsRes] = await Promise.all([
        apiClient.getPages(),
        apiClient.getScraperStatus(),
        apiClient.getScraperLogs(150),
      ]);

      const pagePayload = pagesRes as typeof pagesRes & { pages?: string[] };
      const statusPayload = statusRes as typeof statusRes & { active?: boolean };
      const logsPayload = logsRes as typeof logsRes & { logs?: string };

      const nextPages = pagePayload.pages ?? pagePayload.data?.pages;
      if (Array.isArray(nextPages)) setPages(nextPages);
      if (typeof statusPayload.active === 'boolean') setScraperActive(statusPayload.active);
      if (logsPayload.logs) setScraperLogs(logsPayload.logs);
    } catch (err) {
      console.error('Failed to load scraper config', err);
      setScraperLogs('Дотоод scraper API-тай холбогдож чадсангүй. Хуудасны менежер хөтчөөр дамжуулан ашиглах боломжтой хэвээр байна.');
    } finally {
      setLoadingPages(false);
    }
  };

  useEffect(() => {
    void loadConfiguration();
  }, []);

  useEffect(() => {
    let intervalId: number | undefined;

    const pollLogs = async () => {
      try {
        const [statusRes, logsRes] = await Promise.all([
          apiClient.getScraperStatus(),
          apiClient.getScraperLogs(150),
        ]);
        const statusPayload = statusRes as typeof statusRes & { active?: boolean };
        const logsPayload = logsRes as typeof logsRes & { logs?: string };
        if (typeof statusPayload.active === 'boolean') setScraperActive(statusPayload.active);
        if (logsPayload.logs) setScraperLogs(logsPayload.logs);
      } catch (err) {
        console.warn('Scraper polling failed', err);
      }
    };

    if (scraperActive) {
      intervalId = window.setInterval(pollLogs, 2000);
    }

    return () => {
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [scraperActive]);

  useEffect(() => {
    if (logTerminalRef.current) {
      logTerminalRef.current.scrollTop = logTerminalRef.current.scrollHeight;
    }
  }, [scraperLogs]);

  const handleAddPage = () => {
    const link = newPage.trim();
    if (!link) return;
    if (!pages.includes(link)) setPages((prev) => [...prev, link]);
    setNewPage('');
  };

  const handleSavePages = async () => {
    setSavingPages(true);
    try {
      const res = await apiClient.savePages(pages);
      if (res.status === 'success') {
        setScraperLogs((prev) => `${prev}\n[System] Target list saved successfully.`);
      }
    } catch (err) {
      console.error('Failed to save pages targets', err);
      setScraperLogs((prev) => `${prev}\n[System error] Could not save targets to pages.txt.`);
    } finally {
      setSavingPages(false);
    }
  };

  const handleLaunchScraper = async () => {
    setRunningScraper(true);
    setScraperLogs((prev) => `${prev}\n[System] Requesting scraper start...`);
    try {
      const res = await apiClient.runScraper();
      if (res.status === 'success') {
        setScraperActive(true);
        setScraperLogs((prev) => `${prev}\n[System] Scraper process started.`);
      } else {
        setScraperLogs((prev) => `${prev}\n[System] Scraper refused request: ${res.message ?? 'unknown reason'}`);
      }
    } catch (err) {
      console.error('Failed to start scraper', err);
      setScraperLogs((prev) => `${prev}\n[System error] Could not contact scraper endpoint.`);
    } finally {
      setRunningScraper(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-3">
        <SummaryCard title="Холбогдсон эх сурвалжууд" value={`${connectedCount}/${dataSources.length}`} hint="Боломжит сошиал холболтууд" icon={CheckCircle2} />
        <SummaryCard title="Scraper байдал" value={scraperActive ? 'Ажиллаж байна' : 'Хүлээгдэж байна'} hint={scraperActive ? '2 секунд тутамд лог шалгаж байна' : 'Эхлүүлэхэд бэлэн'} icon={scraperActive ? Loader2 : Play} spin={scraperActive} />
        <SummaryCard title="Зорилтууд" value={String(pages.length)} hint="Тохируулсан цуглуулах хуудсууд" icon={Server} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <CardHeader className="border-b border-slate-200 pb-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle>Цуглуулах зорилтууд</CardTitle>
                <CardDescription>Backend-ийн pages.txt-д хадгалагдсан хуудасны URL эсвэл ID-г удирдах.</CardDescription>
              </div>
              <Badge variant="outline" className="w-fit border-blue-200 bg-blue-50 text-blue-700">{pages.length} targets</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col gap-2 sm:flex-row">
              <Input
                value={newPage}
                onChange={(event) => setNewPage(event.target.value)}
                placeholder="https://www.facebook.com/example-page"
                onKeyDown={(event) => event.key === 'Enter' && handleAddPage()}
              />
              <Button onClick={handleAddPage} className="shrink-0">
                <Plus className="h-4 w-4" />
                Add
              </Button>
            </div>

            {loadingPages ? (
              <EmptyState icon={Loader2} title="Зорилтуудыг ачаалж байна" description="Backend-ээс scraper тохиргоог уншиж байна." spin />
            ) : pages.length === 0 ? (
              <EmptyState icon={Server} title="Зорилт алга" description="Дээр хуудасны URL эсвэл ID оруулж, жагсаалтыг хадгална уу." />
            ) : (
              <div className="max-h-[300px] divide-y divide-slate-200 overflow-y-auto rounded-lg border border-slate-200">
                {pages.map((page, index) => (
                  <div key={`${page}-${index}`} className="flex items-center justify-between gap-3 bg-white p-3 hover:bg-slate-50">
                    <span className="min-w-0 truncate text-sm font-medium text-slate-800">{page}</span>
                    <Button variant="ghost" size="sm" onClick={() => setPages((prev) => prev.filter((_, itemIndex) => itemIndex !== index))} aria-label={`Remove ${page}`}>
                      <Trash2 className="h-4 w-4 text-rose-600" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            <div className="flex flex-col gap-2 sm:flex-row">
              <Button onClick={handleSavePages} disabled={savingPages || loadingPages} className="flex-1">
                {savingPages ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                {savingPages ? 'Хадгалж байна' : 'Зорилтуудыг хадгалах'}
              </Button>
              <Button variant="outline" onClick={loadConfiguration}>
                <RefreshCw className="h-4 w-4" />
                Reload
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b border-slate-200 pb-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle>Автоматжуулалтын консол</CardTitle>
                <CardDescription>Шууд scraper статус болон процессын үр дүн.</CardDescription>
              </div>
              <span className={cn('h-2.5 w-2.5 rounded-full', scraperActive ? 'bg-emerald-500' : 'bg-slate-300')} />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <pre ref={logTerminalRef} className="terminal-console h-[292px] overflow-y-auto rounded-lg p-4 text-xs leading-6 whitespace-pre-wrap">
              {scraperLogs}
            </pre>
            <Button onClick={handleLaunchScraper} disabled={scraperActive || runningScraper} className="w-full">
              {runningScraper ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              {runningScraper ? 'Scraper эхэлж байна' : scraperActive ? 'Scraper ажиллаж байна' : 'Цуглуулж эхлэх'}
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {dataSources.map((source) => (
          <Card key={source.id} className="xl:col-span-1">
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-slate-950">{source.name}</h3>
                  <p className="mt-1 text-xs text-slate-500">
                    {source.connected && source.lastSync
                      ? `Synced ${formatDistanceToNow(new Date(source.lastSync), { addSuffix: true })}`
                      : 'Холбогдоогүй'}
                  </p>
                </div>
                <Badge variant="outline" className={source.connected ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-slate-50 text-slate-500'}>
                  {source.connected ? 'Active' : 'Offline'}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function SummaryCard({
  title,
  value,
  hint,
  icon: Icon,
  spin,
}: {
  title: string;
  value: string;
  hint: string;
  icon: ComponentType<{ className?: string }>;
  spin?: boolean;
}) {
  return (
    <div className="metric-card">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{title}</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
          <p className="mt-2 text-sm text-slate-600">{hint}</p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
          <Icon className={cn('h-5 w-5', spin && 'animate-spin')} />
        </div>
      </div>
    </div>
  );
}

function EmptyState({
  icon: Icon,
  title,
  description,
  spin,
}: {
  icon: ComponentType<{ className?: string }>;
  title: string;
  description: string;
  spin?: boolean;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center">
      <Icon className={cn('h-8 w-8 text-slate-400', spin && 'animate-spin')} />
      <h3 className="mt-3 text-sm font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 max-w-md text-sm leading-6 text-slate-500">{description}</p>
    </div>
  );
}
