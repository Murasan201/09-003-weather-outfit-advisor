#!/usr/bin/env python3
"""
Weather Forecast + Clothing Advice Display App
天気予報＋服装提案掲示板アプリ

This application fetches weather data from OpenWeatherMap API,
generates clothing advice using OpenAI API, and displays the
information on an SSD1306 OLED display with horizontal scrolling.
"""

# === 必要なライブラリのインポート ===
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
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    print(f"Required library not installed: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# === 環境変数の読み込み ===
load_dotenv()

# === ログ設定 ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weather_outfit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === メインクラス：天気予報＋服装提案アドバイザー ===
class WeatherOutfitAdvisor:
    def __init__(self):
        """クラスの初期化: APIキーの取得、OpenAI・OLEDの設定を行う"""
        # 環境変数からAPIキーと都市名を取得
        self.weather_api_key = os.getenv('WEATHER_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.city_name = os.getenv('CITY_NAME', 'Tokyo')

        # OLED display settings
        self.oled_width = int(os.getenv('OLED_WIDTH', '128'))
        self.oled_height = int(os.getenv('OLED_HEIGHT', '64'))
        self.oled_i2c_address = int(os.getenv('OLED_I2C_ADDRESS', '0x3C'), 16)
        self.font_path = os.getenv('FONT_PATH', './assets/fonts/NotoSansCJKjp-Regular.otf')
        self.font_size = int(os.getenv('FONT_SIZE', '14'))
        self.scroll_speed = int(os.getenv('SCROLL_SPEED_PX', '2'))
        self.frame_delay = float(os.getenv('FRAME_DELAY_SEC', '0.05'))

        # APIキーが設定されていない場合はエラーを発生
        if not self.weather_api_key:
            raise ValueError("WEATHER_API_KEY not found in environment variables")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # OpenAI クライアントの初期化
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)

        # OLEDディスプレイの初期化 (I2C address 0x3C is common for SSD1306)
        try:
            serial = i2c(port=1, address=self.oled_i2c_address)
            self.oled = ssd1306(serial, width=self.oled_width, height=self.oled_height)
            self.oled.contrast(255)  # Set maximum brightness
            logger.info(f"OLED initialized successfully: {self.oled_width}×{self.oled_height}, address 0x{self.oled_i2c_address:02X}")
        except Exception as e:
            logger.warning(f"OLED initialization failed: {e}")
            self.oled = None

        # Initialize font
        self.font = None
        if self.oled:
            try:
                self.font = ImageFont.truetype(self.font_path, self.font_size)
                logger.info(f"Font loaded: {self.font_path}, size {self.font_size}")
            except IOError as e:
                logger.warning(f"Font loading failed: {e}. Using default font.")
                self.font = ImageFont.load_default()

    def get_weather_data(self) -> Optional[Dict[str, Any]]:
        """OpenWeatherMap APIから天気データを取得"""
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
        """OpenAI APIを使って天気に基づいた服装アドバイスを生成"""
        if not weather_data:
            return "天気情報を取得できませんでした。"

        # 天気データから必要な情報を抽出
        temperature = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        weather_desc = weather_data['weather'][0]['description']

        # OpenAI APIに送るプロンプトを作成
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
            # OpenAI APIを呼び出して服装アドバイスを生成
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは天気に基づいた服装アドバイザーです。簡潔で実用的なアドバイスを提供してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )

            advice = response.choices[0].message.content.strip()
            logger.info(f"Generated outfit advice: {advice}")
            return advice

        except Exception as e:
            logger.error(f"Failed to generate outfit advice: {e}")
            return "服装アドバイスを生成できませんでした。"

    def format_display_text(self, weather_data: Dict[str, Any], outfit_advice: str) -> str:
        """LCD表示用のテキストを整形"""
        if not weather_data:
            return "天気情報取得失敗"

        temperature = weather_data['main']['temp']
        weather_desc = weather_data['weather'][0]['description']
        city = weather_data['name']

        # 表示形式: "都市名: 気温 天気 | 服装アドバイス"
        display_text = f"{city}: {temperature}°C {weather_desc} | {outfit_advice}"
        return display_text

    def display_scrolling_text(self, text: str, loop_count: int = 3):
        """OLEDに横スクロールでテキストを表示"""
        if not self.oled or not self.font:
            logger.info(f"OLED not available. Text would display: {text}")
            return

        # スクロール用のテキスト幅を計算
        dummy_image = Image.new("1", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_image)
        bbox = dummy_draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]

        # テキストを垂直中央に配置
        margin_y = (self.oled_height - self.font_size) // 2

        logger.info(f"Starting scroll: text width {text_width}px, {loop_count} loops")

        x_position = self.oled_width  # 右端から開始
        loop_counter = 0

        try:
            while loop_counter < loop_count:
                # フレームごとに新しい画像を作成
                image = Image.new("1", (self.oled_width, self.oled_height))
                draw = ImageDraw.Draw(image)

                # 現在位置にテキストを描画
                draw.text((x_position, margin_y), text, font=self.font, fill=255)

                # OLEDに表示
                self.oled.display(image)

                # スクロール位置を更新（右→左へ移動）
                x_position -= self.scroll_speed

                # テキストが完全に画面外に出たら右端に戻す
                if x_position + text_width < 0:
                    x_position = self.oled_width
                    loop_counter += 1

                # フレーム間隔
                time.sleep(self.frame_delay)

        except KeyboardInterrupt:
            logger.info("Scrolling interrupted by user")
            self.oled.clear()
        except Exception as e:
            logger.error(f"OLED display error: {e}")

    def run(self, loop_count: int = 3):
        """メイン実行関数: プログラム全体の流れを制御"""
        logger.info("Starting Weather Outfit Advisor")

        # ステップ1: 天気データの取得
        logger.info("Fetching weather data...")
        weather_data = self.get_weather_data()

        if not weather_data:
            error_msg = "天気データ取得失敗"
            if self.oled:
                # エラーメッセージを表示
                image = Image.new("1", (self.oled_width, self.oled_height))
                draw = ImageDraw.Draw(image)
                draw.text((10, self.oled_height // 2), error_msg, font=self.font, fill=255)
                self.oled.display(image)
                time.sleep(5)
                self.oled.clear()
            logger.error("Failed to get weather data")
            return

        # ステップ2: 服装アドバイスの生成
        logger.info("Generating outfit advice...")
        outfit_advice = self.generate_outfit_advice(weather_data)

        # ステップ3: 表示用テキストの整形
        display_text = self.format_display_text(weather_data, outfit_advice)
        logger.info(f"Display text: {display_text}")

        # ステップ4: OLEDに横スクロール表示
        self.display_scrolling_text(display_text, loop_count=loop_count)

        # ステップ5: 終了処理
        if self.oled:
            self.oled.clear()

        logger.info("Weather Outfit Advisor completed")

# === プログラムのエントリーポイント ===
def main():
    """メイン関数: プログラム全体の起動と例外処理を管理"""
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