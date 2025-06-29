from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import openai

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.form

    # Запазване на снимките
    image_files = request.files.getlist('images')
    image_urls = []
    for image in image_files:
        if image:
            filename = secure_filename(image.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(path)
            image_urls.append(f'/static/uploads/{filename}')

    # Сглобяване на вход за AI
    prompt = f"""
    Създай убедителна, емоционално въздействаща и професионална обява за продажба на имот по следните данни:
    - Локация: {data.get('location')}
    - Цена: {data.get('price')} €
    - Площ: {data.get('area')} кв.м
    - Етаж: {data.get('floor')}
    - Година на строеж: {data.get('year_built')}
    - Месечна вноска: {data.get('installment')} € чрез банков кредит
    - Обзавеждане: {data.get('furnishing')}
    - Панорама: {data.get('panorama')}
    - Асансьор: {data.get('elevator')}
    - Гараж: {data.get('garage')}
    - Ексклузивност: {data.get('exclusive')}
    - Финансиране: {data.get('financing')}
    - Уникални предимства: {data.get('unique_features')}

    Обявата трябва да включва:
    1. Заглавие (в стила на "Купи за 580 €/месец – Напълно обзаведен, с панорама")
    2. Встъпителен абзац с кратко описание и ключовите предимства
    3. Подробности за апартамента
    4. Финансиране: включително фразата:
       "✨ Този имот може да бъде закупен на разсрочено плащане чрез Банков Ипотечен Кредит с месечна вноска от {data.get('installment')} €.\n🔓Без начален капитал, без доказани доходи или с влошена кредитна история – ние съдействаме за успешно банково финансиране.\n📌 Финансирането не е пречка – то е част от решението."
    5. Призив за действие с телефон за връзка: 0896 804 359
    6. Ясен, подреден и четим формат
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ти си експерт по имотни обяви."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1200
        )

        generated_ad = response.choices[0].message.content.strip()

    except Exception as e:
        return jsonify({"error": f"AI грешка: {str(e)}"}), 500

    return jsonify({
        'generated_ad': generated_ad,
        'image_urls': image_urls
    })

if __name__ == '__main__':
    app.run(debug=True)

