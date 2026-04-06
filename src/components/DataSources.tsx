import { formatDistanceToNow } from 'date-fns';
import { mn } from 'date-fns/locale';
import type { ComponentType } from 'react';
import { CheckCircle2, Layers3, PlugZap, RefreshCw, Share2, ShieldAlert } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { dataSources } from '../lib/mockData';
import { cn } from '../lib/utils';

export function DataSources() {
  const connectedCount = dataSources.filter((source) => source.connected).length;

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/70">Sources</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Өгөгдлийн эх сурвалжууд</h2>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-300">
            Social platform бүрийн sync төлөв, шинэчлэлтийн цаг, болон холболтын статусыг нэг дор харна.
          </p>
        </div>
        <Button className="gap-2 self-start lg:self-auto">
          <PlugZap className="h-4 w-4" />
          Шинэ эх сурвалж
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <SummaryCard title="Connected" value={`${connectedCount}/${dataSources.length}`} hint="Active platform links" icon={CheckCircle2} />
        <SummaryCard title="Sync coverage" value="Realtime" hint="Incremental updates enabled" icon={RefreshCw} />
        <SummaryCard title="Source breadth" value="Multi-platform" hint="Facebook, X, Instagram, more" icon={Layers3} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {dataSources.map((source) => (
            <Card key={source.id} className="border-white/10 bg-white/[0.03]">
              <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
                <div>
                  <CardTitle className="text-lg text-white">{source.name}</CardTitle>
                  <CardDescription className="mt-1">{source.connected ? 'Connected and syncing' : 'Disconnected'}</CardDescription>
                </div>
                <Badge variant={source.connected ? 'default' : 'outline'} className={cn(source.connected && 'bg-emerald-400/15 text-emerald-100 ring-emerald-400/20')}>
                  {source.connected ? 'Live' : 'Offline'}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                  <div className="flex items-center justify-between text-sm text-slate-300">
                    <span>Status</span>
                    <span>{source.connected ? 'Healthy' : 'Needs attention'}</span>
                  </div>
                  <div className="mt-3 h-2 rounded-full bg-slate-800">
                    <div className={cn('h-2 rounded-full', source.connected ? 'w-[86%] bg-gradient-to-r from-emerald-400 to-cyan-400' : 'w-[32%] bg-gradient-to-r from-rose-400 to-amber-400')} />
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4 text-sm leading-6 text-slate-300">
                  {source.connected && source.lastSync ? (
                    <p>
                      Сүүлд шинэчлэгдсэн: {formatDistanceToNow(new Date(source.lastSync), { addSuffix: true, locale: mn })}
                    </p>
                  ) : (
                    <p>Одоогоор өгөгдөл татагдаагүй байна.</p>
                  )}
                </div>

                <Button variant={source.connected ? 'outline' : 'default'} className="w-full gap-2">
                  {source.connected ? (
                    <>
                      <Share2 className="h-4 w-4" /> Салгах
                    </>
                  ) : (
                    <>
                      <PlugZap className="h-4 w-4" /> Холбох
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="space-y-5">
          <Card className="border-cyan-400/15 bg-gradient-to-br from-cyan-400/8 to-slate-900/70">
            <CardHeader>
              <CardTitle className="text-lg text-white">Sync pipeline</CardTitle>
              <CardDescription>Ingest → normalize → store → expose.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { label: 'Collect', value: 'Scraper pulls posts and comments', accent: 'bg-cyan-400' },
                { label: 'Normalize', value: 'Fields are mapped into a unified schema', accent: 'bg-emerald-400' },
                { label: 'Persist', value: 'Firebase and local cache stay aligned', accent: 'bg-amber-400' },
              ].map((step) => (
                <div key={step.label} className="flex gap-3 rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                  <span className={cn('mt-1 h-3 w-3 rounded-full', step.accent)} />
                  <div>
                    <p className="text-sm font-medium text-white">{step.label}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-400">{step.value}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-white/[0.03]">
            <CardHeader>
              <CardTitle className="text-lg text-white">Operational note</CardTitle>
              <CardDescription>Connection health and import strategy.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm leading-6 text-slate-300">
              <p>
                Each source is handled as a separate operational lane, so the pipeline can be extended without changing the dashboard layout.
              </p>
              <p>
                When a platform is offline, the interface keeps the last sync timestamp visible to make the state obvious instead of hiding it.
              </p>
              <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4 text-slate-200">
                <div className="flex items-center gap-2 text-cyan-200">
                  <ShieldAlert className="h-4 w-4" />
                  Fail-safe behavior
                </div>
                <p className="mt-2 text-slate-400">Disconnected sources remain visible, but they are clearly marked and toned down.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  title,
  value,
  hint,
  icon: Icon,
}: {
  title: string;
  value: string;
  hint: string;
  icon: ComponentType<{ className?: string }>;
}) {
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
