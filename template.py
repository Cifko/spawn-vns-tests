# type:ignore

from config import DEFAULT_TEMPLATE, REDIRECT_TEMPLATE_STDOUT, REDIRECT_VN_CLI_STDOUT, USE_BINARY_EXECUTABLE
from ports import ports
import subprocess
import re


class Template:
    def __init__(self, template=DEFAULT_TEMPLATE, name=None):
        self.template = template
        self.name = name or template
        self.generate()
        self.compile()

    def generate(self):
        exec = " ".join(
            ["cargo", "generate", "--git", "https://github.com/tari-project/wasm-template.git", "-s", self.template, "-n", self.name]
        )
        if REDIRECT_TEMPLATE_STDOUT:
            subprocess.call(exec, stdout=open(f"stdout/template_{self.name}_cargo_generate.log", "a+"))
        else:
            subprocess.call(exec)

    def compile(self):
        exec = " ".join(
            ["cargo", "build", "--target", "wasm32-unknown-unknown", "--release", f"--manifest-path={self.name}\package\Cargo.toml"]
        )
        if REDIRECT_TEMPLATE_STDOUT:
            subprocess.call(exec, stdout=open(f"stdout/template_{self.name}_cargo_build.log", "a+"))
        else:
            subprocess.call(exec)

    def publish_template(self, jrpc_port, server_port):
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
                f"http://localhost:{server_port}/{self.name}/package/target/wasm32-unknown-unknown/release/{self.name}.wasm",
                "--template-code-path",
                f".\{self.name}/package/",
                "--template-name",
                f"{self.name}",
                "--template-version",
                "1",
            ]
        )
        result = subprocess.run(exec, stdout=subprocess.PIPE)
        if r := re.search(r"The template address will be ([0-9a-f]{64})", result.stdout.decode()):
            self.id = r.group(1)
        else:
            print("Registration failed", result.stdout.decode())

    def call_function(self, function_name, jrpc_port):
        if USE_BINARY_EXECUTABLE:
            run = "tari_validator_node_cli"
        else:
            run = " ".join(["cargo", "run", "--bin", "tari_validator_node_cli", "--manifest-path", "../tari-dan/Cargo.toml", "--"])
        exec = " ".join(
            [
                run,
                "--vn-daemon-jrpc-endpoint",
                f"/ip4/127.0.0.1/tcp/{jrpc_port}",
                "transactions",
                "submit",
                "-n",
                "1",
                "-w",
                "call-function",
                f"{self.id}",
                function_name,
            ]
        )
        if REDIRECT_VN_CLI_STDOUT:
            subprocess.call(exec, stdout=open(f"stdout/vn_cli_for_template_{self.name}.log", "a+"))
        else:
            subprocess.call(exec)
