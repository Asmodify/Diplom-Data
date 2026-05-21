import { useEffect, useState, useRef, type ComponentType } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { mn } from 'date-fns/locale';
import { motion } from 'motion/react';
import {
  CheckCircle2,
  Layers3,
  PlugZap,
  RefreshCw,
  Share2,
  ShieldAlert,
  Play,
  Terminal as TerminalIcon,
  Plus,
  Trash2,
  Save,
  Loader2,
  StopCircle,
} from 'lucide-react';
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
  const [scraperLogs, setScraperLogs] = useState('Console initialized. Press LAUNCH AUTOMATION to begin.');
  const [loadingPages, setLoadingPages] = useState(true);
  const [savingPages, setSavingPages] = useState(false);
  const [runningScraper, setRunningScraper] = useState(false);
  
  const logTerminalRef = useRef<HTMLPreElement>(null);
  const connectedCount = dataSources.filter((source) => source.connected).length;

  // Load pages.txt and scraper status
  const loadConfiguration = async () => {
    try {
      setLoadingPages(true);
      const [pagesRes, statusRes, logsRes] = await Promise.all([
        apiClient.getPages(),
        apiClient.getScraperStatus(),
        apiClient.getScraperLogs(150),
      ]);

      if (pagesRes.status === 'success' && pagesRes.pages) {
        setPages(pagesRes.pages);
      }
      if (statusRes.status === 'success') {
        setScraperActive(statusRes.active);
      }
      if (logsRes.status === 'success' && logsRes.logs) {
        setScraperLogs(logsRes.logs);
      }
    } catch (err) {
      console.error('Failed to load scraper config', err);
      setScraperLogs('Failed to connect to backend scraper API.\nFallback to mock terminal output.');
    } finally {
      setLoadingPages(false);
    }
  };

  useEffect(() => {
    void loadConfiguration();
  }, []);

  // Poll logs and status when scraper is active
  useEffect(() => {
    let intervalId: number;

    const pollLogs = async () => {
      try {
        const [statusRes, logsRes] = await Promise.all([
          apiClient.getScraperStatus(),
          apiClient.getScraperLogs(150),
        ]);

        if (statusRes.status === 'success') {
          setScraperActive(statusRes.active);
        }
        if (logsRes.status === 'success' && logsRes.logs) {
          setScraperLogs(logsRes.logs);
        }
      } catch (err) {
        console.warn('Scraper polling failed', err);
      }
    };

    if (scraperActive) {
      intervalId = window.setInterval(pollLogs, 2000);
    }

    return () => {
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, [scraperActive]);

  // Auto-scroll logs terminal to bottom
  useEffect(() => {
    if (logTerminalRef.current) {
      logTerminalRef.current.scrollTop = logTerminalRef.current.scrollHeight;
    }
  }, [scraperLogs]);

  // Handle adding a page target
  const handleAddPage = () => {
    if (!newPage.trim()) {
      return;
    }
    const link = newPage.trim();
    if (!pages.includes(link)) {
      setPages([...pages, link]);
    }
    setNewPage('');
  };

  // Handle removing a page target
  const handleRemovePage = (indexToRemove: number) => {
    setPages(pages.filter((_, idx) => idx !== indexToRemove));
  };

  // Save updated pages to pages.txt
  const handleSavePages = async () => {
    setSavingPages(true);
    try {
      const res = await apiClient.savePages(pages);
      if (res.status === 'success') {
        setScraperLogs((prev) => `${prev}\n[System] Pages targets updated successfully in pages.txt.`);
      }
    } catch (err) {
      console.error('Failed to save pages targets', err);
      alert('Failed to save targets to pages.txt');
    } finally {
      setSavingPages(false);
    }
  };

  // Trigger background scraping run
  const handleLaunchScraper = async () => {
    setRunningScraper(true);
    setScraperLogs((prev) => `${prev}\n[System] Invoking scraper execution in background thread...`);
    try {
      const res = await apiClient.runScraper();
      if (res.status === 'success') {
        setScraperActive(true);
        setScraperLogs((prev) => `${prev}\n[System] Selenium Scraper process successfully triggered.`);
      } else {
        setScraperLogs((prev) => `${prev}\n[System] Scraper trigger refused: ${res.message}`);
      }
    } catch (err) {
      console.error('Failed to start scraper', err);
      setScraperLogs((prev) => `${prev}\n[System Error] Failed to contact scraper run endpoint.`);
    } finally {
      setRunningScraper(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.08 } },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 350, damping: 26 } },
  };

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-6">
      {/* Title Bar */}
      <motion.div variants={itemVariants} className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between border-b border-slate-200/50 pb-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.35em] text-purple-600/80">Өгөгдлийн Сорьцууд</p>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Эх сурвалж ба скрапинг удирдлага</h2>
          <p className="mt-1.5 max-w-3xl text-xs sm:text-sm text-slate-500">
            Сошиал платформуудын холболтын төлөв, хаягийн удирдлага, болон Selenium скрапинг ажиллагааг удирдах хяналтын төв.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start lg:self-auto">
          <Button 
            onClick={loadConfiguration} 
            variant="outline" 
            size="sm" 
            className="bg-white/60 border-slate-200 text-slate-600 gap-1.5 h-9 rounded-xl"
          >
            <RefreshCw className="h-4 w-4" />
            Дахин ачаалах
          </Button>
        </div>
      </motion.div>

      {/* 3 Quick Summary Cards */}
      <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-3">
        <SummaryCard 
          title="Синхрончлол" 
          value={`${connectedCount}/${dataSources.length} Холбоотой`} 
          hint="Идэвхтэй сошиал холбоосууд" 
          icon={CheckCircle2} 
          accent="purple"
        />
        <SummaryCard 
          title="Скрапинг төлөв" 
          value={scraperActive ? "Скрапинг идэвхтэй" : "Ажиллаагүй байна"} 
          hint={scraperActive ? "Selenium арын горимд ажиллаж байна" : "Скрапинг хийхэд бэлэн"} 
          icon={scraperActive ? Loader2 : Play} 
          accent={scraperActive ? "emerald" : "slate"}
          spin={scraperActive}
        />
        <SummaryCard 
          title="Нэгдсэн өгөгдөл" 
          value="Олон суваг" 
          hint="Facebook, Twitter, Instagram" 
          icon={Layers3} 
          accent="pink"
        />
      </motion.div>

      {/* Split-Screen Dashboard: Left Targets Manager, Right Log Terminal */}
      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        
        {/* Left Screen: Page Targets Manager */}
        <motion.div variants={itemVariants} className="space-y-6">
          <Card className="glass-card shadow-sm h-full flex flex-col">
            <CardHeader className="border-b border-slate-200/50 pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-bold text-slate-900">Скрапинг хаягууд (pages.txt)</CardTitle>
                  <CardDescription className="text-xs text-slate-400">Цуглуулах фэйсбүүк хуудасны хаяг эсвэл ID-нууд.</CardDescription>
                </div>
                <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200/50 font-semibold py-0.5">
                  {pages.length} Хаяг
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-5 flex-1 flex flex-col justify-between space-y-4">
              
              {/* Input for new links */}
              <div className="flex gap-2">
                <Input
                  value={newPage}
                  onChange={(e) => setNewPage(e.target.value)}
                  placeholder="https://www.facebook.com/cnn эсвэл хуудасны ID..."
                  className="rounded-xl border-slate-200 bg-white/50 text-sm h-10 placeholder:text-slate-400"
                  onKeyDown={(e) => e.key === 'Enter' && handleAddPage()}
                />
                <Button 
                  onClick={handleAddPage} 
                  className="bg-purple-600 hover:bg-purple-700 text-white rounded-xl gap-1 h-10 px-4"
                >
                  <Plus className="h-4 w-4" />
                  Нэмэх
                </Button>
              </div>

              {/* Target List */}
              {loadingPages ? (
                <div className="flex flex-col items-center justify-center py-12 text-slate-400">
                  <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
                  <p className="mt-2 text-xs">Хаягуудыг уншиж байна...</p>
                </div>
              ) : pages.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 border border-dashed border-slate-200 rounded-2xl bg-slate-50/50 text-center">
                  <p className="text-sm font-semibold text-slate-500">Скрап хийх хаяг байхгүй байна</p>
                  <p className="mt-1 text-xs text-slate-400">Дээрх талбараар шинэ фэйсбүүк хаяг нэмнэ үү.</p>
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-200/60 bg-white/40 overflow-hidden divide-y divide-slate-100 max-h-[260px] overflow-y-auto p-1.5 space-y-1.5">
                  {pages.map((page, index) => (
                    <div 
                      key={`${page}-${index}`} 
                      className="flex items-center justify-between p-3.5 rounded-xl hover:bg-slate-100/50 transition-colors group"
                    >
                      <span className="text-xs sm:text-sm font-semibold text-slate-700 truncate max-w-[82%]">{page}</span>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRemovePage(index)}
                        className="h-8 w-8 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg opacity-80 group-hover:opacity-100 transition-all"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {/* Save changes button */}
              <Button
                onClick={handleSavePages}
                disabled={savingPages || loadingPages}
                className="w-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-xl gap-2 h-10 shadow-md shadow-purple-500/20"
              >
                {savingPages ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                {savingPages ? 'Хадгалж байна...' : 'Жагсаалтыгpages.txt-д хадгалах'}
              </Button>
            </CardContent>
          </Card>
        </motion.div>

        {/* Right Screen: Virtual Log Streaming Terminal */}
        <motion.div variants={itemVariants} className="space-y-6">
          <Card className="glass-card shadow-sm h-full flex flex-col">
            <CardHeader className="border-b border-slate-200/50 pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TerminalIcon className="h-4 w-4 text-slate-600" />
                  <CardTitle className="text-base font-bold text-slate-900">Системийн Лог Консол</CardTitle>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "h-2 w-2 rounded-full",
                    scraperActive ? "bg-emerald-500 glow-indicator-active animate-pulse" : "bg-rose-500 glow-indicator-inactive"
                  )} />
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                    {scraperActive ? 'Active' : 'Offline'}
                  </span>
                </div>
              </div>
              <CardDescription className="text-xs text-slate-400">Selenium скрапинг ажиллагааны явцын бодит цагийн лог.</CardDescription>
            </CardHeader>
            <CardContent className="pt-4 flex-1 flex flex-col justify-between space-y-4">
              
              {/* Monospaced Log Stream Pre Element */}
              <div className="relative">
                <pre 
                  ref={logTerminalRef}
                  className="terminal-console rounded-2xl p-4 overflow-y-auto h-[260px] text-[10px] sm:text-xs font-mono whitespace-pre-wrap leading-relaxed select-text"
                >
                  {scraperLogs}
                </pre>
                
                {/* Clear button overlay */}
                <button
                  onClick={() => setScraperLogs('[Terminal] Logs box cleared.')}
                  className="absolute top-2 right-2 px-2.5 py-1 text-[9px] font-bold uppercase rounded-lg bg-white/5 text-slate-400 border border-white/10 hover:bg-white/10 hover:text-white transition-colors"
                >
                  Clear Box
                </button>
              </div>

              {/* Automation Launch controller button */}
              <Button
                onClick={handleLaunchScraper}
                disabled={scraperActive || runningScraper}
                className={cn(
                  "w-full rounded-xl gap-2 h-10 shadow-md transition-all duration-300 font-semibold",
                  scraperActive 
                    ? "bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed"
                    : "bg-emerald-500 hover:bg-emerald-600 text-white shadow-emerald-500/10"
                )}
              >
                {runningScraper ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : scraperActive ? (
                  <StopCircle className="h-4 w-4" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                {runningScraper 
                  ? 'Эхлүүлж байна...' 
                  : scraperActive 
                    ? 'СКРАПИНГ ИДЭВХТЭЙ БАЙНА' 
                    : 'СКРАПИНГ АЖИЛЛАГААГ ЭХЛҮҮЛЭХ'
                }
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Connected Source Cards Grid */}
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="grid gap-4 md:grid-cols-3">
          {dataSources.map((source) => (
            <motion.div variants={itemVariants} key={source.id}>
              <Card className="h-full glass-card hover:-translate-y-1 shadow-sm">
                <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0 pb-3">
                  <div>
                    <CardTitle className="text-sm font-bold text-slate-900">{source.name}</CardTitle>
                    <CardDescription className="text-[11px] mt-0.5">{source.connected ? 'Синхрон холболт нээлттэй' : 'Холбогдоогүй'}</CardDescription>
                  </div>
                  <Badge variant={source.connected ? 'default' : 'outline'} className={cn(
                    source.connected ? 'bg-emerald-100 text-emerald-700 border-emerald-200 hover:bg-emerald-100' : 'bg-slate-50 text-slate-400 border-slate-200'
                  )}>
                    {source.connected ? 'Идэвхтэй' : 'Offline'}
                  </Badge>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="rounded-2xl border border-slate-100 bg-slate-50/50 p-3.5">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
                      <span>Sync Health</span>
                      <span>{source.connected ? '100%' : '0%'}</span>
                    </div>
                    <div className="mt-2 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                      <div className={cn(
                        'h-full rounded-full', 
                        source.connected ? 'w-[100%] bg-gradient-to-r from-emerald-400 to-cyan-400' : 'w-[0%] bg-slate-300'
                      )} />
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-white/40 p-3.5 text-xs text-slate-500">
                    {source.connected && source.lastSync ? (
                      <p className="leading-relaxed">
                        Сүүлийн өгөгдөл: <strong className="text-slate-700">{formatDistanceToNow(new Date(source.lastSync), { addSuffix: true, locale: mn })}</strong>
                      </p>
                    ) : (
                      <p className="leading-relaxed">Одоогоор өгөгдөл татагдаагүй байна.</p>
                    )}
                  </div>

                  <Button variant={source.connected ? 'outline' : 'default'} className="w-full gap-1.5 h-9 rounded-xl text-xs">
                    {source.connected ? (
                      <>
                        <Share2 className="h-3.5 w-3.5" /> Салгах
                      </>
                    ) : (
                      <>
                        <PlugZap className="h-3.5 w-3.5" /> Холбох
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Operational notes */}
        <motion.div variants={itemVariants} className="space-y-6">
          <Card className="glass-card bg-gradient-to-br from-purple-500/5 to-indigo-500/5 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-200/50">
              <CardTitle className="text-sm font-bold text-slate-900">Өгөгдөл шинэчлэлийн урсгал</CardTitle>
              <CardDescription className="text-xs text-slate-400">Скрапинг хэрхэн ажилладаг вэ?</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3.5 pt-4">
              {[
                { label: '1. Хаяг унших', value: 'pages.txt-ээс цуглуулах фэйсбүүк хуудсыг тодорхойлно.', accent: 'bg-purple-500' },
                { label: '2. Скрапинг', value: 'Selenium ашиглан хуудасны пост, сэтгэгдлийг цуглуулна.', accent: 'bg-cyan-500' },
                { label: '3. Хадгалах', value: 'Цугларсан өгөгдөл Supabase PostgreSQL рүү шууд орно.', accent: 'bg-emerald-500' },
              ].map((step) => (
                <div key={step.label} className="flex gap-3 rounded-2xl border border-slate-200/60 bg-white/40 p-3 shadow-inner">
                  <span className={cn('mt-1.5 h-2 w-2 rounded-full shrink-0', step.accent)} />
                  <div>
                    <p className="text-xs font-bold text-slate-800">{step.label}</p>
                    <p className="mt-0.5 text-[11px] leading-relaxed text-slate-500">{step.value}</p>
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

interface SummaryCardProps {
  title: string;
  value: string;
  hint: string;
  icon: ComponentType<{ className?: string }>;
  accent: 'purple' | 'emerald' | 'pink' | 'slate';
  spin?: boolean;
}

function SummaryCard({
  title,
  value,
  hint,
  icon: Icon,
  accent,
  spin,
}: SummaryCardProps) {
  const accentClasses = {
    purple: 'bg-purple-50 text-purple-700 border-purple-200/60',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200/60',
    pink: 'bg-pink-50 text-pink-700 border-pink-200/60',
    slate: 'bg-slate-50 text-slate-600 border-slate-200',
  };

  return (
    <Card className="glass-card shadow-sm border border-slate-200/60">
      <CardContent className="flex items-center justify-between gap-4 p-5">
        <div className="space-y-1">
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-400">{title}</p>
          <p className="text-xl font-bold text-slate-850 tracking-tight">{value}</p>
          <p className="text-[11px] text-slate-400">{hint}</p>
        </div>
        <div className={cn("flex h-12 w-12 items-center justify-center rounded-2xl border shadow-inner shrink-0", accentClasses[accent])}>
          <Icon className={cn("h-5 w-5", spin && "animate-spin")} />
        </div>
      </CardContent>
    </Card>
  );
}
