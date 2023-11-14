from web3 import Web3
from web3.exceptions import TransactionNotFound
from web3.middleware import geth_poa_middleware
from eth_utils import to_bytes, to_hex
from typing import List, Optional, Union
from web3.types import BlockData, TxData, ENS
from eth_account.account import Account
import json


class Web3Helper():
    def __init__(self, path='https://arb1.arbitrum.io/rpc', id = None, priv_key = None):
        if isinstance(path, list):
            self.connect_pool = path
            self.url = path[0]
        else:
            self.connect_pool = []
            self.url = path
        if self.url[:2] == 'ws':
            self.w3 = Web3(Web3.WebsocketProvider(self.url, websocket_timeout=30))
        elif self.url[:4] == 'http':
            self.w3 = Web3(Web3.HTTPProvider(self.url, request_kwargs={'timeout': 30}))
        else:
            self.w3 = Web3(Web3.IPCProvider(self.url, timeout=30))
        self.id = id if id in ['eth', 'bsc', 'polygon', 'arbi'] else None
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.priv_key = priv_key
        self.wallet_address = Account.from_key(priv_key).address if priv_key else None
        self.nonce = self.w3.eth.get_transaction_count(self.wallet_address) if self.wallet_address else None
        # print("web3 connect: " + repr(self.w3.is_connected()))

    def process_block(self, block):
        pass

    def process_transaction(self, tx):
        pass

    def reset_connect(self):
        if self.connect_pool:
            for path in self.connect_pool:
                if path[:2] == 'ws':
                    self.w3 = Web3(Web3.WebsocketProvider(path, websocket_timeout=30))
                elif path[:4] == 'http':
                    self.w3 = Web3(Web3.HTTPProvider(path, request_kwargs={'timeout': 30}))
                else:
                    self.w3 = Web3(Web3.IPCProvider(path, timeout=30))
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                try:
                    if self.w3.is_connected():
                            return True
                except:
                    continue
        return False

    def crawl_blocks(self, block_num_list: List[int], with_transactions: bool = True):
        block_list: List[BlockData] = []
        tx_list: List[TxData] = []
        for block_num in block_num_list:
            block: BlockData = self.w3.eth.get_block(block_num, full_transactions=with_transactions)
            self.process_block(block)
            block_list.append(block)
            if with_transactions:
                tx_list.extend(block.transactions)
        return block_list, tx_list

    def crawl_block(self, block_num, with_transactions: bool = True):
        tx_list: List[TxData] = []
        block: BlockData = self.w3.eth.get_block(block_num, full_transactions=with_transactions)
        self.process_block(block)
        if with_transactions:
            tx_list.extend(block.transactions)
        return block, tx_list

    def crawl_transaction_receipt(self, transaction_hash):
        try:
            return self.w3.eth.get_transaction_receipt(transaction_hash)
        except TransactionNotFound as err:
            print(err)
            return None

    def get_block_height(self) -> int:
        return self.w3.eth.get_block_number()

    def get_balance(self, account, token = None):
        abi = '[{"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]'
        if token:
            cntr = self.load_contract(abi, token)
            return cntr.functions.balanceOf(Web3.to_checksum_address(account)).call()
        else:
            return self.w3.eth.get_balance(account)

    def load_contract(self, abi, contract_address):
        if abi[0] != '[':
            with open(abi, 'r') as f:
                abi = f.read()
        abi = json.loads(abi)
        contract = self.w3.eth.contract(address=contract_address, abi=abi)
        return contract
    
    def transfer(self, recipient, amount: int, token = None, priv_key = None, nonce = None) -> bool:
        assert self.nonce != None or priv_key
        tx_param = {}
        if token:
            if isinstance(token, str):
                abi = """
                    {
                        "inputs": [
                            {
                            "internalType": "address",
                            "name": "to",
                            "type": "address"
                            },
                            {
                            "internalType": "uint256",
                            "name": "amount",
                            "type": "uint256"
                            }
                        ],
                        "name": "transfer",
                        "outputs": [
                            {
                            "internalType": "bool",
                            "name": "",
                            "type": "bool"
                            }
                        ],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    }
                    """
                token = self.load_contract(abi, token)
            tx_param = token.functions.transfer(recipient, amount).build_transaction({
                'from': self.wallet_address,
                'nonce': self.get_nonce(Account.from_key(priv_key).address if priv_key else None)
            })
        else:
            tx_param = {
                'to': recipient,
                'value': amount,
                'nonce': self.get_nonce(Account.from_key(priv_key).address if priv_key else None)
            }
            if self.id == 'arbi':
                tx_param['gas'] = 1_000_000
                tx_param['maxFeePerGas'] = Web3.to_wei(0.4, 'gwei')
                tx_param['maxPriorityFeePerGas'] = Web3.to_wei(0.3, 'gwei')
                tx_param['type'] = 2
                tx_param['chainId'] = 42161
            if self.id != 'arbi':
                tx_param['gas'] = 21000
                tx_param['gasPrice'] = self.w3.eth.gas_price
        rc, success = self.send_tx(tx_param, priv_key=priv_key)
        return rc, success

    def send_tx(self, tx_param, priv_key = None) -> bool:
        signed_tx = self.w3.eth.account.sign_transaction(tx_param, priv_key if priv_key else self.priv_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        rc = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if rc['status'] == 1:
            self.update_nonce(self.nonce + 1)
        return rc, rc['status'] == 1

    def get_nonce(self, address = None):
        return self.w3.eth.get_transaction_count(address) if address else self.nonce

    def update_nonce(self, nonce):
        self.nonce = self.nonce + 1 if self.nonce != None else self.nonce
        return self.nonce
    