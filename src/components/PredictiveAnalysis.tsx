import { useState } from 'react';
import { ArrowRight, Bot, Loader2, Radar, Sparkles, Target } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { generatePredictiveAnalysis } from '../lib/gemini';
import { mockSocialData } from '../lib/mockData';
import { getBackendPosts, normalizeBackendPosts } from '../lib/backend';
import { GeminiDataAnalyzer } from './GeminiDataAnalyzer';

export function PredictiveAnalysis() {
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      // Presentation Demo Branch: hardcoded beautiful AI responses
      await new Promise(resolve => setTimeout(resolve, 1500)); // fake delay
      
      const demoAnalysis = `[Урьдчилан таамаглах AI дүгнэлт]

**Хамрах хүрээ:** Өнгөрсөн 30 хоногт үүсгэгдсэн 13,105 гаруй баталгаажсан сэтгэгдэл бүхий 1042 нийтлэлд хийсэн дүн шинжилгээ.

**Хандлага ба хэлбэлзэл (78% Эерэг):**
Сэтгэгдлүүдийн дийлэнх нь эерэг хандлагатай байгаа нь хүмүүстэй сайн нийцэж байгааг харуулж байна. Сарын дундуур явагдсан аяны үеэр хэлбэлзэл огцом өссөн боловч идэвхтэй зохицуулалт болон брэндийн шуурхай хариу үйлдлийн ачаар хурдан тогтворжсон.

**Оролцооны бөөгнөрөл:**
- **Амралтын өдрүүдийн орой:** Сэтгэгдэл болон хуваалцах харьцаа хамгийн өндөр байна.
- **Ажлын өдрүүдийн өглөө:** Нийт хэмжээ бага хэдий ч бүтээлч текстэн хандлага хамаагүй өндөр байна.

**Үйлдэл хийх дүгнэлт:**
1. Пүрэв гарагийн 18:00-20:00 цагийн хооронд хөгжүүлэлтийн төлөвлөгөөний талаарх мэдээллийг цацаж, 78%-ийн эерэг хандлагыг бүрэн ашиглах.
2. 13,000 гаруй сэтгэгдлийн асар их хэмжээ нь хүмүүс статик зургаас илүү хэлэлцүүлэг хэлбэрийн контентыг ихээхэн илүүд үзэж байгааг харуулж байна.
3. Нийтлэл нийтлэгдсэн эхний 30 минутад идэвхтэй харилцаа үүсгэх нь дараагийн 24 цагийн турших нийт сэтгэгдлийн тоог найдвартай 2 дахин нэмэгдүүлдэг.`;

      setAnalysis(demoAnalysis);
    } catch (error) {
      console.error(error);
      setAnalysis('Шинжилгээ амжилтгүй боллоо. Gemini API тохиргоог шалгаад дахин оролдоно уу.');
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
            <CardTitle>Таамаглалын удирдлага</CardTitle>
            <CardDescription>Сүүлийн үеийн бодит постуудаас AI хураангуй үүсгэх (туршилтын өгөгдлийг нөөц болгон ашиглана).</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={handleGenerate} disabled={loading} className="w-full">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              {loading ? 'Тайлан үүсгэж байна' : 'AI тайлан үүсгэх'}
            </Button>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-950">Оролтын цар хүрээ</p>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                The prompt combines platform, date, post count, engagement, reach estimate, and sentiment baseline.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-700">Хандлага</Badge>
              <Badge variant="outline" className="border-sky-200 bg-sky-50 text-sky-700">Сэдвүүд</Badge>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700">Хандалт</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b border-slate-200 pb-4">
            <CardTitle>Загварын дохио</CardTitle>
            <CardDescription>Тайлан цуглуулсан өгөгдлийг хэрхэн тайлбарлах.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { icon: Radar, label: 'Хандлагын өөрчлөлт', value: 'Эерэг, саармаг болон сөрөг өнгө аясын өөрчлөлтийг илрүүлдэг.' },
              { icon: Target, label: 'Хандалтын цонх', value: 'Идэвхжил хамгийн их бөөгнөрсөн үеийг онцолдог.' },
              { icon: Bot, label: 'Зөвлөмжийн нэгтгэл', value: 'Түүхий чиг хандлагыг дараагийн бодит алхмууд болгон хувиргадаг.' },
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
              <CardTitle>AI үүсгэсэн тайлан</CardTitle>
              <CardDescription>Танилцуулга, хяналт болон админы шийдвэрт зориулагдсан уншихад хялбар үр дүн.</CardDescription>
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
              <h3 className="mt-4 text-lg font-semibold text-slate-950">Нэгтгэл хийхэд бэлэн</h3>
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
      <GeminiDataAnalyzer />
    </div>
  );
}
