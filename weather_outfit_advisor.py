#!/usr/bin/env python3
"""
Weather Forecast + Clothing Advice Display App
天気予報＋服装提案掲示板アプリ

This application fetches weather data from OpenWeatherMap API,
generates clothing advice using OpenAI API, and displays the
information on an LCD1602 display with horizontal scrolling.
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import openai
    from dotenv import load_dotenv
    from RPLCD.i2c import CharLCD
    import smbus2
except ImportError as e:
    print(f"Required library not installed: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weather_outfit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WeatherOutfitAdvisor:
    def __init__(self):
        """Initialize the Weather Outfit Advisor"""
        self.weather_api_key = os.getenv('WEATHER_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.city_name = os.getenv('CITY_NAME', 'Tokyo')

        if not self.weather_api_key:
            raise ValueError("WEATHER_API_KEY not found in environment variables")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # Initialize OpenAI client
        openai.api_key = self.openai_api_key

        # Initialize LCD (I2C address 0x27 is common for LCD1602)
        try:
            self.lcd = CharLCD('PCF8574', 0x27)
            self.lcd.clear()
            logger.info("LCD initialized successfully")
        except Exception as e:
            logger.warning(f"LCD initialization failed: {e}")
            self.lcd = None

    def get_weather_data(self) -> Optional[Dict[str, Any]]:
        """Fetch weather data from OpenWeatherMap API"""
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': self.city_name,
            'appid': self.weather_api_key,
            'units': 'metric',
            'lang': 'ja'
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch weather data: {e}")
            return None

    def generate_outfit_advice(self, weather_data: Dict[str, Any]) -> str:
        """Generate outfit advice using OpenAI API"""
        if not weather_data:
            return "天気情報を取得できませんでした。"

        temperature = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        weather_desc = weather_data['weather'][0]['description']

        prompt = f"""
今日の天気情報：
- 気温: {temperature}°C
- 体感温度: {feels_like}°C
- 湿度: {humidity}%
- 天気: {weather_desc}

上記の天気情報を基に、今日の服装アドバイスを日本語で簡潔に(50文字以内で)提案してください。
例：「薄手のジャケットがおすすめです」「傘を忘れずに」など
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは天気に基づいた服装アドバイザーです。簡潔で実用的なアドバイスを提供してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )

            advice = response.choices[0].message.content.strip()
            logger.info(f"Generated outfit advice: {advice}")
            return advice

        except Exception as e:
            logger.error(f"Failed to generate outfit advice: {e}")
            return "服装アドバイスを生成できませんでした。"

    def format_display_text(self, weather_data: Dict[str, Any], outfit_advice: str) -> str:
        """Format weather and outfit information for display"""
        if not weather_data:
            return "天気情報取得失敗"

        temperature = weather_data['main']['temp']
        weather_desc = weather_data['weather'][0]['description']
        city = weather_data['name']

        # Format the display text
        display_text = f"{city}: {temperature}°C {weather_desc} | {outfit_advice}"
        return display_text

    def display_scrolling_text(self, text: str, scroll_delay: float = 0.3):
        """Display scrolling text on LCD1602"""
        if not self.lcd:
            logger.info(f"LCD not available. Text would display: {text}")
            return

        # LCD1602 is 16 characters wide, 2 lines
        lcd_width = 16

        if len(text) <= lcd_width:
            # Text fits on one line
            self.lcd.clear()
            self.lcd.write_string(text.center(lcd_width))
            return

        # Add spaces for smooth scrolling
        scroll_text = f"    {text}    "

        try:
            for i in range(len(scroll_text) - lcd_width + 1):
                self.lcd.clear()
                display_segment = scroll_text[i:i + lcd_width]
                self.lcd.write_string(display_segment)
                time.sleep(scroll_delay)

        except KeyboardInterrupt:
            logger.info("Scrolling interrupted by user")
        except Exception as e:
            logger.error(f"LCD display error: {e}")

    def run(self, display_duration: int = 60):
        """Main execution function"""
        logger.info("Starting Weather Outfit Advisor")

        # Get weather data
        logger.info("Fetching weather data...")
        weather_data = self.get_weather_data()

        if not weather_data:
            error_msg = "天気データ取得失敗"
            if self.lcd:
                self.lcd.clear()
                self.lcd.write_string(error_msg)
            logger.error("Failed to get weather data")
            return

        # Generate outfit advice
        logger.info("Generating outfit advice...")
        outfit_advice = self.generate_outfit_advice(weather_data)

        # Format display text
        display_text = self.format_display_text(weather_data, outfit_advice)
        logger.info(f"Display text: {display_text}")

        # Display on LCD with scrolling
        start_time = time.time()
        while time.time() - start_time < display_duration:
            self.display_scrolling_text(display_text)
            time.sleep(1)  # Brief pause between scroll cycles

        if self.lcd:
            self.lcd.clear()

        logger.info("Weather Outfit Advisor completed")

def main():
    """Main entry point"""
    try:
        advisor = WeatherOutfitAdvisor()
        advisor.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()