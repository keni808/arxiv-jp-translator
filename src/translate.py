import re
import logging

from tqdm import tqdm
from bs4 import BeautifulSoup

from src.llm_client import GeminiClient

logger = logging.getLogger(__name__)


class Translator:
    def __init__(self, llm_model: str = "gemini-2.5-flash-lite") -> None:
        self.llm_client = GeminiClient(model_name=llm_model)
        self.system_prompt = (
            "あなたは専門知識を有する優秀な論文翻訳者です。"
            "入力された文章を日本語に翻訳してください。"
            "文体は自然な常体とします。"
            "文章中の [MATH_XXXX] や [IMG_XXXX] は数式・画像を表すプレースホルダーです。"
            "これらのプレースホルダーは一切変更・削除・追加せず、元の位置関係を維持してください。"
            "出力は翻訳結果のみとし、解説・注釈・前置き・後書きは一切含めないでください。"
        )

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

    def translate(self, html: str) -> str:
        """HTMLソースを翻訳する関数

        Args:
            html (str): HTMLソース

        Returns:
            str: 翻訳されたHTMLソース
        """
        # 数式と画像を保護
        html, math_dict = self._protect_math(html)
        html, img_dict = self._protect_img(html)

        # HTMLをパース
        soup = BeautifulSoup(html, "html.parser")

        # テキストを翻訳
        # TODO: 並列化して高速化
        for p in tqdm(soup.find_all("p")):
            original_text: str = p.get_text()
            translated_text: str | None = self.llm_client.generate_text(
                prompt=original_text, system_prompt=self.system_prompt
            )
            if translated_text:
                p.string = translated_text
            else:
                logger.warning(f"Failed to translate paragraph: {original_text}")

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
