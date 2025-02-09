# SECTION LFCA322A012 
"Real-Time Weather Application with Visual, Timezone, and Currency Conversion Integration"

import sys
import cv2
import os
import requests
from pytz import timezone
from datetime import datetime
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton


def get_weather(city): 
    API_key = "65cc8af054302dac7a0dc5ce7b0819f2"  
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_key}"
    res = requests.get(url)

    if res.status_code == 404:
        return None

    weather = res.json()
    timezone_offset = weather['timezone'] if 'timezone' in weather else 0
    icon_id = weather['weather'][0]['icon']
    temperature = weather['main']['temp'] - 273.15  # Convert Kelvin to Celsius
    description = weather['weather'][0]['description']
    city = weather['name']
    country = weather['sys']['country']

    icon_url = f"https://openweathermap.org/img/wn/{icon_id}@2x.png"
    return icon_url, temperature, description, city, country, timezone_offset


def get_currency_exchange_rate(base_currency, target_currency):
    api_key = "da3f0ec46ed6653a3ca735ad"  # REPLACE "YOUR_API_KEY" with your ExchangeRate API key
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()
    if "conversion_rates" in data:
        return data["conversion_rates"].get(target_currency)

    return None


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather Application (LFCA322M010)")
        self.resize(800, 600)

        # Default timezone
        self.city_timezone = timezone("UTC")

        # Video setup
        script_dir = os.path.dirname(os.path.abspath(__file__))
        video_folder = os.path.join(script_dir, "VIDEOS")

        self.video_paths = {
            "rainy": os.path.join(video_folder, "rainy.mp4"),
            "cloudy": os.path.join(video_folder, "cloudy.mp4"),
            "clear": os.path.join(video_folder, "clear.mp4"),
            "default": os.path.join(video_folder, "default2.mp4"),
            "light_rain": os.path.join(video_folder, "light_rain.mp4"),
            "snow": os.path.join(video_folder, "snow.mp4"),
            "mist": os.path.join(video_folder, "mist.mp4"),
            "fog": os.path.join(video_folder, "fog.mp4"),
        }

        self.cap = cv2.VideoCapture(self.video_paths["default"])
        self.video_label = QLabel(self)
        self.video_label.setGeometry(0, 0, self.width(), self.height())
        self.video_label.setScaledContents(True)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(60)

        # Layout and UI components
        self.layout = QVBoxLayout()

        self.title_label = QLabel("Christian WeatherWeather Lang")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(""" 
            font-size: 28px;
            font-weight: bold;
            color: white;
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
        """)
        self.layout.addWidget(self.title_label)

        self.city_entry = QLineEdit()
        self.city_entry.setPlaceholderText("Enter City Name")
        self.city_entry.setStyleSheet(""" 
            font-size: 18px;
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid gray;
            border-radius: 10px;
        """)
        self.layout.addWidget(self.city_entry)

        self.search_button = QPushButton("Search")
        self.search_button.setStyleSheet(""" 
            font-size: 18px;
            padding: 10px;
            background-color: rgb(135, 206, 235);
            color: white;
            border-radius: 10px;
        """)
        self.search_button.clicked.connect(self.search_weather)
        self.layout.addWidget(self.search_button)

        self.location_label = QLabel()
        self.location_label.setAlignment(Qt.AlignCenter)
        self.location_label.setStyleSheet(""" 
            font-size: 25px;
            color: white;
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
        """)
        self.layout.addWidget(self.location_label)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.icon_label)

        self.temperature_label = QLabel()
        self.temperature_label.setAlignment(Qt.AlignCenter)
        self.temperature_label.setStyleSheet(""" 
            font-size: 20px;
            color: white;
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
        """)
        self.layout.addWidget(self.temperature_label)

        # Currency exchange rate label
        self.currency_label = QLabel()
        self.currency_label.setAlignment(Qt.AlignCenter)
        self.currency_label.setStyleSheet(""" 
            font-size: 20px;
            color: white;
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
        """)
        self.layout.addWidget(self.currency_label)

        # Create the middle part with two borders
        middle_layout = QHBoxLayout()

        self.description_label = QLabel()
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setStyleSheet(""" 
            font-size: 20px;
            color: white;
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            border-right: 1px solid white;
            padding-right: 10px;
        """)
        middle_layout.addWidget(self.description_label)

        self.time_bar = QLabel("Time: Loading...")
        self.time_bar.setAlignment(Qt.AlignCenter)
        self.time_bar.setStyleSheet(""" 
            font-size: 18px;
            color: white;
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            padding-left: 10px;
        """)
        middle_layout.addWidget(self.time_bar)

        self.layout.addLayout(middle_layout)

        self.setLayout(self.layout)

        # Start updating the time bar
        self.update_time_bar()

    def resizeEvent(self, event):
        """Update video label size when window is resized."""
        self.video_label.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def update_time_bar(self):
        """Update the time bar dynamically based on the selected city timezone."""
        if self.city_timezone:
            current_time = datetime.now(self.city_timezone)
            self.time_bar.setText(f"Date: {current_time.strftime('%Y-%m-%d')}\nTime: {current_time.strftime('%H:%M:%S')}")
        QTimer.singleShot(1000, self.update_time_bar)  # Refresh every second

    def search_weather(self):
        city = self.city_entry.text()
        result = get_weather(city)

        if result is None:
            self.location_label.setText("City not found")
            self.icon_label.clear()
            self.temperature_label.setText("")
            self.description_label.setText("")
            self.currency_label.setText("")  # Reset currency label
            self.set_video_background("default")
            self.city_timezone = timezone("UTC")  # Reset to UTC
            return

        icon_url, temperature, description, city, country, timezone_offset = result
        self.location_label.setText(f"{city}, {country}")

        # Set timezone using the offset
        self.city_timezone = timezone(f"Etc/GMT{'+' if timezone_offset < 0 else '-'}{abs(timezone_offset) // 3600}")

        # Convert the country's currency to PHP
        country_currency_map = {
    "AE": "AED", "AF": "AFN", "AG": "XCD", "AL": "ALL", "AM": "AMD",
    "AN": "ANG", "AO": "AOA", "AQ": "AQD", "AR": "ARS", "AU": "AUD",
    "AZ": "AZN", "BA": "BAM", "BB": "BBD", "BD": "BDT", "BE": "XOF",
    "BR": "BRL", "BG": "BGN", "CA": "CAD", "CH": "CHF", "CN": "CNY",
    "CO": "COP", "CR": "CRC", "CZ": "CZK", "DE": "EUR", "DK": "DKK",
    "EG": "EGP", "ES": "EUR", "FR": "EUR", "GB": "GBP", "GR": "EUR",
    "HK": "HKD", "HU": "HUF", "ID": "IDR", "IL": "ILS", "IN": "INR",
    "IT": "EUR", "JP": "JPY", "KR": "KRW", "LK": "LKR", "MY": "MYR",
    "MX": "MXN", "NG": "NGN", "NL": "EUR", "NO": "NOK", "NZ": "NZD",
    "PH": "PHP", "PK": "PKR", "PL": "PLN", "PT": "EUR", "RU": "RUB",
    "SA": "SAR", "SE": "SEK", "SG": "SGD", "TH": "THB", "TR": "TRY",
    "TW": "TWD", "US": "USD", "VN": "VND", "ZA": "ZAR", "ZW": "ZWD"
    }

        country_currency = country_currency_map.get(country, "USD")  # Default to USD if country is not found
        exchange_rate = get_currency_exchange_rate(country_currency, "PHP")

        if exchange_rate:
            self.currency_label.setText(f"1 {country_currency} = {exchange_rate:.2f} PHP")
        else:
            self.currency_label.setText("Currency rate not available")

        # Update other weather details
        image_response = requests.get(icon_url)
        if image_response.status_code == 200:
            pixmap = QPixmap()
            pixmap.loadFromData(image_response.content)
            self.icon_label.setPixmap(pixmap)

        self.temperature_label.setText(f"Temperature: {temperature:.2f}℃")
        self.description_label.setText(f"Description: {description}")

        self.set_video_background(description)

    def set_video_background(self, description):
        """Set the video background based on weather description."""
        if "light rain" in description.lower():
            video_path = self.video_paths["light_rain"]
        elif "rain" in description.lower():
            video_path = self.video_paths["rainy"]
        elif "cloud" in description.lower():
            video_path = self.video_paths["cloudy"]
        elif "clear" in description.lower():
            video_path = self.video_paths["clear"]
        elif "snow" in description.lower():
            video_path = self.video_paths["snow"]
        elif "mist" in description.lower():
            video_path = self.video_paths["mist"]
        elif "fog" in description.lower():
            video_path = self.video_paths["fog"]
        else:
            video_path = self.video_paths["default"]

        self.cap.release()
        self.cap = cv2.VideoCapture(video_path)

    def update_frame(self):
        """Update the video frame."""
        ret, frame = self.cap.read()
        if ret:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            qt_image = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qt_image))
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def closeEvent(self, event):
        """Release resources when the application closes."""
        self.cap.release()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec())
