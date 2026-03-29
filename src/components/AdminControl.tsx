import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';

export function AdminControl() {
  const [controls, setControls] = useState({
    scrapingEnabled: true,
    aiAnalysisEnabled: true,
    apiAccessEnabled: true,
    autoSyncEnabled: false,
  });

  const [limits, setLimits] = useState({
    maxPostsPerRun: '100',
    maxCommentsPerPost: '50',
    scrapeIntervalMinutes: '30',
  });

  const [maintenanceMessage, setMaintenanceMessage] = useState('');

  const toggleControl = (key: keyof typeof controls) => {
    setControls((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Админ хяналтын хуудас</h2>
          <p className="text-muted-foreground">
            Системийн урсгал, API эрх, AI анализ, өгөгдөл цуглуулалтын хязгааруудыг удирдана.
          </p>
        </div>
        <Badge variant="default" className="bg-emerald-600 hover:bg-emerald-700">
          Control Page
        </Badge>
      </div>

      <Tabs defaultValue="system" className="space-y-4">
        <TabsList>
          <TabsTrigger value="system">Систем</TabsTrigger>
          <TabsTrigger value="limits">Хязгаар</TabsTrigger>
          <TabsTrigger value="ops">Үйл ажиллагаа</TabsTrigger>
        </TabsList>

        <TabsContent value="system" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Core Control Switches</CardTitle>
              <CardDescription>
                Гол модуль бүрийн идэвхийг шууд удирдах хэсэг.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              <ControlRow
                label="Скрапинг ажиллуулах"
                description="Scraper модулийг ажиллуулах/зогсоох"
                enabled={controls.scrapingEnabled}
                onToggle={() => toggleControl('scrapingEnabled')}
              />
              <ControlRow
                label="AI анализ"
                description="Predictive, emotion, topic, network анализ"
                enabled={controls.aiAnalysisEnabled}
                onToggle={() => toggleControl('aiAnalysisEnabled')}
              />
              <ControlRow
                label="API хандалт"
                description="REST endpoint-уудыг нээх/хаах"
                enabled={controls.apiAccessEnabled}
                onToggle={() => toggleControl('apiAccessEnabled')}
              />
              <ControlRow
                label="Auto Cloud Sync"
                description="Firebase sync урсгал"
                enabled={controls.autoSyncEnabled}
                onToggle={() => toggleControl('autoSyncEnabled')}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="limits" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Data Collection Limits</CardTitle>
              <CardDescription>
                Системийн нөөц болон API тогтвортой ажиллагаанд зориулсан хязгаарууд.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-3">
              <LimitField
                label="Run бүрийн пост"
                value={limits.maxPostsPerRun}
                onChange={(value) => setLimits((prev) => ({ ...prev, maxPostsPerRun: value }))}
              />
              <LimitField
                label="Пост бүрийн сэтгэгдэл"
                value={limits.maxCommentsPerPost}
                onChange={(value) => setLimits((prev) => ({ ...prev, maxCommentsPerPost: value }))}
              />
              <LimitField
                label="Скрап интервал (минут)"
                value={limits.scrapeIntervalMinutes}
                onChange={(value) => setLimits((prev) => ({ ...prev, scrapeIntervalMinutes: value }))}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ops" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Operational Actions</CardTitle>
              <CardDescription>
                Засвар үйлчилгээ болон хяналтын мессежүүд.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm font-medium">Maintenance Message</p>
                <Input
                  placeholder="Системд түр засвар үйлчилгээ явагдаж байна..."
                  value={maintenanceMessage}
                  onChange={(event) => setMaintenanceMessage(event.target.value)}
                />
              </div>

              <div className="flex flex-wrap gap-2">
                <Button>Хяналтын өөрчлөлт хадгалах</Button>
                <Button variant="outline">Системийн төлөв дахин ачаалах</Button>
                <Button variant="destructive">Emergency Stop</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

type ControlRowProps = {
  label: string;
  description: string;
  enabled: boolean;
  onToggle: () => void;
};

function ControlRow({ label, description, enabled, onToggle }: ControlRowProps) {
  return (
    <div className="rounded-md border p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="font-medium">{label}</p>
        <Badge variant={enabled ? 'default' : 'secondary'}>
          {enabled ? 'ON' : 'OFF'}
        </Badge>
      </div>
      <p className="mb-3 text-sm text-muted-foreground">{description}</p>
      <Button variant={enabled ? 'outline' : 'default'} size="sm" onClick={onToggle}>
        {enabled ? 'Disable' : 'Enable'}
      </Button>
    </div>
  );
}

type LimitFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
};

function LimitField({ label, value, onChange }: LimitFieldProps) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{label}</p>
      <Input value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}
