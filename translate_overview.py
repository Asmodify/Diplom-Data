import os

filepath = 'src/components/Overview.tsx'

replacements = {
    'Generative Artificial Intelligence': 'Үүсгэгч Хиймэл Оюун Ухаан',
    'Models that create new content from learned patterns': 'Суралцсан хэв маягаас шинэ контент үүсгэдэг загварууд',
    'Generative artificial intelligence': 'Үүсгэгч хиймэл оюун ухаан',
    'refers to models that predict and generate': 'нь таамаглал дэвшүүлж, шинээр үүсгэдэг загваруудыг хэлдэг',
    'various types of outputs (such as text, images, or audio) based on what&rsquo;s statistically': 'текст, зураг эсвэл дуу гэх мэт төрөл бүрийн гарагуудыг статистикийн хувьд',
    'likely, pulling from patterns they&rsquo;ve learned from their training data.': 'юу илүү магадлалтай байгааг сургалтын өгөгдлөөс нь авч ашигладаг.',
    '>Examples<': '>Жишээнүүд<',
    'Given a photo, a generative model can generate a caption.': 'Зураг өгөхөд үүсгэгч загвар тайлбар үүсгэж чадна.',
    'Given an audio file, a generative model can generate a transcription.': 'Дуу өгөхөд үүсгэгч загвар бичвэр үүсгэж чадна.',
    'Given a text description, a generative model can generate an image.': 'Бичвэр тайлбар өгөхөд үүсгэгч загвар зураг үүсгэж чадна.',
    'Large Language Models': 'Томоохон хэлний загварууд (LLM)',
    'Text-focused generative models': 'Текстэд төвлөрсөн үүсгэгч загварууд',
    'A <strong>large language model (LLM)</strong> is a subset of generative models focused': '<strong>Томоохон хэлний загвар (LLM)</strong> нь үндсэндээ',
    'primarily on <strong>text</strong>. An LLM takes a sequence of words as input and aims to': '<strong>текст</strong> дээр төвлөрдөг үүсгэгч загваруудын дэд хэсэг юм. LLM нь үгсийн дарааллыг оролт болгон авч,',
    'predict the most likely sequence to follow. It assigns probabilities to potential next': 'дараагийн хамгийн магадлалтай дарааллыг таамаглахыг зорьдог. Энэ нь боломжит',
    'sequences and then selects one. The model continues to generate sequences until it meets a': 'дараагийн дарааллуудад магадлал оноож, нэгийг нь сонгодог. Загвар тогтоосон',
    'specified stopping criterion.': 'зогсох нөхцөлд хүрэх хүртэл үргэлжлүүлэн үүсгэдэг.',
    'LLMs learn by training on massive collections of written text, which means they will be': 'LLM-үүд нь асар их хэмжээний бичвэрээс суралцдаг ба энэ нь',
    'better suited to some use cases than others. For example, a model trained on GitHub data': 'тэд зарим хэрэглээнд илүү тохиромжтой байх болно гэсэн үг юм. Жишээ нь, GitHub өгөгдөл дээр',
    'would understand the probabilities of sequences in source code particularly well.': 'сургагдсан загвар эх кодын дарааллын магадлалыг онцгой сайн ойлгоно.',
    '<strong>âš\xa0 Important:</strong> When asked about less known or absent information,': '<strong>Чухал:</strong> Бага мэддэг эсвэл огт байхгүй мэдээллийн талаар асуухад,',
    'LLMs might &ldquo;hallucinate&rdquo; or make up information. It&rsquo;s essential to': 'LLM-үүд "хий үзэгдэл" харж эсвэл мэдээлэл зохиож магадгүй. Таны хэрэгцээт мэдээлэл',
    'consider how well-represented the information you need is in the model.': 'загварт хэр сайн тусгагдсан болохыг анхаарах нь чухал.',
    'Convert complex data into dense vector representations': 'Нарийн төвөгтэй өгөгдлийг нягт вектор дүрслэл рүү хөрвүүлэх',
    'An <strong>embedding model</strong> is used to convert complex data (like words or images)': '<strong>Эмбеддинг загвар</strong> нь нарийн төвөгтэй өгөгдлийг (үг эсвэл зураг гэх мэт)',
    'into a dense vector (a list of numbers) representation, known as an <strong>embedding</strong>.': 'нягт вектор (тоон жагсаалт) дүрслэл рүү хөрвүүлэхэд ашиглагддаг бөгөөд үүнийг <strong>эмбеддинг</strong> гэдэг.',
    'Unlike generative models, embedding models do not generate new text or data. Instead, they': 'Үүсгэгч загваруудаас ялгаатай нь эмбеддинг загварууд нь шинэ текст эсвэл өгөгдөл үүсгэдэггүй. Харин,',
    'provide representations of semantic and syntactic relationships between entities that can be': 'энэ нь бусад загварууд эсвэл хэл боловсруулах даалгавруудад',
    'used as input for other models or other natural language processing tasks.': 'оролт болгон ашиглаж болох объектуудын утгын болон бүтцийн хамаарлын дүрслэлийг өгдөг.',
    '>Input<': '>Оролт<',
    'Complex data such as text, images, or audio': 'Текст, зураг, эсвэл аудио зэрэг нарийн төвөгтэй өгөгдөл',
    '>Process<': '>Үйл явц<',
    'Converts into a dense numerical vector': 'Нягт тоон вектор руу хөрвүүлнэ',
    '>Output<': '>Гаралт<',
    'Embeddings usable by other models and tasks': 'Бусад загварууд болон даалгавраар ашиглагдахуйц эмбеддингүүд',
    '>How This System Uses AI<': '>Энэ Систем AI-г хэрхэн ашигладаг вэ?<',
    'Our implementation powered by the Vercel AI SDK and Google Gemini': 'Бидний хэрэгжүүлэлт нь Vercel AI SDK болон Google Gemini дээр суурилсан',
    'Collect': 'Цуглуулах',
    'Scrape social media posts from Facebook pages via FastAPI backend': 'FastAPI backend-ийг ашиглан Facebook хуудсуудаас сошиал медиа постуудыг цуглуулах',
    'Store': 'Хадгалах',
    'Persist posts, comments, and images in Supabase (PostgreSQL)': 'Постууд, сэтгэгдлүүд болон зургуудыг Supabase (PostgreSQL) дотор хадгалах',
    'Aggregate': 'Нэгтгэх',
    'Pre-aggregate data to limit payload size before sending to AI': 'AI руу илгээхээс өмнө өгөгдлийн хэмжээг хязгаарлахын тулд урьдчилан нэгтгэх',
    'Analyze': 'Шинжлэх',
    'Send to Gemini 2.0 Flash via Vercel AI SDK for structured insights': 'Бүтэцжсэн дүн шинжилгээ гаргахын тулд Vercel AI SDK-р дамжуулан Gemini 2.0 Flash руу илгээх'
}

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

for eng, mongol in replacements.items():
    content = content.replace(eng, mongol)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Overview.tsx translated.")
