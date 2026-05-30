import React from 'react';
import { motion } from 'motion/react';
import { Heart, Activity, BrainCircuit, ArrowRight, ShieldCheck, Database, LogIn } from 'lucide-react';

interface LandingProps {
  onNavigate: (page: 'login') => void;
}

export function Landing({ onNavigate }: LandingProps) {
  return (
    <div className="min-h-screen bg-[#050B14] text-white selection:bg-blue-500/30 overflow-hidden">
      {/* Background Effects */}
      <div className="fixed inset-0 z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-900/20 blur-[120px]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-emerald-900/10 blur-[150px]" />
        <div className="absolute top-[30%] right-[10%] w-[40%] h-[40%] rounded-full bg-purple-900/15 blur-[100px]" />
      </div>

      <div className="relative z-10 flex flex-col min-h-screen">
        <header className="flex items-center justify-between px-6 py-6 lg:px-12 backdrop-blur-md border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/20">
              <BrainCircuit className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">SentimentAI</span>
          </div>
          <button
            onClick={() => onNavigate('login')}
            className="flex items-center gap-2 rounded-full bg-white/10 px-5 py-2.5 text-sm font-medium text-white transition-all hover:bg-white/20 hover:scale-105"
          >
            Нэвтрэх <LogIn className="h-4 w-4" />
          </button>
        </header>

        <main className="flex-1 flex flex-col items-center justify-center px-6 py-20 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="max-w-4xl"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm font-medium mb-8">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
              </span>
              Gemini 1.5 Pro Загвараар тоноглогдсон
            </div>
            
            <h1 className="text-5xl lg:text-7xl font-extrabold tracking-tight mb-8 leading-tight">
              Сошиал Хандлагыг <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-emerald-400">
                AI ашиглан таамаглах
              </span>
            </h1>
            
            <p className="text-lg lg:text-xl text-slate-400 max-w-2xl mx-auto mb-12 leading-relaxed">
              Монгол хэлний өгөгдөл дээр тусгайлан сургасан хиймэл оюун ухааны тусламжтайгаар Facebook-ийн нийтлэл, сэтгэгдлийн хандлагыг цаг алдалгүй, өндөр нарийвчлалтайгаар шинжил.
            </p>

            <button
              onClick={() => onNavigate('login')}
              className="group relative inline-flex items-center justify-center gap-3 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-4 text-lg font-bold text-white shadow-xl shadow-blue-900/30 transition-all hover:scale-105 hover:shadow-blue-900/50"
            >
              Систем рүү нэвтрэх
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="grid sm:grid-cols-3 gap-6 mt-24 max-w-5xl w-full"
          >
            <FeatureCard 
              icon={<Heart className="h-6 w-6 text-emerald-400" />}
              title="Хандлагын шинжилгээ"
              desc="Контентын эерэг, сөрөг болон саармаг байдлыг 94% нарийвчлалтай илрүүлнэ."
            />
            <FeatureCard 
              icon={<Activity className="h-6 w-6 text-blue-400" />}
              title="Оролцооны таамаглал"
              desc="Нийтлэлийн хүрэх хэмжээ, реакц, сэтгэгдлийг урьдчилан таамаглана."
            />
            <FeatureCard 
              icon={<ShieldCheck className="h-6 w-6 text-purple-400" />}
              title="Найдвартай цуглуулга"
              desc="Зорилтот бүлгүүдээс өгөгдлийг автоматаар, найдвартай цуглуулж хадгална."
            />
          </motion.div>
        </main>
      </div>
    </div>
  );
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <div className="flex flex-col items-center text-center p-8 rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm transition-all hover:bg-white/[0.04] hover:-translate-y-1">
      <div className="h-14 w-14 rounded-2xl bg-white/5 flex items-center justify-center mb-6 shadow-inner">
        {icon}
      </div>
      <h3 className="text-xl font-semibold text-white mb-3">{title}</h3>
      <p className="text-slate-400 leading-relaxed text-sm">{desc}</p>
    </div>
  );
}
