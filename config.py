DELETE_EVERYTHING_BEFORE = True
DELETE_STDOUT_LOGS = True
REDIRECT_BASE_NODE_STDOUT = False
REDIRECT_WALLET_STDOUT = False
REDIRECT_MINER_STDOUT = False
# it will redirect all VNs with index greater or equal to the value, so for 0 all, for 1 will leave the first one
REDIRECT_VN_FROM_INDEX_STDOUT = 1
REDIRECT_DAN_WALLET_STDOUT = 1
# The register vn cli is redirected as VN, this is for the publish template etc.
REDIRECT_VN_CLI_STDOUT = False
REDIRECT_INDEXER_STDOUT = False
# This is for the cargo generate and compilation for the template
REDIRECT_TEMPLATE_STDOUT = False
NETWORK = "localnet"
SPAWN_VNS = 2
DEFAULT_TEMPLATE = "counter"
DEFAULT_TEMPLATE_FUNCTION = "new"
BURN_AMOUNT = 1000000
NO_FEES = "true"
USE_BINARY_EXECUTABLE = False
