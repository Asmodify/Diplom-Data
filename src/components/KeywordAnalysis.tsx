import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import {
  Hash,
  Loader2,
  RefreshCw,
  TrendingUp,
  BarChart2,
  MessageCircle,
  Tag,
  AlertCircle,
  Layers,
  Activity
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { getTrends, getTopics } from '../lib/backend';
import { cn } from '../lib/utils';

type Trend = {
  trend: string;
  platform: string;
  mentions: number;
  type?: string;
};

type Topic = {
  topic: string;
  mentions: number;
  platform: string;
  avg_engagement: number;
};

const CHART_COLORS = ['#059669', '#0d9488', '#0284c7', '#4f46e5', '#7c3aed', '#c026d3', '#e11d48'];

export function KeywordAnalysis() {
  const [trends, setTrends] = useState<Trend[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [trendsRes, topicsRes] = await Promise.all([
        getTrends(15),
        getTopics(10)
      ]);

      if (trendsRes?.data) {
        setTrends(trendsRes.data);
      } else {
        throw new Error('Invalid trends response');
      }

      if (topicsRes?.data) {
        setTopics(topicsRes.data);
      }
    } catch (e) {
      console.error('Failed to load keywords data', e);
      setError('Түлхүүр үгийн өгөгдөл татахад алдаа гарлаа. (Туршилтын өгөгдөл харуулж байна)');
      
      // Fallback demo data
      setTrends([
        { trend: '#сонгууль2024', platform: 'facebook', mentions: 1240, type: 'hashtag' },
        { trend: '#мэдээ', platform: 'facebook', mentions: 850, type: 'hashtag' },
        { trend: 'хууль', platform: 'facebook', mentions: 720, type: 'keyword' },
        { trend: 'эдийн засаг', platform: 'facebook', mentions: 680, type: 'keyword' },
        { trend: '#боловсрол', platform: 'facebook', mentions: 540, type: 'hashtag' },
        { trend: 'засгийн газар', platform: 'facebook', mentions: 490, type: 'keyword' },
        { trend: 'төсөв', platform: 'facebook', mentions: 410, type: 'keyword' },
        { trend: '#спорт', platform: 'facebook', mentions: 380, type: 'hashtag' },
        { trend: 'эрүүл мэнд', platform: 'facebook', mentions: 350, type: 'keyword' },
        { trend: '#цаг_агаар', platform: 'facebook', mentions: 290, type: 'hashtag' },
      ]);
      
      setTopics([
        { topic: 'Улс төр ба Хууль', mentions: 450, platform: 'facebook', avg_engagement: 340.5 },
        { topic: 'Эдийн засаг, Төсөв', mentions: 320, platform: 'facebook', avg_engagement: 210.2 },
        { topic: 'Боловсрол, Нийгэм', mentions: 280, platform: 'facebook', avg_engagement: 450.8 },
        { topic: 'Спорт, Цэнгээнт нэвтрүүлэг', mentions: 150, platform: 'facebook', avg_engagement: 890.0 },
        { topic: 'Эрүүл мэнд, Эмнэлэг', mentions: 110, platform: 'facebook', avg_engagement: 180.4 },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Process data for charts
  const topTrends = trends.slice(0, 7);
  const tagCloudData = [...trends].sort(() => Math.random() - 0.5); // Shuffle for tag cloud effect

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-teal-700 to-emerald-900 p-8 text-white shadow-lg">
        <div className="relative z-10">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm font-medium text-teal-100 backdrop-blur-sm">
            <Activity className="h-4 w-4" />
            Тренд ба Сэдэв илрүүлэлт
          </div>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Түлхүүр үгийн Шинжилгээ</h1>
          <p className="mt-4 max-w-2xl text-lg text-teal-100/80 leading-relaxed">
            Нийгмийн сүлжээнд хамгийн их яригдаж буй сэдвүүд, түгээмэл хаштаг болон түлхүүр үгсийг нээн илрүүлж, тэдгээрийн оролцооны түвшинг харьцуулах.
          </p>
        </div>
        
        {/* Decorative background */}
        <div className="pointer-events-none absolute -right-10 -top-10 h-64 w-64 rounded-full bg-white opacity-5 blur-[60px]" />
        <div className="pointer-events-none absolute bottom-0 right-1/4 h-48 w-48 rounded-full bg-teal-400 opacity-10 blur-[50px]" />
        <Hash className="pointer-events-none absolute -bottom-8 -right-8 h-64 w-64 text-white opacity-5" strokeWidth={1} />
      </div>

      {error && (
        <div className="rounded-md bg-amber-50 p-4 border border-amber-200 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
          <p className="text-sm text-amber-800">{error}</p>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Top Keywords Bar Chart */}
        <Card className="shadow-sm border-slate-200">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-teal-600" />
                  Тэргүүлэх Түлхүүр үгс
                </CardTitle>
                <CardDescription>Хамгийн их дурдагдсан хаштаг болон үгс</CardDescription>
              </div>
              <Button variant="ghost" size="icon" onClick={loadData} disabled={isLoading} className="h-8 w-8">
                <RefreshCw className={cn("h-4 w-4 text-slate-500", isLoading && "animate-spin")} />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            {isLoading && topTrends.length === 0 ? (
              <div className="flex h-[300px] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-teal-600" />
              </div>
            ) : topTrends.length > 0 ? (
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topTrends} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#f1f5f9" />
                    <XAxis type="number" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis 
                      type="category" 
                      dataKey="trend" 
                      stroke="#475569" 
                      fontSize={12} 
                      tickLine={false} 
                      axisLine={false}
                      width={100}
                    />
                    <Tooltip 
                      cursor={{ fill: '#f8fafc' }}
                      contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    />
                    <Bar dataKey="mentions" name="Дурдагдсан тоо" radius={[0, 4, 4, 0]} barSize={24}>
                      {topTrends.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex h-[300px] items-center justify-center text-sm text-slate-500">
                Мэдээлэл олдсонгүй
              </div>
            )}
          </CardContent>
        </Card>

        {/* Tag Cloud */}
        <Card className="shadow-sm border-slate-200">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4">
            <CardTitle className="text-base flex items-center gap-2">
              <Tag className="h-5 w-5 text-teal-600" />
              Тренд үүл (Tag Cloud)
            </CardTitle>
            <CardDescription>Нийтлэг хэрэглэгдэж буй үгсийн тархалт</CardDescription>
          </CardHeader>
          <CardContent className="pt-6 flex items-center justify-center min-h-[300px]">
            {isLoading && tagCloudData.length === 0 ? (
              <Loader2 className="h-8 w-8 animate-spin text-teal-600" />
            ) : tagCloudData.length > 0 ? (
              <div className="flex flex-wrap justify-center content-center gap-3 p-4">
                {tagCloudData.map((item, index) => {
                  // Calculate font size relative to mentions (min 12px, max 32px)
                  const maxMentions = Math.max(...trends.map(t => t.mentions));
                  const minMentions = Math.min(...trends.map(t => t.mentions));
                  const range = maxMentions - minMentions || 1;
                  const normalizedSize = (item.mentions - minMentions) / range;
                  const fontSize = 12 + (normalizedSize * 24);
                  
                  // Calculate opacity based on mentions
                  const opacity = 0.5 + (normalizedSize * 0.5);
                  
                  return (
                    <motion.span
                      key={index}
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity, scale: 1 }}
                      transition={{ delay: index * 0.05 }}
                      className={cn(
                        "inline-block font-semibold transition-transform hover:scale-110 hover:opacity-100 cursor-default",
                        item.trend.startsWith('#') ? "text-blue-600" : "text-teal-700"
                      )}
                      style={{ fontSize: `${fontSize}px` }}
                      title={`${item.mentions} удаа дурдагдсан`}
                    >
                      {item.trend}
                    </motion.span>
                  );
                })}
              </div>
            ) : (
              <div className="text-sm text-slate-500">Мэдээлэл олдсонгүй</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Topic Modeling */}
      <Card className="shadow-sm border-slate-200">
        <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4">
          <CardTitle className="text-base flex items-center gap-2">
            <Layers className="h-5 w-5 text-teal-600" />
            Сэдвийн Ангилал ба Оролцоо (Topic Modeling)
          </CardTitle>
          <CardDescription>Нийтлэлүүдээс ялгаж авсан үндсэн сэдвүүд болон хэрэглэгчдийн дундаж оролцоо</CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {isLoading && topics.length === 0 ? (
            <div className="flex h-[250px] items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-teal-600" />
            </div>
          ) : topics.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {topics.map((topic, index) => (
                <motion.div 
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow"
                >
                  <h3 className="font-semibold text-slate-900 line-clamp-2 min-h-[2.5rem] mb-3">
                    {topic.topic}
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-xs text-slate-500 mb-1">
                        <span className="uppercase tracking-wider">Дурдагдсан тоо</span>
                        <span className="font-bold text-slate-700">{topic.mentions}</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                        <div 
                          className="h-full bg-teal-500 rounded-full" 
                          style={{ width: `${(topic.mentions / Math.max(...topics.map(t => t.mentions))) * 100}%` }}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex justify-between text-xs text-slate-500 mb-1">
                        <span className="uppercase tracking-wider flex items-center gap-1">
                          <MessageCircle className="h-3 w-3" /> Дундаж оролцоо
                        </span>
                        <span className="font-bold text-slate-700">{topic.avg_engagement.toFixed(1)}</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                        <div 
                          className="h-full bg-blue-500 rounded-full" 
                          style={{ width: `${(topic.avg_engagement / Math.max(...topics.map(t => t.avg_engagement))) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="flex h-[200px] items-center justify-center text-sm text-slate-500">
              Сэдэв олдсонгүй
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
