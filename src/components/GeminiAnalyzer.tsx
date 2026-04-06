/**
 * Gemini AI Analysis Component
 * Provides UI for analyzing text with Google Gemini
 */

import { useState } from 'react';
import { apiClient } from '@/lib/api';
import { Button } from './ui/button';
import { Card } from './ui/card';

type AnalysisType = 'summary' | 'insights' | 'questions' | 'improvement' | 'critique';

export function GeminiAnalyzer() {
  const [text, setText] = useState('');
  const [analysisType, setAnalysisType] = useState<AnalysisType>('summary');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const analysisOptions: { label: string; value: AnalysisType }[] = [
    { label: 'Summary', value: 'summary' },
    { label: 'Key Insights', value: 'insights' },
    { label: 'Discussion Questions', value: 'questions' },
    { label: 'Content Improvement', value: 'improvement' },
    { label: 'Constructive Critique', value: 'critique' },
  ];

  const handleAnalyze = async () => {
    if (!text.trim()) {
      setError('Please enter text to analyze');
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
        setError('Analysis failed: ' + response.error);
      }
    } catch (err) {
      setError(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-4">Gemini AI Analysis</h2>

        <div className="space-y-4">
          {/* Text Input */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Text to Analyze
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter text to analyze..."
              className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Analysis Type Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Analysis Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              {analysisOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setAnalysisType(option.value)}
                  className={`p-2 rounded border-2 transition-colors ${
                    analysisType === option.value
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700">
              {error}
            </div>
          )}

          {/* Analyze Button */}
          <Button
            onClick={handleAnalyze}
            disabled={loading || !text.trim()}
            className="w-full"
          >
            {loading ? 'Analyzing...' : 'Analyze with Gemini'}
          </Button>
        </div>
      </Card>

      {/* Result Display */}
      {result && (
        <Card className="p-6 bg-blue-50">
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-bold text-lg capitalize">
              {analysisType.replace(/([A-Z])/g, ' $1').trim()} Result
            </h3>
            <button
              onClick={() => {
                navigator.clipboard.writeText(result);
              }}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Copy
            </button>
          </div>
          <p className="text-gray-800 whitespace-pre-wrap">{result}</p>
        </Card>
      )}
    </div>
  );
}
