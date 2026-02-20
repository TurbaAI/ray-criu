from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RawRequestInfo(_message.Message):
    __slots__ = ("request_id", "headers", "client_ip")
    class HeadersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    HEADERS_FIELD_NUMBER: _ClassVar[int]
    CLIENT_IP_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    headers: _containers.ScalarMap[str, str]
    client_ip: str
    def __init__(self, request_id: _Optional[str] = ..., headers: _Optional[_Mapping[str, str]] = ..., client_ip: _Optional[str] = ...) -> None: ...

class InitializeRequest(_message.Message):
    __slots__ = ("llm_config_json",)
    LLM_CONFIG_JSON_FIELD_NUMBER: _ClassVar[int]
    llm_config_json: str
    def __init__(self, llm_config_json: _Optional[str] = ...) -> None: ...

class InitializeResponse(_message.Message):
    __slots__ = ("success", "error_message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error_message: str
    def __init__(self, success: bool = ..., error_message: _Optional[str] = ...) -> None: ...

class StartRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StartResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ChatRequest(_message.Message):
    __slots__ = ("json_request", "raw_request_info")
    JSON_REQUEST_FIELD_NUMBER: _ClassVar[int]
    RAW_REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    json_request: str
    raw_request_info: RawRequestInfo
    def __init__(self, json_request: _Optional[str] = ..., raw_request_info: _Optional[_Union[RawRequestInfo, _Mapping]] = ...) -> None: ...

class ChatResponse(_message.Message):
    __slots__ = ("stream_chunk", "final_response", "error")
    STREAM_CHUNK_FIELD_NUMBER: _ClassVar[int]
    FINAL_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    stream_chunk: str
    final_response: str
    error: str
    def __init__(self, stream_chunk: _Optional[str] = ..., final_response: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class CompletionsRequest(_message.Message):
    __slots__ = ("json_request", "raw_request_info")
    JSON_REQUEST_FIELD_NUMBER: _ClassVar[int]
    RAW_REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    json_request: str
    raw_request_info: RawRequestInfo
    def __init__(self, json_request: _Optional[str] = ..., raw_request_info: _Optional[_Union[RawRequestInfo, _Mapping]] = ...) -> None: ...

class CompletionsResponse(_message.Message):
    __slots__ = ("stream_chunk", "final_response", "error")
    STREAM_CHUNK_FIELD_NUMBER: _ClassVar[int]
    FINAL_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    stream_chunk: str
    final_response: str
    error: str
    def __init__(self, stream_chunk: _Optional[str] = ..., final_response: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class EmbeddingsRequest(_message.Message):
    __slots__ = ("json_request", "raw_request_info")
    JSON_REQUEST_FIELD_NUMBER: _ClassVar[int]
    RAW_REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    json_request: str
    raw_request_info: RawRequestInfo
    def __init__(self, json_request: _Optional[str] = ..., raw_request_info: _Optional[_Union[RawRequestInfo, _Mapping]] = ...) -> None: ...

class EmbeddingsResponse(_message.Message):
    __slots__ = ("final_response", "error")
    FINAL_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    final_response: str
    error: str
    def __init__(self, final_response: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class TranscriptionsRequest(_message.Message):
    __slots__ = ("audio_data", "json_request", "raw_request_info")
    AUDIO_DATA_FIELD_NUMBER: _ClassVar[int]
    JSON_REQUEST_FIELD_NUMBER: _ClassVar[int]
    RAW_REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    audio_data: bytes
    json_request: str
    raw_request_info: RawRequestInfo
    def __init__(self, audio_data: _Optional[bytes] = ..., json_request: _Optional[str] = ..., raw_request_info: _Optional[_Union[RawRequestInfo, _Mapping]] = ...) -> None: ...

class TranscriptionsResponse(_message.Message):
    __slots__ = ("stream_chunk", "final_response", "error")
    STREAM_CHUNK_FIELD_NUMBER: _ClassVar[int]
    FINAL_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    stream_chunk: str
    final_response: str
    error: str
    def __init__(self, stream_chunk: _Optional[str] = ..., final_response: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class ScoreRequest(_message.Message):
    __slots__ = ("json_request", "raw_request_info")
    JSON_REQUEST_FIELD_NUMBER: _ClassVar[int]
    RAW_REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    json_request: str
    raw_request_info: RawRequestInfo
    def __init__(self, json_request: _Optional[str] = ..., raw_request_info: _Optional[_Union[RawRequestInfo, _Mapping]] = ...) -> None: ...

class ScoreResponse(_message.Message):
    __slots__ = ("final_response", "error")
    FINAL_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    final_response: str
    error: str
    def __init__(self, final_response: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class TokenizeRequest(_message.Message):
    __slots__ = ("json_request", "raw_request_info")
    JSON_REQUEST_FIELD_NUMBER: _ClassVar[int]
    RAW_REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    json_request: str
    raw_request_info: RawRequestInfo
    def __init__(self, json_request: _Optional[str] = ..., raw_request_info: _Optional[_Union[RawRequestInfo, _Mapping]] = ...) -> None: ...

class TokenizeResponse(_message.Message):
    __slots__ = ("final_response", "error")
    FINAL_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    final_response: str
    error: str
    def __init__(self, final_response: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class DetokenizeRequest(_message.Message):
    __slots__ = ("json_request", "raw_request_info")
    JSON_REQUEST_FIELD_NUMBER: _ClassVar[int]
    RAW_REQUEST_INFO_FIELD_NUMBER: _ClassVar[int]
    json_request: str
    raw_request_info: RawRequestInfo
    def __init__(self, json_request: _Optional[str] = ..., raw_request_info: _Optional[_Union[RawRequestInfo, _Mapping]] = ...) -> None: ...

class DetokenizeResponse(_message.Message):
    __slots__ = ("final_response", "error")
    FINAL_RESPONSE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    final_response: str
    error: str
    def __init__(self, final_response: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class ResetPrefixCacheRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResetPrefixCacheResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SleepRequest(_message.Message):
    __slots__ = ("level",)
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    level: int
    def __init__(self, level: _Optional[int] = ...) -> None: ...

class SleepResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class WakeupRequest(_message.Message):
    __slots__ = ("tags",)
    TAGS_FIELD_NUMBER: _ClassVar[int]
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, tags: _Optional[_Iterable[str]] = ...) -> None: ...

class WakeupResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IsSleepingRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IsSleepingResponse(_message.Message):
    __slots__ = ("is_sleeping",)
    IS_SLEEPING_FIELD_NUMBER: _ClassVar[int]
    is_sleeping: bool
    def __init__(self, is_sleeping: bool = ...) -> None: ...

class PauseRequest(_message.Message):
    __slots__ = ("wait_for_inflight_requests", "clear_cache")
    WAIT_FOR_INFLIGHT_REQUESTS_FIELD_NUMBER: _ClassVar[int]
    CLEAR_CACHE_FIELD_NUMBER: _ClassVar[int]
    wait_for_inflight_requests: bool
    clear_cache: bool
    def __init__(self, wait_for_inflight_requests: bool = ..., clear_cache: bool = ...) -> None: ...

class PauseResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResumeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResumeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IsPausedRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IsPausedResponse(_message.Message):
    __slots__ = ("is_paused",)
    IS_PAUSED_FIELD_NUMBER: _ClassVar[int]
    is_paused: bool
    def __init__(self, is_paused: bool = ...) -> None: ...

class StartProfileRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StartProfileResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StopProfileRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StopProfileResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResolveLoraRequest(_message.Message):
    __slots__ = ("model_id", "local_path")
    MODEL_ID_FIELD_NUMBER: _ClassVar[int]
    LOCAL_PATH_FIELD_NUMBER: _ClassVar[int]
    model_id: str
    local_path: str
    def __init__(self, model_id: _Optional[str] = ..., local_path: _Optional[str] = ...) -> None: ...

class ResolveLoraResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CollectiveRpcRequest(_message.Message):
    __slots__ = ("method", "timeout", "args", "kwargs")
    METHOD_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    KWARGS_FIELD_NUMBER: _ClassVar[int]
    method: str
    timeout: float
    args: _containers.RepeatedScalarFieldContainer[bytes]
    kwargs: bytes
    def __init__(self, method: _Optional[str] = ..., timeout: _Optional[float] = ..., args: _Optional[_Iterable[bytes]] = ..., kwargs: _Optional[bytes] = ...) -> None: ...

class CollectiveRpcResponse(_message.Message):
    __slots__ = ("results",)
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, results: _Optional[_Iterable[bytes]] = ...) -> None: ...
