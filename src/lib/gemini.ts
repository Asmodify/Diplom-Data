/**
 * Client wrapper for the Gemini Analysis
 * 
 * Instead of initializing the Gemini API client-side (which exposes the API key),
 * we now securely fetch from our Vercel serverless function endpoint.
 */

export async function generatePredictiveAnalysis(data: any[]) {
  try {
    const response = await fetch('/api/generate-report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ data }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || 'Failed to fetch report');
    }

    const result = await response.json();
    return result.report;
  } catch (error) {
    console.error('Error generating analysis:', error);
    return 'Шинжилгээ хийхэд алдаа гарлаа. Сервер дээр GEMINI_API_KEY тохируулна уу.';
  }
}
