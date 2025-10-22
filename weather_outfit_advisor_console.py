#!/usr/bin/env python3
"""
Weather Forecast + Clothing Advice Display App (Console Version)
天気予報＋服装提案掲示板アプリ（コンソール出力版）

This is a test version that outputs to console instead of LCD1602.
LCDが使えない環境でもテストできるバージョンです。
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
except ImportError as e:
    print(f"Required library not installed: {e}")
    print("Please run: pip install openai python-dotenv requests")
    sys.exit(1)

# === 環境変数の読み込み ===
load_dotenv()

# === ログ設定 ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weather_outfit_console.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === メインクラス：天気予報＋服装提案アドバイザー（コンソール版） ===
class WeatherOutfitAdvisorConsole:
    def __init__(self):
        """クラスの初期化: APIキーの取得、OpenAIの設定を行う"""
        # 環境変数からAPIキーと都市名を取得
        self.weather_api_key = os.getenv('WEATHER_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.city_name = os.getenv('CITY_NAME', 'Tokyo')

        # APIキーが設定されていない場合はエラーを発生
        if not self.weather_api_key:
            raise ValueError("WEATHER_API_KEY not found in environment variables")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # OpenAI クライアントの初期化
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)

        logger.info("Console version initialized (no LCD required)")

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
        """表示用のテキストを整形"""
        if not weather_data:
            return "天気情報取得失敗"

        temperature = weather_data['main']['temp']
        weather_desc = weather_data['weather'][0]['description']
        city = weather_data['name']

        # 表示形式: "都市名: 気温 天気 | 服装アドバイス"
        display_text = f"{city}: {temperature}°C {weather_desc} | {outfit_advice}"
        return display_text

    def display_console_text(self, text: str, scroll_delay: float = 0.3, duration: int = 10):
        """コンソールに横スクロールでテキストを表示（LCD1602の動作をシミュレート）"""
        console_width = 16  # LCD1602の表示幅をシミュレート

        print("\n" + "=" * 50)
        print("LCD1602 シミュレーション (16文字幅)")
        print("=" * 50)

        # テキストが短い場合は中央揃えで表示
        if len(text) <= console_width:
            centered_text = text.center(console_width)
            print(f"[{centered_text}]")
            time.sleep(duration)
            return

        # 長いテキストの場合、スクロール表示
        scroll_text = f"    {text}    "

        try:
            start_time = time.time()
            # スクロールアニメーションを実行
            while time.time() - start_time < duration:
                for i in range(len(scroll_text) - console_width + 1):
                    display_segment = scroll_text[i:i + console_width]
                    # カーソルを行頭に戻して上書き表示
                    print(f"\r[{display_segment}]", end='', flush=True)
                    time.sleep(scroll_delay)
                print()  # 1サイクル終了後に改行

        except KeyboardInterrupt:
            logger.info("Scrolling interrupted by user")
            print()

    def run(self, display_duration: int = 10):
        """メイン実行関数: プログラム全体の流れを制御"""
        logger.info("Starting Weather Outfit Advisor (Console Version)")

        # ステップ1: 天気データの取得
        logger.info("Fetching weather data...")
        weather_data = self.get_weather_data()

        if not weather_data:
            error_msg = "天気データ取得失敗"
            print(f"\n[ERROR] {error_msg}")
            logger.error("Failed to get weather data")
            return

        # ステップ2: 服装アドバイスの生成
        logger.info("Generating outfit advice...")
        outfit_advice = self.generate_outfit_advice(weather_data)

        # ステップ3: 表示用テキストの整形
        display_text = self.format_display_text(weather_data, outfit_advice)
        logger.info(f"Display text: {display_text}")

        # ステップ4: コンソール表示
        self.display_console_text(display_text, scroll_delay=0.3, duration=display_duration)

        # ステップ5: 終了処理
        print("\n" + "=" * 50)
        print("表示完了")
        print("=" * 50)
        logger.info("Weather Outfit Advisor (Console Version) completed")

# === プログラムのエントリーポイント ===
def main():
    """メイン関数: プログラム全体の起動と例外処理を管理"""
    try:
        advisor = WeatherOutfitAdvisorConsole()
        advisor.run(display_duration=10)  # テスト用に10秒に設定
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n\nプログラムを中断しました。")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\n[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
