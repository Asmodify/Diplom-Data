import { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { mockSocialData } from '../lib/mockData';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { getBackendPosts, getBackendStats, normalizeBackendPosts, type LiveAdminPost } from '../lib/backend';

type DashboardPoint = {
  date: string;
  Facebook?: number;
  Twitter?: number;
  Instagram?: number;
  totalEngagement: number;
};

export function Dashboard() {
  const [livePosts, setLivePosts] = useState<LiveAdminPost[]>([]);
  const [liveStats, setLiveStats] = useState<{ totalPosts: number; totalEngagement: number } | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadDashboard = async () => {
      try {
        const [posts, stats] = await Promise.all([getBackendPosts(100), getBackendStats()]);

        if (!mounted) {
          return;
        }

        setLivePosts(normalizeBackendPosts(posts));
        setLiveStats({
          totalPosts: stats.total_posts,
          totalEngagement: posts.reduce(
            (sum, post) => sum + (post.likes ?? 0) + (post.shares ?? 0) * 2 + (post.comment_count ?? 0),
            0,
          ),
        });
      } catch {
        if (mounted) {
          setLivePosts([]);
          setLiveStats(null);
        }
      }
    };

    void loadDashboard();

    return () => {
      mounted = false;
    };
  }, []);

  const sourceData: LiveAdminPost[] = livePosts.length > 0
    ? livePosts
    : mockSocialData.map((item) => ({
        id: `${item.platform}-${item.date}`,
        platform: item.platform.toLowerCase(),
        date: item.date,
        author: item.platform,
        content: '',
        keywords: [],
        engagement: item.engagement,
        likes: item.engagement,
        shares: 0,
        commentCount: 0,
      }));

  const aggregatedByDate = sourceData.reduce((acc, curr) => {
    const existing = acc.find((item) => item.date === curr.date);
    const platformKey = curr.platform.toLowerCase();

    if (existing) {
      if (platformKey === 'facebook') {
        existing.Facebook = (existing.Facebook ?? 0) + curr.engagement;
      }
      if (platformKey === 'twitter') {
        existing.Twitter = (existing.Twitter ?? 0) + curr.engagement;
      }
      if (platformKey === 'instagram') {
        existing.Instagram = (existing.Instagram ?? 0) + curr.engagement;
      }
      existing.totalEngagement += curr.engagement;
    } else {
      acc.push({
        date: curr.date,
        ...(platformKey === 'facebook' ? { Facebook: curr.engagement } : {}),
        ...(platformKey === 'twitter' ? { Twitter: curr.engagement } : {}),
        ...(platformKey === 'instagram' ? { Instagram: curr.engagement } : {}),
        totalEngagement: curr.engagement,
      });
    }
    return acc;
  }, [] as DashboardPoint[]);

  const totalPosts = liveStats?.totalPosts ?? mockSocialData.reduce((sum, item) => sum + item.posts, 0);
  const totalEngagement = liveStats?.totalEngagement ?? mockSocialData.reduce((sum, item) => sum + item.engagement, 0);
  const totalReach = mockSocialData.reduce((sum, item) => sum + item.reach, 0);
  const avgSentiment = mockSocialData.reduce((sum, item) => sum + item.sentiment, 0) / mockSocialData.length;
  const activeSourceLabel = useMemo(() => (livePosts.length > 0 ? 'Live Render data' : 'Local demo data'), [livePosts.length]);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Нийт Пост</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalPosts}</div>
            <p className="text-xs text-muted-foreground">{activeSourceLabel}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Нийт Идэвх (Engagement)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalEngagement.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Backend synced metrics</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Нийт Хүртээмж (Reach)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalReach.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">+15% өмнөх 7 хоногоос</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Дундаж Сентимент</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(avgSentiment * 100).toFixed(1)}% Эерэг</div>
            <p className="text-xs text-muted-foreground">+2% өмнөх 7 хоногоос</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Идэвхийн чиг хандлага (Платформоор)</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={aggregatedByDate}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="Facebook" stroke="#1877F2" strokeWidth={2} activeDot={{ r: 8 }} />
                <Line type="monotone" dataKey="Twitter" stroke="#1DA1F2" strokeWidth={2} />
                <Line type="monotone" dataKey="Instagram" stroke="#E1306C" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Нийт Идэвх (Өдрөөр)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={aggregatedByDate}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip />
                <Bar dataKey="totalEngagement" fill="#4F46E5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
