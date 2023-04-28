# type:ignore
from ports import ports
import requests
import base64
import subprocess
from config import REDIRECT_DAN_WALLET_STDOUT, USE_BINARY_EXECUTABLE


class JrpcDanWalletDaemon:
    def __init__(self, jrpc_url):
        self.id = 0
        self.url = jrpc_url
        self.token = None

    def internal_call(self, method, params=[]):
        self.id += 1
        headers = None
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(self.url, json={"jsonrpc": "2.0", "method": method, "id": self.id, "params": params}, headers=headers)
        return response.json()["result"]

    def call(self, method, params=[]):
        if self.token == None:
            self.token = self.internal_call("auth.login")
        return self.internal_call(method, params)

    def keys_list(self):
        return self.call("keys.list")

    def accounts_create(self, name, signing_key_index=0, custom_access_rules=None, fee=None, is_default=True):
        return self.call("accounts.create", [name, signing_key_index, custom_access_rules, fee, is_default])

    def accounts_list(self, offset=0, limit=1):
        return self.call("accounts.list", [offset, limit])

    def claim_burn(self, burn, account):
        account = "".join("%02X" % x for x in account["account"]["address"]["Component"]["@@TAGGED@@"][1])
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

    def get_balances(self, account):
        return self.call("accounts.get_balances", [account["account"]["name"]])


class DanWalletDaemon:
    def __init__(self, dan_wallet_id, validator_node_endpoint, signaling_server_addr=None):
        self.json_rpc_port = ports.get_free_port()
        self.id = dan_wallet_id
        if USE_BINARY_EXECUTABLE:
            run = "tari_dan_wallet_daemon"
        else:
            run = " ".join(["cargo", "run", "--bin", "tari_dan_wallet_daemon", "--manifest-path", "../tari-dan/Cargo.toml", "--"])
        self.exec = " ".join(
            [
                run,
                "-b",
                f"dan_wallet_daemon{dan_wallet_id}",
                "--network",
                "localnet",
                "--listen-addr",
                f"127.0.0.1:{self.json_rpc_port}",
                "--validator-node-endpoint",
                f"http://127.0.0.1:{validator_node_endpoint}/json_rpc",
                # "--signaling-server-addr",
                # signaling_server_addr
            ]
        )
        if self.id >= REDIRECT_DAN_WALLET_STDOUT:
            self.process = subprocess.Popen(self.exec, stdout=open(f"stdout/dan_wallet_{self.id}.log", "a+"), stderr=subprocess.STDOUT)
        else:
            self.process = subprocess.Popen(self.exec)
        self.jrpc_client = JrpcDanWalletDaemon(f"http://127.0.0.1:{self.json_rpc_port}")

    def __del__(self):
        self.process.kill()
