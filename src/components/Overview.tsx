/**
 * Overview Component
 * 
 * Displays educational content about Generative AI, Large Language Models,
 * and Embedding Models. Provides context for users of the social media
 * analysis system to understand how the AI features work.
 */

import { BookOpen, Brain, MessageSquareText, Layers } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';

export function Overview() {
  return (
    <div className="space-y-5">
      {/* Hero Card */}
      <Card>
        <CardHeader className="border-b border-slate-200 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
              <BookOpen className="h-5 w-5" />
            </div>
            <div>
              <CardTitle>AI Overview</CardTitle>
              <CardDescription>
                Beginner-friendly introduction to the AI concepts powering this system.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-5">
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <p className="text-sm leading-6 text-blue-900">
              <strong>Note:</strong> This page introduces key artificial intelligence concepts used in this
              Social Media Analysis System. The system uses the{' '}
              <span className="font-semibold">Vercel AI SDK</span> to standardize integrating AI models
              across supported providers, enabling us to focus on building great analysis features
              instead of wasting time on technical details.
            </p>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-700">Vercel AI SDK</Badge>
            <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700">Gemini 2.0 Flash</Badge>
            <Badge variant="outline" className="border-violet-200 bg-violet-50 text-violet-700">Supabase</Badge>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-5 xl:grid-cols-2">
        {/* Generative AI */}
        <Card>
          <CardHeader className="border-b border-slate-200 pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-100 text-violet-700">
                <Brain className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-base">Generative Artificial Intelligence</CardTitle>
                <CardDescription>Models that create new content from learned patterns</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-5 space-y-4">
            <p className="text-sm leading-6 text-slate-700">
              <strong>Generative artificial intelligence</strong> refers to models that predict and generate
              various types of outputs (such as text, images, or audio) based on what&rsquo;s statistically
              likely, pulling from patterns they&rsquo;ve learned from their training data.
            </p>
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Examples</p>
              <div className="space-y-2">
                {[
                  'Given a photo, a generative model can generate a caption.',
                  'Given an audio file, a generative model can generate a transcription.',
                  'Given a text description, a generative model can generate an image.',
                ].map((example) => (
                  <div key={example} className="flex items-start gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500" />
                    <p className="text-sm text-slate-700">{example}</p>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Large Language Models */}
        <Card>
          <CardHeader className="border-b border-slate-200 pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
                <MessageSquareText className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-base">Large Language Models</CardTitle>
                <CardDescription>Text-focused generative models</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-5 space-y-4">
            <p className="text-sm leading-6 text-slate-700">
              A <strong>large language model (LLM)</strong> is a subset of generative models focused
              primarily on <strong>text</strong>. An LLM takes a sequence of words as input and aims to
              predict the most likely sequence to follow. It assigns probabilities to potential next
              sequences and then selects one. The model continues to generate sequences until it meets a
              specified stopping criterion.
            </p>
            <p className="text-sm leading-6 text-slate-700">
              LLMs learn by training on massive collections of written text, which means they will be
              better suited to some use cases than others. For example, a model trained on GitHub data
              would understand the probabilities of sequences in source code particularly well.
            </p>
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
              <p className="text-sm leading-6 text-amber-900">
                <strong>⚠ Important:</strong> When asked about less known or absent information,
                LLMs might &ldquo;hallucinate&rdquo; or make up information. It&rsquo;s essential to
                consider how well-represented the information you need is in the model.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Embedding Models */}
      <Card>
        <CardHeader className="border-b border-slate-200 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-100 text-sky-700">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-base">Embedding Models</CardTitle>
              <CardDescription>Convert complex data into dense vector representations</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-5 space-y-4">
          <p className="text-sm leading-6 text-slate-700">
            An <strong>embedding model</strong> is used to convert complex data (like words or images)
            into a dense vector (a list of numbers) representation, known as an <strong>embedding</strong>.
            Unlike generative models, embedding models do not generate new text or data. Instead, they
            provide representations of semantic and syntactic relationships between entities that can be
            used as input for other models or other natural language processing tasks.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { label: 'Input', desc: 'Complex data such as text, images, or audio' },
              { label: 'Process', desc: 'Converts into a dense numerical vector' },
              { label: 'Output', desc: 'Embeddings usable by other models and tasks' },
            ].map((step) => (
              <div key={step.label} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{step.label}</p>
                <p className="mt-1 text-sm text-slate-700">{step.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* How This System Uses AI */}
      <Card>
        <CardHeader className="border-b border-slate-200 pb-4">
          <CardTitle className="text-base">How This System Uses AI</CardTitle>
          <CardDescription>Our implementation powered by the Vercel AI SDK and Google Gemini</CardDescription>
        </CardHeader>
        <CardContent className="pt-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[
              { step: '1', label: 'Collect', desc: 'Scrape social media posts from Facebook pages via FastAPI backend' },
              { step: '2', label: 'Store', desc: 'Persist posts, comments, and images in Supabase (PostgreSQL)' },
              { step: '3', label: 'Aggregate', desc: 'Pre-aggregate data to limit payload size before sending to AI' },
              { step: '4', label: 'Analyze', desc: 'Send to Gemini 2.0 Flash via Vercel AI SDK for structured insights' },
            ].map((item) => (
              <div key={item.step} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700">{item.step}</div>
                <p className="mt-2 text-sm font-semibold text-slate-950">{item.label}</p>
                <p className="mt-1 text-sm leading-6 text-slate-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
