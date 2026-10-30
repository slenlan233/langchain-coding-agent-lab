"""Legacy examples keep importable clients but fail before network use without a key."""

from langchain_openai import ChatOpenAI


class ConfiguredChatOpenAI(ChatOpenAI):
    def _check_key(self):
        if not self.openai_api_key or self.openai_api_key.get_secret_value() == "not-configured":
            raise RuntimeError("模型凭证未配置，请设置 AI_AGENT_API_KEY 或对应供应商环境变量。")

    def _generate(self, *args, **kwargs):
        self._check_key()
        return super()._generate(*args, **kwargs)

    async def _agenerate(self, *args, **kwargs):
        self._check_key()
        return await super()._agenerate(*args, **kwargs)

    def _stream(self, *args, **kwargs):
        self._check_key()
        yield from super()._stream(*args, **kwargs)

    async def _astream(self, *args, **kwargs):
        self._check_key()
        async for chunk in super()._astream(*args, **kwargs):
            yield chunk
