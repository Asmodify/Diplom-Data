/**
 * Overview Component
 * 
 * Displays educational content about Generative AI, Томоохон хэлний загварууд (LLM),
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
              <CardTitle>AI Тойм</CardTitle>
              <CardDescription>
                Beginner-friendly introduction to the AI concepts powering this system.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-5">
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <p className="text-sm leading-6 text-blue-900">
              <strong>Тэмдэглэл:</strong> This page introduces key artificial intelligence concepts used in this
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
                <CardTitle className="text-base">Үүсгэгч Хиймэл Оюун Ухаан</CardTitle>
                <CardDescription>Суралцсан хэв маягаас шинэ контент үүсгэдэг загварууд</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-5 space-y-4">
            <p className="text-sm leading-6 text-slate-700">
              <strong>Үүсгэгч хиймэл оюун ухаан</strong> нь таамаглал дэвшүүлж, шинээр үүсгэдэг загваруудыг хэлдэг
              текст, зураг эсвэл дуу гэх мэт төрөл бүрийн гарагуудыг статистикийн хувьд
              юу илүү магадлалтай байгааг сургалтын өгөгдлөөс нь авч ашигладаг.
            </p>
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Жишээнүүд</p>
              <div className="space-y-2">
                {[
                  'Зураг өгөхөд үүсгэгч загвар тайлбар үүсгэж чадна.',
                  'Дуу өгөхөд үүсгэгч загвар бичвэр үүсгэж чадна.',
                  'Бичвэр тайлбар өгөхөд үүсгэгч загвар зураг үүсгэж чадна.',
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

        {/* Томоохон хэлний загварууд (LLM) */}
        <Card>
          <CardHeader className="border-b border-slate-200 pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
                <MessageSquareText className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-base">Томоохон хэлний загварууд (LLM)</CardTitle>
                <CardDescription>Текстэд төвлөрсөн үүсгэгч загварууд</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-5 space-y-4">
            <p className="text-sm leading-6 text-slate-700">
              <strong>Томоохон хэлний загвар (LLM)</strong> нь үндсэндээ
              <strong>текст</strong> дээр төвлөрдөг үүсгэгч загваруудын дэд хэсэг юм. LLM нь үгсийн дарааллыг оролт болгон авч,
              дараагийн хамгийн магадлалтай дарааллыг таамаглахыг зорьдог. Энэ нь боломжит
              дараагийн дарааллуудад магадлал оноож, нэгийг нь сонгодог. Загвар тогтоосон
              зогсох нөхцөлд хүрэх хүртэл үргэлжлүүлэн үүсгэдэг.
            </p>
            <p className="text-sm leading-6 text-slate-700">
              LLM-үүд нь асар их хэмжээний бичвэрээс суралцдаг ба энэ нь
              тэд зарим хэрэглээнд илүү тохиромжтой байх болно гэсэн үг юм. Жишээ нь, GitHub өгөгдөл дээр
              сургагдсан загвар эх кодын дарааллын магадлалыг онцгой сайн ойлгоно.
            </p>
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
              <p className="text-sm leading-6 text-amber-900">
                <strong>⚠ Important:</strong> When asked about less known or absent information,
                LLM-үүд "хий үзэгдэл" харж эсвэл мэдээлэл зохиож магадгүй. Таны хэрэгцээт мэдээлэл
                загварт хэр сайн тусгагдсан болохыг анхаарах нь чухал.
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
              <CardTitle className="text-base">Эмбеддинг загварууд</CardTitle>
              <CardDescription>Нарийн төвөгтэй өгөгдлийг нягт вектор дүрслэл рүү хөрвүүлэх</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-5 space-y-4">
          <p className="text-sm leading-6 text-slate-700">
            <strong>Эмбеддинг загвар</strong> нь нарийн төвөгтэй өгөгдлийг (үг эсвэл зураг гэх мэт)
            нягт вектор (тоон жагсаалт) дүрслэл рүү хөрвүүлэхэд ашиглагддаг бөгөөд үүнийг <strong>эмбеддинг</strong> гэдэг.
            Үүсгэгч загваруудаас ялгаатай нь эмбеддинг загварууд нь шинэ текст эсвэл өгөгдөл үүсгэдэггүй. Харин,
            энэ нь бусад загварууд эсвэл хэл боловсруулах даалгавруудад
            оролт болгон ашиглаж болох объектуудын утгын болон бүтцийн хамаарлын дүрслэлийг өгдөг.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { label: 'Input', desc: 'Текст, зураг, эсвэл аудио зэрэг нарийн төвөгтэй өгөгдөл' },
              { label: 'Process', desc: 'Нягт тоон вектор руу хөрвүүлнэ' },
              { label: 'Output', desc: 'Бусад загварууд болон даалгавраар ашиглагдахуйц эмбеддингүүд' },
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
          <CardTitle className="text-base">Энэ Систем AI-г хэрхэн ашигладаг вэ?</CardTitle>
          <CardDescription>Бидний хэрэгжүүлэлт нь Vercel AI SDK болон Google Gemini дээр суурилсан</CardDescription>
        </CardHeader>
        <CardContent className="pt-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[
              { step: '1', label: 'Цуглуулах', desc: 'FastAPI backend-ийг ашиглан Facebook хуудсуудаас сошиал медиа постуудыг цуглуулах' },
              { step: '2', label: 'Хадгалах', desc: 'Постууд, сэтгэгдлүүд болон зургуудыг Supabase (PostgreSQL) дотор хадгалах' },
              { step: '3', label: 'Нэгтгэх', desc: 'AI руу илгээхээс өмнө өгөгдлийн хэмжээг хязгаарлахын тулд урьдчилан нэгтгэх' },
              { step: '4', label: 'Шинжлэх', desc: 'Бүтэцжсэн дүн шинжилгээ гаргахын тулд Vercel AI SDK-р дамжуулан Gemini 2.0 Flash руу илгээх' },
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
