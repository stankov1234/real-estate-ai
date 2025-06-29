
from flask import Flask, request, jsonify, render_template
import openai
import os

app = Flask(__name__, template_folder='templates')

openai.api_key = os.getenv("OPENAI_API_KEY")
APP_PASSWORD = "360estate"

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
    data = request.json
    prompt = f"""
Създай ефективна и емоционално въздействаща обява за продажба на имот във Facebook Marketplace, като използваш следните данни:

📌 Заглавие: {data.get('title')}
📍 Локация: {data.get('location')}
💰 Цена: {data.get('price')} €
📐 Площ: {data.get('area')} кв.м
🏢 Етаж: {data.get('floor')}
🏗️ Година на строеж: {data.get('year_built')}
💳 Вноска: {data.get('installment')} €/месец
🛋️ Обзавеждане: {data.get('furnishing')}
🌄 Панорама: {data.get('panorama')}
🛗 Асансьор: {data.get('elevator')}
🚗 Гараж: {data.get('garage')}
💼 Ексклузивност: {data.get('exclusive')}
🏦 Финансиране: {data.get('financing')}
🖼️ Уникални предимства: {data.get('unique_features')}

Използвай емотикони, кратки параграфи и изразителен стил.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Ти си експерт по имотен маркетинг."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.9
    )

    ad_text = response.choices[0].message['content'].strip()
    return jsonify({"generated_ad": ad_text})

if __name__ == '__main__':
    app.run(debug=True)
