import os

replacements = {
    # GeminiAnalyzer.tsx
    'Gemini AI Analysis': 'Gemini AI Шинжилгээ',
    'Generate intelligent insights and text summaries using Google Gemini models.': 'Google Gemini ашиглан ухаалаг дүн шинжилгээ болон текстийн хураангуй үүсгэх.',
    'Enter raw text, JSON data, or descriptions to analyze...': 'Шинжлэх бичвэр, JSON өгөгдөл эсвэл тайлбар оруулна уу...',
    'General analysis': 'Ерөнхий шинжилгээ',
    'Summarization': 'Хураангуйлал',
    'Sentiment check': 'Хандлагын шалгалт',
    'Entity extraction': 'Тодорхой зүйлсийг ялгах (Entity extraction)',
    'Run AI Analysis': 'AI Шинжилгээг эхлүүлэх',
    'Analysis Pipeline is Ready': 'Шинжилгээний дамжлага бэлэн',
    'Input data above to trigger server-side Vercel AI SDK processing.': 'Дээр өгөгдөл оруулж серверийн Vercel AI SDK боловсруулалтыг эхлүүлнэ үү.',
    'Analysis result': 'Шинжилгээний үр дүн',
    'Copy': 'Хуулах',
    'Copied!': 'Хуулагдсан!',
    
    # GeminiQA.tsx
    'AI Assistant Q&A': 'AI Туслах Q&A',
    'Ask questions about the collected social media data.': 'Цуглуулсан сошиал медиа өгөгдлийн талаар асуулт асуух.',
    'Start by asking a question...': 'Асуулт асууж эхэлнэ үү...',
    'Hello! I can analyze the social media data you have collected. What would you like to know?': 'Сайн байна уу! Таны цуглуулсан сошиал медиа өгөгдөлд би дүн шинжилгээ хийж чадна. Та юу мэдэхийг хүсэж байна вэ?'
}

for root, dirs, files in os.walk('src/components'):
    for f in files:
        if f.endswith('.tsx'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            for en, mn in replacements.items():
                content = content.replace(f"'{en}'", f"'{mn}'")
                content = content.replace(f'"{en}"', f'"{mn}"')
                content = content.replace(f'>{en}<', f'>{mn}<')
                
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(content)

print("Translated extras.")
