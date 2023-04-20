#! /bin/bash
pip install grpcio-tools
python3 -m grpc_tools.protoc --proto_path ../tari/applications/tari_app_grpc/proto/  --python_out=./protos --grpc_python_out=./protos ../tari/applications/tari_app_grpc/proto/*.proto 
