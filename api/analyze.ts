/**
 * Anthropic API Analysis Endpoint
 * 
 * This Vercel serverless function receives pre-aggregated data from the client,
 * constructs a prompt, and calls the Anthropic Claude API to generate a structured
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

    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      return res.status(500).json({ error: 'ANTHROPIC_API_KEY is not configured on the server.' });
    }

    // Prepare prompt and schema for Claude
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

    // Call Anthropic API using fetch to avoid adding new dependencies
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514', // Using requested model version
        max_tokens: 1024,
        temperature: 0.2,
        messages: [
          { role: 'user', content: prompt }
        ]
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Anthropic API Error:', errorText);
      return res.status(response.status).json({ error: `Anthropic API error: ${response.statusText}` });
    }

    const result = await response.json();
    let contentText = result.content[0].text;
    
    // Clean up potential markdown blocks from response just in case
    contentText = contentText.replace(/^```json\s*/, '').replace(/\s*```$/, '');
    
    // Parse the JSON returned by Claude
    let parsedResult;
    try {
      parsedResult = JSON.parse(contentText);
    } catch (parseError) {
      console.error('Failed to parse Claude output as JSON:', contentText);
      return res.status(500).json({ error: 'Failed to parse structured JSON from Claude response' });
    }

    return res.status(200).json(parsedResult);
  } catch (error: any) {
    console.error('Unexpected error in analyze endpoint:', error);
    return res.status(500).json({ error: error.message || 'Internal server error during analysis' });
  }
}
