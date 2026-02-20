import subprocess
import sys
import time
import json
import pickle
from typing import Any, AsyncGenerator, List, Optional, Union

import grpc

from ray.llm._internal.serve.core.configs.llm_config import (
    DiskMultiplexConfig,
    LLMConfig,
)
from ray.llm._internal.serve.core.configs.openai_api_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    DetokenizeRequest,
    DetokenizeResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ErrorResponse,
    ScoreRequest,
    ScoreResponse,
    TokenizeRequest,
    TokenizeResponse,
    TranscriptionRequest,
    TranscriptionResponse,
)
from ray.llm._internal.serve.core.engine.protocol import LLMEngine
from ray.llm._internal.serve.core.protocol import RawRequestInfo
from ray.llm._internal.serve.observability.logging import get_logger

# Import generated gRPC code
from ray.llm._internal.serve.engines.vllm import (
    vllm_criu_engine_pb2 as pb2,
    vllm_criu_engine_pb2_grpc as pb2_grpc,
)

logger = get_logger(__name__)


class VLLMCRIUEngine(LLMEngine):
    """gRPC client that wraps VLLMEngine in a separate process."""

    def __init__(
        self,
        llm_config: LLMConfig,
        grpc_server_address: str = "localhost:50051",
        max_message_length: int = 100 * 1024 * 1024,  # 100MB
    ):
        """Create a gRPC client for VLLMEngine.

        Args:
            llm_config: The llm configuration for this engine
            grpc_server_address: Address of the gRPC server (host:port)
            max_message_length: Maximum gRPC message size in bytes
        """
        super().__init__(llm_config)
        self.llm_config = llm_config
        self.grpc_server_address = grpc_server_address
        
        # Configure gRPC channel options for large messages
        self.channel_options = [
            ("grpc.max_send_message_length", max_message_length),
            ("grpc.max_receive_message_length", max_message_length),
        ]
        
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[pb2_grpc.VLLMEngineServiceStub] = None
        self.server_process: Optional[subprocess.Popen] = None  # Will hold the subprocess.Popen object for the server
        self._initialized = False

    async def _ensure_connected(self):
        """Ensure gRPC channel is connected."""
        if self.server_process is None:
            # start the new server in a new process
            try:
                host, port = self.grpc_server_address.split(":")
                self.server_process = subprocess.Popen([
                    sys.executable, "-m", 
                    "ray.llm._internal.serve.engines.vllm.vllm_criu_engine_server",
                    "--host", host,
                    "--port", port,])
            except Exception as e:
                logger.exception(f"Failed to start vLLM gRPC server")
                raise
            time.sleep(5)  # Wait for the server to start

        if self.channel is None:
            logger.info(f"Connecting to vLLM gRPC server at {self.grpc_server_address}...")
            self.channel = grpc.aio.insecure_channel(
                self.grpc_server_address,
                options=self.channel_options,
            )
            self.stub = pb2_grpc.VLLMEngineServiceStub(self.channel)
            logger.info(f"Connected to vLLM gRPC server at {self.grpc_server_address}")

    async def _ensure_initialized(self):
        """Ensure the engine is initialized with llm_config."""
        await self._ensure_connected()
        
        if not self._initialized:
            # Serialize LLMConfig to JSON
            llm_config_json = self.llm_config.model_dump_json()
            
            request = pb2.InitializeRequest(llm_config_json=llm_config_json)
            response = await self.stub.Initialize(request)
            
            if not response.success:
                error_msg = response.error_message or "Unknown initialization error"
                raise RuntimeError(f"Failed to initialize vLLM engine: {error_msg}")
            
            self._initialized = True
            logger.info("Successfully initialized vLLM engine with llm_config via gRPC")

    async def start(self) -> None:
        """Start the vLLM engine."""
        logger.info("Trying to connect to server gRPC...")
        await self._ensure_initialized()
        request = pb2.StartRequest()
        logger.info("Starting vLLM engine via gRPC...")
        await self.stub.Start(request)
        logger.info("Started vLLM engine via gRPC")

    async def check_health(self) -> None:
        """Check engine health."""
        await self._ensure_initialized()
        request = pb2.HealthRequest()
        await self.stub.CheckHealth(request)

    def _serialize_raw_request_info(
        self, raw_request_info: Optional[RawRequestInfo]
    ) -> Optional[pb2.RawRequestInfo]:
        """Convert RawRequestInfo to protobuf message."""
        if raw_request_info is None:
            return None
        
        return pb2.RawRequestInfo(
            request_id=raw_request_info.request_id or "",
            headers=raw_request_info.headers or {},
            client_ip=raw_request_info.client_ip or "",
        )

    async def chat(
        self,
        request: ChatCompletionRequest,
        raw_request_info: Optional[RawRequestInfo] = None,
    ) -> AsyncGenerator[Union[str, ChatCompletionResponse, ErrorResponse], None]:
        """Stream chat completion responses."""
        await self._ensure_initialized()
        
        grpc_request = pb2.ChatRequest(
            json_request=request.model_dump_json(),
            raw_request_info=self._serialize_raw_request_info(raw_request_info),
        )
        
        async for response in self.stub.Chat(grpc_request):
            if response.HasField("stream_chunk"):
                yield response.stream_chunk
            elif response.HasField("final_response"):
                yield ChatCompletionResponse.model_validate_json(response.final_response)
            elif response.HasField("error"):
                yield ErrorResponse.model_validate_json(response.error)

    async def completions(
        self,
        request: CompletionRequest,
        raw_request_info: Optional[RawRequestInfo] = None,
    ) -> AsyncGenerator[Union[str, CompletionResponse, ErrorResponse], None]:
        """Stream completion responses."""
        await self._ensure_initialized()
        
        grpc_request = pb2.CompletionsRequest(
            json_request=request.model_dump_json(),
            raw_request_info=self._serialize_raw_request_info(raw_request_info),
        )
        
        async for response in self.stub.Completions(grpc_request):
            if response.HasField("stream_chunk"):
                yield response.stream_chunk
            elif response.HasField("final_response"):
                yield CompletionResponse.model_validate_json(response.final_response)
            elif response.HasField("error"):
                yield ErrorResponse.model_validate_json(response.error)

    async def embeddings(
        self,
        request: EmbeddingRequest,
        raw_request_info: Optional[RawRequestInfo] = None,
    ) -> AsyncGenerator[Union[EmbeddingResponse, ErrorResponse], None]:
        """Generate embeddings."""
        await self._ensure_initialized()
        
        grpc_request = pb2.EmbeddingsRequest(
            json_request=request.model_dump_json(),
            raw_request_info=self._serialize_raw_request_info(raw_request_info),
        )
        
        response = await self.stub.Embeddings(grpc_request)
        if response.HasField("final_response"):
            yield EmbeddingResponse.model_validate_json(response.final_response)
        elif response.HasField("error"):
            yield ErrorResponse.model_validate_json(response.error)

    async def transcriptions(
        self,
        request: TranscriptionRequest,
        raw_request_info: Optional[RawRequestInfo] = None,
    ) -> AsyncGenerator[Union[str, TranscriptionResponse, ErrorResponse], None]:
        """Stream transcription responses."""
        await self._ensure_initialized()
        
        # Read audio data from the file
        audio_data = await request.file.read()
        
        # Create a copy of request without the file for JSON serialization
        request_dict = request.model_dump(exclude={"file"})
        
        grpc_request = pb2.TranscriptionsRequest(
            audio_data=audio_data,
            json_request=json.dumps(request_dict),
            raw_request_info=self._serialize_raw_request_info(raw_request_info),
        )
        
        async for response in self.stub.Transcriptions(grpc_request):
            if response.HasField("stream_chunk"):
                yield response.stream_chunk
            elif response.HasField("final_response"):
                yield TranscriptionResponse.model_validate_json(response.final_response)
            elif response.HasField("error"):
                yield ErrorResponse.model_validate_json(response.error)

    async def score(
        self,
        request: ScoreRequest,
        raw_request_info: Optional[RawRequestInfo] = None,
    ) -> AsyncGenerator[Union[ScoreResponse, ErrorResponse], None]:
        """Generate scores."""
        await self._ensure_initialized()
        
        grpc_request = pb2.ScoreRequest(
            json_request=request.model_dump_json(),
            raw_request_info=self._serialize_raw_request_info(raw_request_info),
        )
        
        response = await self.stub.Score(grpc_request)
        if response.HasField("final_response"):
            yield ScoreResponse.model_validate_json(response.final_response)
        elif response.HasField("error"):
            yield ErrorResponse.model_validate_json(response.error)

    async def tokenize(
        self,
        request: TokenizeRequest,
        raw_request_info: Optional[RawRequestInfo] = None,
    ) -> AsyncGenerator[Union[TokenizeResponse, ErrorResponse], None]:
        """Tokenize text."""
        await self._ensure_initialized()
        
        grpc_request = pb2.TokenizeRequest(
            json_request=request.model_dump_json(),
            raw_request_info=self._serialize_raw_request_info(raw_request_info),
        )
        
        response = await self.stub.Tokenize(grpc_request)
        if response.HasField("final_response"):
            yield TokenizeResponse.model_validate_json(response.final_response)
        elif response.HasField("error"):
            yield ErrorResponse.model_validate_json(response.error)

    async def detokenize(
        self,
        request: DetokenizeRequest,
        raw_request_info: Optional[RawRequestInfo] = None,
    ) -> AsyncGenerator[Union[DetokenizeResponse, ErrorResponse], None]:
        """Detokenize tokens."""
        await self._ensure_initialized()
        
        grpc_request = pb2.DetokenizeRequest(
            json_request=request.model_dump_json(),
            raw_request_info=self._serialize_raw_request_info(raw_request_info),
        )
        
        response = await self.stub.Detokenize(grpc_request)
        if response.HasField("final_response"):
            yield DetokenizeResponse.model_validate_json(response.final_response)
        elif response.HasField("error"):
            yield ErrorResponse.model_validate_json(response.error)

    async def reset_prefix_cache(self) -> None:
        """Reset the prefix cache."""
        await self._ensure_initialized()
        request = pb2.ResetPrefixCacheRequest()
        await self.stub.ResetPrefixCache(request)

    async def sleep(self, **kwargs: Any) -> None:
        """Put the vLLM engine to sleep."""
        await self._ensure_initialized()
        level = kwargs.get("level", 1)
        request = pb2.SleepRequest(level=level)
        await self.stub.Sleep(request)

    async def wakeup(self, **kwargs: Any) -> None:
        """Wake up the vLLM engine from sleep mode."""
        await self._ensure_initialized()
        tags = kwargs.get("tags", [])
        request = pb2.WakeupRequest(tags=tags or [])
        await self.stub.Wakeup(request)

    async def is_sleeping(self) -> bool:
        """Check whether the vLLM engine is currently sleeping."""
        await self._ensure_initialized()
        request = pb2.IsSleepingRequest()
        response = await self.stub.IsSleeping(request)
        return response.is_sleeping

    async def pause(self, **kwargs: Any) -> None:
        """Pause generation on the vLLM engine."""
        await self._ensure_initialized()
        request = pb2.PauseRequest(
            wait_for_inflight_requests=kwargs.get("wait_for_inflight_requests", False),
            clear_cache=kwargs.get("clear_cache", True),
        )
        await self.stub.Pause(request)

    async def resume(self, **kwargs: Any) -> None:
        """Resume generation on the vLLM engine after pause."""
        await self._ensure_initialized()
        request = pb2.ResumeRequest()
        await self.stub.Resume(request)

    async def is_paused(self) -> bool:
        """Check whether the vLLM engine is currently paused."""
        await self._ensure_initialized()
        request = pb2.IsPausedRequest()
        response = await self.stub.IsPaused(request)
        return response.is_paused

    async def start_profile(self) -> None:
        """Start profiling."""
        await self._ensure_initialized()
        request = pb2.StartProfileRequest()
        await self.stub.StartProfile(request)

    async def stop_profile(self) -> None:
        """Stop profiling."""
        await self._ensure_initialized()
        request = pb2.StopProfileRequest()
        await self.stub.StopProfile(request)

    async def resolve_lora(self, disk_lora_model: DiskMultiplexConfig):
        """Resolve and load a LoRA adapter."""
        await self._ensure_initialized()
        request = pb2.ResolveLoraRequest(
            model_id=disk_lora_model.model_id,
            local_path=disk_lora_model.local_path,
        )
        await self.stub.ResolveLora(request)

    async def collective_rpc(
        self,
        method: str,
        timeout: Optional[float] = None,
        args: tuple = (),
        kwargs: Optional[dict] = None,
    ) -> list:
        """Execute a collective RPC call on all vLLM workers."""
        await self._ensure_initialized()
        
        # Pickle the arguments for transmission
        pickled_args = [pickle.dumps(arg) for arg in args]
        pickled_kwargs = pickle.dumps(kwargs or {})
        
        request = pb2.CollectiveRpcRequest(
            method=method,
            timeout=timeout,
            args=pickled_args,
            kwargs=pickled_kwargs,
        )
        
        response = await self.stub.CollectiveRpc(request)
        
        # Unpickle the results
        return [pickle.loads(result) for result in response.results]

    async def close(self):
        """Close the gRPC channel."""
        if self.channel is not None:
            logger.info("Closing gRPC connection to vLLM engine...")
            await self.channel.close()
            self.channel = None
            self.stub = None
            self._initialized = False
            logger.info("Closed gRPC connection to vLLM engine")
        
        if self.server_process is not None:
            logger.info("Terminating vLLM gRPC server process...")
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
            logger.info("Terminated vLLM gRPC server process")

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_initialized()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
