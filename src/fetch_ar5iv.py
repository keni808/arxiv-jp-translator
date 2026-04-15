import os
import logging
import requests

logger = logging.getLogger(__name__)


def fetch_ar5iv_html(arxiv_id: str, save_dir: str = "./data/en/") -> None:
    """arXiv IDに対応するar5iv.orgのHTMLソースを取得して保存する関数

    Args:
        arxiv_id (str): arXiv ID (例: "2101.00001")
        save_dir (str): 保存先ディレクトリ (デフォルト: "./data/en/")
    """

    # 保存先の設定
    os.makedirs(save_dir, exist_ok=True)
    path: str = os.path.join(save_dir, f"{arxiv_id}.html")

    # すでに保存されている場合はスキップ
    if os.path.exists(path):
        logger.info(
            f'arXiv ID "{arxiv_id}"のHTMLソースは既に取得済みため、スキップします: {path}'
        )
        return

    # ar5iv.orgからHTMLソースを取得
    url: str = f"https://ar5iv.org/html/{arxiv_id}"
    headers: dict = {"User-Agent": "arxiv-jp-translator/0.1 (personal project)"}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f'arXiv ID "{arxiv_id}"のHTMLソースの取得に失敗しました: {e}')

    # HTML内の相対URLを絶対URLに変換して保存
    html = response.text.replace("<head>", '<head><base href="https://ar5iv.org/">')
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f'arXiv ID "{arxiv_id}"のHTMLソースを保存しました: {path}')
