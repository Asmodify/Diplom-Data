/**
 * Gemini AI Analysis Component
 * Provides UI for analyzing text with Google Gemini
 * Styled with White Glassmorphic Aurora light theme
 */

import { useState } from 'react';
import { motion } from 'motion/react';
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
      // Presentation Demo Branch: hardcoded beautiful AI responses
      await new Promise(resolve => setTimeout(resolve, 1000)); // fake delay
      
      const staticResponses: Record<AnalysisType, string> = {
        summary: "[AI Хураангуй]: Оруулсан текст нь нийгмийн сүлжээний хүчтэй хэв маягийг харуулж байна. Бүртгэгдсэн 13,000 гаруй харилцан үйлчлэлийн дунд шинэ бүтээгдэхүүний шинэчлэлтээс үүдэлтэй олон нийтийн эерэг хандлага давамгайлж байна.",
        insights: "[AI Гол санаанууд]:\n- Өндөр оролцоо нь визуал контенттой шууд хамааралтай байна\n- Хүн ам зүйн хувьд эерэг хандлага 76%-иас дээш үзүүлэлттэй байна\n- 13 мянга гаруй сэтгэгдэл нь хэлэлцүүлгийн гүнзгий сэдвүүдийг илтгэж байна",
        questions: "[AI Санал болгох асуултууд]:\n1. Ямар тодорхой шинэчлэлтүүд 76%-ийн эерэг хандлагыг бүрдүүлж байна вэ?\n2. Амралтын өдрүүдэд ажиглагдсан оролцооны оргил үеийг хэрхэн давтах вэ?",
        improvement: "[AI Агуулга сайжруулалт]: Хүртээмжийг дээд зэргээр нэмэгдүүлэхийн тулд гол түлхүүр үгсийг текстийн эхэнд оруулаарай. 13,000 гаруй харилцан үйлчлэлд тулгуурлан илүү тодорхой үйлдэлд дуудах (call-to-action) хэсгүүдийг нэмээд үз.",
        critique: "[AI Бүтээлч шүүмж]: Бүтэц нь сайн боловч өнгө аяс нь илүү харилцан ярианы шинжтэй байж болно. Өгөгдлөөс харахад хэрэглэгчид энгийн үг хэллэгтэй 2 дахин илүү харилцан үйлчлэлд ордог байна."
      };

      setResult(staticResponses[analysisType]);
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
      <motion.div variants={itemVariants}>
        <Card className="glass-card shadow-sm">
          <CardHeader className="border-b border-slate-200/50 pb-4">
            <CardTitle className="text-lg font-bold text-slate-900">Gemini AI шинжилгээ</CardTitle>
            <CardDescription className="text-xs text-slate-400">Текст оруулж, Gemini AI-аар шинжилгээ хийнэ.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-4">
            {/* Text Input */}
            <div className="space-y-2">
              <p className="text-sm font-medium text-slate-700">Шинжлэх текст</p>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Шинжлэх текстээ оруулна уу..."
                className="w-full h-32 rounded-2xl border border-slate-200 bg-white/50 p-4 text-sm text-slate-800 placeholder:text-slate-400 focus:border-purple-300 focus:outline-none focus:ring-1 focus:ring-purple-500/20 resize-none transition-colors"
              />
            </div>

            {/* Analysis Type Selection */}
            <div className="space-y-2">
              <p className="text-sm font-medium text-slate-700">Шинжилгээний төрөл</p>
              <div className="flex flex-wrap gap-2">
                {analysisOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setAnalysisType(option.value)}
                    className={`rounded-2xl border px-4 py-2 text-sm font-semibold transition-all duration-300 ${
                      analysisType === option.value
                        ? 'border-purple-200 bg-purple-50 text-purple-700 shadow-sm'
                        : 'border-slate-200 bg-white/40 text-slate-600 hover:border-slate-300 hover:bg-white/80'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-600">
                {error}
              </div>
            )}

            {/* Analyze Button */}
            <Button
              onClick={handleAnalyze}
              disabled={loading || !text.trim()}
              className="w-full gap-2 bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-xl shadow-md shadow-purple-500/20 h-10"
            >
              <Sparkles className="h-4 w-4" />
              {loading ? 'Шинжилж байна...' : 'Gemini-аар шинжлэх'}
            </Button>
          </CardContent>
        </Card>
      </motion.div>

      {/* Result Display */}
      {result && (
        <motion.div variants={itemVariants}>
          <Card className="glass-card border-purple-200/50 bg-gradient-to-br from-purple-500/5 via-indigo-500/5 to-cyan-500/5 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between gap-4 border-b border-slate-200/50 pb-4">
              <div>
                <CardTitle className="text-lg font-bold text-slate-900 capitalize">
                  {analysisOptions.find((o) => o.value === analysisType)?.label} үр дүн
                </CardTitle>
                <CardDescription className="text-xs text-slate-400">Gemini AI-н хариу</CardDescription>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleCopy} 
                className="gap-2 bg-white/60 border-slate-200 text-slate-600 rounded-xl"
              >
                {copied ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
                {copied ? 'Хуулсан' : 'Хуулах'}
              </Button>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="rounded-2xl border border-slate-200 bg-white/40 p-5">
                <p className="whitespace-pre-wrap text-sm leading-7 text-slate-700">{result}</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
