import { google } from '@ai-sdk/google';
import { generateText } from 'ai';

/**
 * Gemini Structured Analysis Endpoint (Vercel AI SDK)
 * 
 * Vercel serverless function that uses the standardized Vercel AI SDK to 
 * generate structured JSON analysis from pre-aggregated social media data.
 * The AI SDK reads the API key from GOOGLE_GENERATIVE_AI_API_KEY automatically.
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

    if (!process.env.GOOGLE_GENERATIVE_AI_API_KEY) {
      return res.status(500).json({ error: 'GOOGLE_GENERATIVE_AI_API_KEY is not configured on the server.' });
    }

    const prompt = `You are an AI data analyst. Analyze the following social media data summary and return a structured JSON response.

Data Summary:
${JSON.stringify(data, null, 2)}

You MUST respond with exactly the following JSON structure and nothing else. Do not wrap it in a markdown block.
{
  "sentiment_summary": "Overall summary of the sentiment",
  "key_themes": ["theme 1", "theme 2", "theme 3"],
  "engagement_risks": ["risk 1", "risk 2"],
  "content_opportunities": ["opportunity 1", "opportunity 2"]
}`;

    const { text } = await generateText({
      model: google('gemini-2.0-flash'),
      prompt,
    });

    // Clean up potential markdown blocks
    const cleaned = text.replace(/^```json\s*/, '').replace(/\s*```$/, '');

    let parsedResult;
    try {
      parsedResult = JSON.parse(cleaned);
    } catch (parseError) {
      console.error('Failed to parse Gemini output as JSON:', text);
      return res.status(500).json({ error: 'Failed to parse structured JSON from Gemini response' });
    }

    return res.status(200).json(parsedResult);
  } catch (error: any) {
    console.error('Unexpected error in analyze-gemini endpoint:', error);
    return res.status(500).json({ error: error.message || 'Internal server error during analysis' });
  }
}
