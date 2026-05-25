import { GoogleGenerativeAI } from '@google/generative-ai';

/**
 * Generate Report API Endpoint
 * 
 * Secure Vercel serverless function to generate the main Mongolian predictive 
 * analysis report without exposing the Gemini API key to the frontend.
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

    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return res.status(500).json({ error: 'GEMINI_API_KEY is not configured on the server.' });
    }

    const genAI = new GoogleGenerativeAI(apiKey);
    
    // Use gemini-2.0-flash as requested
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });

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

    const result = await model.generateContent(prompt);
    const report = result.response.text();

    return res.status(200).json({ report });
  } catch (error: any) {
    console.error('Error in generate-report endpoint:', error);
    return res.status(500).json({ error: error.message || 'Internal server error' });
  }
}
