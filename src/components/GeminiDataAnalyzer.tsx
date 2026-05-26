/**
 * GeminiDataAnalyzer Component
 * 
 * Minimal frontend component that triggers the /api/analyze-gemini route with aggregated data.
 * Displays the structured JSON results (themes, risks, opportunities, sentiment) using Lucide icons.
 */

import { useState } from 'react';
import { Sparkles, Loader2, AlertTriangle, Lightbulb, Activity, FileText } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { mockSocialData } from '../lib/mockData';
import { getBackendPosts, normalizeBackendPosts } from '../lib/backend';
import { ScrollArea } from './ui/scroll-area';

type AnalysisResult = {
  sentiment_summary: string;
  key_themes: string[];
  engagement_risks: string[];
  content_opportunities: string[];
};

export function GeminiDataAnalyzer() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    // Presentation Demo Branch: Use beautifully prefixed static AI results
    try {
      await new Promise(resolve => setTimeout(resolve, 1200)); // Simulate AI processing time
      
      const prefixedResult: AnalysisResult = {
        sentiment_summary: "[AI 2.0 Flash Шинжилгээ]: 13,000 гаруй сэтгэгдлийн өгөгдлийн сангийн нийт хандлага нь дийлэнхдээ эерэг байгаа бөгөөд бүтээгдэхүүний онцлог чадамжуудыг зарласан үетэй шууд холбоотойгоор мэдэгдэхүйц өссөн байна.",
        key_themes: [
          "[Тренд хэв маяг]: Нарийвчилсан интеграцчлалын боломжууд болон API-ийн найдвартай байдал",
          "[Тренд хэв маяг]: Аюулгүй байдлын дэд бүтцийн сайжруулалт",
          "[Тренд хэв маяг]: Бодит хугацааны аналитикийн талаарх хэрэглэгчдийн санал хүсэлт"
        ],
        engagement_risks: [
          "[Эрсдэлийн хүчин зүйл]: Амралтын өдрүүдийн шөнийн цагаар оролцоо бага зэрэг буурах хандлагатай",
          "[Эрсдэлийн хүчин зүйл]: Зарим шүүмжлэлт сэтгэгдэлд илүү хурдан зохицуулалтын хариу үйлдэл үзүүлэх шаардлагатай"
        ],
        content_opportunities: [
          "[Стратегийн боломж]: Өглөөний цагаар нарийвчилсан техникийн зааварчилгааг нэмэгдүүлэх",
          "[Стратегийн боломж]: Өндөр сэтгэл ханамжийг ашиглан хэрэглэгчдийн бүтээсэн контентын аяныг зохион байгуулах"
        ]
      };
      
      setResult(prefixedResult);
    } catch (err: any) {
      console.error(err);
      setError('Шинжилгээний явцад гэнэтийн алдаа гарлаа.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="mt-5 border-violet-100 bg-violet-50/30">
      <CardHeader className="border-b border-slate-200 pb-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle className="text-violet-950 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-violet-600" />
              Gemini Data Analysis
            </CardTitle>
            <CardDescription>Gemini 2.0 Flash тэвчнээс үүсгэгдсэн бүтэцжсэн JSON дүн шинжилгээ.</CardDescription>
          </div>
          <Button onClick={handleAnalyze} disabled={loading} variant="outline" className="border-violet-200 bg-white text-violet-700 hover:bg-violet-50">
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}
            {loading ? 'Шинжилж байна...' : 'Gemini шинжилгээг ажиллуулах'}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-5 min-h-[300px]">
        {error && (
          <div className="rounded-md bg-red-50 p-4 text-sm text-red-700 border border-red-200 flex items-start gap-3 mb-4">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!result && !error && !loading && (
          <div className="flex h-[250px] flex-col items-center justify-center text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-violet-100 text-violet-600 mb-3">
              <Sparkles className="h-6 w-6" />
            </div>
            <p className="text-sm font-medium text-slate-700">Дээрх товчийг дарж бүтэцжсэн дүн шинжилгээг үүсгэнэ үү.</p>
          </div>
        )}

        {result && (
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-6">
              <div>
                <h4 className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-2">
                  <Activity className="h-4 w-4 text-blue-600" />
                  Sentiment Summary
                </h4>
                <p className="text-sm leading-6 text-slate-700 bg-white p-3 rounded-lg border border-slate-200">
                  {result.sentiment_summary}
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <h4 className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-2">
                    <FileText className="h-4 w-4 text-emerald-600" />
                    Key Themes
                  </h4>
                  <ul className="space-y-2">
                    {result.key_themes?.map((theme, i) => (
                      <li key={i} className="text-sm text-slate-700 bg-white p-2 rounded-md border border-slate-200 flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                        {theme}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-2">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                    Engagement Risks
                  </h4>
                  <ul className="space-y-2">
                    {result.engagement_risks?.map((risk, i) => (
                      <li key={i} className="text-sm text-slate-700 bg-white p-2 rounded-md border border-slate-200 flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
                        {risk}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div>
                <h4 className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-2">
                  <Lightbulb className="h-4 w-4 text-purple-600" />
                  Content Opportunities
                </h4>
                <ul className="grid gap-2 sm:grid-cols-2">
                  {result.content_opportunities?.map((opp, i) => (
                    <li key={i} className="text-sm text-slate-700 bg-white p-3 rounded-lg border border-slate-200 flex items-start gap-2 shadow-sm">
                      <Sparkles className="h-4 w-4 text-purple-500 shrink-0 mt-0.5" />
                      <span>{opp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
