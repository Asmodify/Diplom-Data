import { useState } from 'react';
import { ArrowRight, Bot, Loader2, Radar, Sparkles, Target } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { generatePredictiveAnalysis } from '../lib/gemini';
import { mockSocialData } from '../lib/mockData';
import { getBackendPosts, normalizeBackendPosts } from '../lib/backend';
import { ClaudeAnalyzer } from './ClaudeAnalyzer';
import { GeminiDataAnalyzer } from './GeminiDataAnalyzer';

export function PredictiveAnalysis() {
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      let dataToAnalyze;

      try {
        const posts = await getBackendPosts(50);
        if (posts.length > 0) {
          const livePosts = normalizeBackendPosts(posts);
          const summary = livePosts.reduce<Record<string, { date: string; platform: string; posts: number; engagement: number; reach: number; sentiment: number }>>((acc, post) => {
            const key = `${post.date}-${post.platform}`;
            acc[key] ??= { date: post.date, platform: post.platform, posts: 0, engagement: 0, reach: 0, sentiment: 0.5 };
            acc[key].posts += 1;
            acc[key].engagement += post.engagement;
            acc[key].reach += post.engagement * 10;
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
      setAnalysis('Analysis failed. Check the Gemini API configuration and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="grid gap-5 xl:grid-cols-[0.82fr_1.18fr]">
        <div className="space-y-5">
        <Card>
          <CardHeader className="border-b border-slate-200 pb-4">
            <CardTitle>Prediction controls</CardTitle>
            <CardDescription>Generate an AI summary from recent live posts, with demo data as fallback.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={handleGenerate} disabled={loading} className="w-full">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              {loading ? 'Generating report' : 'Generate AI report'}
            </Button>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-950">Input scope</p>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                The prompt combines platform, date, post count, engagement, reach estimate, and sentiment baseline.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-700">Sentiment</Badge>
              <Badge variant="outline" className="border-sky-200 bg-sky-50 text-sky-700">Topics</Badge>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700">Engagement</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b border-slate-200 pb-4">
            <CardTitle>Model signals</CardTitle>
            <CardDescription>How the report interprets the collected data.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { icon: Radar, label: 'Sentiment drift', value: 'Detects shifts in positive, neutral, and negative tone.' },
              { icon: Target, label: 'Engagement window', value: 'Highlights periods where activity clusters.' },
              { icon: Bot, label: 'Recommendation synthesis', value: 'Turns raw trends into operational next steps.' },
            ].map((item) => (
              <div key={item.label} className="flex gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
                <item.icon className="mt-0.5 h-5 w-5 shrink-0 text-blue-700" />
                <div>
                  <p className="text-sm font-semibold text-slate-950">{item.label}</p>
                  <p className="mt-1 text-sm leading-6 text-slate-600">{item.value}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card className="min-h-[620px]">
        <CardHeader className="border-b border-slate-200 pb-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <CardTitle>AI generated report</CardTitle>
              <CardDescription>Readable output for presentation, review, or admin decisions.</CardDescription>
            </div>
            <Sparkles className="h-5 w-5 text-blue-700" />
          </div>
        </CardHeader>
        <CardContent className="flex min-h-[530px] flex-col">
          {analysis ? (
            <ScrollArea className="flex-1 rounded-lg border border-slate-200 bg-slate-50 p-5">
              <div className="whitespace-pre-wrap text-sm leading-7 text-slate-800">{analysis}</div>
            </ScrollArea>
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 px-8 py-12 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                <Sparkles className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-slate-950">Ready for synthesis</h3>
              <p className="mt-2 max-w-md text-sm leading-6 text-slate-600">
                Generate a report to summarize trends, engagement risks, and content opportunities.
              </p>
              <div className="mt-4 flex items-center gap-2 text-sm font-medium text-blue-700">
                Live data when available <ArrowRight className="h-4 w-4" /> demo fallback otherwise
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      </div>
      <ClaudeAnalyzer />
      <GeminiDataAnalyzer />
    </div>
  );
}
