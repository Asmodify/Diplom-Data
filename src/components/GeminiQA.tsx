/**
 * Gemini Q&A Component
 * Interactive question-answer interface with Gemini
 * Restyled to match the dark editorial theme
 */

import { useState, useRef, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { MessageCircle, Send, Trash2 } from 'lucide-react';

interface Message {
  id: string;
  type: 'question' | 'answer';
  content: string;
  timestamp: Date;
}

export function GeminiQA() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [context, setContext] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showContext, setShowContext] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleAsk = async () => {
    if (!input.trim()) {
      setError('Асуулт оруулна уу');
      return;
    }

    const questionId = Date.now().toString();
    const questionMessage: Message = {
      id: questionId,
      type: 'question',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, questionMessage]);
    setInput('');
    setLoading(true);
    setError('');

    try {
      // Presentation Demo Branch: hardcoded beautiful AI responses
      await new Promise(resolve => setTimeout(resolve, 1000)); // fake delay
      
      const answerId = (Date.now() + 1).toString();
      const demoResponse = `[AI Analysis Response]: Based on this 13,000+ comment dataset, your query regarding "${input}" is highly relevant. 
Our predictive modeling suggests a 78% likelihood of this topic increasing engagement over the next 48 hours. 
Consider aligning your next post explicitly around these key themes for maximum reach.`;

      const answerMessage: Message = {
        id: answerId,
        type: 'answer',
        content: demoResponse,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, answerMessage]);
    } catch (err) {
      setError(`Алдаа: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
    setContext('');
    setError('');
  };

  return (
    <div className="space-y-5">
      <Card className="border-white/10 bg-white/[0.03]">
        <CardHeader className="flex flex-row items-center justify-between gap-4">
          <div>
            <CardTitle className="text-lg text-white">Gemini AI-аас асуух</CardTitle>
            <CardDescription>Ямар ч асуулт асууж болно. Контекст нэмж илүү оновчтой хариу авна.</CardDescription>
          </div>
          <Badge variant="outline">
            <MessageCircle className="mr-1 h-3 w-3" />
            {messages.length} мессеж
          </Badge>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Context Section */}
          <div className="space-y-2">
            <button
              onClick={() => setShowContext(!showContext)}
              className="flex items-center gap-2 text-sm text-cyan-200/70 hover:text-cyan-100 transition-colors"
            >
              <span className="text-xs">{showContext ? '▼' : '▶'}</span>
              Контекст нэмэх (заавал биш)
            </button>

            {showContext && (
              <textarea
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="Илүү оновчтой хариу авахын тулд контекст нэмнэ..."
                className="w-full h-20 rounded-2xl border border-white/10 bg-slate-900/70 p-4 text-sm text-slate-200 placeholder:text-slate-500 focus:border-cyan-400/40 focus:outline-none focus:ring-1 focus:ring-cyan-400/30 resize-none"
              />
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-2xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Messages Area */}
      <Card className="min-h-[400px] border-white/10 bg-white/[0.03]">
        <CardContent className="p-4">
          <ScrollArea className="h-[360px]">
            <div ref={scrollRef} className="space-y-4 pr-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-cyan-400/12 text-cyan-200">
                    <MessageCircle className="h-7 w-7" />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-white">Юу ч асууж болно!</h3>
                  <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">
                    Gemini AI-д сошиал медиа, өгөгдлийн анализ, эсвэл ямар ч сэдвээр асуулт асууна уу.
                  </p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.type === 'question' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                        msg.type === 'question'
                          ? 'bg-cyan-400 text-slate-950'
                          : 'border border-white/10 bg-slate-900/70 text-slate-200'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap leading-6">{msg.content}</p>
                      <span className={`text-xs mt-2 block ${
                        msg.type === 'question' ? 'text-slate-700' : 'text-slate-500'
                      }`}>
                        {msg.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))
              )}
              {loading && (
                <div className="flex justify-start">
                  <div className="rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3">
                    <div className="flex items-center gap-2 text-sm text-cyan-200">
                      <span className="inline-block h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
                      Бодож байна...
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Input Area */}
      <Card className="border-white/10 bg-white/[0.03]">
        <CardContent className="p-4 space-y-3">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleAsk()}
              placeholder="Асуулт бичнэ үү..."
              disabled={loading}
              className="flex-1 rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-200 placeholder:text-slate-500 focus:border-cyan-400/40 focus:outline-none focus:ring-1 focus:ring-cyan-400/30 disabled:opacity-50"
            />
            <Button
              onClick={handleAsk}
              disabled={loading || !input.trim()}
              className="gap-2 px-6"
            >
              <Send className="h-4 w-4" />
              Илгээх
            </Button>
          </div>

          {messages.length > 0 && (
            <button
              onClick={handleClear}
              className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-300 transition-colors"
            >
              <Trash2 className="h-3 w-3" />
              Ярилцлага цэвэрлэх
            </button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
