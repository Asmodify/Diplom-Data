/**
 * Gemini Q&A Component
 * Interactive question-answer interface with Gemini
 */

import { useState, useRef, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { ScrollArea } from './ui/scroll-area';

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
      setError('Please enter a question');
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
      const response = await apiClient.askGemini(input, context || undefined);

      if (response.status === 'success') {
        const answerId = (Date.now() + 1).toString();
        const answerMessage: Message = {
          id: answerId,
          type: 'answer',
          content: response.answer || '',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, answerMessage]);
      } else {
        setError('Failed to get answer: ' + response.error);
      }
    } catch (err) {
      setError(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
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
    <div className="flex flex-col h-full space-y-4">
      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-4">Ask Gemini</h2>

        {/* Context Section */}
        <div className="mb-4 space-y-2">
          <button
            onClick={() => setShowContext(!showContext)}
            className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-2"
          >
            {showContext ? '▼' : '▶'} Optional Context
          </button>

          {showContext && (
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Provide context for more relevant answers..."
              className="w-full h-20 p-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}
      </Card>

      {/* Messages Area */}
      <Card className="flex-1 p-4 overflow-hidden">
        <ScrollArea className="h-full pr-4">
          <div ref={scrollRef} className="space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <p>Ask me anything!</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.type === 'question' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      msg.type === 'question'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-900'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    <span className="text-xs opacity-70 mt-1 block">
                      {msg.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-200 text-gray-900 px-4 py-2 rounded-lg">
                  <p className="text-sm">Thinking...</p>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </Card>

      {/* Input Area */}
      <Card className="p-4 space-y-3">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
            placeholder="Ask a question..."
            disabled={loading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <Button
            onClick={handleAsk}
            disabled={loading || !input.trim()}
            className="px-6"
          >
            {loading ? '...' : 'Send'}
          </Button>
        </div>

        {messages.length > 0 && (
          <button
            onClick={handleClear}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Clear conversation
          </button>
        )}
      </Card>
    </div>
  );
}
