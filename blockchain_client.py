
"""
import os
import os.path
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

# 1. Load environment variables from .env
load_dotenv()

# 2. (Optional) Install solc version 0.8.0 if needed
install_solc('0.8.0')

# 3. Build path to Attendance.sol in the same folder
sol_path = os.path.join(os.path.dirname(__file__), "Attendance.sol")
if not os.path.isfile(sol_path):
    raise FileNotFoundError(f"Could not find Attendance.sol at: {sol_path}")

# 4. Read the Solidity contract
with open(sol_path, "r") as file:
    contract_source = file.read()

# 5. Compile the Solidity contract
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {
            "Attendance.sol": {
                "content": contract_source
            }
        },
        "settings": {
            "outputSelection": {
                "*": {
                    "*": [
                        "abi",
                        "metadata",
                        "evm.bytecode",
                        "evm.sourceMap"
                    ]
                }
            }
        },
    },
    solc_version="0.8.0",
)

# 6. Extract bytecode and ABI
bytecode = compiled_sol["contracts"]["Attendance.sol"]["Attendance"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["Attendance.sol"]["Attendance"]["abi"]

# 7. Connect to local Ethereum node (Ganache)
provider_url = os.getenv("PROVIDER_URL", "http://127.0.0.1:7545")
w3 = Web3(Web3.HTTPProvider(provider_url))
if not w3.is_connected():
    raise Exception(f"Unable to connect to Ethereum node at {provider_url}")

# 8. Load PRIVATE_KEY from .env
private_key = os.getenv("PRIVATE_KEY")
if not private_key:
    raise Exception("Please set PRIVATE_KEY in your .env file")

account = w3.eth.account.from_key(private_key)
deployer_address = account.address
print("Deployer/Authorized address:", deployer_address)

# For convenience: 20 Gwei in wei
GAS_PRICE_20_GWEI = 20 * 10**9

def deploy_contract():
    Attendance = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(deployer_address)

    tx_dict = Attendance.constructor().build_transaction({
        'chainId': w3.eth.chain_id,
        'gas': 3000000,
        'gasPrice': GAS_PRICE_20_GWEI,
        'nonce': nonce,
    })

    signed_tx = w3.eth.account.sign_transaction(tx_dict, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print("Deploying contract...")

    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Contract deployed at address:", tx_receipt.contractAddress)
    return tx_receipt.contractAddress

def get_contract(address):
    return w3.eth.contract(address=address, abi=abi)

def record_attendance(contract_address, name):
    contract = get_contract(contract_address)
    nonce = w3.eth.get_transaction_count(deployer_address)

    tx = contract.functions.recordAttendance(name).build_transaction({
        'chainId': w3.eth.chain_id,
        'gas': 300000,
        'gasPrice': GAS_PRICE_20_GWEI,
        'nonce': nonce,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Submitting attendance for '{name}'...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Attendance recorded in tx {tx_hash.hex()}")
    return receipt

def get_record_count(contract_address):
    # Calls getRecordCount() in the contract
    contract = get_contract(contract_address)
    return contract.functions.getRecordCount().call()

def get_all_records(contract_address):
    contract = get_contract(contract_address)
    
    # 1. Get the total number of records
    record_count = get_record_count(contract_address)
    
    # 2. If record_count is 0 or 1, handle that edge case
    if record_count < 2:
        print("Not enough records or zero records. Returning partial or empty list.")
        # We'll just return what's there, but we must not pass an invalid range
        # If you have 1 record, pass (0,1); if 0 records, pass (0,0) is invalid
        if record_count == 0:
            return []
        else:
            return contract.functions.getAllRecords(0, 1).call()
    
    # 3. Retrieve all records from index 0 to record_count
    return contract.functions.getAllRecords(0, record_count).call()

if __name__ == "__main__":
    try:
        # Deploy contract
        contract_address = deploy_contract()

        # Record attendance for two names
        record_attendance(contract_address, "Alice")
        record_attendance(contract_address, "Bob")

        # Fetch all records
        all_records = get_all_records(contract_address)
        print("All records from chain:", all_records)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
"""
"""
import os
import os.path
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv
import hashlib
import time

# Load environment variables from .env
load_dotenv()

# Install solc version 0.8.0 if needed.
install_solc('0.8.0')

# Build path to Attendance.sol in the same folder
sol_path = os.path.join(os.path.dirname(__file__), "Attendance.sol")
if not os.path.isfile(sol_path):
    raise FileNotFoundError(f"Could not find Attendance.sol at: {sol_path}")

# Read the Solidity contract
with open(sol_path, "r") as file:
    contract_source = file.read()

# Compile the Solidity contract
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {
            "Attendance.sol": {
                "content": contract_source
            }
        },
        "settings": {
            "outputSelection": {
                "*": {
                    "*": [
                        "abi",
                        "metadata",
                        "evm.bytecode",
                        "evm.sourceMap"
                    ]
                }
            }
        },
    },
    solc_version="0.8.0",
)

# Extract bytecode and ABI
bytecode = compiled_sol["contracts"]["Attendance.sol"]["Attendance"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["Attendance.sol"]["Attendance"]["abi"]

# Connect to local Ethereum node (Ganache)
provider_url = os.getenv("PROVIDER_URL", "http://127.0.0.1:7545")
w3 = Web3(Web3.HTTPProvider(provider_url))
if not w3.is_connected():
    raise Exception(f"Unable to connect to Ethereum node at {provider_url}")

# Load PRIVATE_KEY from .env
private_key = os.getenv("PRIVATE_KEY")
if not private_key:
    raise Exception("Please set PRIVATE_KEY in your .env file")

account = w3.eth.account.from_key(private_key)
deployer_address = account.address
print("Deployer/Authorized address:", deployer_address)

# For convenience: 20 Gwei in wei
GAS_PRICE_20_GWEI = 20 * 10**9

def compute_attendance_hash(name, timestamp, secret_key):
    data_str = f"{name}|{timestamp}|{secret_key}"
    return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

def deploy_contract():
    Attendance = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(deployer_address)
    tx_dict = Attendance.constructor().build_transaction({
        'chainId': w3.eth.chain_id,
        'gas': 3000000,
        'gasPrice': GAS_PRICE_20_GWEI,
        'nonce': nonce,
    })
    signed_tx = w3.eth.account.sign_transaction(tx_dict, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print("Deploying contract...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Contract deployed at address:", tx_receipt.contractAddress)
    return tx_receipt.contractAddress

def get_contract(address):
    return w3.eth.contract(address=address, abi=abi)

def record_attendance(contract_address, name, secret_key):
    contract = get_contract(contract_address)
    nonce = w3.eth.get_transaction_count(deployer_address)
    # Use the current timestamp
    record_time = int(time.time())
    # Compute the hash for integrity using secret_key
    record_hash = compute_attendance_hash(name, record_time, secret_key)
    
    # Build transaction for recordAttendance with name and recordHash
    tx = contract.functions.recordAttendance(name, record_hash).build_transaction({
        'chainId': w3.eth.chain_id,
        'gas': 300000,
        'gasPrice': GAS_PRICE_20_GWEI,
        'nonce': nonce,
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Submitting attendance for '{name}' with hash {record_hash}...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Attendance recorded in tx {tx_hash.hex()}")
    return receipt

def get_record_count(contract_address):
    contract = get_contract(contract_address)
    return contract.functions.getRecordCount().call()

def get_all_records(contract_address):
    contract = get_contract(contract_address)
    total_records = get_record_count(contract_address)
    if total_records == 0:
        return []
    return contract.functions.getAllRecords(0, total_records).call()

if __name__ == "__main__":
    # Define a secret key for hashing (should be kept secret in production, e.g., stored in .env)
    SECRET_KEY = "YourSecretKeyHere"
    
    try:
        contract_address = deploy_contract()
        record_attendance(contract_address, "Alice", SECRET_KEY)
        record_attendance(contract_address, "Bob", SECRET_KEY)
        all_records = get_all_records(contract_address)
        print("All records from chain:", all_records)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
"""
import os
import os.path
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv
import hashlib
import time

load_dotenv()
install_solc('0.8.0')

# Adjust path if needed
sol_path = os.path.join(os.path.dirname(__file__), "Attendance.sol")
if not os.path.isfile(sol_path):
    raise FileNotFoundError(f"Could not find Attendance.sol at: {sol_path}")

with open(sol_path, "r") as file:
    contract_source = file.read()

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {
            "Attendance.sol": {
                "content": contract_source
            }
        },
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                }
            }
        },
    },
    solc_version="0.8.0",
)

bytecode = compiled_sol["contracts"]["Attendance.sol"]["Attendance"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["Attendance.sol"]["Attendance"]["abi"]

provider_url = os.getenv("PROVIDER_URL", "http://127.0.0.1:7545")
w3 = Web3(Web3.HTTPProvider(provider_url))
if not w3.is_connected():
    raise Exception(f"Unable to connect to Ethereum node at {provider_url}")

private_key = os.getenv("PRIVATE_KEY")
if not private_key:
    raise Exception("Please set PRIVATE_KEY in your .env file")

account = w3.eth.account.from_key(private_key)
deployer_address = account.address
print("Deployer/Authorized address:", deployer_address)

GAS_PRICE_20_GWEI = 20 * 10**9

def compute_attendance_hash(name, timestamp, secret_key):
    data_str = f"{name}|{timestamp}|{secret_key}"
    return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

def deploy_contract():
    Attendance = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(deployer_address)
    tx_dict = Attendance.constructor().build_transaction({
        'chainId': w3.eth.chain_id,
        'gas': 3000000,
        'gasPrice': GAS_PRICE_20_GWEI,
        'nonce': nonce,
    })
    signed_tx = w3.eth.account.sign_transaction(tx_dict, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print("Deploying contract...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Contract deployed at address:", tx_receipt.contractAddress)
    return tx_receipt.contractAddress

def get_contract(address):
    return w3.eth.contract(address=address, abi=abi)

def record_attendance(contract_address, name, secret_key):
    contract = get_contract(contract_address)
    nonce = w3.eth.get_transaction_count(deployer_address)

    # We'll create a recordHash using the name + timestamp + secret_key
    timestamp = int(time.time())
    record_hash = compute_attendance_hash(name, timestamp, secret_key)

    tx = contract.functions.recordAttendance(name, record_hash).build_transaction({
        'chainId': w3.eth.chain_id,
        'gas': 300000,
        'gasPrice': GAS_PRICE_20_GWEI,
        'nonce': nonce,
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Submitting attendance for '{name}' with recordHash '{record_hash}'...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Attendance recorded in tx {tx_hash.hex()}")
    return receipt

def get_record_count(contract_address):
    contract = get_contract(contract_address)
    return contract.functions.getRecordCount().call()

def get_all_records(contract_address):
    contract = get_contract(contract_address)
    total_records = get_record_count(contract_address)
    if total_records == 0:
        return []
    return contract.functions.getAllRecords(0, total_records).call()

if __name__ == "__main__":
    SECRET_KEY = "YourSecretKeyHere"  # For hashing
    try:
        contract_address = deploy_contract()
        record_attendance(contract_address, "Alice", SECRET_KEY)
        record_attendance(contract_address, "Bob", SECRET_KEY)

        all_recs = get_all_records(contract_address)
        print("All records from chain:", all_recs)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
