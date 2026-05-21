import { useState } from 'react';
import { motion } from 'motion/react';
import { Loader2, Sparkles, Radar, Target, Bot, ArrowUpRight } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { generatePredictiveAnalysis } from '../lib/gemini';
import { mockSocialData } from '../lib/mockData';
import { getBackendPosts, normalizeBackendPosts } from '../lib/backend';

export function PredictiveAnalysis() {
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      // Fetch live data from PostgreSQL (via Python backend)
      let dataToAnalyze;
      try {
        const posts = await getBackendPosts(50);
        if (posts && posts.length > 0) {
          const livePosts = normalizeBackendPosts(posts);
          // Summarize by platform and date to keep prompt size reasonable
          const summary = livePosts.reduce((acc: any, post) => {
            const key = `${post.date}-${post.platform}`;
            if (!acc[key]) {
              acc[key] = { date: post.date, platform: post.platform, posts: 0, engagement: 0, reach: 0, sentiment: 0.5 };
            }
            acc[key].posts += 1;
            acc[key].engagement += post.engagement;
            acc[key].reach += post.engagement * 10; // rough estimate
            return acc;
          }, {});
          dataToAnalyze = Object.values(summary);
        } else {
          dataToAnalyze = mockSocialData;
        }
      } catch (err) {
        console.warn('Backend fetch failed, falling back to mock data', err);
        dataToAnalyze = mockSocialData;
      }

      const result = await generatePredictiveAnalysis(dataToAnalyze);
      setAnalysis(result);
    } catch (error) {
      console.error(error);
      setAnalysis('Шинжилгээ хийхэд алдаа гарлаа.');
    } finally {
      setLoading(false);
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
      {/* Header */}
      <motion.div variants={itemVariants} className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between border-b border-slate-200/50 pb-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.35em] text-purple-600/80">Analysis</p>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Таамаглалт шинжилгээ</h2>
          <p className="mt-1.5 max-w-3xl text-xs sm:text-sm leading-relaxed text-slate-500">
            Gemini ашиглан өгөгдлийн тренд, engagement боломж, болон дараагийн алхмын зөвлөмжүүдийг one-click тайлан болгон гаргана.
          </p>
        </div>
        <Button 
          onClick={handleGenerate} 
          disabled={loading} 
          className="gap-2 self-start lg:self-auto bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-xl shadow-md shadow-purple-500/20 h-10 px-5"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          {loading ? 'Шинжилж байна...' : 'Шинжилгээ үүсгэх'}
        </Button>
      </motion.div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-6">
          {/* Model Signals Card */}
          <motion.div variants={itemVariants}>
            <Card className="glass-card shadow-sm">
              <CardHeader className="border-b border-slate-200/50 pb-4">
                <CardTitle className="text-lg font-bold text-slate-900">Model signals</CardTitle>
                <CardDescription className="text-xs text-slate-400">What the analysis engine is looking at.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 pt-4">
                {[
                  { icon: Radar, label: 'Sentiment drift', value: 'Positive tone leads the trend', accent: 'text-purple-600' },
                  { icon: Target, label: 'Engagement window', value: 'Most activity clusters mid-week', accent: 'text-emerald-600' },
                  { icon: Bot, label: 'AI synthesis', value: 'Gemini merges signals into recommendations', accent: 'text-rose-600' },
                ].map((item) => (
                  <div key={item.label} className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white/40 p-4 transition-all duration-300 hover:bg-white/80 hover:border-slate-300">
                    <div className={item.accent}>
                      <item.icon className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{item.label}</p>
                      <p className="mt-1 text-sm leading-6 text-slate-500">{item.value}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>

          {/* Analysis Workflow Card */}
          <motion.div variants={itemVariants}>
            <Card className="glass-card border-purple-200/50 bg-gradient-to-br from-purple-500/5 via-indigo-500/5 to-cyan-500/5 shadow-sm">
              <CardHeader className="border-b border-slate-200/50 pb-4">
                <CardTitle className="text-lg font-bold text-slate-900">Analysis workflow</CardTitle>
                <CardDescription className="text-xs text-slate-400">Compact view of the prediction pipeline.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm leading-6 text-slate-600 pt-4">
                <p className="flex items-center gap-2 text-purple-700"><ArrowUpRight className="h-4 w-4" /> Collect social signals</p>
                <p className="flex items-center gap-2 text-purple-700"><ArrowUpRight className="h-4 w-4" /> Combine content, timing, and interaction patterns</p>
                <p className="flex items-center gap-2 text-purple-700"><ArrowUpRight className="h-4 w-4" /> Generate readable recommendations</p>
                <div className="flex flex-wrap gap-2 pt-2">
                  <Badge variant="secondary" className="bg-purple-100 text-purple-700 border-purple-200/50 font-semibold">Sentiment</Badge>
                  <Badge variant="secondary" className="bg-cyan-100 text-cyan-700 border-cyan-200/50 font-semibold">Topic</Badge>
                  <Badge variant="outline" className="bg-white/60 border-slate-200 text-slate-600">Engagement</Badge>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* AI Report Card */}
        <motion.div variants={itemVariants}>
          <Card className="min-h-[640px] glass-card shadow-sm">
            <CardHeader className="border-b border-slate-200/50 pb-4">
              <CardTitle className="text-lg font-bold text-slate-900">AI generated report</CardTitle>
              <CardDescription className="text-xs text-slate-400">Generated from recent sample data and backend context.</CardDescription>
            </CardHeader>
            <CardContent className="flex min-h-[560px] flex-col pt-4">
              {analysis ? (
                <ScrollArea className="flex-1 rounded-3xl border border-slate-200 bg-white/40 p-5">
                  <div className="whitespace-pre-wrap text-sm leading-7 text-slate-700">{analysis}</div>
                </ScrollArea>
              ) : (
                <div className="flex flex-1 flex-col items-center justify-center rounded-3xl border border-dashed border-slate-200 bg-slate-50/50 px-8 py-12 text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-purple-100 text-purple-600">
                    <Sparkles className="h-7 w-7" />
                  </div>
                  <h3 className="mt-4 text-lg font-bold text-slate-900">Ready for synthesis</h3>
                  <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">
                    Click the button above to generate a clean AI report on engagement, sentiment, and content opportunities.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  );
}
