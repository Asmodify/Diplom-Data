// =============================================================================
// Mock data derived from the 500-row facebook_posts.csv
// Pages: TechNews Mongolia, Мэдээллийн Технологи, Монголын хөгжүүлэгчид, AI & Data Science MN
// Date range: 2026-05-01 – 2026-05-21  |  500 posts  |  Facebook only
// =============================================================================

export const mockSocialData = [
  { date: '2026-05-01', platform: 'Facebook', posts: 24, engagement: 12840, reach: 38520, sentiment: 0.62 },
  { date: '2026-05-02', platform: 'Facebook', posts: 22, engagement: 11550, reach: 34650, sentiment: 0.58 },
  { date: '2026-05-03', platform: 'Facebook', posts: 26, engagement: 13720, reach: 41160, sentiment: 0.71 },
  { date: '2026-05-04', platform: 'Facebook', posts: 23, engagement: 11960, reach: 35880, sentiment: 0.65 },
  { date: '2026-05-05', platform: 'Facebook', posts: 25, engagement: 13100, reach: 39300, sentiment: 0.60 },
  { date: '2026-05-06', platform: 'Facebook', posts: 21, engagement: 10920, reach: 32760, sentiment: 0.68 },
  { date: '2026-05-07', platform: 'Facebook', posts: 27, engagement: 14310, reach: 42930, sentiment: 0.73 },
  { date: '2026-05-08', platform: 'Facebook', posts: 24, engagement: 12480, reach: 37440, sentiment: 0.64 },
  { date: '2026-05-09', platform: 'Facebook', posts: 22, engagement: 11440, reach: 34320, sentiment: 0.59 },
  { date: '2026-05-10', platform: 'Facebook', posts: 28, engagement: 14840, reach: 44520, sentiment: 0.75 },
  { date: '2026-05-11', platform: 'Facebook', posts: 23, engagement: 12190, reach: 36570, sentiment: 0.66 },
  { date: '2026-05-12', platform: 'Facebook', posts: 25, engagement: 13250, reach: 39750, sentiment: 0.61 },
  { date: '2026-05-13', platform: 'Facebook', posts: 20, engagement: 10600, reach: 31800, sentiment: 0.57 },
  { date: '2026-05-14', platform: 'Facebook', posts: 26, engagement: 13780, reach: 41340, sentiment: 0.70 },
  { date: '2026-05-15', platform: 'Facebook', posts: 24, engagement: 12720, reach: 38160, sentiment: 0.63 },
  { date: '2026-05-16', platform: 'Facebook', posts: 23, engagement: 12070, reach: 36210, sentiment: 0.67 },
  { date: '2026-05-17', platform: 'Facebook', posts: 27, engagement: 14040, reach: 42120, sentiment: 0.72 },
  { date: '2026-05-18', platform: 'Facebook', posts: 25, engagement: 13000, reach: 39000, sentiment: 0.64 },
  { date: '2026-05-19', platform: 'Facebook', posts: 21, engagement: 11130, reach: 33390, sentiment: 0.69 },
  { date: '2026-05-20', platform: 'Facebook', posts: 24, engagement: 12600, reach: 37800, sentiment: 0.66 },
  { date: '2026-05-21', platform: 'Facebook', posts: 20, engagement: 10460, reach: 31380, sentiment: 0.60 },
];

// Total derived from above: 500 posts, ~263,000 total engagement, ~38,000 avg reach/day, 0.65 avg sentiment

export const dataSources = [
  { id: 'facebook', name: 'Facebook', connected: true, lastSync: '2026-05-26T12:00:00Z' },
  { id: 'twitter', name: 'Twitter (X)', connected: false, lastSync: null },
  { id: 'instagram', name: 'Instagram', connected: false, lastSync: null },
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
    date: '2026-05-20',
    author: 'TechNews Mongolia',
    content: 'Шинэ хиймэл оюун ухааны загвар танилцуулагдлаа.',
    keywords: ['AI', 'загвар', 'хиймэл оюун'],
    engagement: 632,
  },
  {
    id: 'fb-002',
    platform: 'facebook',
    date: '2026-05-20',
    author: 'Мэдээллийн Технологи',
    content: 'Python 3.12 хувилбар гарлаа. Олон шинэ боломжууд нэмэгдсэн байна.',
    keywords: ['python', 'хувилбар', 'хөгжүүлэлт'],
    engagement: 410,
  },
  {
    id: 'fb-003',
    platform: 'facebook',
    date: '2026-05-19',
    author: 'AI & Data Science MN',
    content: 'Өгөгдлийн сангийн аюулгүй байдлын талаарх чухал зөвлөгөө.',
    keywords: ['өгөгдлийн сан', 'аюулгүй байдал'],
    engagement: 805,
  },
  {
    id: 'fb-004',
    platform: 'facebook',
    date: '2026-05-19',
    author: 'Монголын хөгжүүлэгчид',
    content: 'React 19 хувилбарыг туршиж үзсэн хүн байна уу? Сэтгэгдлээ хуваалцаарай.',
    keywords: ['react', 'frontend', 'javascript'],
    engagement: 292,
  },
  {
    id: 'fb-005',
    platform: 'facebook',
    date: '2026-05-18',
    author: 'TechNews Mongolia',
    content: 'Шинэ iPhone 16-ийн талаарх цуурхал ба баримтууд.',
    keywords: ['iphone', 'apple', 'гар утас'],
    engagement: 1105,
  },
  {
    id: 'fb-006',
    platform: 'facebook',
    date: '2026-05-17',
    author: 'AI & Data Science MN',
    content: 'Машин сургалтын үндэс сургалт эхэллээ.',
    keywords: ['машин сургалт', 'сургалт', 'AI'],
    engagement: 548,
  },
  {
    id: 'fb-007',
    platform: 'facebook',
    date: '2026-05-16',
    author: 'Мэдээллийн Технологи',
    content: 'Cloud computing-ийн ирээдүй.',
    keywords: ['cloud', 'computing', 'ирээдүй'],
    engagement: 467,
  },
  {
    id: 'fb-008',
    platform: 'facebook',
    date: '2026-05-15',
    author: 'Монголын хөгжүүлэгчид',
    content: 'Javascript хөгжүүлэгчдэд зориулсан 5 зөвлөгөө.',
    keywords: ['javascript', 'зөвлөгөө', 'хөгжүүлэгч'],
    engagement: 371,
  },
];
