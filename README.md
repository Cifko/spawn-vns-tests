The main purpose of this is to quickly spawn a local network of validator nodes. So you can test whatever you want to (e.g. new template always on fresh network, new validator node, etc..)

Just run the python script.
It will create server that will serve the \*.wasm
It will create base node / wallet.
It will spawns VNs (code `SPAWN_VNS`)
It will get `DEFAULT_TEMPLATE`, compile it and call a `DEFAULT_TEMPLATE_FUNCTION` function.
The tari_base_node, tari_wallet, tari_miner, tari_validator_node, tari_validator_node_cli has to be next to script (It will complain if it's not there).
It run on `NETWORK` (currently localnet).
It deletes everything that it's going to use (e.g. ./config, ./data, etc...) this is disabled by default. I want to be sure, I'm not accidentally deleting something when someone runs it from different path. So it's your responsibility when you turn the `DELETE_EVERYTHING_BEFORE` flag in the code to True.

It runs in this order: 0) Deletes everything

1. Spawn a server
2. Get template
3. Compile template
4. Start base node
5. Start wallet
6. Mine (# of VNs)\*3+10 blocks (just to be sure we have money)
7. Spawn the VNs
8. Register each VN
9. Publish template
10. Mine 20 blocks
11. Burn 1000000 (wait for mempool, mine 4 block)
12. 10 seconds wait for the VNs to catch up with the base layer for the claim
13. Claim the burned amount
14. Call function from the template wait for result

After this it is kept running.
If you need something for testing, you can use commands:

- get grpc by call `grpc node` or `grpc wallet`
- get jrpc port of VN e.g. `jrpc vn 0` 0 is the id of the VN
- kill some process e.g. `kill node` or `kill vn 0`. If you kill a process it will print the command so that you can run it manually. E.g. you want to see the transactions in the wallet, just kill the wallet and run the command (it will strip the non-interactive flag for you)
- `live` will just print what was not killed
- `eval <any python evaluable line>` e.g. `eval print(template.id)` (I added this just for debug, was too lazy to restart it everytime)

It uses mainly standard python libraries (maybe all are just python standard, I didn't check).
