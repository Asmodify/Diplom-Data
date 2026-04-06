/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo, useState } from 'react';
import {
  Activity,
  ArrowRight,
  BarChart3,
  Database,
  LayoutDashboard,
  Settings,
  Shield,
  Sparkles,
} from 'lucide-react';
import { cn } from './lib/utils';
import { Dashboard } from './components/Dashboard';
import { DataSources } from './components/DataSources';
import { PredictiveAnalysis } from './components/PredictiveAnalysis';
import { AdminControl } from './components/AdminControl';
import { Badge } from './components/ui/badge';

type TabId = 'dashboard' | 'sources' | 'analysis' | 'admin' | 'settings';

const tabs: Array<{
  id: TabId;
  label: string;
  description: string;
  icon: typeof LayoutDashboard;
}> = [
  {
    id: 'dashboard',
    label: 'Хянах самбар',
    description: 'Live metrics, trend line, and platform overview.',
    icon: LayoutDashboard,
  },
  {
    id: 'sources',
    label: 'Эх сурвалж',
    description: 'Connected platforms and sync health.',
    icon: Database,
  },
  {
    id: 'analysis',
    label: 'Таамаглал',
    description: 'AI-driven analysis and recommendations.',
    icon: BarChart3,
  },
  {
    id: 'admin',
    label: 'Админ',
    description: 'Controls, limits, and backend operations.',
    icon: Shield,
  },
  {
    id: 'settings',
    label: 'Тохиргоо',
    description: 'Branding, preferences, and system polish.',
    icon: Settings,
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');

  const activeTabMeta = useMemo(
    () => tabs.find((tab) => tab.id === activeTab) ?? tabs[0],
    [activeTab],
  );

  const ActiveIcon = activeTabMeta.icon;

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-50">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.18),transparent_30%),radial-gradient(circle_at_top_right,_rgba(16,185,129,0.16),transparent_28%),radial-gradient(circle_at_bottom_left,_rgba(248,113,113,0.09),transparent_26%),linear-gradient(180deg,rgba(15,23,42,1)_0%,rgba(2,6,23,1)_100%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-40 [background-image:linear-gradient(rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.025)_1px,transparent_1px)] [background-size:72px_72px]" />

      <div className="relative mx-auto flex min-h-screen w-full max-w-[1680px] gap-5 p-4 lg:p-6">
        <aside className="hidden w-[290px] flex-col rounded-[2rem] border border-white/10 bg-slate-950/75 p-5 shadow-2xl shadow-cyan-950/10 backdrop-blur-xl lg:flex">
          <div className="flex items-center gap-3 border-b border-white/10 pb-5">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-400 text-slate-950 shadow-lg shadow-cyan-400/30">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/70">Diploma Data</p>
              <h1 className="text-lg font-semibold tracking-tight">Social Intelligence Lab</h1>
            </div>
          </div>

          <div className="mt-5 space-y-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'group w-full rounded-2xl border px-4 py-3 text-left transition-all duration-200',
                    active
                      ? 'border-cyan-400/40 bg-cyan-400/12 shadow-lg shadow-cyan-400/10'
                      : 'border-transparent bg-white/[0.03] hover:border-white/10 hover:bg-white/[0.05]',
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        'flex h-10 w-10 items-center justify-center rounded-xl transition-colors',
                        active ? 'bg-cyan-400 text-slate-950' : 'bg-slate-800 text-slate-300',
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium text-slate-50">{tab.label}</span>
                        {active && <ArrowRight className="h-4 w-4 text-cyan-300" />}
                      </div>
                      <p className="mt-1 text-xs leading-5 text-slate-400">{tab.description}</p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="mt-auto space-y-3 rounded-3xl border border-white/10 bg-gradient-to-b from-cyan-400/10 to-slate-900/80 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.25em] text-cyan-200/70">Runtime</p>
                <h2 className="mt-1 text-sm font-semibold text-slate-50">Live backend ready</h2>
              </div>
              <Activity className="h-5 w-5 text-cyan-300" />
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="default">Render API</Badge>
              <Badge variant="secondary">Firebase sync</Badge>
              <Badge variant="outline">Vite + React</Badge>
            </div>
            <p className="text-sm leading-6 text-slate-300">
              Clean dashboard, predictive analysis, and control surface for the diploma project.
            </p>
          </div>
        </aside>

        <main className="flex min-w-0 flex-1 flex-col gap-5">
          <header className="rounded-[2rem] border border-white/10 bg-slate-950/70 p-5 shadow-2xl shadow-slate-950/30 backdrop-blur-xl lg:p-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="default" className="bg-cyan-400/15 text-cyan-100 ring-cyan-300/20">Live intelligence console</Badge>
                  <Badge variant="outline">Backend synced</Badge>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.4em] text-slate-400">Нийгмийн сүлжээний өгөгдөл цуглуулга ба анализ</p>
                  <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                    {activeTabMeta.label}
                  </h2>
                  <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
                    {activeTabMeta.description}
                  </p>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 lg:w-[360px]">
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Pipeline</p>
                  <p className="mt-2 text-lg font-semibold text-white">Collect → Analyze → Recommend</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Engine</p>
                  <p className="mt-2 text-lg font-semibold text-white">Gemini + Render</p>
                </div>
              </div>
            </div>
          </header>

          <nav className="flex flex-wrap gap-2 lg:hidden">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'inline-flex items-center gap-2 rounded-2xl border px-4 py-2 text-sm transition-colors',
                    active
                      ? 'border-cyan-400/50 bg-cyan-400 text-slate-950'
                      : 'border-white/10 bg-white/[0.03] text-slate-200 hover:bg-white/[0.06]',
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>

          <section className="grid gap-4 md:grid-cols-4">
            <div className="rounded-[1.75rem] border border-white/10 bg-white/[0.04] p-4 backdrop-blur-xl">
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Platforms</p>
              <p className="mt-2 text-2xl font-semibold text-white">3 live sources</p>
              <p className="mt-2 text-sm text-slate-400">Facebook, Twitter, Instagram</p>
            </div>
            <div className="rounded-[1.75rem] border border-white/10 bg-white/[0.04] p-4 backdrop-blur-xl">
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Sync</p>
              <p className="mt-2 text-2xl font-semibold text-white">Render connected</p>
              <p className="mt-2 text-sm text-slate-400">API + scraper heartbeat active</p>
            </div>
            <div className="rounded-[1.75rem] border border-white/10 bg-white/[0.04] p-4 backdrop-blur-xl">
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Analysis</p>
              <p className="mt-2 text-2xl font-semibold text-white">Predictive models</p>
              <p className="mt-2 text-sm text-slate-400">Sentiment, topic, and engagement logic</p>
            </div>
            <div className="rounded-[1.75rem] border border-cyan-400/20 bg-cyan-400/10 p-4 backdrop-blur-xl">
              <p className="text-xs uppercase tracking-[0.3em] text-cyan-200/70">Status</p>
              <p className="mt-2 text-2xl font-semibold text-white">Production UI</p>
              <p className="mt-2 text-sm text-cyan-100/80">Redesigned from the ground up</p>
            </div>
          </section>

          <section className="min-w-0 rounded-[2rem] border border-white/10 bg-slate-950/70 p-4 shadow-2xl shadow-slate-950/30 backdrop-blur-xl sm:p-6 lg:p-7">
            <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/70">Workspace</p>
                <h3 className="mt-2 text-xl font-semibold text-white sm:text-2xl">{activeTabMeta.label}</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">Dark editorial theme</Badge>
                <Badge variant="outline">Responsive</Badge>
              </div>
            </div>

            <div className="min-w-0">
              {activeTab === 'dashboard' && <Dashboard />}
              {activeTab === 'sources' && <DataSources />}
              {activeTab === 'analysis' && <PredictiveAnalysis />}
              {activeTab === 'admin' && <AdminControl />}
              {activeTab === 'settings' && (
                <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
                  <div className="rounded-[1.75rem] border border-white/10 bg-white/[0.03] p-6">
                    <h4 className="text-lg font-semibold text-white">Settings playground</h4>
                    <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-300">
                      This area is intentionally minimal for now. If you want, I can extend it into a full theme, account, and environment settings workspace.
                    </p>
                  </div>
                  <div className="rounded-[1.75rem] border border-white/10 bg-gradient-to-br from-cyan-400/10 to-emerald-400/10 p-6">
                    <h4 className="text-lg font-semibold text-white">Design language</h4>
                    <ul className="mt-4 space-y-3 text-sm text-slate-200">
                      <li>• Deep slate base with cyan accent</li>
                      <li>• Rounded surfaces and strong spacing</li>
                      <li>• Live data surfaces from Render + Firebase</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
