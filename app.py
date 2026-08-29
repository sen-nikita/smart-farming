from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__, template_folder='templates')

WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/crop')
def crop():
    return render_template('pages/crop.html')

@app.route('/weather')
def weather():
    return render_template('pages/weather.html')

@app.route('/disease')
def disease():
    return render_template('pages/disease.html')

@app.route('/market')
def market():
    return render_template('pages/market.html')

@app.route('/login')
def login():
    return render_template('pages/login.html')

# ===== SERVICE WORKER & MANIFEST =====
@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

# ===== WEATHER API ROUTE =====
@app.route('/api/weather')
def get_weather():
    city = request.args.get('city', 'Delhi')
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city},IN&appid={WEATHER_API_KEY}&units=metric&cnt=40"

    try:
        response = requests.get(url)
        data = response.json()

        if data.get('cod') != '200':
            return jsonify({'error': 'City not found'}), 404

        current = data['list'][0]

        forecast = []
        seen_dates = []
        for item in data['list']:
            date = item['dt_txt'].split(' ')[0]
            if date not in seen_dates and len(forecast) < 5:
                seen_dates.append(date)
                forecast.append({
                    'date': date,
                    'temp': round(item['main']['temp']),
                    'desc': item['weather'][0]['description'].title(),
                    'rain': round(item.get('pop', 0) * 100)
                })

        result = {
            'city': data['city']['name'],
            'country': data['city']['country'],
            'temp': round(current['main']['temp']),
            'feels_like': round(current['main']['feels_like']),
            'desc': current['weather'][0]['description'].title(),
            'humidity': current['main']['humidity'],
            'wind': round(current['wind']['speed'] * 3.6),
            'rain': round(current.get('pop', 0) * 100),
            'forecast': forecast
        }
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
