import os
from typing import Protocol

import httpx
from google import genai
from google.genai import types
from dotenv import load_dotenv


class LLMClient(Protocol):
    def generate_text(
        self, prompt: str, system_prompt: str | None = None
    ) -> str | None:
        """(同期版) プロンプトをもとにテキストを生成する関数

        Args:
            prompt (str): プロンプト
            system_prompt (str | None): システムプロンプト

        Returns:
            str | None: 生成されたテキスト。応答が空の場合はNoneを返す。
        """
        ...

    async def async_generate_text(
        self, prompt: str, system_prompt: str | None = None
    ) -> str | None:
        """(非同期版) プロンプトをもとにテキストを生成する関数

        Args:
            prompt (str): プロンプト
            system_prompt (str | None): システムプロンプト

        Returns:
            str | None: 生成されたテキスト。応答が空の場合はNoneを返す。
        """
        ...

    def close(self) -> None:
        """(同期版) クライアントの接続を閉じる関数"""
        ...

    async def aclose(self) -> None:
        """(非同期版) クライアントの接続を閉じる関数"""
        ...


class GeminiClient(LLMClient):
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

    def close(self) -> None:
        """(同期版) クライアントの接続を閉じる関数"""
        self.client.close()

    async def aclose(self) -> None:
        """(非同期版) クライアントの接続を閉じる関数"""
        await self.client.aio.aclose()


class SarashinaClient(LLMClient):
    def __init__(self, model_name: str) -> None:
        """Sarashina Chat Completions API クライアント

        Args:
            model_name (str): 使用するSarashinaモデルの名前 (例: "sarashina3-nano")
        """
        load_dotenv()
        self.model_name = model_name
        headers = {"Authorization": f"Bearer {os.environ['SARASHINA_API_KEY']}"}
        self.client = httpx.Client(
            base_url="https://api.sarashina.ai/v1/",
            headers=headers,
            timeout=120.0,
        )
        self.async_client = httpx.AsyncClient(
            base_url="https://api.sarashina.ai/v1/",
            headers=headers,
            timeout=120.0,
        )

    def generate_text(
        self, prompt: str, system_prompt: str | None = None
    ) -> str | None:
        """(同期版) プロンプトをもとにテキストを生成する関数

        Args:
            prompt (str): プロンプト
            system_prompt (str | None): システムプロンプト

        Returns:
            str | None: 生成されたテキスト。応答が空の場合はNoneを返す。
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.post(
            "chat/completions",
            json={"model": self.model_name, "messages": messages},
        )
        response.raise_for_status()
        choice = response.json()["choices"][0]
        if choice["finish_reason"] != "stop":
            raise RuntimeError(
                f"Sarashinaの生成が正常に完了しませんでした: {choice['finish_reason']}"
            )
        text: str | None = choice["message"]["content"]
        return text or None

    async def async_generate_text(
        self, prompt: str, system_prompt: str | None = None
    ) -> str | None:
        """(非同期版) プロンプトをもとにテキストを生成する関数

        Args:
            prompt (str): プロンプト
            system_prompt (str | None): システムプロンプト

        Returns:
            str | None: 生成されたテキスト。応答が空の場合はNoneを返す。
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.async_client.post(
            "chat/completions",
            json={"model": self.model_name, "messages": messages},
        )
        response.raise_for_status()
        choice = response.json()["choices"][0]
        if choice["finish_reason"] != "stop":
            raise RuntimeError(
                f"Sarashinaの生成が正常に完了しませんでした: {choice['finish_reason']}"
            )
        text: str | None = choice["message"]["content"]
        return text or None

    def close(self) -> None:
        """(同期版) クライアントの接続を閉じる関数"""
        self.client.close()

    async def aclose(self) -> None:
        """(非同期版) クライアントの接続を閉じる関数"""
        await self.async_client.aclose()
