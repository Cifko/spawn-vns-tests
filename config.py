DELETE_EVERYTHING_BEFORE = True
DELETE_STDOUT_LOGS = True
REDIRECT_BASE_NODE_STDOUT = True
REDIRECT_WALLET_STDOUT = True
REDIRECT_MINER_STDOUT = True
# it will redirect all VNs with index greater or equal to the value, so for 0 all, for 1 will leave the first one
REDIRECT_VN_FROM_INDEX_STDOUT = 0
REDIRECT_DAN_WALLET_STDOUT = 0
# The register vn cli is redirected as VN, this is for the publish template etc.
REDIRECT_VN_CLI_STDOUT = True
REDIRECT_INDEXER_STDOUT = True
# This is for the cargo generate and compilation for the template
REDIRECT_TEMPLATE_STDOUT = True
NETWORK = "localnet"
SPAWN_VNS = 7
DEFAULT_TEMPLATE = "counter"
DEFAULT_TEMPLATE_FUNCTION = "new"
BURN_AMOUNT = 1000000
NO_FEES = "true"
USE_BINARY_EXECUTABLE = False
