# -*- coding: utf-8 -*-
# type: ignore

from grpc import insecure_channel

try:
    from protos import wallet_pb2_grpc, wallet_pb2, types_pb2
except:
    print("You forgot to generate protos, run protos.sh or protos.bat")
    exit()

from ports import ports
from config import NETWORK, REDIRECT_WALLET_STDOUT, USE_BINARY_EXECUTABLE
import subprocess


class GrpcWallet:
    def __init__(self, grpc_url):
        self.address = grpc_url
        self.channel = insecure_channel(self.address)
        self.stub = wallet_pb2_grpc.WalletStub(self.channel)

    def get_identity(self):
        request = types_pb2.Empty()
        return self.stub.Identify(request)

    def get_balance(self):
        request = wallet_pb2.GetBalanceRequest()
        return self.stub.GetBalance(request)

    def burn(self, amount, claim_public_key, fee_per_gram=5):
        request = wallet_pb2.CreateBurnTransactionRequest(amount=amount, fee_per_gram=fee_per_gram, claim_public_key=claim_public_key)
        return self.stub.CreateBurnTransaction(request)


class Wallet:
    def __init__(self, base_node_address):
        self.public_address = f"/ip4/127.0.0.1/tcp/{ports.get_free_port()}"
        self.grpc_port = ports.get_free_port()
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
        if REDIRECT_WALLET_STDOUT:
            self.process = subprocess.Popen(self.exec, stdout=open("stdout/wallet_stdout.log", "a+"))
        else:
            self.process = subprocess.Popen(self.exec)
        self.grpc_client = GrpcWallet(f"127.0.0.1:{self.grpc_port}")

    def __del__(self):
        self.process.kill()
