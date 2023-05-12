# -*- coding: utf-8 -*-
# type: ignore

from grpc import insecure_channel

try:
    from protos import wallet_pb2_grpc, wallet_pb2, types_pb2
except:
    print("You forgot to generate protos, run protos.sh or protos.bat")
    exit()

from config import NETWORK, REDIRECT_WALLET_STDOUT, USE_BINARY_EXECUTABLE
from typing import Any
from common_exec import CommonExec


class GrpcWallet:
    def __init__(self, grpc_url):
        self.address = grpc_url
        self.channel = insecure_channel(self.address)
        self.stub = wallet_pb2_grpc.WalletStub(self.channel)

    def get_version(self):
        request = types_pb2.Empty()
        return self.stub.GetVersion(request)

    def get_identity(self):
        request = types_pb2.Empty()
        return self.stub.Identify(request)

    def get_balance(self):
        request = wallet_pb2.GetBalanceRequest()
        return self.stub.GetBalance(request)

    def burn(self, amount: int, claim_public_key: bytes, fee_per_gram: int = 5) -> Any:
        print("amount", amount, type(amount))
        print("claim_public_key", claim_public_key, type(claim_public_key))
        print("fee_per_gram", fee_per_gram, type(fee_per_gram))
        request = wallet_pb2.CreateBurnTransactionRequest(amount=amount, fee_per_gram=fee_per_gram, claim_public_key=claim_public_key)
        print(request)
        return self.stub.CreateBurnTransaction(request)


class Wallet(CommonExec):
    def __init__(self, base_node_address):
        super().__init__("Wallet")
        self.public_port = self.get_port("public_address")
        self.public_address = f"/ip4/127.0.0.1/tcp/{self.public_port}"
        self.grpc_port = self.get_port("GRPC")
        if USE_BINARY_EXECUTABLE:
            run = "tari_console_wallet"
        else:
            run = " ".join(["cargo", "run", "--bin", "tari_console_wallet", "--manifest-path", "../tari/Cargo.toml", "--"])
        self.exec = " ".join(
            [
                run,
                "-b",
                "wallet",
                "-n",
                "--network",
                NETWORK,
                "--enable-grpc",
                "--password",
                "a",
                "-p",
                "wallet.p2p.transport.type=tcp",
                "-p",
                f"wallet.custom_base_node={base_node_address}",
                "-p",
                f"wallet.grpc_address=/ip4/127.0.0.1/tcp/{self.grpc_port}",
                "-p",
                f"wallet.p2p.transport.tcp.listener_address={self.public_address}",
                "-p",
                f"wallet.p2p.public_addresses={self.public_address}",
                "-p",
                "wallet.p2p.allow_test_addresses=true",
                "-p",
                f'{NETWORK}.p2p.seeds.peer_seeds=""',
            ]
        )
        self.run(REDIRECT_WALLET_STDOUT)
        # Sometimes it takes a while to establish the grpc connection
        while True:
            try:
                self.grpc_client = GrpcWallet(f"127.0.0.1:{self.grpc_port}")
                self.grpc_client.get_version()
                break
            except:
                pass
            time.sleep(0.3)
