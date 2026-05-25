import { useState } from 'react';
import { Key, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';

export function ApiKeyChecker() {
  const [keyId, setKeyId] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCheck = async () => {
    if (!keyId.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`/api/anthropic-key-status?id=${encodeURIComponent(keyId)}`);
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error?.message || data.error || 'Failed to fetch API key details');
      }
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm mt-5 xl:col-span-2">
      <h2 className="text-lg font-semibold text-slate-950 flex items-center gap-2">
        <Key className="h-5 w-5 text-slate-500" />
        Anthropic API Key Status Checker
      </h2>
      <p className="mt-1 text-sm leading-6 text-slate-600 mb-4">
        Verify the status of an Anthropic API Key using the Admin API.
      </p>
      
      <div className="flex items-center gap-3 mb-5">
        <Input 
          placeholder="apikey_01Rj2N..." 
          value={keyId} 
          onChange={(e) => setKeyId(e.target.value)}
          className="max-w-sm"
        />
        <Button onClick={handleCheck} disabled={loading || !keyId.trim()}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
          Check Status
        </Button>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4 text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {result && !result.type && result.error && (
        <div className="rounded-md bg-red-50 p-4 text-sm text-red-700 flex items-center gap-2">
           <AlertCircle className="h-4 w-4 shrink-0" />
           <span>{result.error.message || 'Unknown error occurred'}</span>
        </div>
      )}

      {result && result.type === 'api_key' && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Name</p>
              <p className="text-sm font-medium text-slate-900">{result.name}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Status</p>
              <div className="flex items-center gap-1 mt-0.5">
                {result.status === 'active' ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-amber-600" />
                )}
                <span className="text-sm font-medium capitalize">{result.status}</span>
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Created</p>
              <p className="text-sm font-medium text-slate-900">{new Date(result.created_at).toLocaleDateString()}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Hint</p>
              <p className="text-sm font-medium text-slate-900 font-mono">{result.partial_key_hint}</p>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
