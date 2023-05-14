# -*- coding: utf-8 -*-
# type: ignore

from grpc import insecure_channel

try:
    from protos import types_pb2, base_node_pb2_grpc
except:
    print("You forgot to generate protos, run protos.sh or protos.bat")
    exit()

from config import NETWORK, REDIRECT_BASE_NODE_STDOUT, USE_BINARY_EXECUTABLE
import os
import re
import time
from common_exec import CommonExec


class GrpcBaseNode:
    def __init__(self, grpc_url):
        self.address = grpc_url
        self.channel = insecure_channel(self.address)
        self.stub = base_node_pb2_grpc.BaseNodeStub(self.channel)

    def get_version(self):
        request = types_pb2.Empty()
        return self.stub.GetVersion(request)

    def get_mempool_stats(self):
        request = types_pb2.Empty()
        return self.stub.GetMempoolStats(request)

    def get_mempool_size(self):
        return self.get_mempool_stats().unconfirmed_txs

    def get_identity(self):
        request = types_pb2.Empty()
        return self.stub.Identify(request)

    def get_public_key(self):
        return self.get_identity().public_key

    def get_public_addresses(self):
        return self.get_identity().public_addresses

    def get_tip_info(self):
        request = types_pb2.Empty()
        return self.stub.GetTipInfo(request)

    def get_tip(self) -> int:
        return self.get_tip_info().metadata.height_of_longest_chain


class BaseNode(CommonExec):
    def __init__(self):
        super().__init__("Base_node")
        self.public_port = self.get_port("public_address")
        self.public_address = f"/ip4/127.0.0.1/tcp/{self.public_port}"
        self.grpc_port = self.get_port("GRPC")
        if USE_BINARY_EXECUTABLE:
            run = "tari_base_node"
        else:
            run = " ".join(["cargo", "run", "--bin", "tari_base_node", "--manifest-path", "../tari/Cargo.toml", "--"])
        self.exec = " ".join(
            [
                run,
                "-b",
                "base_node",
                "-n",
                "--network",
                NETWORK,
                "-p",
                "base_node.p2p.transport.type=tcp",
                "-p",
                f"base_node.p2p.transport.tcp.listener_address={self.public_address}",
                "-p",
                f"base_node.p2p.public_addresses={self.public_address}",
                "-p",
                f"base_node.grpc_address=/ip4/127.0.0.1/tcp/{self.grpc_port}",
                "-p",
                f"base_node.grpc_enabled=true",
                "-p",
                "base_node.p2p.allow_test_addresses=true",
                "-p",
                f'{NETWORK}.p2p.seeds.peer_seeds=""',
                "-p",
                "base_node.metadata_auto_ping_interval=3",
            ]
        )
        self.run(REDIRECT_BASE_NODE_STDOUT)
        # Sometimes it takes a while to establish the grpc connection
        while True:
            try:
                self.grpc_client = GrpcBaseNode(f"127.0.0.1:{self.grpc_port}")
                self.grpc_client.get_version()
                break
            except:
                pass
            time.sleep(0.3)

    def get_address(self):
        base_node_id_file_name = f"./base_node/{NETWORK}/config/base_node_id.json"
        while not os.path.exists(base_node_id_file_name):
            time.sleep(0.3)
        f = open(base_node_id_file_name, "rt")
        content = "".join(f.readlines())
        node_id, public_key, public_address = re.search(
            r'"node_id":"(.*?)","public_key":"(.*?)".*"public_addresses":\["(.*?)"', content
        ).groups()
        public_address = public_address.replace("\\/", "/")
        return f"{public_key}::{public_address}"
