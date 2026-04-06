import { useState } from 'react';
import { Loader2, Sparkles, Radar, Target, Bot, ArrowUpRight } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { generatePredictiveAnalysis } from '../lib/gemini';
import { mockSocialData } from '../lib/mockData';

export function PredictiveAnalysis() {
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const result = await generatePredictiveAnalysis(mockSocialData);
      setAnalysis(result);
    } catch (error) {
      console.error(error);
      setAnalysis('Шинжилгээ хийхэд алдаа гарлаа.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/70">Analysis</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Таамаглалт шинжилгээ</h2>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-300">
            Gemini ашиглан өгөгдлийн тренд, engagement боломж, болон дараагийн алхмын зөвлөмжүүдийг one-click тайлан болгон гаргана.
          </p>
        </div>
        <Button onClick={handleGenerate} disabled={loading} className="gap-2 self-start lg:self-auto">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          {loading ? 'Шинжилж байна...' : 'Шинжилгээ үүсгэх'}
        </Button>
      </div>

      <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-5">
          <Card className="border-white/10 bg-white/[0.03]">
            <CardHeader>
              <CardTitle className="text-lg text-white">Model signals</CardTitle>
              <CardDescription>What the analysis engine is looking at.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { icon: Radar, label: 'Sentiment drift', value: 'Positive tone leads the trend', accent: 'text-cyan-200' },
                { icon: Target, label: 'Engagement window', value: 'Most activity clusters mid-week', accent: 'text-emerald-200' },
                { icon: Bot, label: 'AI synthesis', value: 'Gemini merges signals into recommendations', accent: 'text-rose-200' },
              ].map((item) => (
                <div key={item.label} className="flex items-start gap-3 rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                  <div className={item.accent}>
                    <item.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{item.label}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-400">{item.value}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-cyan-400/15 bg-gradient-to-br from-cyan-400/10 to-slate-900/70">
            <CardHeader>
              <CardTitle className="text-lg text-white">Analysis workflow</CardTitle>
              <CardDescription>Compact view of the prediction pipeline.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm leading-6 text-slate-300">
              <p className="flex items-center gap-2 text-cyan-100"><ArrowUpRight className="h-4 w-4" /> Collect social signals</p>
              <p className="flex items-center gap-2 text-cyan-100"><ArrowUpRight className="h-4 w-4" /> Combine content, timing, and interaction patterns</p>
              <p className="flex items-center gap-2 text-cyan-100"><ArrowUpRight className="h-4 w-4" /> Generate readable recommendations</p>
              <div className="flex flex-wrap gap-2 pt-2">
                <Badge variant="default">Sentiment</Badge>
                <Badge variant="secondary">Topic</Badge>
                <Badge variant="outline">Engagement</Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="min-h-[640px] border-white/10 bg-white/[0.03]">
          <CardHeader>
            <CardTitle className="text-lg text-white">AI generated report</CardTitle>
            <CardDescription>Generated from recent sample data and backend context.</CardDescription>
          </CardHeader>
          <CardContent className="flex min-h-[560px] flex-col">
            {analysis ? (
              <ScrollArea className="flex-1 rounded-3xl border border-white/10 bg-slate-950/70 p-5">
                <div className="whitespace-pre-wrap text-sm leading-7 text-slate-200">{analysis}</div>
              </ScrollArea>
            ) : (
              <div className="flex flex-1 flex-col items-center justify-center rounded-3xl border border-dashed border-white/10 bg-slate-950/40 px-8 py-12 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-cyan-400/12 text-cyan-200">
                  <Sparkles className="h-7 w-7" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-white">Ready for synthesis</h3>
                <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">
                  Click the button above to generate a clean AI report on engagement, sentiment, and content opportunities.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
