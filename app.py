# Import necessary libraries
from flask import Flask, request, jsonify, render_template, send_from_directory
import openai
import os
from werkzeug.utils import secure_filename # For safe handling of filenames
import json # To handle JSON responses if needed for structured data

# Initialize the Flask application
# Use template_folder to explicitly specify where HTML templates are located
app = Flask(__name__, template_folder='templates', static_folder='static')

# Define the folder for uploading images
# It's crucial this directory exists and is tracked by Git
UPLOAD_FOLDER = 'static/uploads'
# Ensure the upload folder exists. This is important for local development.
# For Render, ensure 'static/uploads' is committed to your GitHub repo (e.g., with a .gitkeep file inside).
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure OpenAI API key from environment variables for security
# Make sure to set OPENAI_API_KEY in your Render environment settings
# New way to initialize OpenAI client for openai>=1.0.0
# The API key is automatically picked up from OPENAI_API_KEY environment variable
try:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    print("DEBUG: OpenAI client initialized successfully.")
except Exception as e:
    print(f"DEBUG ERROR: Failed to initialize OpenAI client: {e}")
    client = None # Set client to None if initialization fails


# Define the application password for authentication
# In a real-world scenario, consider more secure password management (e.g., hashing, database)
APP_PASSWORD = "360estate" # The password for your team

# --- Routes for the application ---

@app.route('/')
def index():
    """
    Renders the login page when the root URL is accessed.
    This is the first page users will see to enter the password.
    """
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """
    Handles the login form submission.
    Checks if the entered password matches the APP_PASSWORD.
    """
    password = request.form.get("password")
    if password == APP_PASSWORD:
        # If password is correct, render the main form for generating ads
        return render_template('form.html')
    else:
        # If password is incorrect, re-render the login page with an error message
        return render_template('login.html', error=True)

@app.route('/generate', methods=['POST'])
def generate_ad():
    """
    Handles the ad generation form submission.
    - Saves uploaded images to the UPLOAD_FOLDER.
    - Constructs a detailed prompt for the AI based on form data.
    - Calls OpenAI API (GPT-4) to generate the ad text.
    - Returns the generated ad text and image URLs as a JSON response.
    """
    print("DEBUG: generate_ad route hit!") # Debug print

    # Extract form data
    data = request.form

    # Save uploaded images
    image_files = request.files.getlist('images')
    image_urls = []
    for image in image_files:
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                print(f"DEBUG: Attempting to save image to {path}") # Debug print
                image.save(path)
                # Store the URL relative to the static folder for display
                image_urls.append(f'/static/uploads/{filename}')
                print(f"DEBUG: Image saved: {filename}") # Debug print
            except Exception as e:
                print(f"DEBUG ERROR: Failed to save image {filename}: {e}")
                # Optionally, you might want to return an error or skip this image
                pass # Continue processing even if one image fails to save

    # Construct the detailed prompt for the AI based on the provided data
    # This prompt incorporates all the refined phrases and structures we discussed
    prompt = f"""
Създай уникална, убедителна и емоционално въздействаща обява за продажба на имот, съобразена с Facebook Marketplace. Използвай емотикони, кратки параграфи и изразителен стил.

Данни за имота:
📌 Локация: {data.get('location', 'неуточнена')}
💰 Цена: {data.get('price', 'неуточнена')} €
📐 Площ: {data.get('area', 'неуточнена')} кв.м
🏢 Етаж: {data.get('floor', 'неуточнен')}
🏗️ Година на строеж: {data.get('year_built', 'неуточнена')}
💳 Месечна вноска: {data.get('installment', 'неуточнена')} €
🛋️ Обзавеждане: {data.get('furnishing', 'неуточнено')}
🌄 Панорама: {data.get('panorama', 'неуточнена')}
🛗 Асансьор: {data.get('elevator', 'неуточнен')}
🚗 Гараж: {data.get('garage', 'неуточнен')}
💼 Ексклузивност: {data.get('exclusive', 'неуточнена')}
🏦 Финансиране: {data.get('financing', 'неуточнено')}
🖼️ Уникални предимства: {data.get('unique_features', 'неуточнени')}

Обявата трябва да включва:
1.  **Заглавие:** Кратко, ударно и подканващо (напр. "💥 Купи за {data.get('installment')} €/месец – {data.get('furnishing', 'обзаведен')}, {data.get('panorama', 'с панорама')}").
2.  **Основен текст:**
    * Встъпителен абзац, който грабва вниманието и представя ключови ползи.
    * Ясно и емоционално описание на възможностите за финансиране:
        "✨ Този имот може да бъде закупен на разсрочено плащане чрез Банков Ипотечен Кредит с месечна вноска от {data.get('installment', 'ХХХ')} €."
        "🔓 Без начален капитал, без доказани доходи или с влошена кредитна история – ние съдействаме за успешно банково финансиране."
        "📌 Финансирането не е пречка – то е част от решението."
    * Подробности за разпределение, характеристики и предимства на имота.
    * Информация за локацията и предимствата на квартала.
    * Раздел "Защо с 360ESTATE?" с акцент върху професионална подкрепа, сигурност и улеснение.
    * Призив за действие с телефон за връзка: 0896 804 359 и опция за лично съобщение.
3.  **Формат:** Използвай емотикони, нови редове и кратки параграфи за лесна четимост.
"""

    generated_ad = "Възникна грешка при генерирането на обявата."
    error_message = None

    try:
        # Check if OpenAI client is initialized
        if client is None:
            raise ValueError("OpenAI клиентът не е инициализиран. API ключът може да липсва или да е невалиден.")

        print(f"DEBUG: OpenAI client is ready.") # Debug print

        # Call OpenAI Chat Completion API using the new syntax (client.chat.completions.create)
        response = client.chat.completions.create( # CORRECTED LINE
            model="gpt-4", # Using GPT-4 as requested
            messages=[
                {"role": "system", "content": "Ти си експерт по имотни обяви и маркетинг за недвижими имоти."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8, # Controls creativity (0.8 is a good balance)
            max_tokens=1200 # Max length of the generated response
        )
        generated_ad = response.choices[0].message.content.strip() # Access content correctly
        print(f"DEBUG: OpenAI Response received. Generated ad length: {len(generated_ad)}") # Debug print

    # Catch specific OpenAI API errors using the correct exception class for newer versions
    except openai.APIError as e: # This should now correctly catch API errors
        error_message = f"AI грешка: Проблем с OpenAI API: {str(e)}. Моля, проверете API ключа и лимитите си."
        print(f"DEBUG ERROR: OpenAI API Error: {error_message}") # Log error for debugging
        return jsonify({"error": error_message}), 500
    except ValueError as e:
        error_message = f"Конфигурационна грешка: {str(e)}"
        print(f"DEBUG ERROR: ValueError: {error_message}") # Log error
        return jsonify({"error": error_message}), 500
    except Exception as e: # Catch any other unexpected errors
        error_message = f"Неочаквана грешка: {str(e)}"
        print(f"DEBUG ERROR: Generic Exception in generate_ad: {error_message}") # Log any other unexpected errors
        return jsonify({"error": error_message}), 500

    print(f"DEBUG: Returning JSON response. Image URLs count: {len(image_urls)}") # Debug print
    # Return the generated ad text and image URLs as JSON
    return jsonify({
        'generated_ad': generated_ad,
        'image_urls': image_urls
    })

def allowed_file(filename):
    """
    Helper function to validate allowed file extensions for uploads.
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Serve static files (images)
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    """
    Route to serve uploaded images.
    """
    print(f"DEBUG: Serving static file: {filename} from {app.config['UPLOAD_FOLDER']}") # Debug print
    # It's good practice to ensure the directory exists before serving to prevent errors
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        print(f"DEBUG ERROR: Upload folder not found at {app.config['UPLOAD_FOLDER']}")
        return "Upload folder not found", 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Main entry point for the Flask application
# When running locally, this will start the development server
# For production (Render), Gunicorn will handle this part,
# but it's good practice to keep it for local testing.
if __name__ == '__main__':
    app.run(debug=True) # debug=True allows for automatic reloading and error messages
