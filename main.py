import os
import logging
import argparse

from src.fetch_ar5iv import fetch_ar5iv_html
from src.translate import Translator

logger = logging.getLogger(__name__)


def main(arxiv_id: str) -> None:
    # loggerの設定
    logging.basicConfig(level=logging.WARNING)

    # ar5iv.orgからHTMLソースを取得して保存
    fetch_ar5iv_html(arxiv_id)

    # 保存したHTMLソースを読み込む
    with open(f"./data/en/{arxiv_id}.html", "r", encoding="utf-8") as f:
        html: str = f.read()

    # HTMLソースを翻訳
    translator: Translator = Translator()
    translated_html: str = translator.translate(html)

    # 論文のタイトルを取得
    title: str | None = translator.get_title(html)
    file_name: str
    if title:
        file_name = f"./data/ja/{title}.html"
    else:
        logger.warning(
            f"論文のタイトルの取得に失敗したため、ファイル名にarXiv IDのみを使用します: {arxiv_id}"
        )
        file_name = f"./data/ja/{arxiv_id}.html"

    # 翻訳されたHTMLソースを保存
    os.makedirs("./data/ja/", exist_ok=True)
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(translated_html)


if __name__ == "__main__":
    # コマンドライン引数の解析
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("arxiv_id", type=str, help="arXiv ID (例: 2101.00001)")
    args: argparse.Namespace = parser.parse_args()

    # 実行
    main(args.arxiv_id.strip())
