import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { dataSources } from '../lib/mockData';
import { formatDistanceToNow } from 'date-fns';
import { mn } from 'date-fns/locale';

export function DataSources() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Өгөгдлийн Эх Сурвалжууд</h2>
          <p className="text-muted-foreground">
            Сошиал медиа хаягуудаа холбож өгөгдөл автоматаар татах тохиргоо хийнэ үү.
          </p>
        </div>
        <Button>Шинэ эх сурвалж нэмэх</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {dataSources.map((source) => (
          <Card key={source.id}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg font-medium">{source.name}</CardTitle>
              {source.connected ? (
                <Badge variant="default" className="bg-green-500 hover:bg-green-600">Холбогдсон</Badge>
              ) : (
                <Badge variant="secondary">Салсан</Badge>
              )}
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground mt-2">
                {source.connected && source.lastSync ? (
                  <p>Сүүлд шинэчлэгдсэн: {formatDistanceToNow(new Date(source.lastSync), { addSuffix: true, locale: mn })}</p>
                ) : (
                  <p>Одоогоор өгөгдөл татаагүй байна.</p>
                )}
              </div>
              <div className="mt-4">
                {source.connected ? (
                  <Button variant="outline" className="w-full">Салгах</Button>
                ) : (
                  <Button className="w-full">Холбох</Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
