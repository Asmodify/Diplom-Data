param(
    [string]$OutputPath = "thesis/2223B_IS_Diploma_rebuilt.pptx"
)

$ErrorActionPreference = "Stop"

function Escape-Xml([string]$Text) {
    if ($null -eq $Text) { return "" }
    return [System.Security.SecurityElement]::Escape($Text)
}

function New-Dir([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Resolve-Path -LiteralPath (Split-Path -Parent $Path)).Path + "\" + (Split-Path -Leaf $Path), $Content, $enc)
}

function Text-Run([string]$Text, [int]$Size = 2400, [string]$Color = "1E293B", [bool]$Bold = $false) {
    $b = if ($Bold) { "<a:b/>" } else { "" }
    return "<a:r><a:rPr lang=`"mn-MN`" sz=`"$Size`">$b<a:solidFill><a:srgbClr val=`"$Color`"/></a:solidFill><a:latin typeface=`"Aptos`"/><a:cs typeface=`"Aptos`"/></a:rPr><a:t>$(Escape-Xml $Text)</a:t></a:r>"
}

function Text-Box([string]$Name, [int]$Id, [int]$X, [int]$Y, [int]$W, [int]$H, [string[]]$Lines, [int]$Size = 2400, [string]$Color = "1E293B", [bool]$Bold = $false, [string]$Align = "l") {
    $paras = foreach ($line in $Lines) {
        "<a:p><a:pPr algn=`"$Align`"><a:endParaRPr lang=`"mn-MN`" sz=`"$Size`"/></a:pPr>$(Text-Run $line $Size $Color $Bold)</a:p>"
    }
    return @"
<p:sp>
  <p:nvSpPr><p:cNvPr id="$Id" name="$(Escape-Xml $Name)"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="$X" y="$Y"/><a:ext cx="$W" cy="$H"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
  <p:txBody><a:bodyPr wrap="square" anchor="t"/><a:lstStyle/>$($paras -join "")
  </p:txBody>
</p:sp>
"@
}

function Shape-Rect([string]$Name, [int]$Id, [int]$X, [int]$Y, [int]$W, [int]$H, [string]$Fill = "FFFFFF", [string]$Line = "FFFFFF", [int]$Radius = 0) {
    $geom = if ($Radius -gt 0) { "roundRect" } else { "rect" }
    return @"
<p:sp>
  <p:nvSpPr><p:cNvPr id="$Id" name="$(Escape-Xml $Name)"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="$X" y="$Y"/><a:ext cx="$W" cy="$H"/></a:xfrm><a:prstGeom prst="$geom"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="$Fill"/></a:solidFill><a:ln><a:solidFill><a:srgbClr val="$Line"/></a:solidFill></a:ln></p:spPr>
</p:sp>
"@
}

function Line-Shape([string]$Name, [int]$Id, [int]$X, [int]$Y, [int]$W, [int]$H, [string]$Color = "CBD5E1", [int]$Width = 19050) {
    return @"
<p:cxnSp>
  <p:nvCxnSpPr><p:cNvPr id="$Id" name="$(Escape-Xml $Name)"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>
  <p:spPr><a:xfrm><a:off x="$X" y="$Y"/><a:ext cx="$W" cy="$H"/></a:xfrm><a:prstGeom prst="line"><a:avLst/></a:prstGeom><a:ln w="$Width"><a:solidFill><a:srgbClr val="$Color"/></a:solidFill></a:ln></p:spPr>
</p:cxnSp>
"@
}

function Bullet-Box([string]$Name, [int]$Id, [int]$X, [int]$Y, [int]$W, [int]$H, [string[]]$Bullets, [int]$Size = 2200) {
    $paras = foreach ($line in $Bullets) {
        "<a:p><a:pPr marL=`"300000`" indent=`"-180000`"><a:buChar char=`"•`"/></a:pPr>$(Text-Run $line $Size "334155" $false)</a:p>"
    }
    return @"
<p:sp>
  <p:nvSpPr><p:cNvPr id="$Id" name="$(Escape-Xml $Name)"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="$X" y="$Y"/><a:ext cx="$W" cy="$H"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
  <p:txBody><a:bodyPr wrap="square" anchor="t"/><a:lstStyle/>$($paras -join "")</p:txBody>
</p:sp>
"@
}

function Chip([string]$Text, [int]$Id, [int]$X, [int]$Y, [int]$W, [string]$Fill, [string]$TextColor = "0F172A") {
    return (Shape-Rect "Chip $Text" $Id $X $Y $W 420000 $Fill $Fill 1) + (Text-Box "Chip Text $Text" ($Id + 1000) ($X + 90000) ($Y + 85000) ($W - 180000) 260000 @($Text) 1250 $TextColor $true "ctr")
}

function Slide-Xml([string]$Title, [string]$Subtitle, [string]$BodyXml, [int]$SlideNo) {
    $titleXml = Text-Box "Title" 2 560000 360000 11000000 600000 @($Title) 2850 "0F172A" $true
    $subXml = if ($Subtitle) { Text-Box "Subtitle" 3 565000 930000 10800000 360000 @($Subtitle) 1450 "64748B" $false } else { "" }
    $footer = Text-Box "Footer" 900 11100000 6640000 900000 240000 @("$SlideNo") 1000 "94A3B8" $false "r"
    return @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="F8FAFC"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    $(Shape-Rect "Accent" 800 0 0 220000 6858000 "0F766E" "0F766E")
    $titleXml
    $subXml
    $(Line-Shape "Rule" 801 560000 1320000 11100000 0 "CBD5E1" 12700)
    $BodyXml
    $footer
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>
"@
}

function Title-Slide-Xml() {
    $body = ""
    $body += Shape-Rect "Hero" 20 0 0 12192000 6858000 "0F766E" "0F766E"
    $body += Shape-Rect "Panel" 21 760000 900000 10350000 4650000 "F8FAFC" "F8FAFC" 1
    $body += Text-Box "University" 22 1030000 1180000 9700000 300000 @("ШУТИС • Мэдээллийн систем") 1300 "0F766E" $true
    $body += Text-Box "Main Title" 23 1020000 1640000 9400000 1180000 @("Нийгмийн сүлжээний өгөгдлийн автомат цуглуулга ба таамаглалт шинжилгээний систем") 3000 "0F172A" $true
    $body += Text-Box "Subtitle" 24 1030000 3100000 9200000 620000 @("Facebook group/page өгөгдөл цуглуулалт, Sentiment Analysis, Engagement Prediction, AI Report") 1650 "334155" $false
    $body += Text-Box "Meta" 25 1030000 4450000 4200000 650000 @("Оюутан: Ө. Хүслэн","Удирдагч багш: Б. Мөнхбуян","Улаанбаатар • 2026") 1350 "475569" $false
    return @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="0F766E"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    $body
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>
"@
}

function Card([string]$Title, [string]$Text, [int]$Id, [int]$X, [int]$Y, [int]$W, [int]$H, [string]$Color = "ECFDF5") {
    return (Shape-Rect "Card $Title" $Id $X $Y $W $H $Color "D1D5DB" 1) +
           (Text-Box "Card title $Title" ($Id + 1) ($X + 220000) ($Y + 170000) ($W - 440000) 300000 @($Title) 1500 "0F172A" $true) +
           (Text-Box "Card body $Title" ($Id + 2) ($X + 220000) ($Y + 560000) ($W - 440000) ($H - 700000) @($Text) 1200 "475569" $false)
}

$slides = @()
$slides += Title-Slide-Xml

$slides += Slide-Xml "Асуудал ба хэрэгцээ" "Яагаад энэ систем хэрэгтэй вэ?" (
    (Bullet-Box "Bullets" 10 720000 1650000 6100000 3600000 @(
        "Сошиал орчинд хэрэглэгчийн санал, хандлага маш хурдан өөрчлөгддөг.",
        "Пост, сэтгэгдлийг гараар уншиж ангилах нь удаан, алдаа ихтэй.",
        "Монгол хэлний богино хэллэг, ёгтлол, локал үг нь ерөнхий NLP аргуудад хүндрэл үүсгэдэг.",
        "Байгууллага, судлаачдад хурдан тайлан, тренд, эрсдэлийн дохио хэрэгтэй."
    ) 1850) +
    (Card "Гол санаа" "Түүхий сошиал өгөгдлийг автоматаар цуглуулж, ML/AI анализаар шийдвэрт ашиглах мэдээлэл болгоно." 50 7600000 1900000 3300000 2150000 "ECFEFF")
) 2

$slides += Slide-Xml "Судалгааны зорилго" "Цуглуулалт → шинжилгээ → таамаглал → тайлан" (
    (Card "Өгөгдөл" "Facebook group/page-үүдээс пост, сэтгэгдэл, like, share, comment count цуглуулах." 10 740000 1700000 3300000 1500000 "ECFDF5") +
    (Card "ML/NLP" "Текстийг positive, negative, neutral гэж ангилах; topic ба engagement шинжүүдийг гаргах." 20 4420000 1700000 3300000 1500000 "EFF6FF") +
    (Card "Тайлан" "Gemini API ашиглан статистик, тренд, зөвлөмжийг Монгол хэлээр тайлбарлах." 30 8100000 1700000 3300000 1500000 "FFF7ED") +
    (Bullet-Box "Goals" 40 1100000 3900000 9500000 1400000 @(
        "Систем нь frontend, backend, scraper, database, ML analyzer гэсэн модультай.",
        "Үр дүнг dashboard болон AI report хэлбэрээр хэрэглэгчид үзүүлнэ."
    ) 1750)
) 3

$slides += Slide-Xml "Системийн архитектур" "Модуль бүр тодорхой үүрэгтэй" (
    (Chip "React Dashboard" 10 750000 1900000 1800000 "DBEAFE") +
    (Chip "FastAPI" 20 3150000 1900000 1350000 "DCFCE7") +
    (Chip "Scraper" 30 5150000 1900000 1350000 "FEF3C7") +
    (Chip "Database" 40 7150000 1900000 1500000 "E0E7FF") +
    (Chip "ML / AI" 50 9300000 1900000 1450000 "FCE7F3") +
    (Line-Shape "l1" 60 2550000 2110000 600000 0 "64748B" 19050) +
    (Line-Shape "l2" 61 4500000 2110000 650000 0 "64748B" 19050) +
    (Line-Shape "l3" 62 6500000 2110000 650000 0 "64748B" 19050) +
    (Line-Shape "l4" 63 8650000 2110000 650000 0 "64748B" 19050) +
    (Bullet-Box "Arch bullets" 70 1000000 3300000 9900000 1700000 @(
        "Frontend нь API-аар scraping эхлүүлэх, status/log харах, үр дүн дүрслэх үүрэгтэй.",
        "FastAPI нь database, ML analyzer, Gemini analyzer, scraper process-ийг нэгтгэн удирдана.",
        "Database нь FacebookPost, PostComment, PostImage, AnalysisResult entity-д төвлөрсөн."
    ) 1700)
) 4

$slides += Slide-Xml "Scraper хэрхэн бүтээгдсэн бэ?" "Selenium browser automation + parsing fallback" (
    (Bullet-Box "Scraper bullets" 10 760000 1680000 10200000 3600000 @(
        "BrowserManager нь Firefox WebDriver session үүсгэж, login/session төлөв, restart, delay, scroll зэрэг browser үйлдлийг удирдсан.",
        "PostScraper нь Facebook group/page feed-ээс role=article болон бусад selector-оор пост элементүүдийг хайсан.",
        "JavaScript-аар ачаалагддаг content-ийг бодит browser дээр нээж, scroll хийж нэмэлт постуудыг ачаалсан.",
        "Пост бүрээс текст, огноо, like, share, comment count, зураг, сэтгэгдлийн мэдээллийг ялгаж авсан.",
        "UI өөрчлөгдөх эрсдэлд зориулж олон selector, fallback logic, random delay, session restart ашигласан."
    ) 1650)
) 5

$slides += Slide-Xml "Scraper хэрхэн ашиглагдсан бэ?" "Бид өгөгдлийг group/page-үүдээс цуглуулсан гэж тайлбарлах хэсэг" (
    (Bullet-Box "Use bullets" 10 760000 1650000 10400000 3550000 @(
        "Хэрэглэгч dashboard дээр зорилтот Facebook group/page URL эсвэл нэрсийг оруулна.",
        "API нь pages.txt файлыг шинэчилж, /api/v1/scraper/run endpoint-оор scraper process ажиллуулна.",
        "Scraper нь page бүрээр орж пост, сэтгэгдэл, engagement metric-үүдийг татаж авна.",
        "Цуглуулсан өгөгдөл PostgreSQL/SQLite/Firebase хадгалалтад бичигдэж, давхардлыг post_id/comment_id-аар хянана.",
        "Frontend нь /scraper/status болон /scraper/logs endpoint-оор явцыг бодит хугацаанд харуулна."
    ) 1650)
) 6

$slides += Slide-Xml "Өгөгдлийн загвар" "ML-д орох нэг ижил бүтэцтэй дата" (
    (Card "FacebookPost" "page_name, post_id, post_url, content, timestamp, likes, shares, comment_count, scraped_at" 10 760000 1700000 3200000 1850000 "F0FDFA") +
    (Card "PostComment" "post_id, comment_id, author_name, content, timestamp, likes, reply_to_id, scraped_at" 20 4450000 1700000 3200000 1850000 "EFF6FF") +
    (Card "AnalysisResult" "post_id, analysis_type, result JSON, analyzed_at. Sentiment, topic, engagement result хадгална." 30 8140000 1700000 3200000 1850000 "FFF7ED") +
    (Bullet-Box "Data note" 40 980000 4300000 9400000 850000 @(
        "Энэ бүтэц нь scraper-ээс ирсэн түүхий өгөгдлийг ML, AI report, dashboard-д дахин ашиглах боломжтой болгосон."
    ) 1650)
) 7

$slides += Slide-Xml "Machine Learning pipeline" "Цуглуулсан датаас таамаглал гаргах урсгал" (
    (Chip "Raw posts/comments" 10 700000 1880000 1900000 "E2E8F0") +
    (Chip "Preprocessing" 20 3000000 1880000 1700000 "DBEAFE") +
    (Chip "Feature engineering" 30 5200000 1880000 2100000 "DCFCE7") +
    (Chip "Models" 40 7800000 1880000 1300000 "FEF3C7") +
    (Chip "Prediction" 50 9700000 1880000 1500000 "FCE7F3") +
    (Line-Shape "m1" 60 2600000 2090000 400000 0 "64748B" 19050) +
    (Line-Shape "m2" 61 4700000 2090000 500000 0 "64748B" 19050) +
    (Line-Shape "m3" 62 7300000 2090000 500000 0 "64748B" 19050) +
    (Line-Shape "m4" 63 9100000 2090000 600000 0 "64748B" 19050) +
    (Bullet-Box "ML bullets" 70 950000 3350000 10000000 1600000 @(
        "Preprocessing: URL, mention, hashtag тэмдэглэгээ, илүүдэл тэмдэгт, whitespace цэвэрлэсэн.",
        "Feature engineering: content_length, word_count, hashtag_count, mention_count, question/exclamation, likes, shares, comment_count, hour, day_of_week.",
        "Model үр дүн: sentiment label, topic cluster, engagement score, high engagement probability."
    ) 1600)
) 8

$slides += Slide-Xml "Sentiment Analysis" "Positive / Negative / Neutral ангилал" (
    (Bullet-Box "Sentiment bullets" 10 760000 1600000 10000000 3800000 @(
        "AdvancedSentimentAnalyzer нь BERT-based model ашиглах боломжтойгоор бүтээгдсэн.",
        "BERT боломжгүй үед TextBlob polarity/subjectivity тооцож, positive/negative/neutral label гаргана.",
        "Keyword fallback нь гаднын dependency алдаа гарсан үед системийг зогсоохгүй.",
        "Post болон comment sentiment-ийг тусад нь тооцож, нийт хандлага болон confidence score гаргасан.",
        "Emotion analysis нь joy, anger, sadness, fear, surprise, neutral зэрэг илүү нарийн дохиог нэмсэн."
    ) 1650)
) 9

$slides += Slide-Xml "Engagement Prediction" "Пост өндөр оролцоо авах магадлалыг тооцох" (
    (Bullet-Box "Engagement bullets" 10 760000 1600000 10200000 3800000 @(
        "Engagement score = like, share, comment_count болон текстийн шинжүүд дээр суурилсан тоон үнэлгээ.",
        "Regression model нь тухайн постын боломжит engagement хэмжээг таамаглана.",
        "75-р percentile босгоор high-engagement label үүсгэж, classification зорилгоор ашигласан.",
        "Topic, sentiment, temporal pattern-уудыг хамтад нь харснаар ямар төрлийн контент илүү оролцоо авч байгааг тодорхойлсон.",
        "Үр дүн нь dashboard дээр risk/trend/recommendation хэлбэрээр харагдана."
    ) 1650)
) 10

$slides += Slide-Xml "AI Report System" "Gemini API нь аналитик тайлан үүсгэнэ" (
    (Bullet-Box "Gemini bullets" 10 760000 1600000 10400000 3700000 @(
        "Database-аас нийт пост, sentiment ratio, өндөр engagement-тэй пост, түлхүүр үг, topic зэрэг context бэлдэнэ.",
        "gemini_analyzer.py болон analyze-gemini.ts нь энэ context-ийг prompt болгон Gemini API руу илгээнэ.",
        "Gemini нь дата аналистын дүрээр trend, эрсдэл, сөрөг шалтгаан, сайжруулах зөвлөмжийг Монгол хэлээр гаргана.",
        "AI report нь Markdown хэлбэрээр frontend dashboard дээр шууд харагдана.",
        "Энэ модуль нь тоон графикийг хүний унших шийдвэрийн тайлан болгож хувиргасан."
    ) 1650)
) 11

$slides += Slide-Xml "Frontend ба Dashboard" "Хэрэглэгчийн ажиллах үндсэн орчин" (
    (Bullet-Box "Frontend bullets" 10 760000 1580000 10100000 3700000 @(
        "React + TypeScript + Vite ашиглан dashboard, admin control, AI report, chart хэсгүүдийг бүтээсэн.",
        "Хэрэглэгч group/page жагсаалт оруулах, scraper асаах, status/log харах боломжтой.",
        "API-аас пост, статистик, sentiment, AI report татаж график болон card хэлбэрээр харуулна.",
        "Backend unavailable үед demo fallback ажиллаж, UI тасралтгүй харагдах боломжтой.",
        "Polling ашиглан шинээр цугларсан өгөгдөл болон scraper log-ийг шинэчилнэ."
    ) 1650)
) 12

$slides += Slide-Xml "Үнэлгээ ба үр дүн" "Танилцуулгад оруулах ёстой хэмжигдэхүүнүүд" (
    (Card "Sentiment" "Accuracy, Precision, Recall, F1-score. Ангиллын чанарыг батлах үндсэн үзүүлэлт." 10 760000 1700000 3200000 1600000 "EFF6FF") +
    (Card "Prediction" "MAE, RMSE, R2. Engagement regression-ийн алдааг хэмжих үзүүлэлт." 20 4450000 1700000 3200000 1600000 "F0FDFA") +
    (Card "System" "Scraping time, API latency, collected posts/comments, success/failure pages." 30 8140000 1700000 3200000 1600000 "FFF7ED") +
    (Bullet-Box "Eval note" 40 900000 4050000 9850000 900000 @(
        "Тоо байхгүй бол demo дээр хэмжсэн бодит утгыг нэмж оруул. Энэ slide хамгаалалт дээр хамгийн их итгэл төрүүлнэ."
    ) 1650)
) 13

$slides += Slide-Xml "Хязгаарлалт ба цаашдын ажил" "Шударга боловч хүчтэй төгсгөл" (
    (Bullet-Box "Future bullets" 10 760000 1600000 10400000 3800000 @(
        "Facebook UI өөрчлөгдөхөд scraper selector шинэчлэх шаардлага гарч болно.",
        "Монгол хэлний sarcasm, товчлол, slang илүү нарийн тусгай model шаарддаг.",
        "Ирээдүйд OAuth-based official integration, X/Instagram/LinkedIn support нэмэх боломжтой.",
        "Зураг, видео content sentiment analysis болон multimodal AI report нэмэх боломжтой.",
        "Монгол хэлний labeled dataset бүрдүүлж custom sentiment model сургах нь дараагийн том сайжруулалт."
    ) 1650)
) 14

$slides += Slide-Xml "Дүгнэлт" "Гол хувь нэмэр" (
    (Bullet-Box "Conclusion bullets" 10 760000 1600000 10400000 3600000 @(
        "Facebook group/page өгөгдлийг автоматаар цуглуулах scraper систем боловсруулсан.",
        "Цуглуулсан пост, сэтгэгдлийг database-д бүтэцтэй хадгалж, ML pipeline-д ашигласан.",
        "Sentiment, topic, engagement prediction ашиглан олон нийтийн хандлага ба оролцоог үнэлсэн.",
        "Gemini API ашиглан тоон үр дүнг шийдвэрт чиглэсэн Монгол хэлний AI report болгосон.",
        "Frontend dashboard нь scraping, analysis, visualization-ийг нэг хэрэглэгчийн урсгалд нэгтгэсэн."
    ) 1650)
) 15

$slides += Slide-Xml "Анхаарал тавьсанд баярлалаа" "Асуулт, хариулт" (
    (Text-Box "Thanks" 10 1700000 2450000 8800000 900000 @("Системийн demo: scraper → ML analysis → AI report → dashboard") 2300 "0F766E" $true "ctr") +
    (Text-Box "Thanks2" 11 2500000 3600000 7200000 500000 @("Ө. Хүслэн • Улаанбаатар 2026") 1500 "475569" $false "ctr")
) 16

$root = Join-Path (Resolve-Path ".").Path ".pptx-build"
if (Test-Path -LiteralPath $root) {
    Remove-Item -LiteralPath $root -Recurse -Force
}
New-Dir $root
New-Dir "$root\_rels"
New-Dir "$root\ppt"
New-Dir "$root\ppt\_rels"
New-Dir "$root\ppt\slides"
New-Dir "$root\ppt\slides\_rels"
New-Dir "$root\ppt\slideLayouts"
New-Dir "$root\ppt\slideLayouts\_rels"
New-Dir "$root\ppt\slideMasters"
New-Dir "$root\ppt\slideMasters\_rels"
New-Dir "$root\ppt\theme"
New-Dir "$root\docProps"

$slideOverrides = ""
for ($i = 1; $i -le $slides.Count; $i++) {
    Write-Utf8NoBom "$root\ppt\slides\slide$i.xml" $slides[$i-1]
    Write-Utf8NoBom "$root\ppt\slides\_rels\slide$i.xml.rels" '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/></Relationships>'
    $slideOverrides += "<Override PartName=`"/ppt/slides/slide$i.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.presentationml.slide+xml`"/>"
}

Write-Utf8NoBom "$root\[Content_Types].xml" @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  $slideOverrides
</Types>
"@

Write-Utf8NoBom "$root\_rels\.rels" '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>'

$sldIds = ""
$rels = '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
for ($i = 1; $i -le $slides.Count; $i++) {
    $rid = $i + 1
    $sid = 255 + $i
    $sldIds += "<p:sldId id=`"$sid`" r:id=`"rId$rid`"/>"
    $rels += "<Relationship Id=`"rId$rid`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide`" Target=`"slides/slide$i.xml`"/>"
}
Write-Utf8NoBom "$root\ppt\presentation.xml" @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>$sldIds</p:sldIdLst>
  <p:sldSz cx="12192000" cy="6858000" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle/>
</p:presentation>
"@
Write-Utf8NoBom "$root\ppt\_rels\presentation.xml.rels" "<?xml version=`"1.0`" encoding=`"UTF-8`" standalone=`"yes`"?><Relationships xmlns=`"http://schemas.openxmlformats.org/package/2006/relationships`">$rels</Relationships>"

Write-Utf8NoBom "$root\ppt\slideMasters\slideMaster1.xml" @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>
"@
Write-Utf8NoBom "$root\ppt\slideMasters\_rels\slideMaster1.xml.rels" '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>'

Write-Utf8NoBom "$root\ppt\slideLayouts\slideLayout1.xml" @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>
"@
Write-Utf8NoBom "$root\ppt\slideLayouts\_rels\slideLayout1.xml.rels" '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>'

Write-Utf8NoBom "$root\ppt\theme\theme1.xml" @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Diploma Theme">
  <a:themeElements>
    <a:clrScheme name="Diploma"><a:dk1><a:srgbClr val="0F172A"/></a:dk1><a:lt1><a:srgbClr val="F8FAFC"/></a:lt1><a:dk2><a:srgbClr val="334155"/></a:dk2><a:lt2><a:srgbClr val="E2E8F0"/></a:lt2><a:accent1><a:srgbClr val="0F766E"/></a:accent1><a:accent2><a:srgbClr val="2563EB"/></a:accent2><a:accent3><a:srgbClr val="F59E0B"/></a:accent3><a:accent4><a:srgbClr val="DB2777"/></a:accent4><a:accent5><a:srgbClr val="7C3AED"/></a:accent5><a:accent6><a:srgbClr val="16A34A"/></a:accent6><a:hlink><a:srgbClr val="2563EB"/></a:hlink><a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="Aptos"><a:majorFont><a:latin typeface="Aptos Display"/><a:cs typeface="Aptos"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/><a:cs typeface="Aptos"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
</a:theme>
"@

$now = (Get-Date).ToUniversalTime().ToString("s") + "Z"
Write-Utf8NoBom "$root\docProps\core.xml" @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Нийгмийн сүлжээний өгөгдлийн автомат цуглуулга ба таамаглалт шинжилгээний систем</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">$now</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">$now</dcterms:modified>
</cp:coreProperties>
"@
Write-Utf8NoBom "$root\docProps\app.xml" @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex PowerShell PPTX Builder</Application>
  <PresentationFormat>On-screen Show (16:9)</PresentationFormat>
  <Slides>$($slides.Count)</Slides>
</Properties>
"@

$resolvedOutput = Join-Path (Resolve-Path ".").Path $OutputPath
$outputDir = Split-Path -Parent $resolvedOutput
New-Dir $outputDir
if (Test-Path -LiteralPath $resolvedOutput) {
    Remove-Item -LiteralPath $resolvedOutput -Force
}
$zipPath = "$resolvedOutput.zip"
if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::Open($zipPath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    $files = Get-ChildItem -LiteralPath $root -Recurse -File
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($root.Length + 1).Replace('\', '/')
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $file.FullName, $relative) | Out-Null
    }
}
finally {
    $archive.Dispose()
}
Move-Item -LiteralPath $zipPath -Destination $resolvedOutput -Force

Write-Host "Created $resolvedOutput"
