# type:ignore
import os
import time
import re
import shutil
import sys
from template_server import Server
from ports import ports
from config import DELETE_EVERYTHING_BEFORE, DELETE_STDOUT_LOGS, SPAWN_VNS, BURN_AMOUNT, DEFAULT_TEMPLATE_FUNCTION, USE_BINARY_EXECUTABLE
from wallet import Wallet
from base_node import BaseNode
from template import Template
from miner import Miner
from validator_node import ValidatorNode
from dan_wallet_daemon import DanWalletDaemon
from indexer import Indexer


def check_executable(file_name):
    if not os.path.exists(f"./{file_name}") and not os.path.exists(f"./{file_name}.exe"):
        print(f"Copy {file_name} executable in here")
        exit()

try:


    if DELETE_EVERYTHING_BEFORE or DELETE_STDOUT_LOGS:
        for file in os.listdir(os.getcwd()):
            full_path = os.path.join(os.getcwd(), file)
            if os.path.isdir(full_path):
                if DELETE_EVERYTHING_BEFORE:
                    if re.match(r"(config|data|base_node|log|peer_db|indexer|miner|vn\d+|wallet|stdout|dan_wallet_daemon|counter)", file):
                        shutil.rmtree(full_path)
                else:
                    if re.match(r"stdout", file):
                        shutil.rmtree(full_path)
    if USE_BINARY_EXECUTABLE:
        check_executable("tari_base_node")
        check_executable("tari_console_wallet")
        check_executable("tari_miner")
        check_executable("tari_validator_node")
        check_executable("tari_validator_node_cli")
    os.mkdir("./stdout")

    # Step 1, start the http server for serving wasm files.
    print("### STARTING HTTP SERVER ###")
    server = Server()
    server.run()
    print("### GENERATING TEMPLATE ###")
    # Generate template
    template = Template()
    print("### STARTING BASE NODE ###")
    # Start base node
    base_node = BaseNode()
    print("### STARTING WALLET ###")
    # Start wallet
    wallet = Wallet(base_node.get_address())

    # Set ports for miner
    miner = Miner(base_node.grpc_port, wallet.grpc_port)
    # Mine some blocks
    miner.mine(SPAWN_VNS * 3 + 10)  # Make sure we have enough funds

    # Start VNs
    print("### CREATING VNS ###")
    VNs = {}
    for vn_id in range(SPAWN_VNS):
        vn = ValidatorNode(base_node.grpc_port, wallet.grpc_port, vn_id, [VNs[vn_id].get_address() for vn_id in VNs])
        VNs[vn_id] = vn

    # indexer = Indexer(base_node.grpc_port, [VNs[vn_id].get_address() for vn_id in VNs])

    print("### REGISTERING VNS AND CREATING DAN WALLETS DAEMONS ###")
    time.sleep(3)

    DanWallets = {}
    # Register VNs
    for vn_id in VNs:
        VNs[vn_id].register()
        DanWallets[vn_id] = DanWalletDaemon(vn_id, VNs[vn_id].json_rpc_port)
        # Uncomment next line if you want to have only one registeration per block
        # miner.mine(1)

    time.sleep(3)

    # Publish template
    print("### PUBLISHING TEMPLATE ###")
    template.publish_template(next(iter(VNs.values())).json_rpc_port, server.port)

    # Mining till the VNs are part of the committees
    miner.mine(20)  # Mine the register TXs

    # Wait for the VNs to pickup the blocks from base layer
    # TODO wait for VN to download and activate the template
    time.sleep(5)

    # Create account
    # account_create(next(iter(VNs.values())).json_rpc_port)
    print("### CREATING ACCOUNT ###")
    some_dan_wallet_jrpc = next(iter(DanWallets.values())).jrpc_client
    print("..")
    some_dan_wallet_jrpc.accounts_create("TestAccount")
    print("...")
    account = some_dan_wallet_jrpc.accounts_list(0, 1)["accounts"][0]
    print("...4")
    public_key = account["public_key"]

    print("...5")
    # needs conversion from string to bytes
    public_key = bytes(int(public_key[i : i + 2], 16) for i in range(0, len(public_key), 2))
    print(f"### BURNING {BURN_AMOUNT} ###")
    burn = wallet.grpc_client.burn(BURN_AMOUNT, public_key)

    # Wait for the burn to be in the mempool
    while base_node.grpc_base_node.get_mempool_size() != 1:
        time.sleep(0.5)
    # Mine the burn
    miner.mine(4)
    # Wait for the VNs to pickup the changes from baselayer
    time.sleep(10)

    some_dan_wallet_jrpc.claim_burn(burn, account)
    # Claim the burn
    while (
        some_dan_wallet_jrpc.get_balances(account)["balances"][0]["balance"]
        + some_dan_wallet_jrpc.get_balances(account)["balances"][0]["confidential_balance"]
        == 0
    ):
        time.sleep(1)

    print("### BURNED AND CLAIMED ###")
    print("Balances:", list(DanWallets.values())[0].jrpc_client.get_balances(account))

    # Call the function
    template.call_function(DEFAULT_TEMPLATE_FUNCTION, next(iter(VNs.values())).json_rpc_port)

    try:
        while True:
            command = input("Command (press ctrl-c to exit or type 'help'): ")
            for_eval = command
            command.lower()
            try:
                if command == "help":
                    print("Commands available : ")
                    print("mine <number of blocks> - to mine blocks")
                    print("grpc <node|wallet> - to get grpc port of node or wallet")
                    print("jrpc <vn <id>|dan <id>|indexer> - to get jrpc port of vn with id <id>, dan wallet with id <id> or indexer")
                    print("http <vn <id>|indexer> - to get http address of vn with id <id> or indexer")
                    print(
                        "kill <node|wallet|indexer|vn <id>|dan <id>> - to kill node, wallet, indexer, vn with id or dan wallet with id, the command how to run it locally will be printed without the `-n` (non-interactive switch)"
                    )
                    print("live - list of things that are still running from this python (base node, wallet, ...)")
                    print("---")
                    print("The VNs are zero based index")
                elif command.startswith("burn"):
                    public_key = command.split()[1]
                    public_key = bytes(int(public_key[i : i + 2], 16) for i in range(0, len(public_key), 2))
                    print(f"### BURNING {BURN_AMOUNT} ###")
                    burn = wallet.grpc_client.burn(BURN_AMOUNT, public_key) 
                    outfile = "burn.json"
                    if command.split().len() > 1:
                        outfile = command.split()[2]

                    with open(outfile, "w") as f:
                        json.dump(burn, f)
                    print("written to file", outfile)

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
                elif command.startswith("jrpc dan"):
                    if r := re.match("jrpc dan (\d+)", command):
                        vn_id = int(r.group(1))
                        if vn_id in VNs:
                            print(DanWallets[vn_id].json_rpc_port)
                        else:
                            print(f"dan id ({vn_id}) is invalid, either it never existed or you already killed it")
                elif command.startswith("jrpc indexer"):
                    print(indexer.json_rpc_port)
                elif command.startswith("http vn"):
                    if r := re.match("http vn (\d+)", command):
                        vn_id = int(r.group(1))
                        if vn_id in VNs:
                            print(f"http://{VNs[vn_id].http_ui_address}")
                        else:
                            print(f"VN id ({vn_id}) is invalid, either it never existed or you already killed it")
                elif command == ("http indexer"):
                    print(f"http://{indexer.http_ui_address}")
                elif command.startswith("kill"):
                    what = command.split(maxsplit=1)[1]
                    match what:
                        case "node":
                            print(f'To run base node : {base_node.exec.replace("-n ", "")}')
                            del base_node
                        case "wallet":
                            print(f'To run the wallet : {wallet.exec.replace("-n ", "")}')
                            del wallet
                        case "indexer":
                            print(f'To run the indexer : {indexer.exec.replace("-n ", "")}')
                            del indexer
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
                            elif r := re.match("dan (\d+)", what):
                                dan_id = int(r.group(1))
                                if dan_id in DanWallets:
                                    print(f"To run the vn : {DanWallets[dan_id].exec}")
                                    del DanWallets[dan_id]
                                else:
                                    print(f"DanWallet id ({dan_id}) is invalid, either it never existed or you already killed it")
                            else:
                                print("Invalid kill command", command)
                            # which = what.split()
                elif command == "live":
                    if "base_node" in locals():
                        print("Base node is running")
                    if "wallet" in locals():
                        print("Wallet is running")
                    if "indexer" in locals():
                        print("Indexer is running")
                    for vn_id in VNs:
                        print(f"VN<{vn_id}> is running")
                    for daemon_id in DanWallets:
                        print(f"DanWallet<{daemon_id}> is running")
                elif command == "tx":
                    template.call_function(DEFAULT_TEMPLATE_FUNCTION, next(iter(VNs.values())).json_rpc_port)
                elif command.startswith("eval"):
                    # In case you need for whatever reason access to the running python script
                    eval(for_eval[len("eval ") :])
                else:
                   print("Wrong command")    
            except Exception as e:
                print("Command errored", e)
    except:
        print("failed in CLI loop")
except Exception as ex:
    print("failed setup:", ex)

print("The commands to run : ")
if "base_node" in locals():
    print("Base Node : ")
    print(base_node.exec.replace("-n ", ""))
if "wallet" in locals():
    print("Wallet : ")
    print(wallet.exec.replace("-n ", ""))
if "indexer" in locals():
    print("Indexer : ")
    print(indexer.exec.replace("-n ", ""))
print("Miner : ")
print(miner.exec)
for vn_id in VNs:
    print(VNs[vn_id].exec)
    print(VNs[vn_id].exec_cli)
server.stop()
