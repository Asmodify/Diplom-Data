export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const apiKeyId = req.query.id;
  if (!apiKeyId) {
    return res.status(400).json({ error: 'Missing id query parameter. Provide an api_key_id (e.g. apikey_...)' });
  }

  const adminKey = process.env.ANTHROPIC_ADMIN_API_KEY;
  if (!adminKey) {
    return res.status(500).json({ error: 'ANTHROPIC_ADMIN_API_KEY is not configured on the server.' });
  }

  try {
    const response = await fetch(`https://api.anthropic.com/v1/organizations/api_keys/${apiKeyId}`, {
      method: 'GET',
      headers: {
        'anthropic-version': '2023-06-01',
        'X-Api-Key': adminKey
      }
    });

    const data = await response.json();
    return res.status(response.status).json(data);
  } catch (err: any) {
    console.error('Error fetching API key status:', err);
    return res.status(500).json({ error: err.message || 'Internal Server Error' });
  }
}
