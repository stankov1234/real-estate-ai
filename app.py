# Import necessary libraries
import os
import json
import base64
from io import BytesIO # To handle image data in memory

from flask import Flask, request, jsonify, render_template, send_from_directory
import openai
from werkzeug.utils import secure_filename

# Initialize the Flask application
app = Flask(__name__, template_folder='templates', static_folder='static')

# Define the folder for uploading images (for serving existing ones, though new uploads go to AI directly)
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
    # Data now includes text fields AND base64 image strings
    data = request.json
    
    # Extract text fields
    form_data = {
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
        'broker_phone': data.get('broker_phone', 'неуточнен телефон') # New field
    }

    # Extract base64 image data
    image_data_base64 = data.get('images', [])
    # For this version, images are sent directly to AI, not saved on server in /uploads
    # We will just pass the base64 URLs to the AI.
    # Frontend handles previewing uploaded images.

    generated_ad = "Възникна грешка при генерирането на обявата."
    error_message = None

    try:
        if client is None:
            raise ValueError("OpenAI клиентът не е инициализиран. API ключът може да липсва или да е невалиден.")

        print("DEBUG: OpenAI client is ready for vision model.")

        # Construct multimodal messages for GPT-4o
        messages_content = [
            {"type": "text", "text": f"""
Ти си експерт по имотни обяви и маркетинг за недвижими и имоти. Твоята задача е да създадеш уникална, убедителна и емоционално въздействаща обява за продажба на имот, съобразена с Facebook Marketplace.

**СТРИКТНО СЕ ПРИДЪРЖАЙ САМО КЪМ ФАКТИЧЕСКИ ДАННИ, ПРЕДОСТАВЕНИ В ТЕКСТА ИЛИ ВИЗУАЛНО ОТКРИТИ В ИЗОБРАЖЕНИЯТА. НЕ ИЗМИСЛЯЙ НИКАКВИ ДОПЪЛНИТЕЛНИ ХАРАКТЕРИСТИКИ ИЛИ ПРЕДИМСТВА.**

Анализирай внимателно предоставените изображения за ключови визуални предимства (напр. луксозен интериор, панорамна гледка, модерни уреди, простор, уют, състояние на стаите, обзавеждане) и ги интегрирай в обявата.

Данни за имота:
📌 Локация: {form_data['location']}
💰 Цена: {form_data['price']} €
📐 Площ: {form_data['area']} кв.м
🏢 Етаж: {form_data['floor']}
🏗️ Година на строеж: {form_data['year_built']}
💳 Месечна вноска: {form_data['installment']} €
🛋️ Обзавеждане: {form_data['furnishing']}
🌄 Панорама: {form_data['panorama']}
🛗 Асансьор: {form_data['elevator']}
🚗 Гараж: {form_data['garage']}
💼 Ексклузивност: {form_data['exclusive']}
🏦 Финансиране: {form_data['financing']}
🖼️ Уникални предимства (допълнителен текст от брокер): {form_data['unique_features']}

Обявата трябва да включва:
1.  **Заглавие:** Започни точно с "💥 Купи за {form_data['installment']} €/месец – " и след това добави най-силните 2-3 предимства, които си открил както от текстовите данни, така и от предоставените изображения (напр. "обзаведен", "с панорама", "готов за нанасяне", "модерна кухня").
2.  **Основен текст:**
    * Встъпителен абзац, който грабва вниманието и представя ключови ползи.
    * **Ясно и емоционално описание на възможностите за финансиране (СТРОГО ТОЗИ ТЕКСТ):**
        "✨ Този имот може да бъде закупен на разсрочено плащане чрез Банков Ипотечен Кредит с месечна вноска от {form_data['installment']} €.\n🔓Без начален капитал, без доказани доходи или с влошена кредитна история – ние съдействаме за успешно банково финансиране.\n📌 Финансирането не е пречка – то е част от решението."
    * Подробности за разпределение, характеристики и предимства на имота, базирани на данните и снимките.
    * Информация за локацията и предимствата на квартала.
    * Раздел "Защо с 360ESTATE?" с акцент върху професионална подкрепа, сигурност и улеснение.
    * **Призив за действие (СТРОГО ТОЗИ ТЕКСТ):**
        "📞 За оглед: {form_data['broker_name']} – {form_data['broker_phone']}"
3.  **Формат:** Използвай емотикони, нови редове и кратки параграфи за лесна четимост.
            """}
        ]

        # Add image URLs to the messages_content if available
        for img_b64 in image_data_base64:
            messages_content.append({"type": "image_url", "image_url": {"url": img_b64}})

        response = client.chat.completions.create(
            model="gpt-4o", # Using GPT-4o for multimodal capabilities
            messages=[{"role": "user", "content": messages_content}],
            temperature=0.8,
            max_tokens=1200
        )
        generated_ad = response.choices[0].message.content.strip()
        print(f"DEBUG: OpenAI Response received. Generated ad length: {len(generated_ad)}")

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

    print(f"DEBUG: Returning JSON response.")
    # Return the generated ad text. image_urls are handled by frontend preview.
    return jsonify({
        'generated_ad': generated_ad,
        'image_urls': [] # No longer saving/serving from server in this flow, frontend previews
    })

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    print(f"DEBUG: Serving static file: {filename} from {app.config['UPLOAD_FOLDER']}")
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        print(f"DEBUG ERROR: Upload folder not found at {app.config['UPLOAD_FOLDER']}")
        return "Upload folder not found", 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)

