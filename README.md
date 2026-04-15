# arxiv-ja-translator
arXiv論文をGeminiを用いて日本語に翻訳するツールです。
arXiv IDを指定することで日本語に翻訳されたHTMLを出力します。

## 使い方
1. リポジトリをクローンします。
```bash
git clone git@github.com:keni808/arxiv-jp-translator.git
cd arxiv-jp-translator
```
2. uvを用いて依存関係をインストールします。
```bash
uv sync
```

3. 環境変数を設定します。
```bash
copy .env.example .env
```
この後、`.env`ファイルを開いて、`GOOGLE_API_KEY`にAPIキーを記載します。

4. `main.py`を実行して、翻訳したいarXiv IDを指定します。
```bash
uv run main.py <arxiv_id>
```

## 注意点
本ツールは ar5iv（arXiv のミラーサービス）の HTML ページを自動取得して利用しています。

- 大量の ID を一度に処理するなど、サーバーに過度な負荷をかける使い方は避けてください。
- 利用にあたっては arXiv / ar5iv の利用規約に従ってください。
- 本ツールは非公式ツールであり、arXiv / ar5iv の運営元とは一切関係ありません。
