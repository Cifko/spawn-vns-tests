# type:ignore
from config import REDIRECT_DAN_WALLET_STDOUT, USE_BINARY_EXECUTABLE, REDIRECT_DAN_WALLET_WEBUI_STDOUT
import base64
import os
import platform
import requests
import subprocess
import signal
import time
from typing import Any
from common_exec import CommonExec


class JrpcDanWalletDaemon:
    def __init__(self, jrpc_url):
        self.id = 0
        self.url = jrpc_url
        self.token = None

    def call(self, method, params=[]):
        self.id += 1
        headers = None
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(self.url, json={"jsonrpc": "2.0", "method": method, "id": self.id, "params": params}, headers=headers)
        return response.json()["result"]

    def auth(self):
        resp = self.call("auth.request", [["Admin"]])
        auth_token = resp["auth_token"]
        resp = self.call("auth.accept", [auth_token])
        self.token = resp["permissions_token"]

    def keys_list(self):
        return self.call("keys.list")

    def accounts_create(
        self, name: str, signing_key_index: int = 0, custom_access_rules: Any = None, fee: int | None = None, is_default: bool = True
    ):
        return self.call("accounts.create", [name, signing_key_index, custom_access_rules, fee, is_default])

    def accounts_list(self, offset=0, limit=1):
        return self.call("accounts.list", [offset, limit])

    def transaction_submit_instruction(self, instruction):
        tx_id = self.call(
            "transactions.submit_instruction",
            {"instruction": instruction, "fee_account": "TestAccount", "dump_outputs_into": "TestAccount", "fee": 1},
        )["hash"]
        while True:
            tx = self.transaction_get(tx_id)
            status = tx["status"]
            if status != "Pending":
                if status == "Rejected":
                    raise Exception(f"Transaction rejected:{tx['transaction_failure']}")
                return tx
            time.sleep(1)

    def transaction_get(self, tx_id):
        return self.call("transactions.get", {"hash": tx_id})

    def claim_burn(self, burn: Any, account: Any):
        account = account["account"]["address"]["Component"]
        claim_proof = {
            "commitment": base64.b64encode(burn.commitment).decode("utf-8"),
            "range_proof": base64.b64encode(burn.range_proof).decode("utf-8"),
            "reciprocal_claim_public_key": base64.b64encode(burn.reciprocal_claim_public_key).decode("utf-8"),
            "ownership_proof": {
                "u": base64.b64encode(burn.ownership_proof.u).decode("utf-8"),
                "v": base64.b64encode(burn.ownership_proof.v).decode("utf-8"),
                "public_nonce": base64.b64encode(burn.ownership_proof.public_nonce).decode("utf-8"),
            },
        }
        ClaimBurnRequest = {"account": account, "claim_proof": claim_proof, "fee": 10}
        return self.call("accounts.claim_burn", ClaimBurnRequest)

    def get_balances(self, account: Any):
        return self.call("accounts.get_balances", [account["account"]["name"], True])


class DanWalletDaemon(CommonExec):
    def __init__(self, dan_wallet_id: int, indexer_jrpc_port: int, signaling_server_port: int):
        super().__init__("Dan_wallet_daemon", dan_wallet_id)
        self.json_rpc_port = super().get_port("JRPC")
        if USE_BINARY_EXECUTABLE:
            run = "tari_dan_wallet_daemon"
        else:
            run = " ".join(["cargo", "run", "--bin", "tari_dan_wallet_daemon", "--manifest-path", "../tari-dan/Cargo.toml", "--"])
        self.exec = " ".join(
            [
                run,
                "-b",
                f"dan_wallet_daemon_{dan_wallet_id}",
                "--network",
                "localnet",
                "--listen-addr",
                f"127.0.0.1:{self.json_rpc_port}",
                "--indexer_url",
                f"http://127.0.0.1:{indexer_jrpc_port}/json_rpc",
            ]
        )
        if signaling_server_port:
            self.exec = " ".join([self.exec, "--signaling_server_address", f"127.0.0.1:{signaling_server_port}"])
        self.run(REDIRECT_DAN_WALLET_STDOUT)

        # (out, err) = self.process.communicate()
        jrpc_address = f"http://127.0.0.1:{self.json_rpc_port}"
        self.jrpc_client = JrpcDanWalletDaemon(jrpc_address)
        self.http_client = DanWalletUI(self.id, jrpc_address)
        print("Waiting for dan wallet to start", end="")
        while not os.path.exists(f"dan_wallet_daemon_{dan_wallet_id}/localnet/pid"):
            print(".", end="")
            if self.process.poll() is None:
                time.sleep(1)
            else:
                raise Exception(f"DAN wallet did not start successfully: Exit code:{self.process.poll()}")
        print("done")


class DanWalletUI(CommonExec):
    def __init__(self, dan_wallet_id, daemon_jrpc_address):
        super().__init__("dan_wallet_ui", dan_wallet_id)
        if platform.system() == "Windows":
            npm = "npm.cmd"
        else:
            npm = "npm"
        self.http_port = self.get_port("HTTP")
        self.exec = " ".join(
            [npm, "--prefix", "../tari-dan/applications/tari_dan_wallet_web_ui", "run", "dev", "--", "--port", str(self.http_port)]
        )
        self.daemon_jrpc_address = daemon_jrpc_address
        self.env["VITE_DAEMON_JRPC_ADDRESS"] = daemon_jrpc_address
        self.run(REDIRECT_DAN_WALLET_WEBUI_STDOUT)
