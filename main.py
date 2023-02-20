# type:ignore
import os
import subprocess
import threading
import time
import socket, errno
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

DELETE_EVERYTHING_BEFORE = True
NETWORK = "localnet"
SPAWN_VNS = 4
DEFAULT_TEMPLATE = "counter"
DEFAULT_TEMPLATE_FUNCTION = "new"


def is_port_used(port):
    sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sck.bind(("127.0.0.1", port))
    except socket.error as e:
        if e.errno != errno.EADDRINUSE:
            print(f"Some error on getting port usage {e}")
        return True
    sck.close()
    return False


class RequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, file_path):
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.send_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
        self.end_headers()
        with open(file_path, "rb") as f:
            self.wfile.write(f.read())

    def do_GET(self):
        file_path = self.path[1:]
        print(file_path)
        if os.path.isfile(file_path):
            self._send_response(file_path)
        else:
            message = "File not found"
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(message, "utf8"))


class Server:
    def run(self, server_class=HTTPServer, handler_class=RequestHandler):
        self.port = ports.get_free_port()
        server_address = ("", self.port)
        self.httpd = server_class(server_address, handler_class)
        print(f"Starting httpd on port {self.port}...")
        self.server = threading.Thread(target=self.httpd.serve_forever)
        self.server.start()

    def stop(self):
        t = threading.Thread(target=self.httpd.shutdown)
        t.start()


class Ports:
    def __init__(self):
        self.last_used = 18003

    def get_free_port(self):
        self.last_used += 1
        while is_port_used(self.last_used):
            self.last_used += 1
        return self.last_used


def check_executable(file_name):
    if not os.path.exists(f"./{file_name}") and not os.path.exists(f"./{file_name}.exe"):
        print(f"Copy {file_name} executable in here")
        exit()


class BaseNode:
    def __init__(self):
        self.public_address = f"/ip4/127.0.0.1/tcp/{ports.get_free_port()}"
        self.grpc_port = ports.get_free_port()
        self.exec = " ".join(
            [
                "tari_base_node",
                "-b",
                ".",
                "-n",
                "--network",
                NETWORK,
                "-p",
                "base_node.p2p.transport.type=tcp",
                "-p",
                f"base_node.p2p.transport.tcp.listener_address={self.public_address}",
                "-p",
                f"base_node.p2p.public_address={self.public_address}",
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
        print(self.exec)
        self.process = subprocess.Popen(self.exec)

    def __del__(self):
        self.process.kill()

    def get_address(self):
        if NETWORK == "localnet":
            base_node_id_file_name = f"./config/base_node_id.json"
        else:
            base_node_id_file_name = f"./config/base_node_id_{NETWORK}.json"
        while not os.path.exists(base_node_id_file_name):
            time.sleep(0.3)
        f = open(base_node_id_file_name, "rt")
        content = "".join(f.readlines())
        node_id, public_key, public_address = re.search(
            r'"node_id":"(.*?)","public_key":"(.*?)".*"public_address":"(.*?)"', content
        ).groups()
        public_address = public_address.replace("\\/", "/")
        return f"{public_key}::{public_address}"


class Wallet:
    def __init__(self, base_node_address):
        self.public_address = f"/ip4/127.0.0.1/tcp/{ports.get_free_port()}"
        self.grpc_port = ports.get_free_port()
        self.exec = " ".join(
            [
                "tari_console_wallet",
                "-b",
                ".",
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
                f"wallet.p2p.public_address={self.public_address}",
                "-p",
                "wallet.p2p.allow_test_addresses=true",
                "-p",
                f'{NETWORK}.p2p.seeds.peer_seeds=""',
            ]
        )
        print(self.exec)
        self.process = subprocess.Popen(self.exec)

    def __del__(self):
        self.process.kill()


class Miner:
    def __init__(self, base_node_grpc_port, wallet_grpc_port):
        self.exec = " ".join(
            [
                "tari_miner",
                "--max-blocks",
                "#blocks",
                "-p",
                f"miner.base_node_grpc_address=/ip4/127.0.0.1/tcp/{base_node_grpc_port}",
                "-p",
                f"miner.wallet_grpc_address=/ip4/127.0.0.1/tcp/{wallet_grpc_port}",
            ]
        )

    def mine(self, blocks):
        self.process = subprocess.call(self.exec.replace("#blocks", str(blocks)))


class ValidatorNode:
    def __init__(self, base_node_grpc_port, wallet_grpc_port, node_id, peers=[]):
        self.public_adress = f"/ip4/127.0.0.1/tcp/{ports.get_free_port()}"
        self.json_rpc_port = ports.get_free_port()
        self.json_rpc_address = f"127.0.0.1:{self.json_rpc_port}"
        self.http_ui_address = f"127.0.0.1:{ports.get_free_port()}"
        self.id = node_id
        self.exec = " ".join(
            [
                "tari_validator_node",
                "-b",
                f"vn{node_id}",
                "--network",
                NETWORK,
                "-p",
                f"validator_node.base_node_grpc_address=127.0.0.1:{base_node_grpc_port}",
                "-p",
                f"validator_node.wallet_grpc_address=127.0.0.1:{wallet_grpc_port}",
                "-p",
                "validator_node.p2p.transport.type=tcp",
                "-p",
                f"validator_node.p2p.transport.tcp.listener_address={self.public_adress}",
                "-p",
                "validator_node.p2p.allow_test_addresses=true",
                "-p",
                f"{NETWORK}.p2p.seeds.peer_seeds={','.join(peers)}",
                "-p",
                f"validator_node.public_address={self.public_adress}",
                "-p",
                f"validator_node.json_rpc_address={self.json_rpc_address}",
                "-p",
                f"validator_node.http_ui_address={self.http_ui_address}",
            ]
        )
        self.process = subprocess.Popen(self.exec)

    def get_address(self):
        if NETWORK == "localnet":
            validator_node_id_file_name = f"./vn{self.id}/validator_node_id.json"
        else:
            validator_node_id_file_name = f"./vn{self.id}/validator_node_id_{NETWORK}.json"
        while not os.path.exists(validator_node_id_file_name):
            time.sleep(0.3)
        f = open(validator_node_id_file_name, "rt")
        content = "".join(f.readlines())
        node_id, public_key, public_address = re.search(
            r'"node_id":"(.*?)","public_key":"(.*?)".*"public_address":"(.*?)"', content
        ).groups()
        public_address = public_address.replace("\\/", "/")
        return f"{public_key}::{public_address}"

    def __del__(self):
        print("vn kill")
        self.process.kill()

    def register(self):
        self.exec_cli = " ".join(
            ["tari_validator_node_cli", "--vn-daemon-jrpc-endpoint", f"/ip4/127.0.0.1/tcp/{self.json_rpc_port}", "vn", "register"]
        )
        self.cli_process = subprocess.call(self.exec_cli)


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
        subprocess.call(exec)

    def compile(self):
        exec = " ".join(
            ["cargo", "build", "--target", "wasm32-unknown-unknown", "--release", f"--manifest-path={self.name}\package\Cargo.toml"]
        )
        subprocess.call(exec)

    def publish_template(self, jrpc_port):
        exec = " ".join(
            [
                "tari_validator_node_cli",
                "--vn-daemon-jrpc-endpoint",
                f"/ip4/127.0.0.1/tcp/{jrpc_port}",
                "templates",
                "publish",
                "--binary-url",
                f"http://localhost:{server.port}/{self.name}/package/target/wasm32-unknown-unknown/release/{self.name}.wasm",
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
        exec = " ".join(
            [
                "tari_validator_node_cli",
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
        subprocess.call(exec)


def account_create(jrpc_port):
    exec = " ".join(
        [
            "tari_validator_node_cli",
            "--vn-daemon-jrpc-endpoint",
            f"/ip4/127.0.0.1/tcp/{jrpc_port}",
            "accounts",
            "create",
        ]
    )
    subprocess.call(exec)


if DELETE_EVERYTHING_BEFORE:
    subprocess.call(["rm", "-f", "-r", "./config"])
    subprocess.call(["rm", "-f", "-r", "./data"])
    subprocess.call(["rm", "-f", "-r", "./log"])
    subprocess.call(["rm", "-f", "-r", "./peer_db"])
    subprocess.call(["rm", "-f", "-r", "./vn*"])
    # subprocess.call(["rm", "-f", "-r", "./accounts*"])
    # We usually don't want to recompile the template all the time
    # subprocess.call(["rm", "-f", "-r", f"./{DEFAULT_TEMPLATE}"])

# Class for getting available ports
ports = Ports()
check_executable("tari_base_node")
check_executable("tari_console_wallet")
check_executable("tari_miner")
check_executable("tari_validator_node")
check_executable("tari_validator_node_cli")

# Step 1, start the http server for serving wasm files.
server = Server()
server.run()

# Generate template
template = Template()
# Start base ndoe
base_node = BaseNode()
# Start wallet
wallet = Wallet(base_node.get_address())

# Set ports for miner
miner = Miner(base_node.grpc_port, wallet.grpc_port)
# Mine some blocks
miner.mine(SPAWN_VNS * 3 + 10)  # Make sure we have enough funds


# Start VNs
print("Creating VNs")
VNs = {}
for vn_id in range(SPAWN_VNS):
    print("[+]", vn_id)
    vn = ValidatorNode(base_node.grpc_port, wallet.grpc_port, vn_id, [VNs[vn_id].get_address() for vn_id in VNs])
    VNs[vn_id] = vn
    print("[-]", vn_id)

print("Registering VNs")
time.sleep(3)

# Register VNs
for vn_id in VNs:
    VNs[vn_id].register()
    # Uncomment next line if you want to have only one registeration per block
    # miner.mine(1)

time.sleep(3)

# Publish template
template.publish_template(next(iter(VNs.values())).json_rpc_port)

# Mining till the VNs are part of the committees
miner.mine(20)  # Mine the register TXs

# Wait for the VNs to pickup the blocks from base layer
# TODO wait for VN to download and activate the template
time.sleep(10)

# Let's kill one VN and see that if I send transactions it should always pass
# del VNs[0]
# time.sleep(5)

# Create account
account_create(next(iter(VNs.values())).json_rpc_port)


# Call the function
# template.call_function(DEFAULT_TEMPLATE_FUNCTION, next(iter(VNs.values())).json_rpc_port)

try:
    while True:
        command = input("Command (press ctrl-c to exit or type 'help'): ").lower()
        try:
            if command == "help":
                print("Commands available : ")
                print("mine <number of blocks> - to mine blocks")
                print("grpc <node|wallet> - to get grpc port of node or wallet")
                print("jrpc vn <id> - to get jrpc port of vn with id <id>")
                print(
                    "kill <node|wallet|vn <id>> - to kill node, wallet or vn with id, the command how to run it locally will be printed without the `-n` (non-interactive switch)"
                )
                print("live - list of things that are still running from this python (base node, wallet, vns)")
                print("---")
                print("The VNs are zero based index")
            elif command.startswith("mine"):
                blocks = int(command.split()[1])
                miner.mine(blocks)  # Mine the register TXs
            elif command.startswith("grpc"):
                what = command.split()[1]
                match what:
                    case "node":
                        print(base_node.grpc_port)
                    case "wallet":
                        print(wallet.grpc_port)
            elif command.startswith("jrpc vn"):
                if r := re.match("jrpc vn (\d+)", command):
                    vn_id = int(r.group(1))
                    if vn_id in VNs:
                        print(VNs[vn_id].json_rpc_port)
                    else:
                        print(f"VN id ({vn_id}) is invalid, either it never existed or you already killed it")
            elif command.startswith("http vn"):
                if r := re.match("http vn (\d+)", command):
                    vn_id = int(r.group(1))
                    if vn_id in VNs:
                        print(VNs[vn_id].http_ui_address)
                    else:
                        print(f"VN id ({vn_id}) is invalid, either it never existed or you already killed it")
            elif command.startswith("kill"):
                what = command.split()[1]
                match what:
                    case "node":
                        print(f'To run base node : {base_node.exec.replace("-n ", "")}')
                        del base_node
                    case "wallet":
                        print(f'To run the wallet : {wallet.exec.replace("-n ", "")}')
                        del wallet
                    case _:
                        # This should be 'VN <id>'
                        if r := re.match("vn (\d+)", what):
                            vn_id = int(r.group(1))
                            if vn_id in VNs:
                                print(f"To run the vn : {VNs[vn_id].exec}")
                                print(f"Command that was used to register the VN : {VNs[vn_id].exec_cli}")
                                del VNs[vn_id]
                            else:
                                print(f"VN id ({vn_id}) is invalid, either it never existed or you already killed it")
                        else:
                            print("Invalid kill command", command)
                        # which = what.split()
            elif command == "live":
                if "base_node" in locals():
                    print("Base node is running")
                if "wallet" in locals():
                    print("Wallet is running")
                for vn_id in VNs:
                    print(f"VN<{vn_id}> is running")
            elif command == "tx":
                template.call_function(DEFAULT_TEMPLATE_FUNCTION, next(iter(VNs.values())).json_rpc_port)
            elif command.startswith("eval"):
                # In case you need for whatever reason access to the running python script
                eval(command[len("eval ") :])
        except:
            print("Wrong command", command)
except:
    pass
print("The commands to run : ")
if "base_node" in locals():
    print("Base Node : ")
    print(base_node.exec.replace("-n ", ""))
if "wallet" in locals():
    print("Wallet : ")
    print(wallet.exec.replace("-n ", ""))
print("Miner : ")
print(miner.exec)
for vn_id in VNs:
    print(VNs[vn_id].exec)
    print(VNs[vn_id].exec_cli)
server.stop()
