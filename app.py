# Import necessary libraries
import os
import json
import base64
from io import BytesIO 
import re 

from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
import openai
from werkzeug.utils import secure_filename

# Import ReportLab for PDF generation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Import platform to check OS for font path (optional, for local development specific fonts)
import platform

# Initialize the Flask application
app = Flask(__name__, template_folder='templates', static_folder='static')

# Define the folder for uploading images (primarily for historical reference or direct serving if needed)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure OpenAI API client
try:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    print("DEBUG: OpenAI client initialized successfully.")
except Exception as e:
    print(f"DEBUG ERROR: Failed to initialize OpenAI client: {e}")
    client = None

# Define the application password
APP_PASSWORD = "360estate"

# --- Routes for the application ---

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get("password")
    if password == APP_PASSWORD:
        return render_template('form.html')
    else:
        return render_template('login.html', error=True)

@app.route('/generate', methods=['POST'])
def generate_ad():
    print("DEBUG: generate_ad route hit!")

    # Parse JSON data from the request
    data = request.json
    
    # Extract text fields
    form_data = {
        'property_type': data.get('property_type', 'Апартамент'), # New field
        'location': data.get('location', 'неуточнена'),
        'price': data.get('price', 'неуточнена'),
        'area': data.get('area', 'неуточнена'),
        'floor': data.get('floor', 'неуточнен'),
        'year_built': data.get('year_built', 'неуточнена'),
        'installment': data.get('installment', 'неуточнена'),
        'furnishing': data.get('furnishing', 'неуточнено'),
        'panorama': data.get('panorama', 'неуточнена'),
        'elevator': data.get('elevator', 'неуточнен'),
        'garage': data.get('garage', 'неуточнен'),
        'exclusive': data.get('exclusive', 'неуточнена'),
        'financing': data.get('financing', 'неуточнено'),
        'unique_features': data.get('unique_features', 'неуточнени'),
        'broker_name': data.get('broker_name', 'брокер'), # New field
        'broker_phone': data.get('broker_phone', 'неуточнен телефон'), # New field
        # New specific fields for different property types
        'yard_area': data.get('yard_area', ''),
        'number_of_floors': data.get('number_of_floors', ''),
        'heating_system': data.get('heating_system', ''),
        'pool': data.get('pool', ''),
        'garden': data.get('garden', ''),
        'zoning': data.get('zoning', ''),
        'utilities': data.get('utilities', ''),
        'access_road': data.get('access_road', ''),
        'commercial_type': data.get('commercial_type', ''),
        'foot_traffic': data.get('foot_traffic', ''),
        'current_business': data.get('current_business', ''),
        'facilities': data.get('facilities', ''),
        'total_built_up_area': data.get('total_built_up_area', ''),
        'number_of_units': data.get('number_of_units', ''),
        'occupancy': data.get('occupancy', ''),
        'income_potential': data.get('income_potential', ''),
    }

    # Extract base64 image data
    image_data_base64 = data.get('images', [])

    generated_short_ad = "Възникна грешка при генерирането на кратката обява."
    generated_long_ad = "Възникна грешка при генерирането на дългата обява."
    error_message = None

    try:
        if client is None:
            raise ValueError("OpenAI клиентът не е инициализиран. API ключът може да липсва или да е невалиден.")

        print("DEBUG: OpenAI client is ready for vision model.")

        # Construct basic text prompt based on property type and all available data
        base_text_prompt = f"""
Ти си експерт по имотни обяви и маркетинг за недвижими имоти. Твоята задача е да създадеш ДВЕ ВЕРСИИ на обява за продажба на имот, съобразена с Facebook Marketplace:
1.  **КРАТКА ВЕРСИЯ:** Много сбита, акцентираща на основните предимства, подходяща за бързо сканиране.
2.  **ДЪЛГА ВЕРСИЯ:** Подробна и описателна, с повече детайли за всички характеристики.

**СТРОГО СЕ ПРИДЪРЖАЙ САМО КЪМ ФАКТИЧЕСКИ ДАННИ, ПРЕДОСТАВЕНИ В ТЕКСТА ИЛИ ВИЗУАЛНО ОТКРИТИ В ИЗОБРАЖЕНИЯТА. НЕ ИЗМИСЛЯЙ НИКАКВИ ДОПЪЛНИТЕЛНИ ХАРАКТЕРИСТИКИ ИЛИ ПРЕДИМСТВА.**
**НЕ ВКЛЮЧВАЙ НОМЕРИРАНИ СПИСЪЦИ (1., 2., 3. и т.н.) ИЛИ ВЪТРЕШНИ МАРКЕРИ ЗА СЕКЦИИ В ГЕНЕРИРАНИЯ ТЕКСТ НА ОБЯВИТЕ. Генерирай директно съдържанието.**

Анализирай внимателно предоставените изображения за ключови визуални предимства (напр. луксозен интериор, панорамна гледка, модерни уреди, простор, уют, състояние на стаите, обзавеждане, състояние на двор/градина, комуникации за парцел, лице на улица за магазин) и ги интегрирай в обявата.

Данни за имота (Тип: {form_data['property_type']}):
📌 Локация: {form_data['location']}
💰 Цена: {form_data['price']} €
📐 Площ: {form_data['area']} кв.м
{f"🌳 Площ на двор: {form_data['yard_area']}" if form_data['yard_area'] else ""}
{f"🏢 Етаж: {form_data['floor']}" if form_data['floor'] else ""}
{f"🏗️ Година на строеж: {form_data['year_built']}" if form_data['year_built'] else ""}
💳 Месечна вноска: {form_data['installment']} €
🛋️ Обзавеждане: {form_data['furnishing']}
🌄 Панорама: {form_data['panorama']}
🛗 Асансьор: {form_data['elevator']}
🚗 Гараж: {form_data['garage']}
💼 Ексклузивност: {form_data['exclusive']}
🏦 Финансиране: {form_data['financing']}
🖼️ Уникални предимства (допълнителен текст от брокер): {form_data['unique_features']}
{f"🏡 Брой етажи: {form_data['number_of_floors']}" if form_data['number_of_floors'] else ""}
{f"🔥 Отопление: {form_data['heating_system']}" if form_data['heating_system'] else ""}
{f"🏊 Басейн: {form_data['pool']}" if form_data['pool'] else ""}
{f"🌿 Градина: {form_data['garden']}" if form_data['garden'] else ""}
{f"🎯 Зониране/Предназначение: {form_data['zoning']}" if form_data['zoning'] else ""}
{f"💧 Комуникации: {form_data['utilities']}" if form_data['utilities'] else ""}
{f"🛣️ Достъп до път: {form_data['access_road']}" if form_data['access_road'] else ""}
{f"🛍️ Тип обект: {form_data['commercial_type']}" if form_data['commercial_type'] else ""}
{f"🚶 Поток от хора: {form_data['foot_traffic']}" if form_data['foot_traffic'] else ""}
{f"🏢 Настоящ бизнес: {form_data['current_business']}" if form_data['current_business'] else ""}
{f"🚽 Удобства в обекта: {form_data['facilities']}" if form_data['facilities'] else ""}
{f"🏗️ Обща РЗП: {form_data['total_built_up_area']}" if form_data['total_built_up_area'] else ""}
{f"🏘️ Брой обекти/единици: {form_data['number_of_units']}" if form_data['number_of_units'] else ""}
{f"📈 Заетост: {form_data['occupancy']}" if form_data['occupancy'] else ""}
{f"💰 Потенциал за доход: {form_data['income_potential']}" if form_data['income_potential'] else ""}

---КРАТКА ОБЯВА START---
💥 Купи за {form_data['installment']} €/месец – [2-3 най-силни, ключови предимства, извлечени от данните и снимките, релевантни за {form_data['property_type']}]
[Кратък, емоционален встъпителен ред. Кратко описание на имота, с акцент върху 2-3 най-важни характеристики за {form_data['property_type']}, открити от снимките и данните.]
✨ Този имот може да бъде закупен на разсрочено плащане чрез Банков Ипотечен Кредит с месечна вноска от {form_data['installment']} €.\n🔓Без начален капитал, без доказани доходи или с влошена кредитна история – ние съдействаме за успешно банково финансиране.\n📌 Финансирането не е пречка – то е част от решението.
📞 За оглед: {form_data['broker_name']} – {form_data['broker_phone']}
---КРАТКА ОБЯВА END---

---ДЪЛГА ОБЯВА START---
💥 Купи за {form_data['installment']} €/месец – [2-3 най-силни, ключови предимства, извлечени от данните и снимките, релевантни за {form_data['property_type']}]
[Емоционален встъпителен абзац, представящ най-големите ползи.]
Ключови Характеристики (Резюме):
📐 Площ: {form_data['area']} кв.м | 💰 Цена: {form_data['price']} € | 📍 Локация: {form_data['location']} | 🛋️ Обзавеждане: {form_data['furnishing']}
[Подробно описание на {form_data['property_type']}, неговото разпределение, състояние, характеристики и предимства, извлечени от снимките и данните.]
[Информация за локацията и предимствата на квартала/района, специфични за {form_data['property_type']}.]
Защо с 360ESTATE?:
[Акцент върху професионална подкрепа, сигурност и улеснение.]
Идеален избор за:
[2-3 подходящи групи (напр. Младо семейство, Инвестиция с висока доходност).]
✨ Този имот може да бъде закупен на разсрочено плащане чрез Банков Ипотечен Кредит с месечна вноска от {form_data['installment']} €.\n🔓Без начален капитал, без доказани доходи или с влошена кредитна история – ние съдействаме за успешно банково финансиране.\n📌 Финансирането не е пречка – то е част от решението.
📞 За оглед: {form_data['broker_name']} – {form_data['broker_phone']}
[Генерирай подходящи хаштагове за {form_data['property_type']} и локацията.]
---ДЪЛГА ОБЯВА END---
"""
        messages_content = [{"type": "text", "text": base_text_prompt}]

        # Add image URLs to the messages_content if available
        for img_b64 in image_data_base64:
            # ReportLab only supports JPEG, PNG, GIF, BMP. Check image type if possible.
            # For simplicity, we just pass the base64 string directly
            messages_content.append({"type": "image_url", "image_url": {"url": img_b64}})

        response = client.chat.completions.create(
            model="gpt-4o", # Using GPT-4o for multimodal capabilities
            messages=[{"role": "user", "content": messages_content}],
            temperature=0.8,
            max_tokens=2500 # Increased max_tokens to ensure enough space for detailed output
        )
        full_generated_text = response.choices[0].message.content.strip()
        print(f"DEBUG: OpenAI Response received. Full text length: {len(full_generated_text)}")

        # Parse the full generated text into short and long versions using updated markers
        short_ad_start_marker = "---КРАТКА ОБЯВА START---"
        short_ad_end_marker = "---КРАТКА ОБЯВА END---"
        long_ad_start_marker = "---ДЪЛГА ОБЯВА START---"
        long_ad_end_marker = "---ДЪЛГА ОБЯВА END---"

        short_ad = "Неуспешно генериране на кратка обява. Моля, проверете логовете."
        long_ad = "Неуспешно генериране на дълга обява. Моля, проверете логовете."

        # Extract Short Ad
        start_index = full_generated_text.find(short_ad_start_marker)
        end_index = full_generated_text.find(short_ad_end_marker)
        if start_index != -1 and end_index != -1:
            short_ad = full_generated_text[start_index + len(short_ad_start_marker):end_index].strip()
        
        # Extract Long Ad
        start_index = full_generated_text.find(long_ad_start_marker)
        end_index = full_generated_text.find(long_ad_end_marker)
        if start_index != -1 and end_index != -1:
            long_ad = full_generated_text[start_index + len(long_ad_start_marker):end_index].strip()


    except openai.APIError as e:
        error_message = f"AI грешка: Проблем с OpenAI API: {str(e)}. Моля, проверете API ключа и лимитите си."
        print(f"DEBUG ERROR: OpenAI API Error: {error_message}")
        return jsonify({"error": error_message}), 500
    except ValueError as e:
        error_message = f"Конфигурационна грешка: {str(e)}"
        print(f"DEBUG ERROR: ValueError: {error_message}")
        return jsonify({"error": error_message}), 500
    except Exception as e:
        error_message = f"Неочаквана грешка: {str(e)}"
        print(f"DEBUG ERROR: Generic Exception in generate_ad: {error_message}")
        return jsonify({"error": error_message}), 500

    print(f"DEBUG: Returning JSON response with two ad versions.")
    return jsonify({
        'short_ad': short_ad,
        'long_ad': long_ad,
        'images_for_pdf': image_data_base64 # Pass base64 images to frontend for PDF generation
    })

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    print("DEBUG: generate_pdf route hit!")
    data = request.json
    ad_text = data.get('ad_text', 'Няма текст за обявата.')
    images_b64 = data.get('images_for_pdf', [])
    
    buffer = BytesIO()
    # Use portrait(A4) for standard portrait orientation
    doc = SimpleDocTemplate(buffer, pagesize=portrait(A4),
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    styles = getSampleStyleSheet()

    # Register a font that supports Cyrillic characters
    # This requires the font file to be available on the Render server.
    # Common cross-platform fonts: DejaVu Sans, Liberation Sans, or Noto Sans.
    # For simplicity and common availability in Linux environments (like Render),
    # we'll try to register DejaVuSans.
    # On Render, you might need to ensure these fonts are present in the build environment.
    # A robust solution often involves bundling the font files with your app.
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Attempt to register a common font with Cyrillic support
    # You might need to upload this .ttf file to your project and adjust the path
    # For Render, a common strategy is to place fonts in a 'fonts' directory within your app.
    try:
        # Example path if you bundle the font in a 'fonts' folder in your root project
        font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf')
        if not os.path.exists(font_path):
            # Fallback to system path or commonly available paths on Linux (like Render's base image)
            # This is less reliable without bundling.
            # On Render, fonts like DejaVuSans might be in /usr/share/fonts/truetype/dejavu/
            # For a guaranteed solution, bundle DejaVuSans.ttf in your 'fonts' folder.
            print("DEBUG: DejaVuSans.ttf not found in app's fonts folder. Trying system path.")
            if platform.system() == "Linux":
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # Common path on Linux
            else:
                font_path = "DejaVuSans.ttf" # Fallback, might not work
                
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_path)) # Register bold if available
            styles.add(ParagraphStyle(name='CyrillicNormal', parent=styles['Normal'], fontName='DejaVuSans', fontSize=10, leading=14, spaceAfter=6, alignment=TA_LEFT))
            styles.add(ParagraphStyle(name='CyrillicBold', parent=styles['h2'], fontName='DejaVuSans-Bold', fontSize=12, leading=14, alignment=TA_LEFT))
            styles.add(ParagraphStyle(name='CyrillicTitle', parent=styles['h1'], fontName='DejaVuSans-Bold', fontSize=16, leading=18, alignment=TA_CENTER, spaceAfter=12))
            styles.add(ParagraphStyle(name='CyrillicImageCaption', parent=styles['Normal'], fontName='DejaVuSans', fontSize=8, alignment=TA_CENTER, spaceAfter=6))
            styles.add(ParagraphStyle(name='CyrillicBullet', parent=styles['Normal'], fontName='DejaVuSans', fontSize=10, leading=14, spaceAfter=2, leftIndent=36))

            # Update default styles to use Cyrillic-compatible fonts
            styles['Normal'].fontName = 'DejaVuSans'
            styles['h1'].fontName = 'DejaVuSans-Bold'
            styles['h2'].fontName = 'DejaVuSans-Bold'
            styles['Bullet'].fontName = 'DejaVuSans'
            
            # Update custom styles to use Cyrillic-compatible fonts
            styles.add(ParagraphStyle(name='AdTitle', parent=styles['CyrillicTitle']))
            styles.add(ParagraphStyle(name='AdBody', parent=styles['CyrillicNormal']))
            styles.add(ParagraphStyle(name='ImageCaption', parent=styles['CyrillicImageCaption']))
            styles.add(ParagraphStyle(name='BulletPoint', parent=styles['CyrillicBullet']))

            print("DEBUG: DejaVuSans font registered successfully.")
        else:
            print(f"DEBUG ERROR: DejaVuSans.ttf not found at {font_path}. Cyrillic might not display correctly.")
            # Fallback to default fonts if DejaVuSans is not found
            styles.add(ParagraphStyle(name='AdTitle', parent=styles['h1'], fontSize=16, leading=18, alignment=TA_CENTER, spaceAfter=12))
            styles.add(ParagraphStyle(name='AdBody', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=6, alignment=TA_LEFT))
            styles.add(ParagraphStyle(name='ImageCaption', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, spaceAfter=6))
            styles.add(ParagraphStyle(name='BulletPoint', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=2, leftIndent=36))

    except Exception as e:
        print(f"DEBUG ERROR: Failed to register font: {e}. Cyrillic might not display correctly.")
        # Fallback to default fonts if font registration fails
        styles.add(ParagraphStyle(name='AdTitle', parent=styles['h1'], fontSize=16, leading=18, alignment=TA_CENTER, spaceAfter=12))
        styles.add(ParagraphStyle(name='AdBody', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=6, alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='ImageCaption', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, spaceAfter=6))
        styles.add(ParagraphStyle(name='BulletPoint', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=2, leftIndent=36))


    story = []

    story.append(Paragraph("<b><font size=16>Генерирана Обява от 360ESTATE</font></b>", styles['AdTitle']))
    story.append(Spacer(1, 0.2 * inch))

    # Add ad text
    lines = ad_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line: # Empty line
            story.append(Spacer(1, 0.1 * inch))
            continue

        # Convert markdown bold/italic/underline to ReportLab's RML
        formatted_line = line
        
        # Regex to replace markdown bold (**text** or __text__)
        formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted_line)
        formatted_line = re.sub(r'__(.*?)__', r'<b>\1</b>', formatted_line)
        
        # Regex to replace markdown italic (*text* or _text_) - ReportLab needs <i>
        formatted_line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', formatted_line)
        formatted_line = re.sub(r'_(.*?)_', r'<i>\1</i>', formatted_line)

        # Replace common emojis with their text equivalents for PDF compatibility
        emoji_map = {
            '💥': 'Взрив: ', '✨': 'Звезда: ', '🔓': 'Отключено: ', '📌': 'Пин: ', '📞': 'Телефон: ',
            '✅': 'ОК: ', '🏡': 'Къща: ', '📐': 'Площ: ', '💰': 'Пари: ', '📍': 'Локация: ',
            '🛋️': 'Мебели: ', '🌳': 'Дърво: ', '🏊': 'Басейн: ', '🚗': 'Кола: ', '🔥': 'Огън: ',
            '🏞️': 'Пейзаж: ', '💧': 'Вода: ', '⚡': 'Ел.: ', '🛣️': 'Път: ', '🛍️': 'Магазин: ',
            '📈': 'Графика: ', '🚶‍♂️': 'Човек: ', '🏗️': 'Строеж: ', '🏘️': 'Сгради: ', '🎯': 'Цел: ',
            '💡': 'Идея: ', '🛗': 'Асансьор: ', '🛌': 'Спалня: ', '🛀': 'Баня: ', '🍽️': 'Кухня: ',
            '🌿': 'Растение: ', '🏢': 'Сграда: ', '🔑': 'Ключ: ', '☀️': 'Слънце: ', '🌊': 'Вълни: '
        }
        for emoji, text_eq in emoji_map.items():
            formatted_line = formatted_line.replace(emoji, text_eq)
        
        # Remove any other complex unicode/emojis that might cause issues and are not in map
        # This is a broad approach to prevent errors.
        formatted_line = formatted_line.encode('ascii', 'ignore').decode('ascii')


        # Handle list items for bullet points
        if formatted_line.startswith('• ') or formatted_line.startswith('- ') or formatted_line.startswith('* '):
            story.append(Paragraph(formatted_line, styles['BulletPoint']))
        elif formatted_line.startswith('ОК: '): # Handle emojis replaced by text_eq like 'ОК: '
            story.append(Paragraph(f'• {formatted_line[4:]}', styles['BulletPoint']))
        else:
            story.append(Paragraph(formatted_line, styles['AdBody']))

    story.append(Spacer(1, 0.2 * inch)) # Reduced space after text

    # Add images
    if images_b64:
        # Max height for all images combined to try to fit on one page
        # A4 height (842 points) - top/bottom margins (2*0.75*72 points = 108) - text height (estimated 200-300) = remaining height
        # Remaining height approx 400-500 points
        max_total_images_height = (portrait(A4)[1] - (2 * 0.75 * inch) - (len(story) * 14)) * 0.6 # Adjust multiplier for content space
        current_images_height = 0
        
        story.append(Paragraph("<b>Прикачени изображения:</b>", styles['CyrillicBold'] if 'CyrillicBold' in styles else styles['h2']))
        story.append(Spacer(1, 0.1 * inch)) # Reduced space

        for i, img_b64 in enumerate(images_b64):
            try:
                # Remove data:image/png;base64, or similar prefix
                header, base64_string = img_b64.split(',', 1)
                img_data = base64.b64decode(base64_string)
                img = Image(BytesIO(img_data))
                
                # Scale image to fit page width, maintaining aspect ratio
                max_img_width = A4[0] - 1.5 * inch # A4 width minus side margins (0.75 inch each side)
                
                img_width = img.drawWidth
                img_height = img.drawHeight
                
                if img_width > max_img_width:
                    scale_factor = max_img_width / img_width
                    img_width = max_img_width
                    img_height = img_height * scale_factor
                
                # Further scale height if it's still too large for total page space (and for single image display)
                # Max height for a single image, try to balance for multiple images
                max_single_img_height = 2.5 * inch # Reduced max single image height
                if img_height > max_single_img_height:
                    scale_factor = max_single_img_height / img_height
                    img_width = img_width * scale_factor
                    img_height = max_single_img_height
                
                # Check if adding this image exceeds total allowed height (and if it's the last one)
                if (current_images_height + img_height + (0.1 * inch * 2) > max_total_images_height) and (i < len(images_b64) - 1):
                    # If this image would overflow AND it's not the last image,
                    # consider adding it to a new page or reducing more.
                    # For "fit on one page", we might need to skip some images or dramatically scale down.
                    # For now, if it overflows, it will just go to next page, but overall smaller.
                    pass 

                img.drawWidth = img_width
                img.drawHeight = img_height
                
                story.append(img)
                story.append(Paragraph(f"<i>Снимка {i+1}</i>", styles['ImageCaption']))
                story.append(Spacer(1, 0.1 * inch))
                current_images_height += img_height + (0.1 * inch * 2) # Update current height

            except Exception as e:
                print(f"DEBUG ERROR: Failed to embed image {i+1} in PDF: {e}")
                story.append(Paragraph(f"<i>Неуспешно зареждане на снимка {i+1}</i>", styles['ImageCaption']))
                story.append(Spacer(1, 0.1 * inch))

    try:
        # Build the PDF
        doc.build(story)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name='Obyava_za_Imot.pdf', mimetype='application/pdf')
    except Exception as e:
        print(f"DEBUG ERROR: Failed to build PDF: {e}")
        return jsonify({"error": f"Грешка при генериране на PDF: {str(e)}"}), 500

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Serve static files (images) - This route is kept for consistency but not actively used for new uploads in this version
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    print(f"DEBUG: Serving static file: {filename} from {app.config['UPLOAD_FOLDER']}")
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        print(f"DEBUG ERROR: Upload folder not found at {app.config['UPLOAD_FOLDER']}")
        return "Upload folder not found", 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
