import re
import asyncio
import logging

from tqdm.asyncio import tqdm
from bs4 import BeautifulSoup, Tag

from src.llm_client import GeminiClient

logger = logging.getLogger(__name__)


class Translator:
    def __init__(
        self, llm_model: str = "gemini-2.5-flash-lite", concurrency: int = 1
    ) -> None:
        self.llm_client = GeminiClient(model_name=llm_model)
        self.system_prompt = (
            "あなたは専門知識を有する優秀な論文翻訳者です。"
            "入力された文章を日本語に翻訳してください。"
            "文体はだ・である調で統一してください。"
            "文章中の [MATH_0001] や [IMG_0001] のような、"
            "[MATH_数字4桁]・[IMG_数字4桁] 形式の文字列は、数式・画像を表す翻訳対象外の識別子です。"
            "各識別子は角括弧・英字・アンダースコア・数字を含め、入力から一字も変えずにコピーしてください。"
            "各識別子の出現回数と、識別子同士の出現順序を入力と完全に一致させてください。"
            "識別子の削除・追加・複製・分割・全角化や、番号の振り直しを禁止します。"
            "識別子は入力に存在するものだけを使用し、新しい識別子を生成しないでください。"
            "文中の図表への参照は識別子に置き換えず、通常の文章として翻訳してください。"
            "例えば Fig. 1 や Figure 1 は「図1」、Table 1 は「表1」と訳し、参照番号を保持してください。"
            "識別子を数式・画像の内容や説明文に置き換えず、元の段落内に保持してください。"
            "日本語の語順に合わせる場合も、識別子とそれを説明する語句の対応を維持してください。"
            "入力が識別子だけの場合は、そのまま出力してください。"
            "出力前に、すべての識別子の文字列・出現回数・出現順序が入力と一致することを確認してください。"
            "出力は翻訳結果のみとし、解説・注釈・前置き・後書きは一切含めないでください。"
        )
        self.semaphore = asyncio.Semaphore(concurrency)
        self.num_retries = 3

    @staticmethod
    def _protect_math(html: str) -> tuple[str, dict[str, str]]:
        """HTMLソース内の数式を保護する関数

        Args:
            html (str): HTMLソース

        Returns:
            str: 数式が保護されたHTMLソース
            dict[str, str]: 数式のプレースホルダーと元の数式の対応辞書
        """
        math_dict: dict[str, str] = {}

        def _replace(match: re.Match) -> str:
            idx = len(math_dict) + 1
            placeholder = f"[MATH_{idx:04d}]"
            math_dict[placeholder] = match.group(0)
            return placeholder

        # 数式を保護
        html = re.sub(r"<math\b[^>]*?>.*?</math>", _replace, html, flags=re.DOTALL)

        return html, math_dict

    @staticmethod
    def _restore_math(html: str, math_dict: dict[str, str]) -> str:
        """HTMLソース内の数式を復元する関数

        Args:
            html (str): 数式が保護されたHTMLソース
            math_dict (dict[str, str]): 数式のプレースホルダーと元の数式の対応辞書
        Returns:
            str: 数式が復元されたHTMLソース
        """
        for placeholder, math in math_dict.items():
            html = html.replace(placeholder, math)
        return html

    @staticmethod
    def _protect_img(html: str) -> tuple[str, dict[str, str]]:
        """HTMLソース内の画像を保護する関数

        Args:
            html (str): HTMLソース

        Returns:
            str: 画像が保護されたHTMLソース
            dict[str, str]: 画像のプレースホルダーと元の画像の対応辞書
        """
        img_dict: dict[str, str] = {}

        def _replace(match: re.Match) -> str:
            idx = len(img_dict) + 1
            placeholder = f"[IMG_{idx:04d}]"
            img_dict[placeholder] = match.group(0)
            return placeholder

        # 画像を保護
        html = re.sub(r"<img\b[^>]*?>", _replace, html)

        return html, img_dict

    @staticmethod
    def _restore_img(html: str, img_dict: dict[str, str]) -> str:
        """HTMLソース内の画像を復元する関数

        Args:
            html (str): 画像が保護されたHTMLソース
            img_dict (dict[str, str]): 画像のプレースホルダーと元の画像の対応辞書
        Returns:
            str: 画像が復元されたHTMLソース
        """
        for placeholder, img in img_dict.items():
            html = html.replace(placeholder, img)
        return html

    async def _translate_p(self, p: Tag) -> None:
        """1つの段落を翻訳する関数

        Args:
            p (Tag): <p>タグ
        """
        async with self.semaphore:
            text: str = p.get_text()
            for i in range(self.num_retries):
                try:
                    transleted: str | None = await self.llm_client.async_generate_text(
                        prompt=text, system_prompt=self.system_prompt
                    )
                    break
                except Exception as e:
                    if i == self.num_retries - 1:
                        logger.warning(f"LLMとの通信中にエラーが発生しました: {e}")
                        transleted = None

            if transleted:
                p.string = transleted
            else:
                logger.warning(f"パラグラフの翻訳に失敗しました: {text}")
                p.string = text

    async def translate(self, html: str, skip_appendix: bool = False) -> str:
        """HTMLソースを翻訳する関数

        Args:
            html (str): HTMLソース
            skip_appendix (bool): Appendix内の段落を原文のまま残す。

        Returns:
            str: 翻訳されたHTMLソース
        """
        # 数式と画像を保護
        html, math_dict = self._protect_math(html)
        html, img_dict = self._protect_img(html)

        # HTMLをパース
        soup = BeautifulSoup(html, "html.parser")

        # 段落を取得
        paragraphs = list(soup.find_all("p"))
        # skip_appendixがTrueの場合、Appendix内の段落を除外
        if skip_appendix:
            paragraphs = [
                p for p in paragraphs if p.find_parent(class_="ltx_appendix") is None
            ]

        # テキストを翻訳
        tasks = [self._translate_p(p) for p in paragraphs]
        await tqdm.gather(*tasks)

        # 数式と画像を復元
        translated_html: str = str(soup)
        translated_html = self._restore_math(translated_html, math_dict)
        translated_html = self._restore_img(translated_html, img_dict)

        return translated_html

    @staticmethod
    def get_title(html: str) -> str | None:
        """HTMLソースからタイトルを取得する関数

        Args:
            html (str): HTMLソース

        Returns:
            str | None: タイトル。取得に失敗した場合はNoneを返す。
        """
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("title")
        if title:
            return title.get_text()
        else:
            return None
