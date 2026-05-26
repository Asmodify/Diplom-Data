const fs = require('fs');
const path = require('path');

const dirs = ['src/components'];

const replacements = [
  ['Posts collected', 'Цуглуулсан постууд'],
  ['Live backend data', 'Бодит backend өгөгдөл'],
  ['Demo fallback data', 'Туршилтын өгөгдөл'],
  ['Engagement trend', 'Хандалтын чиг хандлага'],
  ['Engagement', 'Хандалт'],
  ['Likes, comments, and shares', 'Таалагдалт, сэтгэгдэл, болон хуваалцалт'],
  ['Estimated reach', 'Тооцоолсон хүртээмж'],
  ['Calculated from sample data', 'Өгөгдлөөс тооцоолсон'],
  ['Avg. sentiment', 'Дундаж хандлага'],
  ['Positive leaning score', 'Эерэг хандлагын оноо'],
  ['Daily engagement grouped by social platform.', 'Сошиал платформоор бүлэглэсэн өдөр тутмын хандалт.'],
  ['Refresh', 'Шинэчлэх'],
  ['System snapshot', 'Системийн тойм'],
  ['Current data source and collection shape.', 'Одоогийн өгөгдлийн эх сурвалж болон цуглуулгын байдал.'],
  ['Data source', 'Өгөгдлийн эх сурвалж'],
  ['Render backend', 'Render backend'],
  ['Local demo data', 'Дотоод туршилтын өгөгдөл'],
  ['Samples loaded', 'Ачаалагдсан өгөгдөл'],
  ['Active platforms', 'Идэвхтэй платформууд'],
  ['Recent volume', 'Сүүлийн үеийн хэмжээ'],
  ['Total engagement in the latest chart window.', 'Сүүлийн графикийн хугацаан дахь нийт хандалт.'],
  ['Latest signals', 'Сүүлийн үеийн мэдээллүүд'],
  ['Newest collected posts shown as compact operational cards.', 'Хамгийн сүүлд цуглуулсан постуудыг картууд хэлбэрээр харуулж байна.'],
  ['No post text available.', 'Мэдээллийн текст байхгүй байна.'],
  ['Live', 'Шууд'],
  ['Loading', 'Ачаалж байна'],
  ['Demo', 'Туршилт']
];

for (const dir of dirs) {
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.tsx'));
  for (const file of files) {
    const filePath = path.join(dir, file);
    let content = fs.readFileSync(filePath, 'utf-8');
    for (const [en, mn] of replacements) {
      content = content.replace(new RegExp("'" + en + "'", 'g'), "'" + mn + "'");
      content = content.replace(new RegExp('"' + en + '"', 'g'), '"' + mn + '"');
      content = content.replace(new RegExp('>' + en + '<', 'g'), '>' + mn + '<');
    }
    fs.writeFileSync(filePath, content);
  }
}
