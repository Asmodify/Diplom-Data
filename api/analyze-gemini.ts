import { GoogleGenerativeAI } from '@google/generative-ai';

/**
 * Gemini API Analysis Endpoint
 * 
 * This Vercel serverless function receives pre-aggregated data from the client,
 * constructs a prompt, and calls the Google Gemini API to generate a structured
 * JSON analysis based on the provided schema.
 */

export default async function handler(req: any, res: any) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { data } = req.body;
    
    if (!data) {
      return res.status(400).json({ error: 'No data provided for analysis' });
    }

    // Never hardcode the API key. Ensure it is read from environment variables.
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return res.status(500).json({ error: 'GEMINI_API_KEY is not configured on the server.' });
    }

    const genAI = new GoogleGenerativeAI(apiKey);
    
    // We use gemini-2.0-flash as requested
    const model = genAI.getGenerativeModel({
      model: 'gemini-2.0-flash',
      generationConfig: {
        responseMimeType: 'application/json',
      }
    });

    // Prepare prompt and schema
    const prompt = `You are an AI data analyst. Analyze the following social media data summary and return a structured JSON response.

Data Summary:
${JSON.stringify(data, null, 2)}

You MUST respond with exactly the following JSON structure and nothing else:
{
  "sentiment_summary": "Overall summary of the sentiment",
  "key_themes": ["theme 1", "theme 2", "theme 3"],
  "engagement_risks": ["risk 1", "risk 2"],
  "content_opportunities": ["opportunity 1", "opportunity 2"]
}`;

    const result = await model.generateContent(prompt);
    const responseText = result.response.text();
    
    // Parse the JSON returned by Gemini
    let parsedResult;
    try {
      parsedResult = JSON.parse(responseText);
    } catch (parseError) {
      console.error('Failed to parse Gemini output as JSON:', responseText);
      return res.status(500).json({ error: 'Failed to parse structured JSON from Gemini response' });
    }

    return res.status(200).json(parsedResult);
  } catch (error: any) {
    console.error('Unexpected error in analyze-gemini endpoint:', error);
    return res.status(500).json({ error: error.message || 'Internal server error during analysis' });
  }
}
