# 天気予報＋服装提案掲示板アプリ

OpenWeatherMap APIから取得した天気情報を基に、OpenAI APIで生成した服装アドバイスをSSD1306 OLEDディスプレイに日本語で横スクロール表示するRaspberry Pi用Pythonアプリケーションです。

## 機能

- OpenWeatherMap APIから当日の天気情報を取得
- OpenAI APIを使用して天気に応じた服装アドバイスを生成
- SSD1306 OLEDディスプレイに日本語で情報を横スクロール表示
- エラーハンドリングとログ出力
- 環境変数による柔軟な設定

## 必要なハードウェア

- Raspberry Pi 5
- SSD1306 OLEDディスプレイモジュール（I²C接続、128×64 または 128×32）
- I²Cレベル変換モジュール（5V OLEDの場合）
- ジャンパーワイヤ
- ブレッドボード

## OLED接続方法

### 3.3V OLED の場合（レベル変換不要）

```
[Raspberry Pi 5]       [3.3V OLED]
Pin 1  (3.3V)  ------> VCC
Pin 3  (GPIO2) ------> SDA
Pin 5  (GPIO3) ------> SCL
Pin 6  (GND)   ------> GND
```

### 5V OLED の場合（レベル変換必須）

```
[Raspberry Pi 5]       [レベル変換]        [5V OLED]
Pin 1  (3.3V)  ------> LV
Pin 3  (GPIO2) ------> LV-SDA  ----> HV-SDA  ----> SDA
Pin 5  (GPIO3) ------> LV-SCL  ----> HV-SCL  ----> SCL
Pin 6  (GND)   ------> GND     <---- GND     <---- GND
                       HV      <---- VCC (5V)
```

⚠️ **重要**: 5V OLEDをRaspberry Piに直結しないでください。GPIO破損の原因になります。

## セットアップ

### 1. I²Cの有効化

```bash
sudo raspi-config
```

- `3 Interface Options` → `I5 I2C` → `Yes`
- 再起動

```bash
sudo reboot
```

### 2. I²Cデバイスの確認

```bash
i2cdetect -y 1
```

`3c`（0x3C）または `3d`（0x3D）が表示されればOKです。

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. 日本語フォントのダウンロード

```bash
cd assets/fonts/
wget https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf
wget https://raw.githubusercontent.com/googlefonts/noto-cjk/main/LICENSE
cd ../..
```

詳細は `assets/fonts/README.md` を参照してください。

### 5. APIキーの設定

`.env.example`を`.env`にコピーして、APIキーを設定：

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```
WEATHER_API_KEY=your_openweathermap_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
CITY_NAME=Tokyo

# OLED Display Settings
OLED_WIDTH=128
OLED_HEIGHT=64
OLED_I2C_ADDRESS=0x3C

# Font Settings
FONT_PATH=./assets/fonts/NotoSansCJKjp-Regular.otf
FONT_SIZE=14

# Scroll Settings
SCROLL_SPEED_PX=2
FRAME_DELAY_SEC=0.05
```

### 6. APIキーの取得

#### OpenWeatherMap API
1. [OpenWeatherMap](https://openweathermap.org/api)にアクセス
2. アカウント作成後、API keyを取得

#### OpenAI API
1. [OpenAI Platform](https://platform.openai.com/api-keys)にアクセス
2. アカウント作成後、API keyを取得

## 使用方法

### 基本実行

```bash
python weather_outfit_advisor.py
```

### 実行時の動作

アプリケーションは以下の動作を行います：

1. 天気情報をOpenWeatherMap APIから取得
2. OpenAI APIで服装アドバイスを生成
3. SSD1306 OLEDに日本語で情報を横スクロール表示（デフォルト3回ループ）

### 定期実行の設定

毎朝8時に自動実行する場合、cronジョブを設定：

```bash
crontab -e
```

以下を追加：

```
0 8 * * * cd /path/to/09-002-weather-outfit-advisor && /usr/bin/python3 weather_outfit_advisor.py
```

## ログ出力

アプリケーションは`weather_outfit.log`ファイルにログを出力します。エラーやデバッグ情報を確認できます。

## トラブルシューティング

### OLED接続エラー

| 症状 | 原因 | 対処方法 |
|------|------|----------|
| `i2cdetect` でデバイスが見つからない | I²C未有効化、配線誤り | I²C有効化、配線確認 |
| `[Errno 121] Remote I/O error` | I²C通信失敗 | 配線・レベル変換確認 |
| 画面が真っ暗 | 電源・コントラスト問題 | VCC接続確認、コントラスト設定確認 |

### フォント関連エラー

| 症状 | 原因 | 対処方法 |
|------|------|----------|
| 日本語が「□」になる | フォント未配置 | Noto Sans CJK JPを配置 |
| `cannot open resource` | フォントパス誤り | `.env`のFONT_PATHを確認 |

### API接続エラー
- インターネット接続を確認
- APIキーが正しく設定されているか確認
- API利用制限に達していないか確認

### 依存関係エラー
```bash
pip install --upgrade -r requirements.txt
```

## ファイル構成

```
09-002-weather-outfit-advisor/
├── weather_outfit_advisor.py                           # メインアプリケーション
├── requirements.txt                                    # Python依存関係
├── .env.example                                       # 環境変数テンプレート
├── .env                                               # 環境変数（ユーザーが作成）
├── assets/
│   └── fonts/
│       ├── README.md                                  # フォント配置手順
│       ├── NotoSansCJKjp-Regular.otf                  # 日本語フォント（要ダウンロード）
│       └── LICENSE                                    # フォントライセンス
├── 09-002_天気予報＋服装提案掲示板アプリ_要件定義書.md  # 要件定義書
├── CLAUDE.md                                          # Claude Code作業ルール
├── weather_outfit.log                                 # ログファイル（実行時作成）
└── README.md                                          # このファイル
```

## 参考資料

- **OLED表示実装参照**: https://github.com/Murasan201/06-004-ssd1306-oled-jp-display
- **luma.oled ドキュメント**: https://luma-oled.readthedocs.io/
- **OpenWeatherMap API**: https://openweathermap.org/api
- **OpenAI API**: https://platform.openai.com/docs

## ライセンス

### プロジェクトコード

このプロジェクトはMITライセンスの下で公開されています。

### フォント

Noto Sans CJK JPは **SIL Open Font License (OFL-1.1)** で提供されています。

- ✅ 商用利用可
- ✅ 改変可
- ✅ 再配布可