import { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Activity,
  BarChart3,
  BookOpen,
  Bot,
  Database,
  LayoutDashboard,
  Menu,
  ServerCog,
  Settings,
  ShieldCheck,
  X,
} from 'lucide-react';
import { cn } from './lib/utils';
import { Dashboard } from './components/Dashboard';
import { DataSources } from './components/DataSources';
import { PredictiveAnalysis } from './components/PredictiveAnalysis';
import { AdminControl } from './components/AdminControl';
import { Badge } from './components/ui/badge';
import { Overview } from './components/Overview';

type TabId = 'dashboard' | 'sources' | 'analysis' | 'admin' | 'overview' | 'settings';

const tabs: Array<{
  id: TabId;
  label: string;
  description: string;
  icon: typeof LayoutDashboard;
}> = [
  {
    id: 'dashboard',
    label: 'Хянах самбар',
    description: 'Шууд цуглуулсан тоон үзүүлэлтүүд, хандалтын чиг хандлага болон сүүлийн үеийн сошиал мэдээллүүд.',
    icon: LayoutDashboard,
  },
  {
    id: 'sources',
    label: 'Өгөгдлийн эх сурвалжууд',
    description: 'Цуглуулах зорилтууд, эх сурвалжийн байдал болон автоматжуулалтын түүхийг удирдах.',
    icon: Database,
  },
  {
    id: 'analysis',
    label: 'AI Шинжилгээ',
    description: 'Хамгийн сүүлд цуглуулсан постуудаас урьдчилан таамагласан хураангуй үүсгэх.',
    icon: BarChart3,
  },
  {
    id: 'admin',
    label: 'Админ',
    description: 'Арын системийн эрүүл мэндийг шалгах, цуглуулсан өгөгдлийг шүүх болон хязгаарыг тохируулах.',
    icon: ShieldCheck,
  },
  {
    id: 'overview',
    label: 'AI Тойм',
    description: 'AI ойлголтуудын талаар суралцах: үүсгэгч загварууд, LLMs болон эмбеддингүүд.',
    icon: BookOpen,
  },
  {
    id: 'settings',
    label: 'Тохиргоо',
    description: 'Системийн тохиргоо болон байршуулах төгсгөлийн цэгүүдийг шалгах.',
    icon: Settings,
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');
  const [mobileOpen, setMobileOpen] = useState(false);

  const activeTabMeta = useMemo(
    () => tabs.find((tab) => tab.id === activeTab) ?? tabs[0],
    [activeTab],
  );

  const selectTab = (tab: TabId) => {
    setActiveTab(tab);
    setMobileOpen(false);
  };

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-slate-900">
      <div className="mx-auto flex min-h-screen w-full max-w-[1680px]">
        <aside className="sticky top-0 hidden h-screen w-72 shrink-0 border-r border-slate-200 bg-white px-5 py-6 lg:block">
          <Sidebar activeTab={activeTab} onSelect={selectTab} />
        </aside>

        {mobileOpen && (
          <div className="fixed inset-0 z-40 bg-slate-950/30 backdrop-blur-sm lg:hidden" onClick={() => setMobileOpen(false)}>
            <aside
              className="h-full w-[min(22rem,88vw)] border-r border-slate-200 bg-white px-5 py-5 shadow-2xl"
              onClick={(event) => event.stopPropagation()}
            >
              <div className="mb-5 flex items-center justify-between">
                <Brand />
                <button
                  type="button"
                  onClick={() => setMobileOpen(false)}
                  className="rounded-lg border border-slate-200 p-2 text-slate-500 hover:bg-slate-50"
                  aria-label="Close navigation"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <Sidebar activeTab={activeTab} onSelect={selectTab} compactBrand />
            </aside>
          </div>
        )}

        <main className="min-w-0 flex-1 px-4 py-4 sm:px-6 lg:px-8 lg:py-6">
          <header className="mb-5 rounded-lg border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div className="min-w-0">
                <div className="mb-3 flex items-center gap-3 lg:hidden">
                  <button
                    type="button"
                    onClick={() => setMobileOpen(true)}
                    className="rounded-lg border border-slate-200 p-2 text-slate-600 hover:bg-slate-50"
                    aria-label="Open navigation"
                  >
                    <Menu className="h-5 w-5" />
                  </button>
                  <Brand />
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-700">
                    Сошиал Медиа Шинжилгээний Систем
                  </Badge>
                  <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700">
                    Backend-тэй холбогдсон
                  </Badge>
                </div>
                <h1 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">
                  {activeTabMeta.label}
                </h1>
                <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600">
                  {activeTabMeta.description}
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-3 xl:w-[560px]">
                <StatusTile icon={Activity} label="Дамжлага" value="Цуглуулах -> Хадгалах -> Шинжлэх" />
                <StatusTile icon={ServerCog} label="Ажиллах орчин" value="FastAPI + Supabase" />
                <StatusTile icon={Bot} label="AI давхарга" value="Gemini тайлангууд" />
              </div>
            </div>
          </header>

          <AnimatePresence mode="wait">
            <motion.section
              key={activeTab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === 'dashboard' && <Dashboard />}
              {activeTab === 'sources' && <DataSources />}
              {activeTab === 'analysis' && <PredictiveAnalysis />}
              {activeTab === 'admin' && <AdminControl />}
              {activeTab === 'overview' && <Overview />}
              {activeTab === 'settings' && <SettingsPanel />}
            </motion.section>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

function Sidebar({
  activeTab,
  onSelect,
  compactBrand = false,
}: {
  activeTab: TabId;
  onSelect: (tab: TabId) => void;
  compactBrand?: boolean;
}) {
  return (
    <div className="flex h-full flex-col">
      {!compactBrand && <Brand />}
      <nav className={cn('space-y-1.5', !compactBrand && 'mt-8')}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const active = tab.id === activeTab;

          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onSelect(tab.id)}
              className={cn(
                'flex w-full items-center gap-3 rounded-lg border px-3 py-3 text-left transition-colors',
                active
                  ? 'border-blue-200 bg-blue-50 text-blue-800'
                  : 'border-transparent text-slate-600 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-950',
              )}
            >
              <Icon className={cn('h-5 w-5 shrink-0', active ? 'text-blue-700' : 'text-slate-400')} />
              <span className="min-w-0">
                <span className="block text-sm font-semibold">{tab.label}</span>
                <span className="mt-0.5 line-clamp-1 block text-xs text-slate-500">{tab.description}</span>
              </span>
            </button>
          );
        })}
      </nav>

      <div className="mt-auto rounded-lg border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Төслийн цар хүрээ</p>
        <p className="mt-2 text-sm leading-6 text-slate-700">
          Дипломын судалгааны өгөгдөлд зориулсан мэдээлэл цуглуулах, хадгалах, хянах болон AI-ийн тусламжтай тайлагнах.
        </p>
      </div>
    </div>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white">
        <BarChart3 className="h-5 w-5" />
      </div>
      <div>
        <p className="text-sm font-semibold leading-5 text-slate-950">Ойлголтын Удирдлага</p>
        <p className="text-xs text-slate-500">Сошиал шинжилгээний ажлын талбар</p>
      </div>
    </div>
  );
}

function StatusTile({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Activity;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className="mt-2 text-sm font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function SettingsPanel() {
  const items = [
    ['Backend API', import.meta.env.VITE_BACKEND_API_URL || 'https://diplom-data-api.onrender.com'],
    ['Дотоод API', import.meta.env.VITE_API_URL || 'http://localhost:8000'],
    ['Баталгаажуулах горим', import.meta.env.VITE_API_TOKEN ? 'Токен тохируулагдсан' : 'Хөгжүүлэлтийн токен'],
    ['Байршуулалт', 'Vite frontend, Render/FastAPI backend'],
  ];

  return (
    <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">Тохиргоо</h2>
        <p className="mt-1 text-sm leading-6 text-slate-600">
          Эдгээр утгуудыг Vite орчноос уншиж, frontend API харилцагчид ашигладаг.
        </p>
        <div className="mt-5 divide-y divide-slate-200 rounded-lg border border-slate-200">
          {items.map(([label, value]) => (
            <div key={label} className="grid gap-1 p-4 sm:grid-cols-[11rem_1fr] sm:items-center">
              <p className="text-sm font-medium text-slate-600">{label}</p>
              <p className="break-all text-sm font-semibold text-slate-950">{value}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">Системийн Тэмдэглэл</h2>
        <div className="mt-4 space-y-3">
          {[
            'Хянах самбар нь backend-ээс бодит постуудыг ашиглах ба холбогдох боломжгүй үед туршилтын өгөгдлийг ашигладаг.',
            'Цуглуулах зорилтуудыг удирдах хэсэг нь дотоод FastAPI үйлчилгээг ажиллаж байхыг шаарддаг.',
            'Сүлжээний ачааллыг тодорхой байлгахын тулд AI тайлангуудыг зөвхөн шаардлагатай үед үүсгэдэг.',
          ].map((note) => (
            <p key={note} className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm leading-6 text-slate-700">
              {note}
            </p>
          ))}
        </div>
      </section>
    </div>
  );
}
