import { GoogleGenAI } from '@google/genai';

let ai: any = null;

try {
  const apiKey = import.meta.env.VITE_GEMINI_API_KEY;
  if (apiKey) {
    ai = new GoogleGenAI({ apiKey });
  }
} catch (error) {
  console.warn('Gemini AI not initialized:', error);
}

export async function generatePredictiveAnalysis(data: any[]) {
  if (!ai) {
    return 'Gemini API нүүлгэлтэгдээгүй байна. .env файлд VITE_GEMINI_API_KEY тохируулна уу.';
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

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3.1-pro-preview',
      contents: prompt,
    });
    return response.text;
  } catch (error) {
    console.error('Error generating analysis:', error);
    return 'Шинжилгээ хийхэд алдаа гарлаа. Дахин оролдоно уу.';
  }
}
