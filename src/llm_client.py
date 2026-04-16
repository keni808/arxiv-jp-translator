from google import genai
from google.genai import types
from dotenv import load_dotenv


class GeminiClient:
    def __init__(self, model_name: str) -> None:
        """Google Gemini API クライアント

        Args:
            model_name (str): 使用するGeminiモデルの名前 (例: "gemini-2.5-flash-lite")
        """
        load_dotenv()
        self.model_name = model_name
        self.client = genai.Client()

    def generate_text(
        self, prompt: str, system_prompt: str | None = None
    ) -> str | None:
        """(同期版) プロンプトをもとにテキストを生成する関数

        Args:
            prompt (str): プロンプト
            system_prompt (str | None): システムプロンプト

        Returns:
            str | None: 生成されたテキスト。生成に失敗した場合はNoneを返す。
        """
        # システムプロンプトが指定されている場合は、GenerateContentConfigに設定
        config: types.GenerateContentConfig | None = None
        if system_prompt:
            config = types.GenerateContentConfig(system_instruction=system_prompt)

        # テキスト生成の実行
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt, config=config
        )
        if response and response.text:
            return response.text
        else:
            return None

    async def async_generate_text(
        self, prompt: str, system_prompt: str | None = None
    ) -> str | None:
        """(非同期版) プロンプトをもとにテキストを生成する関数

        Args:
            prompt (str): プロンプト
            system_prompt (str | None): システムプロンプト

        Returns:
            str | None: 生成されたテキスト。生成に失敗した場合はNoneを返す。
        """
        # システムプロンプトが指定されている場合は、GenerateContentConfigに設定
        config: types.GenerateContentConfig | None = None
        if system_prompt:
            config = types.GenerateContentConfig(system_instruction=system_prompt)

        # テキスト生成の実行
        response = await self.client.aio.models.generate_content(
            model=self.model_name, contents=prompt, config=config
        )
        if response and response.text:
            return response.text
        else:
            return None
