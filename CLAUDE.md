# Claude Code ルールファイル

## プロジェクト概要
- **プロジェクト名**: 天気予報＋服装提案掲示板アプリ
- **文書番号**: 09-003
- **リポジトリ**: https://github.com/Murasan201/09-003-weather-outfit-advisor

## 作業開始時の必須手順
1. **要件定義書の確認**: 作業開始時は必ず `09-003_天気予報＋服装提案掲示板アプリ_要件定義書.md` を確認すること
2. 要件定義書の内容に基づいて作業を進めること
3. 機能要件・非機能要件・受け入れ基準を満たしているか確認すること

## 技術スタック
- **言語**: Python 3.9以上
- **ハードウェア**: Raspberry Pi 5 + SSD1306 OLED（I²C接続、128×64）
- **API**:
  - OpenWeatherMap API（天気情報取得）
  - OpenAI API: gpt-5-mini（服装アドバイス生成）
    - パラメータ: `max_completion_tokens=1000`
    - 推論トークン使用実績: 平均427トークン
- **主要ライブラリ**: requests, openai, luma.oled, Pillow, python-dotenv
- **参照実装**:
  - OLED日本語表示: https://github.com/Murasan201/06-004-ssd1306-oled-jp-display
  - GPT-5 API呼び出し: https://github.com/Murasan201/09-001-gpt-response-minimal

## コーディング規約
- PEP8準拠のコードスタイル
- 適切なコメント記載
- 関数分割による可読性の向上
- 単一ファイル完結を基本とする

## エラーハンドリング要件
- API通信エラー時のリトライ機能
- エラーログの適切な出力
- ネットワーク切断時の対応

## テスト要件
以下のテストを実装・実行すること：
- API取得テスト（無効APIキー、ネットワーク切断対応）
- 判定ロジックテスト（各気温・天気パターン）
- OLED表示テスト（横スクロール動作、日本語表示）
- 定期実行テスト（指定時刻での実行）

## 受け入れ基準
1. 当日の天気と服装アドバイスがSSD1306 OLEDで正しく日本語スクロール表示される ✅
2. APIエラー発生時にログが出力され、次実行で回復する ✅
3. 環境変数変更が即時反映される ✅
4. GPT-5-miniでの服装アドバイス生成が正常動作する ✅
5. トークン使用状況がログに記録される ✅

## 実装完了日
- 2025年10月28日
- 動作確認: コンソール版・OLED版ともに正常動作確認済み

## 環境設定
- `.env`ファイルでAPI認証情報とディスプレイ設定を管理
- 必要なAPIキー: `WEATHER_API_KEY`, `OPENAI_API_KEY`
- デフォルト都市: Tokyo（`CITY_NAME`で変更可能）
- OLED設定: `OLED_WIDTH`, `OLED_HEIGHT`, `OLED_I2C_ADDRESS`
- フォント設定: `FONT_PATH`, `FONT_SIZE`
- スクロール設定: `SCROLL_SPEED_PX`, `FRAME_DELAY_SEC`

## 実行・デプロイメント
- メインファイル: `weather_outfit_advisor.py`
- 定期実行: cronジョブによる毎朝8時実行を推奨
- ログファイル: `weather_outfit.log`で動作確認

## 開発時の注意事項
- ハードウェア依存部分（OLED制御）のモックアップ対応
- API利用制限を考慮した実装
- Raspberry Pi環境での動作確認必須
- 日本語フォント（Noto Sans CJK JP）の配置が必要
- I²C通信の有効化とデバイスアドレス確認（`i2cdetect -y 1`）