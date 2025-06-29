# Import necessary libraries
import os
import json
import base64
from io import BytesIO 
import re 

from flask import Flask, request, jsonify, render_template, send_from_directory
import openai
from werkzeug.utils import secure_filename

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

    # Extract base64 image data (still used by AI for vision)
    image_data_base64 = data.get('images', [])

    generated_short_ad = "Възникна грешка при генерирането на кратката обява."
    generated_long_ad = "Възникна грешка при генерирането на дългата обява."
    error_message = None

    try:
        if client is None:
            raise ValueError("OpenAI клиентът не е инициализиран. API ключът може да липсва или да е невалиден.")

        print("DEBUG: OpenAI client is ready for vision model.")

        # Construct basic text prompt based on property type and all available data
        # This prompt is NOW STRUCTURED TO STRICTLY ADHERE TO THE USER'S DEFINED FORMAT.
        # It uses explicit markers and instructions for each section.
        base_text_prompt = f"""
Ти си експерт по имотни обяви и маркетинг за недвижими и имоти. Твоята задача е да създадеш ДВЕ ВЕРСИИ на обява за продажба на имот, съобразена с Facebook Marketplace. Всяка обява трябва да следва стриктно дефинираните секции и техния ред.

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

Заглавие: 
💥 Купи за {form_data['installment']} €/месец – [2-3 най-силни, ключови предимства, извлечени от данните и снимките, релевантни за {form_data['property_type']}]
Откриващ текст: 
🏡 [Кратко и ясно, едно вдъхновяващо изречение, което подчертава готовност за нанасяне или финансова достъпност. Веднага след това основните параметри на имота: {form_data['area']} кв.м | САМО {form_data['price']} € | {form_data['location']}]
Финансов блок: 
✨ Този имот може да бъде закупен на разсрочено плащане чрез Банков Ипотечен Кредит с месечна вноска от {form_data['installment']} €.\n🔓Без начален капитал, без доказани доходи или с влошена кредитна история – ние съдействаме за успешно банково финансиране.\n📌 Финансирането не е пречка – то е част от решението.
За оглед: 
📞 {form_data['broker_name']} – {form_data['broker_phone']}
---КРАТКА ОБЯВА END---

---ДЪЛГА ОБЯВА START---

Заглавие: 
💥 Купи за {form_data['installment']} €/месец – [2-3 най-силни, ключови предимства, извлечени от данните и снимките, релевантни за {form_data['property_type']}]
Откриващ текст: 
🏡 [Кратко и ясно, едно вдъхновяващо изречение, което подчертава готовност за нанасяне или финансова достъпност, преплетено с основните характеристики: цена {form_data['price']} €, местоположение {form_data['location']} и вид имот {form_data['property_type']}].
Финансов блок: 
✨ Този имот може да бъде закупен на разсрочено плащане чрез Банков Ипотечен Кредит с месечна вноска от {form_data['installment']} €.\n🔓Без начален капитал, без доказани доходи или с влошена кредитна история – ние съдействаме за успешно банково финансиране.\n📌 Финансирането не е пречка – то е част от решението.
Описание на имота:
[Подробно описание на {form_data['property_type']}, неговото разпределение, състояние, екстри и ключови подобрения. Започни тази секция с кратко резюме на основните параметри: 📐 Площ: {form_data['area']} кв.м | 💰 Цена: {form_data['price']} € | 📍 Локация: {form_data['location']} | 🛋️ Обзавеждане: {form_data['furnishing']} . AI ще интегрира и визуално откритите предимства от снимките.]
Предимства на Локацията:
[Текст, който подчертава удобствата и привлекателността на квартала/района, базиран на въведените данни (напр. близост до плаж, паркове, магазини, училища, транспорт, спокойствие).]
Допълнително:
[Включи всички други важни, но незадължителни характеристики, въведени от брокера (напр. включено мазе, тухлена сграда, етаж, опция за гараж).]
Защо с 360ESTATE?:
[Акцент върху професионална подкрепа, сигурност и улеснение.]
Идеален избор за:
[2-3 подходящи групи (напр. Младо семейство, Инвестиция с висока доходност).]
За оглед: 
📞 {form_data['broker_name']} – {form_data['broker_phone']}
Финален щрих: [Генерирай кратко, емоционално заключение, което да остави силно впечатление (напр. "Тук не просто купувате апартамент – купувате стил на живот.").]
Хаштагове: [Генерирай подходящи хаштагове за {form_data['property_type']} и локацията.]
---ДЪЛГА ОБЯВА END---
"""
        messages_content = [{"type": "text", "text": base_text_prompt}]

        # Add image URLs to the messages_content if available
        for img_b64 in image_data_base64:
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

# The /generate_pdf route and all its dependencies are removed.
# @app.route('/generate_pdf', methods=['POST'])
# def generate_pdf():
#    ... (removed code) ...

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
