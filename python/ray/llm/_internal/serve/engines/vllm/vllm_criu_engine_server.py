"""gRPC server that wraps VLLMEngine in a separate process."""

import asyncio
import json
import pickle
from typing import Optional

import grpc

from ray.llm._internal.serve.core.configs.llm_config import (
    DiskMultiplexConfig,
    LLMConfig,
)
from ray.llm._internal.serve.core.configs.openai_api_models import (
    ChatCompletionRequest,
    CompletionRequest,
    DetokenizeRequest,
    EmbeddingRequest,
    ErrorResponse,
    ScoreRequest,
    TokenizeRequest,
    TranscriptionRequest,
)
from ray.llm._internal.serve.core.protocol import RawRequestInfo
from ray.llm._internal.serve.engines.vllm.vllm_engine import VLLMEngine
from ray.llm._internal.serve.observability.logging import get_logger

# Import generated gRPC code
from ray.llm._internal.serve.engines.vllm.generated import (
    vllm_criu_engine_pb2 as pb2,
    vllm_criu_engine_pb2_grpc as pb2_grpc,
)

logger = get_logger(__name__)


class VLLMEngineServicer(pb2_grpc.VLLMEngineServiceServicer):
    """gRPC servicer that wraps the VLLMEngine."""

    def __init__(self):
        """Initialize the servicer without an engine.
        
        The engine will be created when Initialize is called with llm_config.
        """
        self.engine: Optional[VLLMEngine] = None

    def _deserialize_raw_request_info(
        self, raw_request_info: Optional[pb2.RawRequestInfo]
    ) -> Optional[RawRequestInfo]:
        """Convert protobuf RawRequestInfo to domain object."""
        if raw_request_info is None:
            return None
        
        return RawRequestInfo(
            request_id=raw_request_info.request_id or None,
            headers=dict(raw_request_info.headers) if raw_request_info.headers else None,
            client_ip=raw_request_info.client_ip or None,
        )

    def _check_initialized(self):
        """Check if the engine has been initialized."""
        if self.engine is None:
            raise RuntimeError("Engine not initialized. Call Initialize first.")

    async def Initialize(self, request: pb2.InitializeRequest, context):
        """Initialize the vLLM engine with llm_config."""
        try:
            if self.engine is not None:
                logger.warning("Engine already initialized, reinitializing...")
            
            # Deserialize LLMConfig from JSON
            llm_config = LLMConfig.model_validate_json(request.llm_config_json)
            
            # Create the engine
            self.engine = VLLMEngine(llm_config)
            
            logger.info("Successfully initialized VLLMEngine from llm_config")
            return pb2.InitializeResponse(success=True)
        except Exception as e:
            logger.error(f"Error initializing engine: {e}", exc_info=True)
            return pb2.InitializeResponse(
                success=False,
                error_message=str(e),
            )

    async def Start(self, request: pb2.StartRequest, context):
        """Start the vLLM engine."""
        try:
            self._check_initialized()
            await self.engine.start()
            return pb2.StartResponse()
        except Exception as e:
            logger.error(f"Error starting engine: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def CheckHealth(self, request: pb2.HealthRequest, context):
        """Check engine health."""
        try:
            self._check_initialized()
            await self.engine.check_health()
            return pb2.HealthResponse()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def Chat(self, request: pb2.ChatRequest, context):
        """Stream chat completion responses."""
        try:
            self._check_initialized()
            chat_request = ChatCompletionRequest.model_validate_json(request.json_request)
            raw_request_info = self._deserialize_raw_request_info(request.raw_request_info)
            
            async for response in self.engine.chat(chat_request, raw_request_info):
                if isinstance(response, str):
                    yield pb2.ChatResponse(stream_chunk=response)
                elif isinstance(response, ErrorResponse):
                    yield pb2.ChatResponse(error=response.model_dump_json())
                else:
                    yield pb2.ChatResponse(final_response=response.model_dump_json())
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            error_response = ErrorResponse.from_exception(e)
            yield pb2.ChatResponse(error=error_response.model_dump_json())

    async def Completions(self, request: pb2.CompletionsRequest, context):
        """Stream completion responses."""
        try:
            self._check_initialized()
            completion_request = CompletionRequest.model_validate_json(request.json_request)
            raw_request_info = self._deserialize_raw_request_info(request.raw_request_info)
            
            async for response in self.engine.completions(completion_request, raw_request_info):
                if isinstance(response, str):
                    yield pb2.CompletionsResponse(stream_chunk=response)
                elif isinstance(response, ErrorResponse):
                    yield pb2.CompletionsResponse(error=response.model_dump_json())
                else:
                    yield pb2.CompletionsResponse(final_response=response.model_dump_json())
        except Exception as e:
            logger.error(f"Error in completions: {e}")
            error_response = ErrorResponse.from_exception(e)
            yield pb2.CompletionsResponse(error=error_response.model_dump_json())

    async def Embeddings(self, request: pb2.EmbeddingsRequest, context):
        """Generate embeddings."""
        try:
            self._check_initialized()
            embedding_request = EmbeddingRequest.model_validate_json(request.json_request)
            raw_request_info = self._deserialize_raw_request_info(request.raw_request_info)
            
            async for response in self.engine.embeddings(embedding_request, raw_request_info):
                if isinstance(response, ErrorResponse):
                    return pb2.EmbeddingsResponse(error=response.model_dump_json())
                else:
                    return pb2.EmbeddingsResponse(final_response=response.model_dump_json())
        except Exception as e:
            logger.error(f"Error in embeddings: {e}")
            error_response = ErrorResponse.from_exception(e)
            return pb2.EmbeddingsResponse(error=error_response.model_dump_json())

    async def Transcriptions(self, request: pb2.TranscriptionsRequest, context):
        """Stream transcription responses."""
        try:
            self._check_initialized()
            # Reconstruct the request with audio data
            request_dict = json.loads(request.json_request)
            # Note: We need to create a file-like object from audio_data
            # This is a simplified version - actual implementation may need a proper file wrapper
            transcription_request = TranscriptionRequest.model_validate(request_dict)
            # TODO: Set the audio file from request.audio_data
            
            raw_request_info = self._deserialize_raw_request_info(request.raw_request_info)
            
            async for response in self.engine.transcriptions(transcription_request, raw_request_info):
                if isinstance(response, str):
                    yield pb2.TranscriptionsResponse(stream_chunk=response)
                elif isinstance(response, ErrorResponse):
                    yield pb2.TranscriptionsResponse(error=response.model_dump_json())
                else:
                    yield pb2.TranscriptionsResponse(final_response=response.model_dump_json())
        except Exception as e:
            logger.error(f"Error in transcriptions: {e}")
            error_response = ErrorResponse.from_exception(e)
            yield pb2.TranscriptionsResponse(error=error_response.model_dump_json())

    async def Score(self, request: pb2.ScoreRequest, context):
        """Generate scores."""
        try:
            self._check_initialized()
            score_request = ScoreRequest.model_validate_json(request.json_request)
            raw_request_info = self._deserialize_raw_request_info(request.raw_request_info)
            
            async for response in self.engine.score(score_request, raw_request_info):
                if isinstance(response, ErrorResponse):
                    return pb2.ScoreResponse(error=response.model_dump_json())
                else:
                    return pb2.ScoreResponse(final_response=response.model_dump_json())
        except Exception as e:
            logger.error(f"Error in score: {e}")
            error_response = ErrorResponse.from_exception(e)
            return pb2.ScoreResponse(error=error_response.model_dump_json())

    async def Tokenize(self, request: pb2.TokenizeRequest, context):
        """Tokenize text."""
        try:
            self._check_initialized()
            tokenize_request = TokenizeRequest.model_validate_json(request.json_request)
            raw_request_info = self._deserialize_raw_request_info(request.raw_request_info)
            
            async for response in self.engine.tokenize(tokenize_request, raw_request_info):
                if isinstance(response, ErrorResponse):
                    return pb2.TokenizeResponse(error=response.model_dump_json())
                else:
                    return pb2.TokenizeResponse(final_response=response.model_dump_json())
        except Exception as e:
            logger.error(f"Error in tokenize: {e}")
            error_response = ErrorResponse.from_exception(e)
            return pb2.TokenizeResponse(error=error_response.model_dump_json())

    async def Detokenize(self, request: pb2.DetokenizeRequest, context):
        """Detokenize tokens."""
        try:
            self._check_initialized()
            detokenize_request = DetokenizeRequest.model_validate_json(request.json_request)
            raw_request_info = self._deserialize_raw_request_info(request.raw_request_info)
            
            async for response in self.engine.detokenize(detokenize_request, raw_request_info):
                if isinstance(response, ErrorResponse):
                    return pb2.DetokenizeResponse(error=response.model_dump_json())
                else:
                    return pb2.DetokenizeResponse(final_response=response.model_dump_json())
        except Exception as e:
            logger.error(f"Error in detokenize: {e}")
            error_response = ErrorResponse.from_exception(e)
            return pb2.DetokenizeResponse(error=error_response.model_dump_json())

    async def ResetPrefixCache(self, request: pb2.ResetPrefixCacheRequest, context):
        """Reset the prefix cache."""
        try:
            self._check_initialized()
            await self.engine.reset_prefix_cache()
            return pb2.ResetPrefixCacheResponse()
        except Exception as e:
            logger.error(f"Error resetting prefix cache: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def Sleep(self, request: pb2.SleepRequest, context):
        """Put the engine to sleep."""
        try:
            self._check_initialized()
            await self.engine.sleep(level=request.level)
            return pb2.SleepResponse()
        except Exception as e:
            logger.error(f"Error putting engine to sleep: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def Wakeup(self, request: pb2.WakeupRequest, context):
        """Wake up the engine."""
        try:
            self._check_initialized()
            tags = list(request.tags) if request.tags else None
            await self.engine.wakeup(tags=tags)
            return pb2.WakeupResponse()
        except Exception as e:
            logger.error(f"Error waking up engine: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def IsSleeping(self, request: pb2.IsSleepingRequest, context):
        """Check if engine is sleeping."""
        try:
            self._check_initialized()
            is_sleeping = await self.engine.is_sleeping()
            return pb2.IsSleepingResponse(is_sleeping=is_sleeping)
        except Exception as e:
            logger.error(f"Error checking sleep status: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def Pause(self, request: pb2.PauseRequest, context):
        """Pause the engine."""
        try:
            self._check_initialized()
            await self.engine.pause(
                wait_for_inflight_requests=request.wait_for_inflight_requests,
                clear_cache=request.clear_cache,
            )
            return pb2.PauseResponse()
        except Exception as e:
            logger.error(f"Error pausing engine: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def Resume(self, request: pb2.ResumeRequest, context):
        """Resume the engine."""
        try:
            self._check_initialized()
            await self.engine.resume()
            return pb2.ResumeResponse()
        except Exception as e:
            logger.error(f"Error resuming engine: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def IsPaused(self, request: pb2.IsPausedRequest, context):
        """Check if engine is paused."""
        try:
            self._check_initialized()
            is_paused = await self.engine.is_paused()
            return pb2.IsPausedResponse(is_paused=is_paused)
        except Exception as e:
            logger.error(f"Error checking pause status: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def StartProfile(self, request: pb2.StartProfileRequest, context):
        """Start profiling."""
        try:
            self._check_initialized()
            await self.engine.start_profile()
            return pb2.StartProfileResponse()
        except Exception as e:
            logger.error(f"Error starting profile: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def StopProfile(self, request: pb2.StopProfileRequest, context):
        """Stop profiling."""
        try:
            self._check_initialized()
            await self.engine.stop_profile()
            return pb2.StopProfileResponse()
        except Exception as e:
            logger.error(f"Error stopping profile: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def ResolveLora(self, request: pb2.ResolveLoraRequest, context):
        """Resolve and load a LoRA adapter."""
        try:
            self._check_initialized()
            disk_lora_model = DiskMultiplexConfig(
                model_id=request.model_id,
                local_path=request.local_path,
            )
            await self.engine.resolve_lora(disk_lora_model)
            return pb2.ResolveLoraResponse()
        except Exception as e:
            logger.error(f"Error resolving LoRA: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def CollectiveRpc(self, request: pb2.CollectiveRpcRequest, context):
        """Execute a collective RPC."""
        try:
            self._check_initialized()
            # Unpickle arguments
            args = tuple(pickle.loads(arg) for arg in request.args)
            kwargs = pickle.loads(request.kwargs) if request.kwargs else {}
            
            # Execute the RPC
            results = await self.engine.collective_rpc(
                method=request.method,
                timeout=request.timeout if request.HasField("timeout") else None,
                args=args,
                kwargs=kwargs,
            )
            
            # Pickle results
            pickled_results = [pickle.dumps(result) for result in results]
            
            return pb2.CollectiveRpcResponse(results=pickled_results)
        except Exception as e:
            logger.error(f"Error in collective RPC: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, str(e))


async def serve(
    host: str = "0.0.0.0",
    port: int = 50051,
    max_message_length: int = 100 * 1024 * 1024,  # 100MB
):
    """Start the gRPC server.

    The server waits for an Initialize call with llm_config before starting the engine.

    Args:
        host: Host to bind to
        port: Port to bind to
        max_message_length: Maximum gRPC message size
    """
    server = grpc.aio.server(
        options=[
            ("grpc.max_send_message_length", max_message_length),
            ("grpc.max_receive_message_length", max_message_length),
        ]
    )
    
    servicer = VLLMEngineServicer()
    pb2_grpc.add_VLLMEngineServiceServicer_to_server(servicer, server)
    
    listen_addr = f"{host}:{port}"
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting vLLM gRPC server on {listen_addr}")
    logger.info("Waiting for Initialize call with llm_config...")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        await server.stop(grace=5.0)


if __name__ == "__main__":
    import sys
    
    from argparse import ArgumentParser
    args = ArgumentParser(description="vLLM gRPC Engine Server")
    args.add_argument("--host", type=str, default="0.0.0.0")
    args.add_argument("--port", type=int, default=50051)
    parsed_args = args.parse_args()

    # Parse command line arguments for host and port
    host = parsed_args.host
    port = parsed_args.port
    
    asyncio.run(serve(host=host, port=port))