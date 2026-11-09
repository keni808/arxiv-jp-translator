import logging
import asyncio
import argparse
import math
from pathlib import Path

from src.fetch_ar5iv import fetch_ar5iv_html
from src.llm_client import GeminiClient, LLMClient, SarashinaClient
from src.translate import Translator
from src.sanitize import sanitize_title

logger = logging.getLogger(__name__)


async def main(
    arxiv_id: str,
    model: str | None,
    concurrency: int,
    skip_appendix: bool = False,
    provider: str = "gemini",
    request_interval: float = 0.0,
) -> None:
    # loggerの設定
    logging.basicConfig(level=logging.WARNING)

    # ar5iv.orgからHTMLソースを取得して保存
    save_dir = Path("./data/en")
    fetch_ar5iv_html(arxiv_id)

    # 保存したHTMLソースを読み込む
    en_path: Path = save_dir / f"{arxiv_id}.html"
    if not en_path.exists():
        raise FileNotFoundError(f"HTMLファイルが見つかりません: {en_path}")
    with open(en_path, "r", encoding="utf-8") as f:
        html: str = f.read()

    # HTMLソースを翻訳
    llm_client: LLMClient
    if provider == "gemini":
        if model is None:
            model = "gemini-3.1-flash-lite"
        llm_client = GeminiClient(model_name=model)
    elif provider == "sarashina":
        if model is None:
            model = "sarashina3-nano"
        llm_client = SarashinaClient(model_name=model)
    else:
        raise ValueError(f"未対応のproviderです: {provider}")
    translator: Translator = Translator(
        llm_client=llm_client,
        concurrency=concurrency,
        request_interval=request_interval,
    )
    translated_html: str = await translator.translate(html, skip_appendix=skip_appendix)

    # 論文のタイトルを取得
    title: str = sanitize_title(translator.get_title(html))
    ja_path: Path
    if title.strip() != "":
        ja_path = Path(f"./data/ja/{title}.html")
    else:
        logger.warning(
            f"論文のタイトルの取得に失敗したため、ファイル名にarXiv IDのみを使用します: {arxiv_id}"
        )
        ja_path = Path(f"./data/ja/{arxiv_id}.html")

    # 翻訳されたHTMLソースを保存
    ja_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ja_path, "w", encoding="utf-8") as f:
        f.write(translated_html)


if __name__ == "__main__":
    # コマンドライン引数の解析
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("arxiv_id", type=str, help="arXiv ID (例: 2101.00001)")
    parser.add_argument(
        "--provider",
        choices=["gemini", "sarashina"],
        default="gemini",
        help="使用するLLMプロバイダー (デフォルト: gemini)",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,
        help="使用するモデルの名前 (省略時: geminiはgemini-3.1-flash-lite、sarashinaはsarashina3-nano)",
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=3,
        help="翻訳の同時実行数 (デフォルト: 3)",
    )
    parser.add_argument(
        "--request-interval",
        type=float,
        default=0.0,
        help="APIリクエストの最小開始間隔（秒） (デフォルト: 0、間隔の制御なし)",
    )
    parser.add_argument(
        "--skip-appendix",
        action="store_true",
        help="Appendix内の段落を翻訳せず原文のまま残す",
    )
    args: argparse.Namespace = parser.parse_args()

    if args.concurrency < 1:
        parser.error("--concurrencyには1以上の整数を指定してください")
    if not math.isfinite(args.request_interval) or args.request_interval < 0:
        parser.error("--request-intervalには0以上の有限の秒数を指定してください")

    # 実行
    asyncio.run(
        main(
            args.arxiv_id,
            args.model,
            args.concurrency,
            skip_appendix=args.skip_appendix,
            provider=args.provider,
            request_interval=args.request_interval,
        )
    )
