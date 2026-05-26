import { google } from '@ai-sdk/google';
import { generateText } from 'ai';

/**
 * Generate Report API Endpoint (Vercel AI SDK)
 * 
 * Secure Vercel serverless function that uses the standardized Vercel AI SDK
 * to generate the main Mongolian predictive analysis report.
 * The AI SDK allows easy switching between providers (Google, OpenAI, Anthropic).
 */

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { data } = req.body;
    
    if (!data) {
      return res.status(400).json({ error: 'No data provided' });
    }

    if (!process.env.GOOGLE_GENERATIVE_AI_API_KEY) {
      return res.status(500).json({ error: 'GOOGLE_GENERATIVE_AI_API_KEY is not configured on the server.' });
    }

    const prompt = `
Та бол сошиал медиа өгөгдлийн шинжээч бөгөөд таамаглалт шинжилгээ хийдэг хиймэл оюун ухаан юм.
Дараах сүүлийн 7 хоногийн сошиал медиа өгөгдөл (Facebook, Twitter, Instagram) дээр үндэслэн дараагийн 7 хоногийн чиг хандлага, таамаглал, болон зөвлөмжийг гаргаж өгнө үү.
Өгөгдөл:
${JSON.stringify(data, null, 2)}

Хариултаа дараах бүтэцтэйгээр Монгол хэлээр гаргана уу:
1. Одоогийн нөхцөл байдлын дүгнэлт (Хамгийн өндөр хандалттай платформ, сентимент буюу хандлагын төлөв)
2. Дараагийн 7 хоногийн таамаглал (Хандалт өсөх эсвэл буурах, аль платформ илүү үр дүнтэй байх)
3. Стратегийн зөвлөмж (Юун дээр анхаарах, ямар төрлийн контент оруулах)
`;

    const { text } = await generateText({
      model: google('gemini-2.0-flash'),
      prompt,
    });

    return res.status(200).json({ report: text });
  } catch (error: any) {
    console.error('Error in generate-report endpoint:', error);
    return res.status(500).json({ error: error.message || 'Internal server error' });
  }
}
