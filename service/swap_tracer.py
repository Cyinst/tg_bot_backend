
import logging
from web3_helper import Web3Helper
from web3.types import LogReceipt, TxData
import json

logger = logging.getLogger(__name__)

miss_pair_cache = []

def find_swaps(block_start, w3 = None):
    if not w3:
        w3 = Web3Helper()
    block_end = w3.get_block_height()

    signature_uni_v3 = '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67'
    event_filter = {
        'topics': [signature_uni_v3],
        'fromBlock': block_start,
        'toBlock': block_end,
    }
    logs = w3.w3.eth.get_logs(event_filter)
    swaps = []
    for log in logs:
        isSwap, swap_tuple = uniswap_v3_filter(w3=w3.w3, log=log)
        if isSwap and swap_tuple:
            swap = {}
            swap['transaction_hash'] = swap_tuple[0]
            swap['block_number'] = swap_tuple[1]
            swap['from_address'] = w3.w3.to_checksum_address(swap_tuple[2])
            swap['to_address'] = w3.w3.to_checksum_address(swap_tuple[3])
            # amount with minimal decimal, example: 1 eth amount = 1 * 10**18 here.
            swap['from_amount'] = int(swap_tuple[4])
            swap['to_amount'] = int(swap_tuple[5])
            swap['from_token'] = w3.w3.to_checksum_address(swap_tuple[6])
            swap['to_token'] = w3.w3.to_checksum_address(swap_tuple[7])
            swap['tx_origin'] = w3.w3.to_checksum_address(swap_tuple[8])
            swap['pair_address'] = w3.w3.to_checksum_address(swap_tuple[9])
            swap['protocol'] = swap_tuple[10]
            swap['fee'] = swap_tuple[11]
            swaps.append(swap)
    return swaps, block_end + 1


def uniswap_v3_filter(w3, log: LogReceipt, tx: TxData = None):
    if len(log['topics']) > 0:
        # Swap Event
        if log['topics'][0].hex() == '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67':  # Swap
            from_address = '0x' + log['topics'][1].hex()[26:]
            to_address = '0x' + log['topics'][2].hex()[26:]
            data = log['data'].hex()[2:]
            hex_0xf = 2**256 - 1
            amount0 = data[:64]
            amount1 = data[64: 64 * 2]
            pair_address = log['address']

            if pair_address in miss_pair_cache:
                return False, ()

            # in case some shit bots write Swap Event in their own comtracts
            try:
                from_token, to_token, fee = get_pair(w3, pair_address)
            except:
                logger.warning(
                    f"log[{log['blockNumber']}-{log['transactionHash'].hex()}-{log['logIndex']}] pair_address: {pair_address} not found token0/1!")
                miss_pair_cache.append(pair_address)
                return False, ()
            
            block_number = log['blockNumber']
            transaction_hash = log['transactionHash'].hex()
            protocol = 'UniswapV3'
            tx_origin = get_tx_origin(w3, transaction_hash, tx)
            if int(amount0[0], 16) < 8 and int(amount1[0], 16) >= 8:
                from_amount = int(amount0, 16)
                to_amount = 2**256 - int(amount1, 16)
                from_token, to_token = from_token, to_token
                return True, (
                    transaction_hash, block_number, from_address, to_address, str(from_amount), str(to_amount),
                    from_token,
                    to_token, tx_origin, pair_address, protocol, fee)
            elif int(amount0[0], 16) >= 8 and int(amount1[0], 16) < 8:
                from_amount = int(amount1, 16)
                to_amount = 2**256 - int(amount0, 16)
                to_token, from_token = from_token, to_token
                return True, (
                    transaction_hash, block_number, from_address, to_address, str(from_amount), str(to_amount),
                    from_token,
                    to_token, tx_origin, pair_address, protocol, fee)
            elif (int(amount0[0], 16) == 0 and int(amount1[0], 16) >= 0) or (int(amount0[0], 16) >= 0 and int(amount1[0], 16) == 0):
                return False, ()
            else:
                logger.warning(f"log[{log['blockNumber']}-{log['transactionHash'].hex()}-{log['logIndex']}] amount calculate error!")
                return False, ()
        else:
            return False, ()
    else:
        return False, ()


def get_pair(w3, pair_address):
    abi = '[{"constant": true,"inputs": [],"name": "token0","outputs": [{"internalType": "address","name": "","type": "address"}],"payable": false,"stateMutability": "view","type": "function"},{"constant": true,"inputs": [],"name": "token1","outputs": [{"internalType": "address","name": "","type": "address"}],"payable": false,"stateMutability": "view","type": "function"}, {"inputs":[],"name":"fee","outputs":[{"internalType":"uint24","name":"","type":"uint24"}],"stateMutability":"view","type":"function"}]'
    abi = json.loads(abi)
    contract = w3.eth.contract(address=pair_address, abi=abi)
    token0 = contract.functions.token0().call()
    token1 = contract.functions.token1().call()
    fee = contract.functions.fee().call()
    return token0, token1, fee


def get_tx_origin(w3, transaction_hash, tx):
    if tx is not None:
        return tx["from"]
    return w3.eth.get_transaction(transaction_hash)['from']