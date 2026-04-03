export const mockSocialData = [
  { date: '2026-03-20', platform: 'Facebook', posts: 12, engagement: 1450, reach: 12000, sentiment: 0.65 },
  { date: '2026-03-20', platform: 'Twitter', posts: 25, engagement: 3200, reach: 45000, sentiment: 0.45 },
  { date: '2026-03-20', platform: 'Instagram', posts: 5, engagement: 5400, reach: 25000, sentiment: 0.85 },
  
  { date: '2026-03-21', platform: 'Facebook', posts: 10, engagement: 1200, reach: 11000, sentiment: 0.60 },
  { date: '2026-03-21', platform: 'Twitter', posts: 30, engagement: 4100, reach: 52000, sentiment: 0.50 },
  { date: '2026-03-21', platform: 'Instagram', posts: 6, engagement: 6100, reach: 28000, sentiment: 0.88 },
  
  { date: '2026-03-22', platform: 'Facebook', posts: 15, engagement: 1800, reach: 15000, sentiment: 0.70 },
  { date: '2026-03-22', platform: 'Twitter', posts: 22, engagement: 2900, reach: 41000, sentiment: 0.42 },
  { date: '2026-03-22', platform: 'Instagram', posts: 4, engagement: 4800, reach: 22000, sentiment: 0.82 },
  
  { date: '2026-03-23', platform: 'Facebook', posts: 14, engagement: 1650, reach: 14000, sentiment: 0.68 },
  { date: '2026-03-23', platform: 'Twitter', posts: 28, engagement: 3800, reach: 48000, sentiment: 0.48 },
  { date: '2026-03-23', platform: 'Instagram', posts: 7, engagement: 7200, reach: 31000, sentiment: 0.90 },
  
  { date: '2026-03-24', platform: 'Facebook', posts: 11, engagement: 1350, reach: 11500, sentiment: 0.62 },
  { date: '2026-03-24', platform: 'Twitter', posts: 35, engagement: 4500, reach: 55000, sentiment: 0.55 },
  { date: '2026-03-24', platform: 'Instagram', posts: 5, engagement: 5600, reach: 26000, sentiment: 0.86 },
  
  { date: '2026-03-25', platform: 'Facebook', posts: 13, engagement: 1550, reach: 13000, sentiment: 0.66 },
  { date: '2026-03-25', platform: 'Twitter', posts: 26, engagement: 3400, reach: 46000, sentiment: 0.46 },
  { date: '2026-03-25', platform: 'Instagram', posts: 6, engagement: 6400, reach: 29000, sentiment: 0.89 },
  
  { date: '2026-03-26', platform: 'Facebook', posts: 16, engagement: 1950, reach: 16000, sentiment: 0.72 },
  { date: '2026-03-26', platform: 'Twitter', posts: 24, engagement: 3100, reach: 43000, sentiment: 0.44 },
  { date: '2026-03-26', platform: 'Instagram', posts: 8, engagement: 8100, reach: 35000, sentiment: 0.92 },
];

export const dataSources = [
  { id: 'facebook', name: 'Facebook', connected: true, lastSync: '2026-03-27T10:30:00Z' },
  { id: 'twitter', name: 'Twitter (X)', connected: true, lastSync: '2026-03-27T10:35:00Z' },
  { id: 'instagram', name: 'Instagram', connected: true, lastSync: '2026-03-27T10:40:00Z' },
  { id: 'linkedin', name: 'LinkedIn', connected: false, lastSync: null },
  { id: 'tiktok', name: 'TikTok', connected: false, lastSync: null },
];

export type MockCollectedPost = {
  id: string;
  platform: 'facebook' | 'twitter' | 'instagram';
  date: string;
  author: string;
  content: string;
  keywords: string[];
  engagement: number;
};

export const mockCollectedPosts: MockCollectedPost[] = [
  {
    id: 'fb-001',
    platform: 'facebook',
    date: '2026-03-20',
    author: 'Tech Mongolia Hub',
    content: 'AI policy forum starts next week with open civic discussion.',
    keywords: ['ai', 'policy', 'forum'],
    engagement: 342,
  },
  {
    id: 'fb-002',
    platform: 'facebook',
    date: '2026-03-22',
    author: 'Data Club Ulaanbaatar',
    content: 'Data science meetup focuses on youth participation analytics.',
    keywords: ['data science', 'analytics', 'youth'],
    engagement: 221,
  },
  {
    id: 'tw-001',
    platform: 'twitter',
    date: '2026-03-21',
    author: 'CivicWatchMN',
    content: 'Election monitoring dashboard updated with sentiment signals.',
    keywords: ['election', 'dashboard', 'sentiment'],
    engagement: 411,
  },
  {
    id: 'tw-002',
    platform: 'twitter',
    date: '2026-03-24',
    author: 'OpenDataLab',
    content: 'Real-time network analysis reveals key influence clusters.',
    keywords: ['network', 'analysis', 'influence'],
    engagement: 389,
  },
  {
    id: 'ig-001',
    platform: 'instagram',
    date: '2026-03-23',
    author: 'socialinsight.mn',
    content: 'Visual recap of AI education campaign performance.',
    keywords: ['ai', 'education', 'campaign'],
    engagement: 512,
  },
  {
    id: 'ig-002',
    platform: 'instagram',
    date: '2026-03-26',
    author: 'trendpulse.mn',
    content: 'Topic heatmap: policy and transparency dominated this week.',
    keywords: ['topic', 'policy', 'transparency'],
    engagement: 476,
  },
  {
    id: 'fb-003',
    platform: 'facebook',
    date: '2026-03-25',
    author: 'Insight Studio',
    content: 'Keyword tracker shows sustained growth for data science posts.',
    keywords: ['keyword', 'data science', 'tracker'],
    engagement: 267,
  },
  {
    id: 'tw-003',
    platform: 'twitter',
    date: '2026-03-26',
    author: 'AIResearchMN',
    content: 'New model predicts engagement spikes around civic events.',
    keywords: ['ai', 'model', 'engagement'],
    engagement: 438,
  },
];
