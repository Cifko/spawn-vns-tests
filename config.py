DELETE_EVERYTHING_BEFORE = True
DELETE_STDOUT_LOGS = True
REDIRECT_BASE_NODE_STDOUT = False
REDIRECT_WALLET_STDOUT = False
REDIRECT_MINER_STDOUT = False
# how many VNs should print to console
REDIRECT_VN_FROM_INDEX_STDOUT = 1
# how many dan wallets should print to console
REDIRECT_DAN_WALLET_STDOUT = 1
# The register vn cli is redirected as VN, this is for the publish template etc.
REDIRECT_VN_CLI_STDOUT = False
REDIRECT_INDEXER_STDOUT = False
# This is for the cargo generate and compilation for the template
REDIRECT_TEMPLATE_STDOUT = False
REDIRECT_DAN_WALLET_WEBUI_STDOUT = False
REDIRECT_SIGNALING_STDOUT = False
NETWORK = "localnet"
SPAWN_VNS = 1
SPAWN_WALLETS = 1
SPAWN_INDEXER = True
# Any one of the templates from `wasm_template`
DEFAULT_TEMPLATE = "fungible"
# Specify args e.g. mint=10000,10001,1. Start the value with "w:" to choose Workspace arg
# DEFAULT_TEMPLATE_FUNCTION = "mint"
DEFAULT_TEMPLATE_FUNCTION = "mint=1000000"
BURN_AMOUNT = 1000000
NO_FEES = True
USE_BINARY_EXECUTABLE = True
STEPS_CREATE_ACCOUNT = True
STEPS_CREATE_TEMPLATE = False
STEPS_RUN_TARI_CONNECTOR_TEST_SITE = True
STEPS_RUN_SIGNALLING_SERVER = True
