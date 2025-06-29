# Import necessary libraries
import os
import json
import base64
from io import BytesIO # To handle image data in memory

from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
import openai
from werkzeug.utils import secure_filename

# Import ReportLab for PDF generation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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

**СТРИКТНО СЕ ПРИДЪРЖАЙ САМО КЪМ ФАКТИЧЕСКИ ДАННИ, ПРЕДОСТАВЕНИ В ТЕКСТА ИЛИ ВИЗУАЛНО ОТКРИТИ В ИЗОБРАЖЕНИЯТА. НЕ ИЗМИСЛЯЙ НИКАКВИ ДОПЪЛНИТЕЛНИ ХАРАКТЕРИСТИКИ ИЛИ ПРЕДИМСТВА.**

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

--- КРАТКА ВЕРСИЯ ---

1.  **Заглавие (СТРОГО ТОЗИ ФОРМАТ):** "💥 Купи за {form_data['installment']} €/месец – [2-3 най-силни, ключови предимства, извлечени от данните и снимките, релевантни за {form_data['property_type']}]"
2.  **Основен текст (МНОГО КРАТЪК - 3-5 реда макс, без измислици):**
    * Кратък, емоционален встъпителен ред.
    * Кратко описание на имота, с акцент върху 2-3 най-важни характеристики за {form_data['property_type']}, открити от снимките и данните.
    * **Финансов блок (СТРОГО ТОЗИ ТЕКСТ):**
        "✨ Този имот може да бъде закупен на разсрочено плащане чрез Банков Ипотечен Кредит с месечна вноска от {form_data['installment']} €.\n🔓Без начален капитал, без доказани доходи или с влошена кредитна история – ние съдействаме за успешно банково финансиране.\n📌 Финансирането не е пречка – то е част от решението."
    * **Призив за действие (СТРОГО ТОЗИ ТЕКСТ):** "📞 За оглед: {form_data['broker_name']} – {form_data['broker_phone']}"

--- ДЪЛГА ВЕРСИЯ ---

1.  **Заглавие (СТРОГО ТОЗИ ФОРМАТ):** "💥 Купи за {form_data['installment']} €/месец – [2-3 най-силни, ключови предимства, извлечени от данните и снимките, релевантни за {form_data['property_type']}]"
2.  **Основен текст (ПОДРОБЕН - 10-15+ реда, без измислици):**
    * Емоционален встъпителен абзац, представящ най-големите ползи.
    * Подробно описание на {form_data['property_type']}, неговото разпределение, състояние, характеристики и предимства, извлечени от снимките и данните.
    * Информация за локацията и предимствата на квартала/района, специфични за {form_data['property_type']}.
    * Раздел "Защо с 360ESTATE?" с акцент върху професионална подкрепа, сигурност и улеснение.
    * Раздел "Идеален избор за:" (с 2-3 подходящи групи).
    * **Финансов блок (СТРОГО ТОЗИ ТЕКСТ):**
        "✨ Този имот може да бъде закупен на разсрочено плащане чрез Банков Ипотечен Кредит с месечна вноска от {form_data['installment']} €.\n🔓Без начален капитал, без доказани доходи или с влошена кредитна история – ние съдействаме за успешно банково финансиране.\n📌 Финансирането не е пречка – то е част от решението."
    * **Призив за действие (СТРОГО ТОЗИ ТЕКСТ):** "📞 За оглед: {form_data['broker_name']} – {form_data['broker_phone']}"
3.  **Хаштагове:** Генерирай подходящи хаштагове за {form_data['property_type']} и локацията.

Моля, раздели КРАТКАТА и ДЪЛГАТА обява с маркери "---КРАТКА ОБЯВА START---" и "---ДЪЛГА ОБЯВА START---" и ги завърши с "---КРАЙ ОБЯВА---"
"""
        messages_content = [{"type": "text", "text": base_text_prompt}]

        # Add image URLs to the messages_content if available
        for img_b64 in image_data_base64:
            messages_content.append({"type": "image_url", "image_url": {"url": img_b64}})

        response = client.chat.completions.create(
            model="gpt-4o", # Using GPT-4o for multimodal capabilities
            messages=[{"role": "user", "content": messages_content}],
            temperature=0.8,
            max_tokens=2000 # Increased max_tokens to accommodate two ad versions
        )
        full_generated_text = response.choices[0].message.content.strip()
        print(f"DEBUG: OpenAI Response received. Full text length: {len(full_generated_text)}")

        # Parse the full generated text into short and long versions
        short_ad_start_marker = "---КРАТКА ОБЯВА START---"
        long_ad_start_marker = "---ДЪЛГА ОБЯВА START---"
        end_ad_marker = "---КРАЙ ОБЯВА---"

        short_ad = "Неуспешно генериране на кратка обява."
        long_ad = "Неуспешно генериране на дълга обява."

        if short_ad_start_marker in full_generated_text and long_ad_start_marker in full_generated_text:
            short_start_index = full_generated_text.find(short_ad_start_marker) + len(short_ad_start_marker)
            long_start_index = full_generated_text.find(long_ad_start_marker) + len(long_ad_start_marker)

            short_ad_temp = full_generated_text[short_start_index:long_start_index].strip()
            long_ad_temp = full_generated_text[long_start_index:].strip()

            if end_ad_marker in short_ad_temp:
                short_ad = short_ad_temp[:short_ad_temp.find(end_ad_marker)].strip()
            else:
                short_ad = short_ad_temp.strip() # If end marker missing, take until long version start

            if end_ad_marker in long_ad_temp:
                long_ad = long_ad_temp[:long_ad_temp.find(end_ad_marker)].strip()
            else:
                long_ad = long_ad_temp.strip() # If end marker missing, take till end of text
        else:
            # Fallback if markers are not found, return full text as long ad and a generic short ad
            long_ad = full_generated_text
            short_ad = "Кратка версия не може да бъде извлечена. Моля, вижте дългата обява."


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
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom style for title and body
    styles.add(ParagraphStyle(name='AdTitle', parent=styles['h1'], fontSize=16, leading=18, alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name='AdBody', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=6, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='ImageCaption', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, spaceAfter=6))

    story = []

    story.append(Paragraph("<b><font size=16>Генерирана Обява от 360ESTATE</font></b>", styles['AdTitle']))
    story.append(Spacer(1, 0.2 * inch))

    # Add ad text
    for line in ad_text.split('\n'):
        if line.strip(): # Add non-empty lines as paragraphs
            story.append(Paragraph(line.replace('💥', '<b>💥</b>').replace('✨', '<b>✨</b>').replace('🔓', '<b>🔓</b>').replace('📌', '<b>📌</b>').replace('📞', '<b>📞</b>'), styles['AdBody']))
        else: # For empty lines, add a small spacer
            story.append(Spacer(1, 0.1 * inch))

    story.append(Spacer(1, 0.4 * inch))

    # Add images
    if images_b64:
        story.append(Paragraph("<b><font size=12>Прикачени изображения:</font></b>", styles['h2']))
        story.append(Spacer(1, 0.2 * inch))
        for i, img_b64 in enumerate(images_b64):
            try:
                # Remove data:image/png;base64, or similar prefix
                header, base64_string = img_b64.split(',', 1)
                img_data = base64.b64decode(base64_string)
                img = Image(BytesIO(img_data))
                
                # Scale image to fit page width, maintaining aspect ratio
                # Assuming A4 width (595 points) and some margins (e.g., 50 points per side)
                # Image width should be max 495 points (A4 width - 2*50 margins)
                img_width = img.drawWidth
                img_height = img.drawHeight
                
                max_img_width = A4[0] - 2 * inch # A4 width minus 2 inches margin
                
                if img_width > max_img_width:
                    scale_factor = max_img_width / img_width
                    img_width = max_img_width
                    img_height = img_height * scale_factor
                
                # If after scaling width, height is too big, scale based on height (e.g., max 4 inches)
                max_img_height = 4 * inch
                if img_height > max_img_height:
                    scale_factor = max_img_height / img_height
                    img_width = img_width * scale_factor
                    img_height = max_img_height

                img.drawWidth = img_width
                img.drawHeight = img_height
                
                story.append(img)
                story.append(Paragraph(f"<i>Снимка {i+1}</i>", styles['ImageCaption']))
                story.append(Spacer(1, 0.1 * inch))
            except Exception as e:
                print(f"DEBUG ERROR: Failed to embed image {i+1} in PDF: {e}")
                story.append(Paragraph(f"<i>Неуспешно зареждане на снимка {i+1}</i>", styles['ImageCaption']))
                story.append(Spacer(1, 0.1 * inch))

    try:
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
