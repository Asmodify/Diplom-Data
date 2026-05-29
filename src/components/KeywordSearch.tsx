import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import {
  Search,
  Filter,
  Loader2,
  Calendar,
  ThumbsUp,
  Share2,
  MessageCircle,
  Hash,
  Download,
  Copy,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { searchPosts, normalizeBackendPosts, type LiveAdminPost } from '../lib/backend';
import { cn } from '../lib/utils';

export function KeywordSearch() {
  const [query, setQuery] = useState('');
  const [platform, setPlatform] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  const [allPosts, setAllPosts] = useState<LiveAdminPost[]>([]);
  const [filteredPosts, setFilteredPosts] = useState<LiveAdminPost[]>([]);
  
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [lastSearchInfo, setLastSearchInfo] = useState<string | null>(null);

  useEffect(() => {
    // Initial load of posts
    handleSearch(true);
  }, []);

  const handleSearch = async (initial = false) => {
    if (!initial) {
      setIsSearching(true);
    } else {
      setIsLoading(true);
    }
    
    setError(null);
    
    try {
      // For a real implementation, we would pass search queries to the backend.
      // Since the backend doesn't have a full-text search endpoint yet, 
      // we fetch a larger batch of posts and filter them client-side.
      
      let postsToFilter = allPosts;
      
      // If we don't have posts yet, fetch them
      if (allPosts.length === 0) {
        const rawPosts = await searchPosts(platform === 'all' ? undefined : platform, 500);
        postsToFilter = normalizeBackendPosts(rawPosts);
        setAllPosts(postsToFilter);
      }
      
      // Filter logic
      const searchTerms = query.toLowerCase().split(',').map(t => t.trim()).filter(Boolean);
      
      const results = postsToFilter.filter(post => {
        // Platform filter
        const platformMatch = platform === 'all' || post.platform.toLowerCase() === platform.toLowerCase();
        
        // Date filter
        const startMatch = !startDate || post.date >= startDate;
        const endMatch = !endDate || post.date <= endDate;
        
        // Keyword filter
        let keywordMatch = true;
        if (searchTerms.length > 0) {
          const contentStr = `${post.author} ${post.content} ${post.keywords.join(' ')}`.toLowerCase();
          keywordMatch = searchTerms.some(term => contentStr.includes(term));
        }
        
        return platformMatch && startMatch && endMatch && keywordMatch;
      });
      
      setFilteredPosts(results);
      
      if (!initial) {
        setLastSearchInfo(`Олдсон илэрц: ${results.length} | Түлхүүр үг: ${query || 'Бүгд'} | Платформ: ${platform}`);
      }
      
    } catch (e) {
      console.error('Search failed', e);
      setError('Хайлт хийхэд алдаа гарлаа. (Туршилтын өгөгдөл ашиглаж байна)');
      
      // Fallback demo data
      setTimeout(() => {
        const demoData: LiveAdminPost[] = Array.from({ length: 8 }).map((_, i) => ({
          id: `search-${i}`,
          platform: ['facebook', 'twitter', 'instagram'][i % 3],
          date: new Date(Date.now() - i * 86400000).toISOString().split('T')[0],
          author: `News Page ${i+1}`,
          content: `Энэ бол түлхүүр үгсийн хайлт хийхэд зориулагдсан туршилтын пост юм. ${query ? `Таны хайсан үг: ${query}` : ''} #${['сонгууль', 'мэдээ', 'спорт'][i % 3]}`,
          keywords: ['мэдээ', 'хайлт', 'туршилт'],
          engagement: Math.floor(100 + Math.random() * 900),
          likes: Math.floor(50 + Math.random() * 400),
          shares: Math.floor(10 + Math.random() * 100),
          commentCount: Math.floor(20 + Math.random() * 200)
        }));
        
        setFilteredPosts(demoData);
        if (!initial) {
          setLastSearchInfo(`Олдсон илэрц: ${demoData.length} (Туршилтын өгөгдөл)`);
        }
        setIsSearching(false);
      }, 800);
      
      return; // Early return to avoid setting isSearching to false twice
    }
    
    setIsLoading(false);
    setIsSearching(false);
  };

  const exportToCSV = () => {
    if (filteredPosts.length === 0) return;
    
    // Simple CSV export
    const headers = ['ID', 'Платформ', 'Огноо', 'Хуудас', 'Агуулга', 'Таалагдсан', 'Хуваалцсан', 'Сэтгэгдэл'];
    const rows = filteredPosts.map(p => [
      p.id,
      p.platform,
      p.date,
      `"${p.author.replace(/"/g, '""')}"`,
      `"${p.content.replace(/"/g, '""')}"`,
      p.likes,
      p.shares,
      p.commentCount
    ]);
    
    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `search_results_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const copyToClipboard = () => {
    if (filteredPosts.length === 0) return;
    
    const text = filteredPosts.map(p => 
      `[${p.date}] ${p.author} (${p.platform}): ${p.content.substring(0, 100)}... (Likes: ${p.likes}, Comments: ${p.commentCount})`
    ).join('\n\n');
    
    navigator.clipboard.writeText(text)
      .then(() => alert('Амжилттай хуулагдлаа!'))
      .catch(err => console.error('Failed to copy: ', err));
  };

  // Helper to highlight search terms
  const highlightText = (text: string, highlight: string) => {
    if (!highlight.trim()) return <span>{text}</span>;
    
    const terms = highlight.toLowerCase().split(',').map(t => t.trim()).filter(Boolean);
    if (terms.length === 0) return <span>{text}</span>;
    
    // Simple highlighting for the first matching term
    const term = terms[0];
    const regex = new RegExp(`(${term})`, 'gi');
    const parts = text.split(regex);
    
    return (
      <span>
        {parts.map((part, i) => 
          regex.test(part) ? (
            <mark key={i} className="bg-yellow-200 text-slate-900 rounded-sm px-0.5">{part}</mark>
          ) : (
            <span key={i}>{part}</span>
          )
        )}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Search Interface */}
      <Card className="shadow-md border-slate-200 overflow-visible">
        <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
              <Search className="h-5 w-5" />
            </div>
            <div>
              <CardTitle>Өгөгдөл Хайх</CardTitle>
              <CardDescription>Нийтлэлүүд дундаас түлхүүр үг болон шүүлтүүр ашиглан нарийвчилсан хайлт хийх</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid gap-5 md:grid-cols-12">
            <div className="md:col-span-12 space-y-2">
              <label className="text-sm font-medium text-slate-700">Хайх утга (Таслалаар тусгаарлана уу)</label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                <Input 
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch(false)}
                  placeholder="Жишээ: сонгууль, засгийн газар, татвар..."
                  className="pl-10 h-11 text-base shadow-sm"
                />
              </div>
            </div>
            
            <div className="md:col-span-4 space-y-2">
              <label className="text-sm font-medium text-slate-700 flex items-center gap-1">
                <Filter className="h-4 w-4" /> Платформ
              </label>
              <select 
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
                className="w-full h-10 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">Бүх платформууд</option>
                <option value="facebook">Facebook</option>
                <option value="twitter">Twitter</option>
                <option value="instagram">Instagram</option>
              </select>
            </div>
            
            <div className="md:col-span-4 space-y-2">
              <label className="text-sm font-medium text-slate-700 flex items-center gap-1">
                <Calendar className="h-4 w-4" /> Эхлэх огноо
              </label>
              <Input 
                type="date" 
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="h-10"
              />
            </div>
            
            <div className="md:col-span-4 space-y-2">
              <label className="text-sm font-medium text-slate-700 flex items-center gap-1">
                <Calendar className="h-4 w-4" /> Дуусах огноо
              </label>
              <Input 
                type="date" 
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="h-10"
              />
            </div>
            
            <div className="md:col-span-12 pt-2 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-100 pt-5">
              <div className="text-sm text-slate-500 w-full sm:w-auto">
                {lastSearchInfo || (isLoading ? 'Өгөгдөл татаж байна...' : 'Хайлт хийхэд бэлэн')}
              </div>
              <div className="flex w-full sm:w-auto gap-2">
                <Button variant="outline" onClick={() => { setQuery(''); setPlatform('all'); setStartDate(''); setEndDate(''); }}>
                  Цэвэрлэх
                </Button>
                <Button onClick={() => handleSearch(false)} disabled={isSearching || isLoading} className="bg-blue-600 hover:bg-blue-700 min-w-[120px]">
                  {isSearching ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                  Хайх
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">
            Илэрц ({filteredPosts.length})
          </h2>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={copyToClipboard} disabled={filteredPosts.length === 0}>
              <Copy className="mr-2 h-4 w-4" />
              Хуулах
            </Button>
            <Button variant="outline" size="sm" onClick={exportToCSV} disabled={filteredPosts.length === 0}>
              <Download className="mr-2 h-4 w-4" />
              CSV татах
            </Button>
          </div>
        </div>
        
        {error && (
          <div className="rounded-md bg-amber-50 p-4 border border-amber-200 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
            <p className="text-sm text-amber-800">{error}</p>
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {isLoading || isSearching ? (
            // Skeleton loaders
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-xl border border-slate-200 bg-white p-5 h-[220px] animate-pulse">
                <div className="flex justify-between items-start mb-4">
                  <div className="h-4 bg-slate-200 rounded w-1/3"></div>
                  <div className="h-4 bg-slate-200 rounded w-1/4"></div>
                </div>
                <div className="space-y-2 mb-6">
                  <div className="h-3 bg-slate-200 rounded w-full"></div>
                  <div className="h-3 bg-slate-200 rounded w-full"></div>
                  <div className="h-3 bg-slate-200 rounded w-2/3"></div>
                </div>
                <div className="flex gap-4 mt-auto">
                  <div className="h-4 bg-slate-200 rounded w-12"></div>
                  <div className="h-4 bg-slate-200 rounded w-12"></div>
                </div>
              </div>
            ))
          ) : filteredPosts.length > 0 ? (
            filteredPosts.map((post, index) => (
              <motion.div 
                key={post.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.2, delay: Math.min(index * 0.05, 0.5) }}
              >
                <Card className="h-full flex flex-col hover:shadow-md transition-shadow border-slate-200">
                  <CardHeader className="p-4 pb-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <CardTitle className="text-sm truncate text-slate-900" title={post.author}>
                          {post.author}
                        </CardTitle>
                        <CardDescription className="text-xs uppercase tracking-wider mt-1">
                          {post.platform} • {post.date}
                        </CardDescription>
                      </div>
                      <Badge variant="secondary" className="shrink-0 font-mono text-xs bg-slate-100">
                        ID: {post.id.substring(0, 6)}...
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 pt-2 flex-1 flex flex-col">
                    <ScrollArea className="flex-1 h-[100px] mb-4 pr-3">
                      <p className="text-sm text-slate-700 leading-relaxed break-words whitespace-pre-wrap">
                        {highlightText(post.content, query)}
                      </p>
                    </ScrollArea>
                    
                    {post.keywords && post.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-4">
                        {post.keywords.slice(0, 3).map((kw, i) => (
                          <span key={i} className="inline-flex items-center text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
                            <Hash className="h-2.5 w-2.5 mr-0.5" /> {kw}
                          </span>
                        ))}
                      </div>
                    )}
                    
                    <div className="mt-auto grid grid-cols-3 gap-2 border-t border-slate-100 pt-3">
                      <div className="flex items-center gap-1.5 text-slate-500" title="Таалагдсан">
                        <ThumbsUp className="h-4 w-4 text-blue-500" />
                        <span className="text-xs font-semibold">{post.likes > 999 ? `${(post.likes/1000).toFixed(1)}k` : post.likes}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-500" title="Сэтгэгдэл">
                        <MessageCircle className="h-4 w-4 text-emerald-500" />
                        <span className="text-xs font-semibold">{post.commentCount > 999 ? `${(post.commentCount/1000).toFixed(1)}k` : post.commentCount}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-500" title="Хуваалцсан">
                        <Share2 className="h-4 w-4 text-purple-500" />
                        <span className="text-xs font-semibold">{post.shares > 999 ? `${(post.shares/1000).toFixed(1)}k` : post.shares}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))
          ) : (
            <div className="col-span-full py-12 flex flex-col items-center justify-center text-center bg-white rounded-xl border border-dashed border-slate-300">
              <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
                <Search className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-medium text-slate-900">Илэрц олдсонгүй</h3>
              <p className="text-sm text-slate-500 mt-1 max-w-sm">
                Таны хайсан түлхүүр үг болон шүүлтүүрт тохирох нийтлэл олдсонгүй. Өөр түлхүүр үгээр хайгаад үзнэ үү.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
