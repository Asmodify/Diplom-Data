/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
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
  enLabel: string;
  description: string;
  icon: typeof LayoutDashboard;
}> = [
  {
    id: 'dashboard',
    label: 'Хянах самбар',
    enLabel: 'Dashboard',
    description: 'Бодит цагийн статистик, идэвхжлийн тренд, платформын удирдлага.',
    icon: LayoutDashboard,
  },
  {
    id: 'sources',
    label: 'Эх сурвалж',
    enLabel: 'Data Sources',
    description: 'Scraper тохиргоо, pages.txt удирдлага, системийн лог консол.',
    icon: Database,
  },
  {
    id: 'analysis',
    label: 'AI Таамаглал',
    enLabel: 'Predictive AI',
    description: 'Gemini AI-д суурилсан өгөгдлийн шинжилгээ, тайлан зөвлөмж.',
    icon: BarChart3,
  },
  {
    id: 'admin',
    label: 'Админ хяналт',
    enLabel: 'Admin Control',
    description: 'Системийн төлөв, хязгаарлалтууд, backend оношилгоо.',
    icon: Shield,
  },
  {
    id: 'settings',
    label: 'Тохиргоо',
    enLabel: 'System Settings',
    description: 'Брэнд тохируулга, API холболтууд, системийн үзүүлэлтүүд.',
    icon: Settings,
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');

  const activeTabMeta = useMemo(
    () => tabs.find((tab) => tab.id === activeTab) ?? tabs[0],
    [activeTab],
  );

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-slate-50 text-slate-800 font-sans">
      {/* Aurora Ambient Lighting Glows */}
      <div className="pointer-events-none absolute top-[-10%] left-[-10%] h-[50%] w-[50%] rounded-full bg-cyan-200/20 blur-[120px]" />
      <div className="pointer-events-none absolute top-[20%] right-[-10%] h-[40%] w-[40%] rounded-full bg-purple-200/25 blur-[100px]" />
      <div className="pointer-events-none absolute bottom-[-10%] left-[20%] h-[35%] w-[40%] rounded-full bg-rose-200/15 blur-[120px]" />
      
      {/* Editorial Gridlines Overlay */}
      <div className="pointer-events-none absolute inset-0 opacity-[0.03] [background-image:linear-gradient(rgba(0,0,0,0.15)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.15)_1px,transparent_1px)] [background-size:48px_48px]" />

      <div className="relative mx-auto flex min-h-screen w-full max-w-[1720px] gap-6 p-4 md:p-6">
        {/* Floating Sidebar Navigation */}
        <aside className="glass-panel hidden w-[310px] flex-col rounded-[2.5rem] p-6 shadow-xl shadow-slate-100/50 backdrop-blur-2xl lg:flex">
          {/* Sidebar Brand Header */}
          <div className="flex items-center gap-4 border-b border-slate-200/60 pb-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg shadow-purple-500/25">
              <Sparkles className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-purple-600/80">Social Analytics</p>
              <h1 className="text-lg font-bold tracking-tight text-slate-900">Intelligence Lab</h1>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="mt-6 flex-1 space-y-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'group w-full rounded-2xl border px-4 py-3.5 text-left transition-all duration-300 relative overflow-hidden',
                    active
                      ? 'border-purple-200 bg-white/70 shadow-md shadow-slate-200/40 text-slate-900'
                      : 'border-transparent bg-transparent text-slate-600 hover:bg-white/30 hover:text-slate-900',
                  )}
                >
                  {/* Subtle active background glow */}
                  {active && (
                    <motion.div
                      layoutId="activeGlow"
                      className="absolute inset-0 bg-gradient-to-r from-purple-500/5 to-cyan-500/5 -z-10"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                  
                  <div className="flex items-center gap-3.5 relative z-10">
                    <div
                      className={cn(
                        'flex h-10 w-10 items-center justify-center rounded-xl transition-all duration-300',
                        active 
                          ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-md shadow-purple-500/20' 
                          : 'bg-slate-100/80 text-slate-500 group-hover:bg-slate-200/80 group-hover:text-slate-700',
                      )}
                    >
                      <Icon className="h-4.5 w-4.5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-sm tracking-tight">{tab.label}</span>
                        {active && (
                          <motion.div
                            initial={{ opacity: 0, x: -5 }}
                            animate={{ opacity: 1, x: 0 }}
                          >
                            <ArrowRight className="h-3.5 w-3.5 text-purple-600" />
                          </motion.div>
                        )}
                      </div>
                      <p className="mt-0.5 text-[11px] leading-relaxed text-slate-400 group-hover:text-slate-500 transition-colors line-clamp-1">
                        {tab.enLabel}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Footer Info Widget */}
          <div className="mt-auto space-y-4 rounded-3xl border border-slate-200/60 bg-white/40 p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-400">Системийн Төлөв</p>
                <h2 className="mt-1 text-sm font-bold text-slate-800">API Идэвхтэй байна</h2>
              </div>
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                <Activity className="h-4 w-4" />
              </div>
            </div>
            <div className="flex flex-wrap gap-1.5">
              <Badge variant="outline" className="bg-slate-50/80 text-[10px] border-slate-200">FastAPI</Badge>
              <Badge variant="outline" className="bg-slate-50/80 text-[10px] border-slate-200">PostgreSQL</Badge>
              <Badge variant="outline" className="bg-slate-50/80 text-[10px] border-slate-200">Realtime</Badge>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-400">
              Дипломын ажлын хүрээнд хийгдсэн сошиал сувгуудын өгөгдөл цуглуулалт, AI таамаглалын нэгдсэн систем.
            </p>
          </div>
        </aside>

        {/* Main Work Area */}
        <main className="flex min-w-0 flex-1 flex-col gap-6">
          {/* Header Panel */}
          <header className="glass-panel rounded-[2.5rem] p-6 shadow-lg shadow-slate-100/50 backdrop-blur-2xl">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="secondary" className="bg-gradient-to-r from-purple-500/10 to-indigo-500/10 text-purple-700 font-bold border-purple-200/50 py-0.5 px-2.5">
                    Сошиал Аналитик Систем v2.0
                  </Badge>
                  <Badge variant="outline" className="bg-white/80 border-slate-200 text-slate-500 text-[11px]">Backend Synced</Badge>
                </div>
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.35em] text-slate-400">Нийгмийн сүлжээний өгөгдөл цуглуулга ба анализ</p>
                  <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                    {activeTabMeta.label}
                  </h2>
                  <p className="mt-1.5 max-w-3xl text-xs leading-relaxed text-slate-400 sm:text-sm">
                    {activeTabMeta.description}
                  </p>
                </div>
              </div>

              {/* Status snapshots */}
              <div className="grid gap-3 grid-cols-2 lg:w-[380px]">
                <div className="rounded-2xl border border-slate-200/60 bg-white/40 p-4 shadow-sm">
                  <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-400">Өгөгдлийн Урсгал</p>
                  <p className="mt-1 text-sm font-bold text-slate-800">Scrape → Store → Analyze</p>
                </div>
                <div className="rounded-2xl border border-slate-200/60 bg-white/40 p-4 shadow-sm">
                  <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-400">Шинжилгээний Цөм</p>
                  <p className="mt-1 text-sm font-bold text-slate-800">Gemini Pro AI</p>
                </div>
              </div>
            </div>
          </header>

          {/* Mobile Navigation Header */}
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
                    'inline-flex items-center gap-2 rounded-2xl border px-4 py-2.5 text-xs font-semibold tracking-tight transition-all duration-300',
                    active
                      ? 'border-purple-200 bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-md shadow-purple-500/20'
                      : 'border-slate-200 bg-white/60 text-slate-600 hover:bg-white',
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {tab.label}
                </button>
              );
            })}
          </nav>

          {/* Top Quick Readouts Section */}
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="glass-card rounded-3xl p-5 shadow-sm">
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-400">Платформууд</p>
              <p className="mt-1.5 text-2xl font-bold text-slate-900">3 Идэвхтэй Суваг</p>
              <p className="mt-1 text-xs text-slate-400">Facebook, Twitter, Instagram</p>
            </div>
            <div className="glass-card rounded-3xl p-5 shadow-sm">
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-400">Синхрончлол</p>
              <p className="mt-1.5 text-2xl font-bold text-slate-900">Холбогдсон</p>
              <p className="mt-1 text-xs text-slate-400">API + Scraper heartbeat active</p>
            </div>
            <div className="glass-card rounded-3xl p-5 shadow-sm">
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-400">Шинжилгээ</p>
              <p className="mt-1.5 text-2xl font-bold text-slate-900">Таамаглалт Загварууд</p>
              <p className="mt-1 text-xs text-slate-400">Sentiment, topic, engagement metrics</p>
            </div>
            <div className="glass-card border-purple-200/50 bg-gradient-to-br from-purple-500/5 to-indigo-500/5 rounded-3xl p-5 shadow-sm">
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-purple-600/70">Дизайн Загвар</p>
              <p className="mt-1.5 text-2xl font-bold text-slate-900">White Glassmorphism</p>
              <p className="mt-1 text-xs text-purple-600/80">Premium light-reflective interfaces</p>
            </div>
          </section>

          {/* Active Workspace View */}
          <section className="glass-panel min-w-0 rounded-[2.5rem] p-5 shadow-xl shadow-slate-100/50 backdrop-blur-2xl sm:p-6 lg:p-8">
            {/* View Header with Workspace Label */}
            <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200/60 pb-5">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-purple-600/80">Ажлын Бүс</p>
                <h3 className="mt-1 text-xl font-bold tracking-tight text-slate-900">{activeTabMeta.label}</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary" className="bg-slate-100 text-slate-600 font-semibold border-slate-200">Light Editorial Theme</Badge>
                <Badge variant="outline" className="bg-white/60 border-slate-200 text-slate-500">Fully Responsive</Badge>
              </div>
            </div>

            {/* Render with Tab Switch Animation */}
            <div className="min-w-0 relative">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 12, filter: 'blur(4px)' }}
                  animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                  exit={{ opacity: 0, y: -12, filter: 'blur(4px)' }}
                  transition={{ duration: 0.35, ease: 'easeInOut' }}
                >
                  {activeTab === 'dashboard' && <Dashboard />}
                  {activeTab === 'sources' && <DataSources />}
                  {activeTab === 'analysis' && <PredictiveAnalysis />}
                  {activeTab === 'admin' && <AdminControl />}
                  {activeTab === 'settings' && (
                    <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
                      <div className="glass-card rounded-[2rem] p-6 shadow-inner">
                        <h4 className="text-lg font-bold text-slate-900">Системийн тохиргоо</h4>
                        <p className="mt-2 text-xs sm:text-sm leading-relaxed text-slate-500">
                          Системийн ерөнхий тохиргоо, API холболт, мэдэгдлийн тохируулга зэрэг нэмэлт функцүүд энд нэмэгдэнэ. Одоогоор бүх тохиргоо backend environment variables-ээр удирдагдаж байна.
                        </p>
                        <div className="mt-6 space-y-3">
                          <div className="group rounded-2xl border border-slate-200 bg-white/40 p-4 transition-colors hover:border-slate-300">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-semibold text-slate-700 group-hover:text-slate-900 transition-colors">Backend API URL</span>
                              <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100/80 border-emerald-200 py-0.5">Холбогдсон</Badge>
                            </div>
                          </div>
                          <div className="group rounded-2xl border border-slate-200 bg-white/40 p-4 transition-colors hover:border-slate-300">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-semibold text-slate-700 group-hover:text-slate-900 transition-colors">Supabase DB Sync</span>
                              <Badge variant="outline" className="bg-white/80 border-slate-200 text-slate-500">Realtime Active</Badge>
                            </div>
                          </div>
                          <div className="group rounded-2xl border border-slate-200 bg-white/40 p-4 transition-colors hover:border-slate-300">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-semibold text-slate-700 group-hover:text-slate-900 transition-colors">Gemini AI Model</span>
                              <Badge variant="outline" className="bg-white/80 border-slate-200 text-slate-500">gemini-1.5-pro</Badge>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="relative overflow-hidden rounded-[2rem] border border-purple-200/50 bg-gradient-to-br from-purple-500/5 via-indigo-500/5 to-cyan-500/5 p-6 shadow-sm">
                        <div className="pointer-events-none absolute top-[-10%] right-[-10%] h-[60%] w-[60%] rounded-full bg-purple-200/20 blur-2xl" />
                        <h4 className="relative text-lg font-bold text-slate-900">Дизайн систем ба загвар</h4>
                        <ul className="relative mt-4 space-y-3.5 text-xs sm:text-sm text-slate-600">
                          <li className="flex items-start gap-2.5">
                            <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-purple-500" />
                            <span><strong>Theme:</strong> White Glassmorphism Aurora Light-reflecting panel system.</span>
                          </li>
                          <li className="flex items-start gap-2.5">
                            <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-purple-500" />
                            <span><strong>Aesthetic Elements:</strong> High blur, translucent outline strokes, soft shadow overlays, colorful auroras.</span>
                          </li>
                          <li className="flex items-start gap-2.5">
                            <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-purple-500" />
                            <span><strong>Data Integration:</strong> FastAPI Python backplane + real-time incremental Supabase event listeners.</span>
                          </li>
                          <li className="flex items-start gap-2.5">
                            <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-purple-500" />
                            <span><strong>Responsive Grid:</strong> Perfectly scaling layout elements suitable for all tablet and desktop viewports.</span>
                          </li>
                        </ul>
                      </div>
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
