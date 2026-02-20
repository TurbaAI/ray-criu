#!/usr/bin/env python3
"""Compile protobuf definitions for vLLM CRIU engine gRPC interface."""

import sys
from pathlib import Path


def compile_protos():
    """Compile the vllm_criu_engine.proto file to generate Python gRPC code."""
    try:
        from grpc_tools import protoc
    except ImportError:
        print(
            "Error: grpc_tools not found. Install it with: pip install grpcio-tools",
            file=sys.stderr,
        )
        return 1
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    
    # Define paths
    proto_file = script_dir / "vllm_criu_engine.proto"
    # generated_dir = script_dir / "generated"
    generated_dir = script_dir
    
    # Ensure the proto file exists
    if not proto_file.exists():
        print(f"Error: Proto file not found at {proto_file}", file=sys.stderr)
        return 1
    
    # Create generated directory if it doesn't exist
    generated_dir.mkdir(exist_ok=True)
    
    # Create __init__.py in generated directory to make it a package
    init_file = generated_dir / "__init__.py"
    if not init_file.exists():
        init_file.touch()
    
    # Compile the proto file using protoc.main()
    try:
        result = protoc.main([
            'grpc_tools.protoc',  # Program name (argv[0])
            f'-I{script_dir}',
            f'--python_out={generated_dir}',
            f'--grpc_python_out={generated_dir}',
            f'--pyi_out={generated_dir}',  # Generate type stubs
            str(proto_file),
        ])
        
        if result == 0:
            print(f"Successfully compiled {proto_file.name}")
            print(f"Generated files in {generated_dir}")
            return 0
        else:
            print(f"Error: protoc returned exit code {result}", file=sys.stderr)
            return result
    except Exception as e:
        print(f"Error compiling proto file: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(compile_protos())
