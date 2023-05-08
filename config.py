DELETE_EVERYTHING_BEFORE = True
DELETE_STDOUT_LOGS = True
REDIRECT_BASE_NODE_STDOUT = True
REDIRECT_WALLET_STDOUT = True
REDIRECT_MINER_STDOUT = True
# how many VNs should print to console
REDIRECT_VN_FROM_INDEX_STDOUT = 0
# how many dan wallets should print to console
REDIRECT_DAN_WALLET_STDOUT = 0
# The register vn cli is redirected as VN, this is for the publish template etc.
REDIRECT_VN_CLI_STDOUT = True
REDIRECT_INDEXER_STDOUT = True
# This is for the cargo generate and compilation for the template
REDIRECT_TEMPLATE_STDOUT = True
REDIRECT_DAN_WALLET_WEBUI_STDOUT = False
REDIRECT_SIGNALING_STDOUT = True
NETWORK = "localnet"
SPAWN_VNS = 1
SPAWN_WALLETS = 1
SPAWN_INDEXER = True
RUN_SIGNALLING_SERVER = True
# Any one of the templates from `wasm_template`
DEFAULT_TEMPLATE = "fungible"
# Specify args e.g. mint=10000,10001,1
DEFAULT_TEMPLATE_FUNCTION = "mint=1000000"
BURN_AMOUNT = 1000000
NO_FEES = "false"
USE_BINARY_EXECUTABLE = False
STEPS_CREATE_ACCOUNT = False
STEPS_CREATE_TEMPLATE = False
