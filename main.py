# type:ignore
from base_node import BaseNode
from config import DELETE_EVERYTHING_BEFORE, DELETE_STDOUT_LOGS, SPAWN_VNS, SPAWN_WALLETS, RUN_SIGNALLING_SERVER, BURN_AMOUNT, DEFAULT_TEMPLATE_FUNCTION, USE_BINARY_EXECUTABLE
from dan_wallet_daemon import DanWalletDaemon
from indexer import Indexer
from miner import Miner
from ports import ports
from template import Template
from template_server import Server
from validator_node import ValidatorNode
from wallet import Wallet
import base64
import json
import os
import re
import shutil
import sys
import time


def check_executable(file_name):
    if not os.path.exists(f"./{file_name}") and not os.path.exists(f"./{file_name}.exe"):
        print(f"Copy {file_name} executable in here")
        exit()


def wait_for_vns_to_sync():
    print("Waiting for VNs to sync to", base_node.grpc_base_node.get_tip(), end=" ")
    # We have to check if VNs are already running their jrpc server
    while True:
        try:
            any(
                vn.jrpc_client.get_epoch_manager_stats()["current_block_height"] != base_node.grpc_base_node.get_tip() - 3
                for vn in VNs.values()
            )
            break
        except:
            print("VNs not ready")
            time.sleep(1)
    while any(
        vn.jrpc_client.get_epoch_manager_stats()["current_block_height"] != base_node.grpc_base_node.get_tip() - 3 for vn in VNs.values()
    ):
        print(".", end="")
        time.sleep(1)
    print(" done")


try:
    if DELETE_EVERYTHING_BEFORE or DELETE_STDOUT_LOGS:
        for file in os.listdir(os.getcwd()):
            full_path = os.path.join(os.getcwd(), file)
            if os.path.isdir(full_path):
                if DELETE_EVERYTHING_BEFORE:
                    if re.match(
                        r"(config|data|base_node|log|peer_db|indexer|miner|vn\d+|wallet|stdout|dan_wallet_daemon|dan_wallet_daemon\d+|counter)", file
                    ):
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
    # Sometimes it takes a while to establish the grpc connection
    while True:
        try:
            wallet.init_grpc()
            wallet.grpc_client.get_version()
            break
        except:
            pass
        time.sleep(0.3)

    # Set ports for miner
    miner = Miner(base_node.grpc_port, wallet.grpc_port)
    # Mine some blocks
    miner.mine(SPAWN_VNS + 13)  # Make sure we have enough funds
    # Start VNs
    print("### CREATING VNS ###")
    VNs = {}
    for vn_id in range(SPAWN_VNS):
        vn = ValidatorNode(base_node.grpc_port, wallet.grpc_port, vn_id, [VNs[vn_id].get_address() for vn_id in VNs])
        VNs[vn_id] = vn

    # indexer = Indexer(base_node.grpc_port, [VNs[vn_id].get_address() for vn_id in VNs])
    time.sleep(1)
    print("### REGISTERING VNS AND CREATING DAN WALLETS DAEMONS ###")

    wait_for_vns_to_sync()

    print("here")
    DanWallets = {}
    # Register VNs
    for vn_id in VNs:
        VNs[vn_id].register()
        # Uncomment next line if you want to have only one registeration per block
        # miner.mine(1)

    for dwallet_id in range(SPAWN_WALLETS):    
        # vn_id = min(SPAWN_VNS - 1, dwallet_id)
        DanWallets[dwallet_id] = DanWalletDaemon(dwallet_id, VNs[dwallet_id].json_rpc_port)

    wait_for_vns_to_sync()
    for d_id in range(SPAWN_WALLETS):
        DanWallets[d_id].jrpc_client.auth()

    # Publish template
    print("### PUBLISHING TEMPLATE ###")
    template.publish_template(next(iter(VNs.values())).json_rpc_port, server.port)

    # Wait until they are all in the mempool
    i = 0
    while i < 10:
        if base_node.grpc_base_node.get_mempool_size() < len(VNs) + 1:
            print("Waiting for X tx's in mempool...")
            time.sleep(3)
        else:
            break
        i += 1

    # Mining till the VNs are part of the committees
    miner.mine(20)  # Mine the register TXs
    time.sleep(1)

    # Wait for the VNs to pickup the blocks from base layer
    # TODO wait for VN to download and activate the template
    wait_for_vns_to_sync()

    # Create account
    # account_create(next(iter(VNs.values())).json_rpc_port)
    print("### CREATING ACCOUNT ###")
    some_dan_wallet_jrpc = next(iter(DanWallets.values())).jrpc_client
    some_dan_wallet_jrpc.accounts_create("TestAccount")
    account = some_dan_wallet_jrpc.accounts_list(0, 1)["accounts"][0]
    public_key = account["public_key"]

    # needs conversion from string to bytes
    public_key = bytes(int(public_key[i : i + 2], 16) for i in range(0, len(public_key), 2))
    print(f"### BURNING {BURN_AMOUNT} ###")
    burn = wallet.grpc_client.burn(BURN_AMOUNT, public_key)

    # Wait for the burn to be in the mempool
    while base_node.grpc_base_node.get_mempool_size() != 1:
        time.sleep(0.5)
    miner.mine(4)  # Mine the burn
    # Mine the burn
    wait_for_vns_to_sync()

    print(f"### CLAIM BURN ###")
    some_dan_wallet_jrpc.claim_burn(burn, account)
    print(f"### CHECKING THE BALANCE ###")
    # Claim the burn
    while (
        some_dan_wallet_jrpc.get_balances(account)["balances"][0]["balance"]
        + some_dan_wallet_jrpc.get_balances(account)["balances"][0]["confidential_balance"]
        == 0
    ):
        time.sleep(1)

    print("### BURNED AND CLAIMED ###")
    print("Balances:", list(DanWallets.values())[0].jrpc_client.get_balances(account))


    if RUN_SIGNALLING_SERVER:
        print("### Starting signalling server")
        

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
                    print("burn <public_key> <path = 'burn.json'>")
                    print("mine <number of blocks> - to mine blocks")
                    print("grpc <node|wallet> - to get grpc port of node or wallet")
                    print("jrpc <vn <id>|dan <id>|indexer> - to get jrpc port of vn with id <id>, dan wallet with id <id> or indexer")
                    print("http <vn <id>|dan <id>|indexer> - to get http address of vn with id <id>, dan with id <id> or indexer")
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
                    os.mkdir("output")
                    outfile = "burn.json"
                    if len(command.split()) > 2:
                        outfile = command.split()[2]

                    with open("output/" + outfile, "w") as f:
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

                        json.dump(claim_proof, f)
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
                elif command.startswith("http"):
                    if command.startswith("http vn"):
                        if r := re.match("http vn (\d+)", command):
                            vn_id = int(r.group(1))
                            if vn_id in VNs:
                                print(f"http://{VNs[vn_id].http_ui_address}")
                            else:
                                print(f"VN id ({vn_id}) is invalid, either it never existed or you already killed it")
                    elif command.startswith("http dan"):
                        if r := re.match("http dan (\d+)", command):
                            dan_id = int(r.group(1))
                            if dan_id in DanWallets:
                                print(f"http://localhost:{DanWallets[dan_id].http_client.http_port}")
                            else:
                                print(f"DAN id ({vn_id}) is invalid, either it never existed or you already killed it")
                    elif command == ("http indexer"):
                        print(f"http://{indexer.http_ui_address}")
                    else:
                        print("Invalid http request")
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
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)

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
server.stop()
for vn_id in VNs:
    print(VNs[vn_id].exec)
    #print(VNs[vn_id].exec_cli)
# for dan_id in DanWallets:
del DanWallets
