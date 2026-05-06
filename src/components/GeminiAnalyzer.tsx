/**
 * Gemini AI Analysis Component
 * Provides UI for analyzing text with Google Gemini
 * Restyled to match the dark editorial theme
 */

import { useState } from 'react';
import { apiClient } from '@/lib/api';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Sparkles, Copy, CheckCircle2 } from 'lucide-react';

type AnalysisType = 'summary' | 'insights' | 'questions' | 'improvement' | 'critique';

export function GeminiAnalyzer() {
  const [text, setText] = useState('');
  const [analysisType, setAnalysisType] = useState<AnalysisType>('summary');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const analysisOptions: { label: string; value: AnalysisType }[] = [
    { label: 'Хураангуй', value: 'summary' },
    { label: 'Гол санаанууд', value: 'insights' },
    { label: 'Хэлэлцүүлгийн асуулт', value: 'questions' },
    { label: 'Сайжруулалт', value: 'improvement' },
    { label: 'Шүүмж', value: 'critique' },
  ];

  const handleAnalyze = async () => {
    if (!text.trim()) {
      setError('Шинжлэх текст оруулна уу');
      return;
    }

    setLoading(true);
    setError('');
    setResult('');

    try {
      const response = await apiClient.analyzeWithGemini(text, analysisType);

      if (response.status === 'success') {
        setResult(response.result || '');
      } else {
        setError('Шинжилгээ амжилтгүй: ' + response.error);
      }
    } catch (err) {
      setError(`Алдаа: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-5">
      <Card className="border-white/10 bg-white/[0.03]">
        <CardHeader>
          <CardTitle className="text-lg text-white">Gemini AI шинжилгээ</CardTitle>
          <CardDescription>Текст оруулж, Gemini AI-аар шинжилгээ хийнэ.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Text Input */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-slate-200">Шинжлэх текст</p>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Шинжлэх текстээ оруулна уу..."
              className="w-full h-32 rounded-2xl border border-white/10 bg-slate-900/70 p-4 text-sm text-slate-200 placeholder:text-slate-500 focus:border-cyan-400/40 focus:outline-none focus:ring-1 focus:ring-cyan-400/30 resize-none"
            />
          </div>

          {/* Analysis Type Selection */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-slate-200">Шинжилгээний төрөл</p>
            <div className="flex flex-wrap gap-2">
              {analysisOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setAnalysisType(option.value)}
                  className={`rounded-2xl border px-4 py-2 text-sm transition-colors ${
                    analysisType === option.value
                      ? 'border-cyan-400/40 bg-cyan-400/12 text-cyan-100'
                      : 'border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20 hover:bg-white/[0.05]'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-2xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200">
              {error}
            </div>
          )}

          {/* Analyze Button */}
          <Button
            onClick={handleAnalyze}
            disabled={loading || !text.trim()}
            className="w-full gap-2"
          >
            <Sparkles className="h-4 w-4" />
            {loading ? 'Шинжилж байна...' : 'Gemini-аар шинжлэх'}
          </Button>
        </CardContent>
      </Card>

      {/* Result Display */}
      {result && (
        <Card className="border-cyan-400/15 bg-gradient-to-br from-cyan-400/10 to-slate-900/70">
          <CardHeader className="flex flex-row items-center justify-between gap-4">
            <div>
              <CardTitle className="text-lg text-white capitalize">
                {analysisOptions.find((o) => o.value === analysisType)?.label} үр дүн
              </CardTitle>
              <CardDescription>Gemini AI-н хариу</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={handleCopy} className="gap-2">
              {copied ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
              {copied ? 'Хуулсан' : 'Хуулах'}
            </Button>
          </CardHeader>
          <CardContent>
            <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-5">
              <p className="whitespace-pre-wrap text-sm leading-7 text-slate-200">{result}</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
