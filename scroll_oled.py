#!/usr/bin/env python3
"""
SSD1306 OLED スクロール表示ライブラリ
日本語テキストを横スクロール表示する機能を提供
要件定義書: 06-004-ssd_1306_oled_要件定義書（rev.md
"""

import sys
import time

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

# ========================================
# 設定定数
# ========================================
FONT_PATH = "../assets/fonts/NotoSansCJKjp-Regular.otf"
FONT_SIZE = 16
WIDTH = 128
HEIGHT = 64
I2C_ADDRESS = 0x3C


class OLEDScroller:
    """OLED横スクロール表示クラス"""

    def __init__(self, font_path=FONT_PATH, font_size=FONT_SIZE,
                 width=WIDTH, height=HEIGHT, address=I2C_ADDRESS):
        """
        OLEDデバイスとフォントを初期化

        Args:
            font_path (str): フォントファイルのパス
            font_size (int): フォントサイズ
            width (int): 画面幅（128）
            height (int): 画面高さ（64または32）
            address (int): I²Cアドレス（0x3Cまたは0x3D）
        """
        self.width = width
        self.height = height

        # I²C・デバイス初期化
        try:
            serial = i2c(port=1, address=address)
            self.device = ssd1306(serial, width=width, height=height)
            self.device.contrast(255)
        except Exception as e:
            print(f"[OLED初期化]エラー: {e}")
            print("ヒント: i2cdetect -y 1 でデバイスを確認")
            sys.exit(1)

        # フォント読み込み
        try:
            self.font = ImageFont.truetype(font_path, font_size)
        except IOError as e:
            print(f"[フォント読み込み]エラー: {e}")
            print(f"ヒント: {font_path} にフォントを配置")
            sys.exit(1)

    def scroll(self, text, speed=2, delay=0.05, loops=None, y_pos=24):
        """
        テキストを右から左へスクロール表示

        Args:
            text (str): 表示するテキスト
            speed (int): スクロール速度（ピクセル/フレーム）
            delay (float): フレーム間隔（秒）
            loops (int): ループ回数（Noneで無限）
            y_pos (int): テキストのY座標
        """
        # テキスト幅を計算
        bbox = ImageDraw.Draw(Image.new("1", (1, 1))).textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]

        x = self.width
        loop_count = 0

        try:
            while True:
                # 画像作成・描画
                image = Image.new("1", (self.width, self.height))
                ImageDraw.Draw(image).text((x, y_pos), text, font=self.font, fill=255)
                self.device.display(image)

                # 位置更新
                x -= speed
                if x + text_width < 0:
                    x = self.width
                    loop_count += 1
                    if loops is not None and loop_count >= loops:
                        break

                time.sleep(delay)

        except KeyboardInterrupt:
            self.device.clear()

    def clear(self):
        """画面をクリア"""
        self.device.clear()


def main():
    """動作テスト用"""
    scroller = OLEDScroller()
    print("スクロールテスト開始（3回ループ）")
    scroller.scroll("こんにちは Raspberry Pi！", loops=3)
    scroller.clear()
    print("テスト完了")


if __name__ == "__main__":
    main()
