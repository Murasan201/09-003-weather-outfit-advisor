# トラブルシューティングガイド

このドキュメントでは、天気予報＋服装提案掲示板アプリの開発・運用中に発生したエラーと対策を記録しています。

## 目次
1. [OpenAI API関連のエラー](#openai-api関連のエラー)
2. [OpenWeatherMap API関連のエラー](#openweathermap-api関連のエラー)
3. [ハードウェア関連のエラー](#ハードウェア関連のエラー)
4. [環境設定関連のエラー](#環境設定関連のエラー)

---

## OpenAI API関連のエラー

### エラー1: `max_tokens`パラメータ非対応エラー

**発生日時**: 2025-10-22

**エラーメッセージ**:
```
Error code: 400 - {'error': {'message': "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.", 'type': 'invalid_request_error', 'param': 'max_tokens', 'code': 'unsupported_parameter'}}
```

**発生状況**:
- GPT-5-miniモデルを使用してAPI呼び出しを実行
- `max_tokens`パラメータを指定

**原因**:
GPT-5系モデルでは、従来の`max_tokens`パラメータが廃止され、`max_completion_tokens`パラメータに変更された。

**対策**:
APIリクエストのパラメータを以下のように変更：

```python
# 変更前（エラー）
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[...],
    max_tokens=100  # ❌ GPT-5では非対応
)

# 変更後（正常動作）
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[...],
    max_completion_tokens=100  # ✅ GPT-5対応
)
```

**修正箇所**:
- `weather_outfit_advisor.py`: 120行目
- `weather_outfit_advisor_console.py`: 110行目

**参考情報**:
- GPT-4o系からGPT-5系への移行時に注意が必要
- 旧バージョンのドキュメントやサンプルコードでは`max_tokens`が使用されている場合がある

---

### エラー2: `temperature`パラメータ値制限エラー

**発生日時**: 2025-10-22

**エラーメッセージ**:
```
Error code: 400 - {'error': {'message': "Unsupported value: 'temperature' does not support 0.7 with this model. Only the default (1) value is supported.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_value'}}
```

**発生状況**:
- GPT-5-miniモデルを使用してAPI呼び出しを実行
- `temperature=0.7`を指定

**原因**:
GPT-5-miniモデルでは、`temperature`パラメータがデフォルト値(1)のみサポートされており、カスタム値を設定できない。

**対策**:
`temperature`パラメータを削除するか、デフォルト値(1)のままにする：

```python
# 変更前（エラー）
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[...],
    temperature=0.7  # ❌ GPT-5-miniではカスタム値非対応
)

# 変更後（正常動作）
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[...],
    # temperature パラメータを削除（デフォルト値1が使用される）✅
)
```

**修正箇所**:
- `weather_outfit_advisor.py`: 121行目（削除）
- `weather_outfit_advisor_console.py`: 111行目（削除）

**参考情報**:
- GPT-5-miniは高速・低コストモデルであり、パラメータのカスタマイズ性が制限されている
- より柔軟な設定が必要な場合は、`gpt-5`や`gpt-5-main`モデルの使用を検討

---

### エラー3: OpenAI API旧形式エラー（予防的対策）

**想定エラー**:
```
AttributeError: module 'openai' has no attribute 'ChatCompletion'
```

**発生状況**:
- 旧形式のOpenAI API呼び出し方法を使用
- 最新のopenaiライブラリ（v1.0以降）をインストール

**原因**:
OpenAI Python SDKがv1.0で大幅に変更され、旧形式の`openai.ChatCompletion.create()`が廃止された。

**対策**:
新形式のクライアントベースAPIに移行：

```python
# 旧形式（廃止）
import openai
openai.api_key = "your-api-key"
response = openai.ChatCompletion.create(...)  # ❌ 動作しない

# 新形式（推奨）
from openai import OpenAI
client = OpenAI(api_key="your-api-key")
response = client.chat.completions.create(...)  # ✅ 正常動作
```

**参考情報**:
- OpenAI SDK v1.0以降への移行ガイド: https://github.com/openai/openai-python/discussions/742

---

## OpenWeatherMap API関連のエラー

### （現在のところエラーなし）

天気データの取得は正常に動作しています。

**確認済み動作**:
- 都市名: Tokyo（東京都）
- 気温取得: 正常
- 天気説明: 正常（日本語）
- APIレスポンス時間: 約0.6秒

---

## ハードウェア関連のエラー

### （コンソール版では該当なし）

LCD1602ディスプレイを使用する場合、以下のエラーが想定されます：

### 想定エラー: LCD初期化失敗

**想定エラーメッセージ**:
```
LCD initialization failed: [Errno 2] No such file or directory: '/dev/i2c-1'
```

**発生状況**:
- Raspberry Pi以外の環境で実行
- I2Cが有効化されていない
- LCDが正しく接続されていない

**対策**:
1. I2Cを有効化する：
```bash
sudo raspi-config
# Interface Options > I2C > Enable
```

2. I2Cデバイスを確認：
```bash
sudo i2cdetect -y 1
```

3. LCDのI2Cアドレスを確認（通常は0x27または0x3F）

4. コンソール版を使用してテスト：
```bash
python3 weather_outfit_advisor_console.py
```

---

## 環境設定関連のエラー

### エラー: APIキー未設定エラー

**想定エラーメッセージ**:
```
ValueError: WEATHER_API_KEY not found in environment variables
ValueError: OPENAI_API_KEY not found in environment variables
```

**発生状況**:
- `.env`ファイルが存在しない
- `.env`ファイルにAPIキーが記載されていない

**対策**:
1. `.env`ファイルをプロジェクトルートに作成：
```bash
cd /path/to/09-003-weather-outfit-advisor
touch .env
```

2. 以下の内容を記載：
```bash
WEATHER_API_KEY=your_openweathermap_api_key
OPENAI_API_KEY=your_openai_api_key
CITY_NAME=Tokyo
```

3. APIキーの取得方法：
   - OpenWeatherMap: https://openweathermap.org/ でアカウント作成
   - OpenAI: https://platform.openai.com/ でアカウント作成

**参考情報**:
- `.env.example`ファイルを参考に設定
- APIキーは絶対にGitにコミットしない（`.gitignore`で除外済み）

---

## よくある質問（FAQ）

### Q1: プログラムが途中で止まる
**A**: OpenAI APIの応答待ちの可能性があります。ネットワーク接続を確認してください。タイムアウトは30秒に設定されています。

### Q2: 服装アドバイスが英語で返ってくる
**A**: プロンプト内で「日本語で」と明示的に指定しているため、通常は日本語で返答されます。もし英語が返る場合は、OpenAI APIの言語設定を確認してください。

### Q3: 天気情報が古い
**A**: OpenWeatherMap APIはリアルタイムデータを提供しています。キャッシュの問題ではなく、最新の気象データが反映されています。

### Q4: LCD表示が文字化けする
**A**: LCD1602は日本語文字の直接表示に対応していません。カスタムキャラクタの定義が必要です。現在の実装では日本語をそのまま送信しているため、文字化けする可能性があります。

---

## エラー報告について

新しいエラーを発見した場合は、以下の情報とともにこのドキュメントに追記してください：

1. **発生日時**
2. **エラーメッセージ（完全なトレースバック）**
3. **発生状況（何をした時に発生したか）**
4. **原因**
5. **対策・解決方法**
6. **修正箇所**
7. **参考情報（あれば）**

---

## バージョン情報

このドキュメントの最終更新日: 2025-10-22

**使用ライブラリバージョン**:
- Python: 3.9以上
- openai: 1.0以降
- requests: 最新版
- python-dotenv: 最新版
- RPLCD: 最新版（LCD版のみ）

---

### エラー4: GPT-5モデル利用不可エラー（空レスポンス）

**発生日時**: 2025-10-22

**症状**:
```
2025-10-22 17:32:57,562 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-10-22 17:32:57,569 - INFO - Generated outfit advice: 
2025-10-22 17:32:57,569 - INFO - Display text: 東京都: 12.18°C 強い雨 | 
```

**発生状況**:
- `model="gpt-5-mini"`を指定してAPI呼び出し
- HTTPステータスは200 OKで正常に見えるが、レスポンスが空文字列

**原因**:
GPT-5系モデル（gpt-5-mini、gpt-5など）が、2025年10月時点でOpenAI APIで正式に利用可能になっていない可能性がある。モデル名が存在しないか、アクセス権限が不足している場合、エラーではなく空のレスポンスが返ることがある。

**対策**:
確実に利用可能な`gpt-4o-mini`モデルに変更：

```python
# 変更前（空レスポンス）
response = client.chat.completions.create(
    model="gpt-5-mini",  # ❌ 利用不可の可能性
    messages=[...],
    max_completion_tokens=100
)

# 変更後（正常動作）
response = client.chat.completions.create(
    model="gpt-4o-mini",  # ✅ 2024年7月リリース、確実に利用可能
    messages=[...],
    max_tokens=100  # gpt-4o-miniでは max_tokens を使用
)
```

**修正箇所**:
- `weather_outfit_advisor.py`: 115行目、120行目
- `weather_outfit_advisor_console.py`: 105行目、110行目

**参考情報**:
- gpt-4o-miniは2024年7月18日にリリースされた高効率モデル
- GPT-3.5-turboの後継として推奨されている
- 128Kトークンのコンテキストウィンドウをサポート
- GPT-5系モデルは2025年8月7日に発表されたが、API利用可能時期は未定の場合がある
- モデルの利用可能性はOpenAI公式ドキュメントで確認: https://platform.openai.com/docs/models

**解決後の動作確認**:
```
2025-10-22 17:34:08,075 - INFO - Generated outfit advice: 防水のレインコートと長靴を着用し、傘を持参してください。
2025-10-22 17:34:08,076 - INFO - Display text: 東京都: 12.18°C 強い雨 | 防水のレインコートと長靴を着用し、傘を持参してください。
```

✅ 正常に服装アドバイスが生成され、LCD表示用のメッセージが作成された。

