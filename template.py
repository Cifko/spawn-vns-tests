# type:ignore
import struct

from config import DEFAULT_TEMPLATE, REDIRECT_TEMPLATE_STDOUT, REDIRECT_VN_CLI_STDOUT, USE_BINARY_EXECUTABLE
from ports import ports
from dan_wallet_daemon import JrpcDanWalletDaemon
from typing import Any
import subprocess
import re
import os
import array


class Template:
    def __init__(self, template=DEFAULT_TEMPLATE, name=None):
        self.template = template
        self.name = name or template
        self.generate()
        self.compile()

    def generate(self):
        wd = os.getcwd()
        try:
            os.mkdir("templates")
        except:
            pass
        os.chdir("templates")

        exec = " ".join(
            ["cargo", "generate", "--git", "https://github.com/tari-project/wasm-template.git", "-s", self.template, "-n", self.name]
        )
        if REDIRECT_TEMPLATE_STDOUT:
            subprocess.call(exec, stdout=open(f"../stdout/template_{self.name}_cargo_generate.log", "a+"), stderr=subprocess.STDOUT)
        else:
            subprocess.call(exec)
        os.chdir(wd)

    def compile(self):
        wd = os.getcwd()
        os.chdir(f"templates/{self.name}/package")
        exec = " ".join(["cargo", "build", "--target", "wasm32-unknown-unknown", "--release"])
        if REDIRECT_TEMPLATE_STDOUT:
            subprocess.call(exec, stdout=open(f"../../../stdout/template_{self.name}_cargo_build.log", "a+"), stderr=subprocess.STDOUT)
        else:
            subprocess.call(exec)
        os.chdir(wd)

    def publish_template(self, jrpc_port: int, server_port: int):
        if USE_BINARY_EXECUTABLE:
            run = "tari_validator_node_cli"
        else:
            run = " ".join(["cargo", "run", "--bin", "tari_validator_node_cli", "--manifest-path", "../tari-dan/Cargo.toml", "--"])

        exec = " ".join(
            [
                run,
                "--vn-daemon-jrpc-endpoint",
                f"/ip4/127.0.0.1/tcp/{jrpc_port}",
                "templates",
                "publish",
                "--binary-url",
                f"http://localhost:{server_port}/templates/{self.name}/package/target/wasm32-unknown-unknown/release/{self.name}.wasm",
                "--template-code-path",
                f"./templates/{self.name}/package/",
                "--template-name",
                f"{self.name}",
                "--template-version",
                "1",
                "--template-type",
                "wasm",
            ]
        )
        result = subprocess.run(exec, stdout=subprocess.PIPE)
        if r := re.search(r"The template address will be ([0-9a-f]{64})", result.stdout.decode()):
            self.id = r.group(1)
        else:
            print("Registration failed", result.stdout.decode())

    def call_function(self, function_name: str, dan_wallet_client: JrpcDanWalletDaemon, params: list[Any] = []):
        for p in range(len(params)):
            if params[p].startswith("w:"):
                params[p] = {"type": "Workspace", "value": params[p][2:]}
            else:
                try:
                    i = int(params[p])
                    params[p] = array.array("B", struct.pack("<I", i)).tolist()
                except:
                    pass
                params[p] = {"type": "Literal", "value": params[p]}
        result = dan_wallet_client.transaction_submit_instruction(
            {
                "CallFunction": {
                    "template_address": array.array("B", bytes.fromhex(self.id)).tolist(),
                    "function": function_name,
                    "args": params,
                }
            }
        )
        print(result)
        return result
