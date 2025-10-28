#!/usr/bin/env python3
"""
天気予報＋服装提案掲示板アプリ
OpenWeatherMap APIで天気を取得し、OpenAI APIで服装アドバイスを生成して、SSD1306 OLEDに日本語スクロール表示します
要件定義書: 09-003_天気予報＋服装提案掲示板アプリ_要件定義書.md
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
    """
    天気予報と服装アドバイスを取得してOLED表示するクラス
    初心者向けに単一ファイルで完結する設計としています
    """

    def __init__(self):
        """
        天気予報＋服装提案アドバイザーの初期化

        環境変数(.env)からAPIキーと設定を読み込み、OpenAI APIクライアントと
        SSD1306 OLEDディスプレイを初期化します
        """
        # 環境変数からAPIキーと都市名を取得
        self.weather_api_key = os.getenv('WEATHER_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.city_name = os.getenv('CITY_NAME', 'Tokyo')  # デフォルトはTokyo

        # OLEDディスプレイ設定（.envファイルから読み込み）
        self.oled_width = int(os.getenv('OLED_WIDTH', '128'))      # 画面幅（通常128）
        self.oled_height = int(os.getenv('OLED_HEIGHT', '64'))     # 画面高さ（64または32）
        self.oled_i2c_address = int(os.getenv('OLED_I2C_ADDRESS', '0x3C'), 16)  # I²Cアドレス（通常0x3Cまたは0x3D）

        # フォント設定
        self.font_path = os.getenv('FONT_PATH', './assets/fonts/NotoSansCJKjp-Regular.otf')  # 日本語フォントのパス
        self.font_size = int(os.getenv('FONT_SIZE', '14'))         # フォントサイズ（14推奨）

        # スクロール設定
        self.scroll_speed = int(os.getenv('SCROLL_SPEED_PX', '2'))      # スクロール速度（ピクセル/フレーム）
        self.frame_delay = float(os.getenv('FRAME_DELAY_SEC', '0.05'))  # フレーム間隔（秒）

        # APIキーが設定されていない場合はエラーを発生
        if not self.weather_api_key:
            raise ValueError("WEATHER_API_KEY not found in environment variables")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # OpenAI クライアントの初期化
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)

        # OLEDディスプレイの初期化
        # I²Cインターフェース初期化（Raspberry Pi 5ではポート1: GPIO2=SDA, GPIO3=SCL）
        try:
            serial = i2c(port=1, address=self.oled_i2c_address)
            logger.info(f"I²C初期化完了: アドレス 0x{self.oled_i2c_address:02X}, ポート 1")
        except Exception as e:
            logger.error(f"[I²C初期化]エラー: {e}")
            logger.error("対処方法: I²C設定と配線を確認してください")
            logger.error("ヒント: raspi-config で I²C を有効化")
            logger.error("ヒント: i2cdetect -y 1 でデバイスを確認")
            self.oled = None
            self.font = None
            return

        # SSD1306デバイスの初期化
        try:
            self.oled = ssd1306(serial, width=self.oled_width, height=self.oled_height)
            self.oled.contrast(255)  # コントラストを最大に設定（明るさ調整）
            logger.info(f"OLED初期化完了: {self.oled_width}×{self.oled_height}")
            logger.info("コントラスト設定: 255 (最大)")
        except Exception as e:
            logger.error(f"[OLED初期化]エラー: {e}")
            logger.error("対処方法: デバイスとの通信を確認してください")
            logger.error("ヒント: レベル変換モジュールの配線確認（LV=3.3V, HV=OLED電源）")
            self.oled = None
            self.font = None
            return

        # 日本語フォントの読み込み
        try:
            self.font = ImageFont.truetype(self.font_path, self.font_size)
            logger.info(f"フォント読み込み完了: {self.font_path}, サイズ {self.font_size}")
        except IOError as e:
            logger.error(f"[フォント読み込み]エラー: {e}")
            logger.error(f"対処方法: フォントファイルを {self.font_path} に配置してください")
            logger.error("ヒント: Noto Sans CJK JP などの OFL ライセンスフォントを使用")
            logger.error("ヒント: 相対パスの場合、スクリプト実行ディレクトリからのパスを確認")
            self.font = None

    def get_weather_data(self) -> Optional[Dict[str, Any]]:
        """
        OpenWeatherMap APIから天気データを取得

        Returns:
            dict: 天気データ（気温、湿度、天気など）を含む辞書
                  取得失敗時はNoneを返す
        """
        # OpenWeatherMap API のエンドポイント
        base_url = "https://api.openweathermap.org/data/2.5/weather"

        # APIリクエストパラメータ
        params = {
            'q': self.city_name,                # 都市名（例: Tokyo, Osaka）
            'appid': self.weather_api_key,      # APIキー
            'units': 'metric',                  # 温度単位（metric=摂氏、imperial=華氏）
            'lang': 'ja'                        # 言語（ja=日本語）
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch weather data: {e}")
            return None

    def generate_outfit_advice(self, weather_data: Dict[str, Any]) -> str:
        """
        OpenAI APIを使って天気に基づいた服装アドバイスを生成

        Args:
            weather_data (dict): get_weather_data()から取得した天気データ

        Returns:
            str: 服装アドバイスの文字列（50文字以内）
                 エラー時はエラーメッセージを返す
        """
        if not weather_data:
            return "天気情報を取得できませんでした。"

        # 天気データから必要な情報を抽出
        temperature = weather_data['main']['temp']          # 気温（摂氏）
        feels_like = weather_data['main']['feels_like']    # 体感温度（摂氏）
        humidity = weather_data['main']['humidity']        # 湿度（%）
        weather_desc = weather_data['weather'][0]['description']  # 天気の説明（日本語）

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
            # gpt-5-mini: GPT-5の軽量モデル（推論機能付き）
            # 参考実装: https://github.com/Murasan201/09-001-gpt-response-minimal
            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",  # GPT-5の軽量モデル
                messages=[
                    {"role": "system", "content": "あなたは天気に基づいた服装アドバイザーです。簡潔で実用的なアドバイスを提供してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=1000  # 推論トークン+レスポンストークンの合計
            )

            advice = response.choices[0].message.content.strip()

            # トークン使用状況をログ出力（GPT-5の推論トークンを含む）
            usage = response.usage
            logger.info(f"Generated outfit advice: {advice}")
            logger.info(f"Token usage - Total: {usage.total_tokens}, "
                       f"Input: {usage.prompt_tokens}, "
                       f"Output: {usage.completion_tokens}")

            # GPT-5では推論トークン数も確認可能（存在する場合）
            if hasattr(usage, 'completion_tokens_details'):
                details = usage.completion_tokens_details
                if hasattr(details, 'reasoning_tokens'):
                    logger.info(f"Reasoning tokens: {details.reasoning_tokens}")

            return advice

        except Exception as e:
            logger.error(f"Failed to generate outfit advice: {e}")
            return "服装アドバイスを生成できませんでした。"

    def format_display_text(self, weather_data: Dict[str, Any], outfit_advice: str) -> str:
        """
        OLED表示用のテキストを整形

        Args:
            weather_data (dict): 天気データ
            outfit_advice (str): 服装アドバイス

        Returns:
            str: スクロール表示用に整形されたテキスト
                 形式: "都市名: 気温 天気 | 服装アドバイス"
        """
        if not weather_data:
            return "天気情報取得失敗"

        # 天気データから表示に必要な情報を抽出
        temperature = weather_data['main']['temp']             # 気温
        weather_desc = weather_data['weather'][0]['description']  # 天気の説明
        city = weather_data['name']                            # 都市名

        # 表示形式: "都市名: 気温 天気 | 服装アドバイス"
        display_text = f"{city}: {temperature}°C {weather_desc} | {outfit_advice}"
        return display_text

    def display_scrolling_text(self, text: str, loop_count: int = 3):
        """
        OLEDに横スクロールでテキストを表示

        Args:
            text (str): スクロール表示するテキスト
            loop_count (int): スクロールループ回数（デフォルト: 3回）

        参照実装: 06-004-ssd1306-oled-jp-display/src/scroll_oled.py
        """
        if not self.oled or not self.font:
            logger.info(f"OLED利用不可。表示予定テキスト: {text}")
            return

        # テキストの幅を事前に計算
        # getbbox() はテキストの境界ボックスを返す（left, top, right, bottom）
        dummy_image = Image.new("1", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_image)
        bbox = dummy_draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]  # right - left = テキストの幅

        # テキストを垂直中央に配置
        margin_y = (self.oled_height - self.font_size) // 2

        logger.info(f"スクロール開始: テキスト幅 {text_width}px")
        logger.info(f"スクロール速度: {self.scroll_speed}px/フレーム, 間隔: {self.frame_delay}秒")
        logger.info(f"ループ回数: {loop_count}回")

        # スクロール表示のメインループ
        x_position = self.oled_width  # 画面右端から開始
        loop_counter = 0

        try:
            while loop_counter < loop_count:
                # 新しい画像を作成（毎フレーム再描画）
                image = Image.new("1", (self.oled_width, self.oled_height))
                draw = ImageDraw.Draw(image)

                # 現在位置にテキストを描画
                draw.text((x_position, margin_y), text, font=self.font, fill=255)

                # OLEDに表示
                self.oled.display(image)

                # スクロール位置を更新（右→左へ移動）
                x_position -= self.scroll_speed

                # テキストが完全に画面外に出たら右端に戻す
                # テキスト全体が左端を通過したら（x + text_width < 0）リセット
                if x_position + text_width < 0:
                    x_position = self.oled_width
                    loop_counter += 1

                # フレーム間隔待機
                time.sleep(self.frame_delay)

            logger.info(f"スクロール完了: {loop_counter}回")

        except KeyboardInterrupt:
            logger.info("スクロール停止: ユーザー割り込み")
            self.oled.clear()
        except Exception as e:
            logger.error(f"[スクロール表示]エラー: {e}")
            logger.error("対処方法: デバイス接続を確認してください")

    def run(self, loop_count: int = 3):
        """
        メイン実行関数：天気取得→アドバイス生成→OLED表示の全工程を実行

        Args:
            loop_count (int): OLEDスクロール回数（デフォルト: 3回）
        """
        logger.info("Starting Weather Outfit Advisor")

        # ステップ1: 天気データの取得
        logger.info("天気データを取得中...")
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
        logger.info("服装アドバイスを生成中...")
        outfit_advice = self.generate_outfit_advice(weather_data)

        # ステップ3: 表示用テキストの整形
        display_text = self.format_display_text(weather_data, outfit_advice)
        logger.info(f"表示テキスト: {display_text}")

        # ステップ4: OLEDに横スクロール表示
        self.display_scrolling_text(display_text, loop_count=loop_count)

        # ステップ5: 終了処理（画面をクリア）
        if self.oled:
            self.oled.clear()

        logger.info("天気予報＋服装提案アドバイザー完了")

# === プログラムのエントリーポイント ===
def main():
    """
    メイン関数：プログラム全体の起動と例外処理を管理

    WeatherOutfitAdvisorクラスのインスタンスを作成し、
    天気予報と服装アドバイスの取得・表示を実行します
    """
    try:
        # WeatherOutfitAdvisorクラスのインスタンス作成
        advisor = WeatherOutfitAdvisor()

        # メイン処理の実行
        advisor.run()

    except KeyboardInterrupt:
        # Ctrl+Cで中断された場合
        logger.info("ユーザーによる割り込みでアプリケーションを終了します")

    except Exception as e:
        # 予期しないエラーが発生した場合
        logger.error(f"アプリケーションエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()