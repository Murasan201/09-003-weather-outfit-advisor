#!/usr/bin/env python3
"""
天気予報＋服装提案掲示板アプリ（MVP版）
天気情報を取得し、AIで服装アドバイスを生成してOLEDにスクロール表示
"""

import os
import sys
import requests
import openai
from dotenv import load_dotenv
from scroll_oled import OLEDScroller

# === 設定定数 ===
FONT_PATH = "./assets/fonts/NotoSansCJKjp-Regular.otf"
FONT_SIZE = 14
OLED_WIDTH = 128
OLED_HEIGHT = 64
I2C_ADDRESS = 0x3C
SCROLL_SPEED = 2
FRAME_DELAY = 0.05

load_dotenv()


class WeatherOutfitAdvisor:
    """天気予報と服装アドバイスをOLED表示するクラス"""

    def __init__(self):
        """APIキー取得とOLED初期化"""
        self.weather_api_key = os.getenv('WEATHER_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.city_name = os.getenv('CITY_NAME', 'Tokyo')

        if not self.weather_api_key or not self.openai_api_key:
            print("[エラー] APIキーが設定されていません")
            print("ヒント: .envファイルにWEATHER_API_KEYとOPENAI_API_KEYを設定")
            sys.exit(1)

        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)

        try:
            self.scroller = OLEDScroller(
                font_path=FONT_PATH,
                font_size=FONT_SIZE,
                width=OLED_WIDTH,
                height=OLED_HEIGHT,
                address=I2C_ADDRESS
            )
        except Exception as e:
            print(f"[OLED初期化エラー] {e}")
            self.scroller = None

    def get_weather_data(self):
        """OpenWeatherMap APIから天気データを取得"""
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': self.city_name,
            'appid': self.weather_api_key,
            'units': 'metric',
            'lang': 'ja'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[天気取得エラー] {e}")
            return None

    def generate_outfit_advice(self, weather_data):
        """OpenAI APIで服装アドバイスを生成"""
        if not weather_data:
            return "天気情報を取得できませんでした。"

        temp = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        desc = weather_data['weather'][0]['description']

        prompt = f"""今日の天気: 気温{temp}°C, 体感{feels_like}°C, 湿度{humidity}%, {desc}
この天気に合う服装を50文字以内で提案してください。"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "服装アドバイザーです。簡潔に回答してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[AI生成エラー] {e}")
            return "服装アドバイスを生成できませんでした。"

    def run(self, loop_count=3):
        """メイン処理: 天気取得→アドバイス生成→OLED表示"""
        # 天気データ取得
        weather_data = self.get_weather_data()
        if not weather_data:
            if self.scroller:
                self.scroller.scroll("天気データ取得失敗", loops=1)
                self.scroller.clear()
            return

        # 服装アドバイス生成
        advice = self.generate_outfit_advice(weather_data)

        # 表示テキスト作成
        temp = weather_data['main']['temp']
        desc = weather_data['weather'][0]['description']
        city = weather_data['name']
        text = f"{city}: {temp}°C {desc} | {advice}"

        # OLED表示
        if self.scroller:
            self.scroller.scroll(text, speed=SCROLL_SPEED, delay=FRAME_DELAY, loops=loop_count)
            self.scroller.clear()
        else:
            print(f"[表示テキスト] {text}")


def main():
    """エントリーポイント"""
    try:
        advisor = WeatherOutfitAdvisor()
        advisor.run()
    except Exception as e:
        print(f"[エラー] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
