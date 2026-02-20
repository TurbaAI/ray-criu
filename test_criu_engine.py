import asyncio
import sys
import time
from typing import AsyncGenerator, Optional
from unittest.mock import patch

import numpy as np
import pytest

from ray import serve
from ray.llm._internal.serve.core.configs.llm_config import (
    LLMConfig,
    LoraConfig,
    ModelLoadingConfig,
)
from ray.llm._internal.serve.core.server.llm_server import LLMServer
from ray.llm._internal.serve.engines.vllm.vllm_engine import VLLMEngine
from ray.llm._internal.serve.engines.vllm.vllm_criu_engine import VLLMCRIUEngine
from ray.llm.tests.serve.utils.testing_utils import LLMResponseValidator


TEST_MODEL = "HuggingFaceTB/SmolLM2-135M-Instruct"


LLM_CONFIG = LLMConfig(
    model_loading_config=ModelLoadingConfig(
        model_id=TEST_MODEL,
        model_source=TEST_MODEL,
    ),
    deployment_config={
        "autoscaling_config": {
            "min_replicas": 1,
            "max_replicas": 1,
        },
        "max_ongoing_requests": 8192,
    },
    engine_kwargs={
        "trust_remote_code": True,
        "dtype": "bfloat16",
        "enable_prefix_caching": True,
        "max_model_len": 512,
    },
)

# @pytest.mark.parametrize("api_type", ["chat", "completion"])
# @pytest.mark.parametrize("stream", [False, True])
# @pytest.mark.parametrize("max_tokens", [5])
# @pytest.mark.asyncio
async def test_unified_llm_engine(
    mock_llm_config,
    mock_chat_request,
    mock_completion_request,
    api_type: str = "completion",
    stream: bool = False,
    max_tokens: int = 5,
):
    """Unified test for both chat and completion APIs, streaming and non-streaming."""
    # Create and start the engine
    engine = VLLMEngine(mock_llm_config)
    print("Starting engine...")
    await engine.start()
    print("Engine started successfully")

    # Create request based on API type
    if api_type == "chat":
        request = mock_chat_request
        response_generator = engine.chat(request)
    elif api_type == "completion":
        request = mock_completion_request
        print("Sending completion request...")
        response_generator = engine.completions(request)
        print("Received response generator")

    print(
        f"\n\n_____ {api_type.upper()} ({'STREAMING' if stream else 'NON-STREAMING'}) max_tokens={max_tokens} _____\n\n"
    )

    if stream:
        # Collect streaming chunks
        chunks = []
        async for chunk in response_generator:
            assert isinstance(chunk, str)
            chunks.append(chunk)

        # Validate streaming response
        LLMResponseValidator.validate_streaming_chunks(chunks, api_type, max_tokens)
    else:
        # Validate non-streaming response
        async for response in response_generator:
            LLMResponseValidator.validate_non_streaming_response(
                response, api_type, max_tokens
            )


if __name__ == "__main__":
    asyncio.run(test_unified_llm_engine(LLM_CONFIG, "asdf", "asdf"))