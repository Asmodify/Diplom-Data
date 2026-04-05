import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { ScrollArea } from '../../components/ui/scroll-area';
import { generatePredictiveAnalysis } from '../lib/gemini';
import { mockSocialData } from '../lib/mockData';
import { Loader2, Sparkles } from 'lucide-react';

export function PredictiveAnalysis() {
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const result = await generatePredictiveAnalysis(mockSocialData);
      setAnalysis(result);
    } catch (_error) {
      setAnalysis('Шинжилгээ хийхэд алдаа гарлаа.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Таамаглалт Шинжилгээ</h2>
          <p className="text-muted-foreground">
            Хиймэл оюун ухаан (Gemini) ашиглан сошиал медиа өгөгдөлдөө дүн шинжилгээ хийж, дараагийн алхмаа төлөвлөнө үү.
          </p>
        </div>
        <Button onClick={handleGenerate} disabled={loading} className="gap-2">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          {loading ? 'Шинжилж байна...' : 'Шинжилгээ үүсгэх'}
        </Button>
      </div>

      <Card className="h-[600px] flex flex-col">
        <CardHeader>
          <CardTitle>Хиймэл Оюун Ухааны Тайлан</CardTitle>
          <CardDescription>
            Сүүлийн 7 хоногийн өгөгдөл дээр үндэслэсэн таамаглал болон зөвлөмжүүд.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-1 overflow-hidden">
          {analysis ? (
            <ScrollArea className="h-full w-full rounded-md border p-4">
              <div className="whitespace-pre-wrap text-sm leading-relaxed">
                {analysis}
              </div>
            </ScrollArea>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground space-y-4">
              <Sparkles className="h-12 w-12 opacity-20" />
              <p>Шинжилгээ үүсгэх товчийг дарж тайлангаа авна уу.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
