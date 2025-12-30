# 天気予報＋服装提案アプリ セットアップガイド

このガイドでは、Raspberry Pi 5でアプリケーションを動かすまでの全手順を説明します。

---

## 目次

1. [必要なもの](#1-必要なもの)
2. [ハードウェアの準備](#2-ハードウェアの準備)
3. [Raspberry Piの初期設定](#3-raspberry-piの初期設定)
4. [プロジェクトのダウンロード](#4-プロジェクトのダウンロード)
5. [ライブラリのインストール](#5-ライブラリのインストール)
6. [日本語フォントの準備](#6-日本語フォントの準備)
7. [APIキーの取得と設定](#7-apiキーの取得と設定)
8. [動作確認](#8-動作確認)
9. [トラブルシューティング](#9-トラブルシューティング)

---

## 1. 必要なもの

### ハードウェア

| 部品 | 説明 |
|------|------|
| Raspberry Pi 5 | メインボード |
| microSDカード | 32GB以上推奨、Raspberry Pi OS インストール済み |
| SSD1306 OLED | 128×64ピクセル、I²C接続タイプ |
| ジャンパーワイヤ | メス-メス 4本 |
| 電源アダプタ | Raspberry Pi 5用 5V/5A |

### ソフトウェア・アカウント

| 項目 | 用途 |
|------|------|
| Raspberry Pi OS | OSインストール済みであること |
| OpenWeatherMap アカウント | 天気情報取得用（無料） |
| OpenAI アカウント | 服装アドバイス生成用（有料） |

---

## 2. ハードウェアの準備

### OLED ディスプレイの接続

SSD1306 OLEDをRaspberry Pi 5に接続します。

```
Raspberry Pi 5          SSD1306 OLED
─────────────          ────────────
Pin 1 (3.3V)  ───────→  VCC
Pin 3 (GPIO2) ───────→  SDA
Pin 5 (GPIO3) ───────→  SCL
Pin 6 (GND)   ───────→  GND
```

### 配線図

```
[Raspberry Pi 5]
    ┌─────────────────┐
    │ ○ ○ ○ ○ ○ ...   │  ← GPIOピンヘッダ
    │ 1 3 5 7 9 ...   │
    │ 2 4 6 8 10...   │
    └─────────────────┘
      │ │ │
      │ │ └─ Pin 6 (GND)   → OLED GND
      │ └─── Pin 5 (SCL)   → OLED SCL
      └───── Pin 3 (SDA)   → OLED SDA

    Pin 1 (3.3V) → OLED VCC
```

### 注意事項

- **3.3V OLEDを使用してください**（VCC=3.3V対応のもの）
- 5V OLEDを使用する場合は、レベル変換モジュールが必要です
- 配線は電源を切った状態で行ってください

---

## 3. Raspberry Piの初期設定

### 3.1 I²C の有効化

Raspberry Piの設定画面を開きます。

```bash
sudo raspi-config
```

以下の手順で I²C を有効化します：

1. `3 Interface Options` を選択
2. `I5 I2C` を選択
3. `Yes` を選択して有効化
4. `Finish` で終了

### 3.2 再起動

設定を反映するため再起動します。

```bash
sudo reboot
```

### 3.3 I²C 接続の確認

再起動後、OLEDが認識されているか確認します。

```bash
i2cdetect -y 1
```

**正常な場合の出力例：**

```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```

`3c` が表示されていれば、OLEDは正常に接続されています。

---

## 4. プロジェクトのダウンロード

### 4.1 作業ディレクトリの作成

```bash
mkdir -p ~/projects
cd ~/projects
```

### 4.2 プロジェクトのクローン

```bash
git clone https://github.com/Murasan201/09-003-weather-outfit-advisor.git
cd 09-003-weather-outfit-advisor
```

### 4.3 ディレクトリ構成の確認

```bash
ls -la
```

以下のファイルがあることを確認：

```
09-003-weather-outfit-advisor/
├── weather_outfit_advisor.py   # メインプログラム
├── scroll_oled.py              # OLED表示ライブラリ
├── requirements.txt            # 依存ライブラリ一覧
├── .env.example                # 環境変数テンプレート
└── assets/
    └── fonts/                  # フォント配置場所
```

---

## 5. ライブラリのインストール

### 5.1 pip のアップグレード

```bash
pip install --upgrade pip
```

### 5.2 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

### インストールされるライブラリ

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| requests | 2.31.0 | HTTP通信（天気API） |
| openai | 2.0.0以上 | OpenAI API クライアント |
| luma.oled | 3.13.0 | OLED制御 |
| Pillow | 10.2.0 | 画像処理・フォント描画 |
| python-dotenv | 1.0.0 | 環境変数管理 |

### 5.3 インストール確認

```bash
pip list | grep -E "(requests|openai|luma|Pillow|dotenv)"
```

---

## 6. 日本語フォントの準備

OLED に日本語を表示するため、日本語フォントをダウンロードします。

### 6.1 フォントディレクトリの作成

```bash
mkdir -p assets/fonts
cd assets/fonts
```

### 6.2 Noto Sans CJK JP のダウンロード

```bash
wget https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf
```

### 6.3 ライセンスファイルのダウンロード

```bash
wget https://raw.githubusercontent.com/googlefonts/noto-cjk/main/LICENSE
```

### 6.4 ダウンロード確認

```bash
ls -la
```

以下のファイルがあることを確認：

```
assets/fonts/
├── NotoSansCJKjp-Regular.otf   # 日本語フォント（約16MB）
└── LICENSE                      # ライセンスファイル
```

### 6.5 プロジェクトルートに戻る

```bash
cd ../..
```

---

## 7. APIキーの取得と設定

### 7.1 OpenWeatherMap APIキーの取得

1. [OpenWeatherMap](https://openweathermap.org/) にアクセス
2. 「Sign Up」からアカウントを作成（無料）
3. ログイン後、「API keys」タブを開く
4. 表示されているAPIキーをコピー

**注意**: 新規作成したAPIキーは有効化まで数時間かかる場合があります。

### 7.2 OpenAI APIキーの取得

1. [OpenAI Platform](https://platform.openai.com/) にアクセス
2. アカウントを作成またはログイン
3. 「API keys」ページを開く
4. 「Create new secret key」をクリック
5. 表示されたAPIキーをコピー（一度しか表示されません）

**注意**: OpenAI APIは従量課金制です。利用料金が発生します。

### 7.3 環境変数ファイルの作成

```bash
cp .env.example .env
```

### 7.4 APIキーの設定

`.env` ファイルをエディタで開きます。

```bash
nano .env
```

以下の2行を、取得したAPIキーで書き換えます：

```
WEATHER_API_KEY=ここにOpenWeatherMapのAPIキーを貼り付け
OPENAI_API_KEY=ここにOpenAIのAPIキーを貼り付け
CITY_NAME=Tokyo
```

保存して終了：`Ctrl+O` → `Enter` → `Ctrl+X`

### 7.5 設定の確認

```bash
cat .env | grep -E "(WEATHER_API_KEY|OPENAI_API_KEY|CITY_NAME)"
```

APIキーが正しく設定されていることを確認してください。

---

## 8. 動作確認

### 8.1 プログラムの実行

```bash
python weather_outfit_advisor.py
```

### 8.2 正常動作時の流れ

1. 天気データを取得
2. AIが服装アドバイスを生成
3. OLEDに日本語テキストがスクロール表示（3回ループ）
4. 表示終了後、画面がクリア

### 8.3 表示例

OLEDには以下のようなテキストがスクロール表示されます：

```
Tokyo: 15.2°C 晴れ | 薄手のジャケットがおすすめです
```

### 8.4 OLED なしでの動作確認

OLEDが接続されていない場合でも、プログラムは動作します。
生成されたテキストはコンソールに出力されます。

```
[表示テキスト] Tokyo: 15.2°C 晴れ | 薄手のジャケットがおすすめです
```

---

## 9. トラブルシューティング

### OLED が表示されない

| 症状 | 原因 | 対処法 |
|------|------|--------|
| `i2cdetect` で `3c` が表示されない | 配線ミス | VCC/GND/SDA/SCL の接続を確認 |
| `i2cdetect` で `3c` が表示されない | I²C 無効 | `raspi-config` で I²C を有効化 |
| エラー: `Remote I/O error` | 通信エラー | 配線の接触不良を確認 |

### フォント関連のエラー

| 症状 | 原因 | 対処法 |
|------|------|--------|
| 日本語が「□」で表示 | フォント未配置 | 手順6を再実行 |
| `cannot open resource` | パス誤り | `assets/fonts/` にフォントがあるか確認 |

### API 関連のエラー

| 症状 | 原因 | 対処法 |
|------|------|--------|
| `401 Unauthorized` | APIキー誤り | `.env` のAPIキーを確認 |
| `429 Too Many Requests` | 利用制限超過 | しばらく待ってから再実行 |
| 接続タイムアウト | ネットワーク | インターネット接続を確認 |

### ライブラリ関連のエラー

```bash
# ライブラリの再インストール
pip install --upgrade -r requirements.txt
```

---

## セットアップ完了チェックリスト

以下の項目がすべて完了していることを確認してください：

- [ ] OLEDが正しく配線されている
- [ ] I²Cが有効化されている（`i2cdetect -y 1` で `3c` 表示）
- [ ] ライブラリがインストールされている
- [ ] 日本語フォントが `assets/fonts/` に配置されている
- [ ] `.env` ファイルにAPIキーが設定されている
- [ ] `python weather_outfit_advisor.py` で正常動作

すべて完了すれば、セットアップ完了です。

---

## 次のステップ

### 定期実行の設定

毎朝8時に自動実行する場合は、cron を設定します：

```bash
crontab -e
```

以下の行を追加：

```
0 8 * * * cd ~/projects/09-003-weather-outfit-advisor && python weather_outfit_advisor.py
```

### 都市の変更

`.env` ファイルの `CITY_NAME` を変更することで、別の都市の天気を取得できます：

```
CITY_NAME=Osaka
```

対応都市例：Tokyo, Osaka, Kyoto, Nagoya, Sapporo, Fukuoka など

---

## 参考リンク

- [OpenWeatherMap API](https://openweathermap.org/api)
- [OpenAI Platform](https://platform.openai.com/)
- [Raspberry Pi 公式ドキュメント](https://www.raspberrypi.com/documentation/)
- [Noto Sans CJK JP](https://github.com/googlefonts/noto-cjk)
