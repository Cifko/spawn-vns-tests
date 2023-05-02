# type:ignore
from config import REDIRECT_DAN_WALLET_STDOUT, USE_BINARY_EXECUTABLE, REDIRECT_DAN_WALLET_WEBUI_STDOUT
from ports import ports
import base64
import os
import platform
import requests
import subprocess
import signal
import time

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
        print(response.json())
        return response.json()["result"]

    def auth(self):
        resp = self.call("auth.request", [["Admin"]])
        print(resp)
        auth_token = resp["auth_token"]
        resp = self.call("auth.accept", [auth_token])
        print(resp)
        self.token = resp["permissions_token"]

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
        return self.call("accounts.get_balances", [account["account"]["name"], True])


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
        jrpc_address = f"http://127.0.0.1:{self.json_rpc_port}"
        self.jrpc_client = JrpcDanWalletDaemon(jrpc_address)
        self.http_client = DanWalletUI(self.id, jrpc_address)
        while not os.path.exists(f"dan_wallet_daemon{dan_wallet_id}/localnet/pid"):
            print("waiting for dan wallet to start")
            time.sleep(1)
        

    def __del__(self):
        self.process.kill()
        print("del wallet")
        del self.http_client


class DanWalletUI:
    def __init__(self, dan_wallet_id, daemon_jrpc_address):
        if platform.system() == "Windows":
            npm = "npm.cmd"
        else:
            npm = "npm"
        self.http_port = ports.get_free_port()
        self.id = dan_wallet_id
        self.exec = " ".join(
            [npm, "--prefix", "../tari-dan/applications/tari_dan_wallet_web_ui", "run", "dev", "--", "--port", str(self.http_port)]
        )
        env = os.environ.copy()
        env["VITE_DAEMON_JRPC_ADDRESS"] = daemon_jrpc_address
        if self.id >= REDIRECT_DAN_WALLET_WEBUI_STDOUT:
            self.process = subprocess.Popen(
                self.exec,
                stdin=subprocess.PIPE,
                stdout=open(f"stdout/dan_wallet_web_ui_{self.id}.log", "a+"),
                stderr=subprocess.STDOUT,
                env=env,
            )
        else:
            self.process = subprocess.Popen(self.exec, stdin=subprocess.PIPE, env=env)

    def __del__(self):
        print("del wallet ui")
        # for p in self.process.active_children():
        # p.terminate()
        # p.kill()
        # self.process.terminate()
        # self.process.kill()
        # kill all children
        try:
          os.kill(self.process.pid, signal.CTRL_C_EVENT)
        except: 
          pass
        self.process.kill()
        # os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
