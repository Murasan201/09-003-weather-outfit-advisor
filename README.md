# 天気予報＋服装提案掲示板アプリ

OpenWeatherMap APIから取得した天気情報を基に、OpenAI APIで生成した服装アドバイスをLCD1602モジュールに横スクロール表示するRaspberry Pi用Pythonアプリケーションです。

## 機能

- OpenWeatherMap APIから当日の天気情報を取得
- OpenAI APIを使用して天気に応じた服装アドバイスを生成
- LCD1602ディスプレイに情報を横スクロール表示
- エラーハンドリングとログ出力

## 必要なハードウェア

- Raspberry Pi 5
- LCD1602ディスプレイモジュール（I²C接続）
- ジャンパーワイヤ
- ブレッドボードまたはLCD固定具

## LCD1602接続方法

LCD1602をI²C経由で接続：

- VCC → 5V
- GND → GND
- SDA → GPIO2 (Pin 3)
- SCL → GPIO3 (Pin 5)

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. APIキーの設定

`.env.example`を`.env`にコピーして、APIキーを設定：

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```
WEATHER_API_KEY=your_openweathermap_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
CITY_NAME=Tokyo
```

### 3. APIキーの取得

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

### 実行時オプション

アプリケーションは以下の動作を行います：

1. 天気情報をOpenWeatherMap APIから取得
2. OpenAI APIで服装アドバイスを生成
3. LCD1602に情報を横スクロール表示（60秒間）

### 定期実行の設定

毎朝8時に自動実行する場合、cronジョブを設定：

```bash
crontab -e
```

以下を追加：

```
0 8 * * * cd /path/to/weather-outfit-advisor && /usr/bin/python3 weather_outfit_advisor.py
```

## ログ出力

アプリケーションは`weather_outfit.log`ファイルにログを出力します。エラーやデバッグ情報を確認できます。

## トラブルシューティング

### LCD接続エラー
- I²Cが有効になっているか確認：`sudo raspi-config`
- I²Cアドレスを確認：`sudo i2cdetect -y 1`
- 配線を再確認

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
weather-outfit-advisor/
├── weather_outfit_advisor.py  # メインアプリケーション
├── requirements.txt          # Python依存関係
├── .env.example             # 環境変数テンプレート
├── .env                     # 環境変数（ユーザーが作成）
├── weather_outfit.log       # ログファイル（実行時作成）
└── README.md               # このファイル
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。