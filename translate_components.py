import os
import glob
import re

directories = ['src/components', 'src/components/ui']
replacements = {
    # DataSources.tsx
    'Console initialized. Start automation to collect data.': 'Консол эхэллээ. Мэдээлэл цуглуулахын тулд автоматжуулалтыг эхлүүлнэ үү.',
    'Could not reach the local scraper API. The page manager is still available in the browser.': 'Дотоод scraper API-тай холбогдож чадсангүй. Хуудасны менежер хөтчөөр дамжуулан ашиглах боломжтой хэвээр байна.',
    '[System] Target list saved successfully.': '[Систем] Зорилтот жагсаалт амжилттай хадгалагдлаа.',
    '[System error] Could not save targets to pages.txt.': '[Системийн алдаа] pages.txt руу зорилтуудыг хадгалж чадсангүй.',
    '[System] Requesting scraper start...': '[Систем] Scraper эхлүүлэхийг хүсэж байна...',
    '[System] Scraper process started.': '[Систем] Scraper процесс эхэллээ.',
    '[System error] Could not contact scraper endpoint.': '[Системийн алдаа] Scraper-ийн цэгтэй холбогдож чадсангүй.',
    'Connected sources': 'Холбогдсон эх сурвалжууд',
    'Available social connectors': 'Боломжит сошиал холболтууд',
    'Scraper status': 'Scraper байдал',
    'Running': 'Ажиллаж байна',
    'Idle': 'Хүлээгдэж байна',
    'Polling logs every 2 seconds': '2 секунд тутамд лог шалгаж байна',
    'Ready to start': 'Эхлүүлэхэд бэлэн',
    'Targets': 'Зорилтууд',
    'Configured scraping pages': 'Тохируулсан цуглуулах хуудсууд',
    'Scraping targets': 'Цуглуулах зорилтууд',
    'Manage page URLs or IDs stored by the backend pages.txt workflow.': 'Backend-ийн pages.txt-д хадгалагдсан хуудасны URL эсвэл ID-г удирдах.',
    ' targets': ' зорилтууд',
    'Add': 'Нэмэх',
    'Loading targets': 'Зорилтуудыг ачаалж байна',
    'Reading scraper configuration from the backend.': 'Backend-ээс scraper тохиргоог уншиж байна.',
    'No targets yet': 'Зорилт алга',
    'Add a page URL or ID above, then save the list.': 'Дээр хуудасны URL эсвэл ID оруулж, жагсаалтыг хадгална уу.',
    'Saving': 'Хадгалж байна',
    'Save targets': 'Зорилтуудыг хадгалах',
    'Reload': 'Дахин ачаалах',
    'Automation console': 'Автоматжуулалтын консол',
    'Live scraper status and process output.': 'Шууд scraper статус болон процессын үр дүн.',
    'Starting scraper': 'Scraper эхэлж байна',
    'Scraper is running': 'Scraper ажиллаж байна',
    'Start scraping': 'Цуглуулж эхлэх',
    'Not connected': 'Холбогдоогүй',
    '>Active<': '>Идэвхтэй<',
    '>Offline<': '>Холбогдоогүй<',
    # AdminControl.tsx
    'Backend status': 'Backend төлөв',
    '>checking<': '>Шалгаж байна<',
    '>offline<': '>Салангид<',
    'Live posts': 'Бодит постууд',
    'Scraper database records': 'Scraper баазын бичлэгүүд',
    'Storage': 'Хадгалалт',
    '>Connected<': '>Холбогдсон<',
    'Fallback': 'Нөөц',
    'Firebase/Supabase integration': 'Firebase/Supabase нэгтгэл',
    'Frontend': 'Фронтенд',
    '>Ready<': '>Бэлэн<',
    'Refreshing snapshot': 'Төлөвийг шинэчилж байна',
    'Static Vite build': 'Статик Vite хувилбар',
    '>Overview<': '>Тойм<',
    '>Limits<': '>Хязгаарууд<',
    '>Query<': '>Хайлт<',
    '>Operations<': '>Журмууд<',
    'Control switches': 'Удирдлагын тохируулга',
    'Browser-side controls for the main system modules.': 'Гол системийн модулиудын хөтөч дээрх удирдлага.',
    'Scraping': 'Цуглуулах',
    'Allow scraper automation tasks to run.': 'Автоматжуулсан цуглуулах ажлуудыг ажиллахыг зөвшөөрөх.',
    'AI analysis': 'AI Шинжилгээ',
    'Enable predictive and text analysis features.': 'Урьдчилан таамаглах болон текст шинжилгээний функцуудыг идэвхжүүлэх.',
    'API access': 'API хандалт',
    'Keep protected REST endpoints available.': 'Хамгаалагдсан REST цэгүүдийг нээлттэй байлгах.',
    'Auto sync': 'Автомат синхрончлол',
    'Mirror collected data to cloud storage.': 'Цуглуулсан өгөгдлийг үүлэн хадгалалттай синхрончлох.',
    'Backend sync': 'Backend синхрончлол',
    'Health and data status for the connected API.': 'Холбогдсон API-н эрүүл мэнд болон өгөгдлийн төлөв.',
    'Refresh backend': 'Backend шинэчлэх',
    'Collection limits': 'Цуглуулах хязгаар',
    'Operational limits used to keep scraping and API workloads predictable.': 'Цуглуулах болон API ачааллыг хянахын тулд ашиглагддаг үйл ажиллагааны хязгаар.',
    'Posts per run': 'Нэг удаагийн гүйлт дэх пост',
    'Comments per post': 'Пост тус бүрийн сэтгэгдэл',
    'Interval minutes': 'Завсарлах хугацаа (минут)',
    'Keyword and date query': 'Түлхүүр үг болон огнооны хайлт',
    'Filter the currently loaded posts by platform, terms, and date range.': 'Одоо ачаалагдсан постуудыг платформ, үг болон огноогоор шүүх.',
    'Platform': 'Платформ',
    'Keywords': 'Түлхүүр үгс',
    'Start date': 'Эхлэх огноо',
    'End date': 'Дуусах огноо',
    'Run query': 'Хайлт хийх',
    'No query has been executed yet.': 'Одоогоор ямар нэг хайлт хийгдээгүй байна.',
    'Backend health': 'Backend эрүүл мэнд',
    'Current operational flags returned by the backend health endpoint.': 'Backend эрүүл мэндийн цэгээс буцаагдсан одоогийн төлөвүүд.',
    '>Status<': '>Статус<',
    'Version': 'Хувилбар',
    '>Analyzer<': '>Шинжлэгч<',
    'unknown': 'Тодорхойгүй',
    'Enabled': 'Идэвхжсэн',
    'Disabled': 'Хаагдсан',
    '>On<': '>Асаалттай<',
    '>Off<': '>Унтраалттай<',
    ' engagement': ' хандалт',
    # GeminiAnalyzer.tsx / GeminiQA.tsx / etc...
    'Analysis type': 'Шинжилгээний төрөл',
    'Content themes': 'Агуулгын сэдвүүд',
    'Engagement prediction': 'Хандалтын таамаг',
    'Sentiment scan': 'Хандлагын шинжилгээ',
    'Run Analysis': 'Шинжилгээ хийх',
    'Ask Gemini...': 'Gemini-с асуух...',
    'Send': 'Илгээх',
    'Clear': 'Устгах',
    'Predictive Analysis': 'Урьдчилан таамаглах шинжилгээ'
}

for d in directories:
    for root, dirs, files in os.walk(d):
        for f in files:
            if f.endswith('.tsx'):
                filepath = os.path.join(root, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                for en, mn in replacements.items():
                    if en.startswith('>'):
                        content = content.replace(en, mn)
                    else:
                        content = content.replace(f"'{en}'", f"'{mn}'")
                        content = content.replace(f'"{en}"', f'"{mn}"')
                        content = content.replace(f'>{en}<', f'>{mn}<')
                        
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(content)

print("Translation applied.")
