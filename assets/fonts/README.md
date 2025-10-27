# 日本語フォントについて

## フォントのダウンロード

このアプリケーションでは日本語表示のために **Noto Sans CJK JP** フォントを使用します。

### ダウンロード手順

```bash
cd assets/fonts/
wget https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf
wget https://raw.githubusercontent.com/googlefonts/noto-cjk/main/LICENSE
```

### ライセンス

Noto Sans CJK JP は **SIL Open Font License (OFL-1.1)** で提供されています。

- ✅ 商用利用可
- ✅ 改変可
- ✅ 再配布可

詳細は `LICENSE` ファイルを参照してください。

## 代替フォント

別の日本語フォントを使用する場合は、`.env` ファイルで `FONT_PATH` を設定してください：

```
FONT_PATH=./assets/fonts/your-font.otf
```
