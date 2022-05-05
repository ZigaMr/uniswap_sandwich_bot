#!/usr/bin/python
import datetime
import time
import random
import json

import pandas as pd
import requests
from fetchABI import fetch_abi
# from web3.auto import w3
from web3 import Web3, HTTPProvider
from helper_functions import competition, get_acceptable_tokens, get_blocks
import traceback
from etherscan_analysis.EtherScan import EtherScan
from tests.thegraph_test import *
import sqlite3 as sql
import datetime as dt
import numpy as np
from bloxroute_cli.provider.ws_provider import WsProvider
import asyncio
from eth_account.signers.local import LocalAccount
from web3.middleware import construct_sign_and_send_raw_middleware
from flashbots import flashbot
import rlp
from eth_utils import keccak, to_checksum_address, to_bytes
import time
from eth_account.account import Account
import hexbytes
from tests.ABIs import WETH_ABI, uniswap_pair_abi, erc_20_abi, \
    my_contract_abi, chiGasToken_abi, my_contract_bytecode
import websockets

# import logging
pd.set_option('display.float_format', lambda x: '%.3f' % x)
# logging.basicConfig(filename='LogTx.log', encoding='utf-8', level=logging.DEBUG)
# logging.info('=================================================================')
# logging.info('Starting logger at datetime, '+str(datetime.now()))
conn_main_db = sql.connect('etherscan_analysis/main_db.db')

w3 = Web3(HTTPProvider("https://mainnet.infura.io/v3/"))  # Mainnet w3
# w3 = Web3(HTTPProvider("https://eth-mainnet.alchemyapi.io/v2/"))
etherscan_key = ''  # Enter your Etherscan API key here
pvt_key = ''  # Enter your private key here
sig_key = ''  # Enter your signature key here
ETH_ACCOUNT_FROM: LocalAccount = Account.from_key(pvt_key)  # Mainnet ETH account
my_contract = w3.eth.contract(address="contract_address", bytecode=my_contract_bytecode)
ETH_ACCOUNT_SIGNATURE: LocalAccount = Account.from_key(sig_key)

w3.middleware_onion.add(construct_sign_and_send_raw_middleware(ETH_ACCOUNT_FROM))
flashbot(w3, ETH_ACCOUNT_SIGNATURE)

WETH_ERC20_TOKEN = w3.toChecksumAddress('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
weth_contract = w3.eth.contract(WETH_ERC20_TOKEN, abi=erc_20_abi)
uniswap_address = '0x7a250d5630b4cf539739df2c5dacb4c659f2488d'
sushiswap_address = '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F'.lower()

uniswap_contract = w3.eth.contract(w3.toChecksumAddress('0x7a250d5630b4cf539739df2c5dacb4c659f2488d'),
                                   abi=json.load(open('UniswapABI.json', 'r'))['abi'])
sushiswap_contract = w3.eth.contract(w3.toChecksumAddress('0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F'),
                                     abi=json.load(open('UniswapABI.json', 'r'))['abi'])

tokens = {'POLK': [w3.toChecksumAddress('0xd478161c952357f05f0292b56012cd8457f1cfbf'),
                   w3.toChecksumAddress('0x05f04F112A286c4c551897fB19ED2300272656c8')],
          'MOD': [w3.toChecksumAddress('0xea1ea0972fa092dd463f2968f9bb51cc4c981d71'),
                  w3.toChecksumAddress('0xfca090c1868004bec9c91f53db013288dc21c55b')],
          'BMI': [w3.toChecksumAddress('0x725c263e32c72ddc3a19bea12c5a0479a81ee688'),
                  w3.toChecksumAddress('0xa9bd7eef0c7affbdbdae92105712e9ff8b06ed49')],
          'DAO': [w3.toChecksumAddress('0x0f51bb10119727a7e5ea3538074fb341f56b09ad'),
                  w3.toChecksumAddress('0x7dd3f5705504002dc946aeafe6629b9481b72272')]
          # w3.toChecksumAddress('0xf3dcbc6d72a4e1892f7917b7c43b74131df8480e'): 'BDP'
          }
contract_df = pd.DataFrame(columns=['name', 'token', 'contract'])
contracts = dict()
for i, j in tokens.items():
    contract_df.loc[len(contract_df)] = [i, j[0], j[1]]
    fetch_abi(j[1], etherscan_key)
    abi = json.load(open(j[1] + '.json', 'r'))['abi']
    contracts[i] = [w3.eth.contract(address=j[0], abi=abi).functions.balanceOf(j[1]),
                    w3.eth.contract(address=WETH_ERC20_TOKEN, abi=abi).functions.balanceOf(j[1])]

uni = UniGraph()
sushi = UniGraph(dex='sushi')
# uni.get_history(size_max=10000)
sushi.get_all_pairs(size_max=3000, first=500, orderby='reserveETH')
uni.get_all_pairs(size_max=5000, first=500, orderby='reserveETH')


# uni.pairs = pd.read_pickle('pairs.pkl')
def prepare_data(uni):
    uni.pairs['token1_hash'] = uni.pairs['token1_hash'].apply(w3.toChecksumAddress)
    uni.pairs['token0_hash'] = uni.pairs['token0_hash'].apply(w3.toChecksumAddress)
    uni.pairs['id'] = uni.pairs['id'].apply(w3.toChecksumAddress)

    d = uni.pairs[['token0_hash', 'token0_symbol']].set_index('token0_hash').to_dict()['token0_symbol']
    d.update(uni.pairs[['token1_hash', 'token1_symbol']].set_index('token1_hash').to_dict()['token1_symbol'])

    empirical_pairs = list(map(w3.toChecksumAddress,
                               list(filter(lambda x: len(x) == 42,
                                           set(
                                               get_acceptable_tokens(sql,
                                                                     '0x000000005736775feb0c8568e7dee77222a26880',
                                                                     '0x000000005736775feb0c8568e7dee77222a26880') +
                                               get_acceptable_tokens(sql,
                                                                     '0xfad95B6089c53A0D1d861eabFaadd8901b0F8533'.lower(),
                                                                     '0xfad95B6089c53A0D1d861eabFaadd8901b0F8533'.lower()) +
                                               get_acceptable_tokens(sql,
                                                                     '0x00000000b7ca7e12dcc72290d1fe47b2ef14c607'.lower(),
                                                                     '0x00000000b7ca7e12dcc72290d1fe47b2ef14c607'.lower()) +
                                               get_acceptable_tokens(sql,
                                                                     '0x00000000003b3cc22af3ae1eac0440bcee416b40',
                                                                     '0x00000000003b3cc22af3ae1eac0440bcee416b40') +
                                               get_acceptable_tokens(sql,
                                                                     '0x000000000000cb53d776774284822b1298ade47f'.lower(),
                                                                     '0x000000000000cb53d776774284822b1298ade47f'.lower()) +
                                               get_acceptable_tokens(sql,
                                                                     '0x0000000099cb7fc48a935bceb9f05bbae54e8987'.lower(),
                                                                     '0x0000000099cb7fc48a935bceb9f05bbae54e8987'.lower())
                                           )))))
    print('Nr. of empirical pairs ', len(empirical_pairs))
    # Check the % deflationary tokens
    c = dict()
    token_supplies = dict()
    t1 = time.time()
    k = c.keys()
    for i, j in uni.pairs[['id', 'token0_hash', 'token1_hash']].iterrows():
        if j['token0_hash'] == WETH_ERC20_TOKEN or j['token1_hash'] == WETH_ERC20_TOKEN:
            token_hash = j['token0_hash' if j['token0_hash'] != WETH_ERC20_TOKEN else 'token1_hash']
            if token_hash not in k and token_hash in empirical_pairs:
                c[token_hash] = [
                    w3.eth.contract(address=token_hash,
                                    abi=abi).functions.balanceOf(j['id']),
                    w3.eth.contract(address=WETH_ERC20_TOKEN, abi=abi).functions.balanceOf(j['id'])]
                token_supplies[token_hash] = w3.eth.contract(address=token_hash,
                                                             abi=abi).functions.totalSupply()
    print(time.time() - t1)
    return c, d, token_supplies

c, d, token_supplies = prepare_data(uni)
c_sushi, d_sushi, token_supplies_sushi = prepare_data(sushi)

def log(*args):
    print('-' * 40)
    print(time.ctime())
    print(args)

def mk_contract_address(sender: str, nonce: int) -> str:
    """Create a contract address using eth-utils.
    # https://ethereum.stackexchange.com/a/761/620
    """
    sender_bytes = to_bytes(hexstr=sender)
    raw = rlp.encode([sender_bytes, nonce])
    h = keccak(raw)
    address_bytes = h[12:]
    return to_checksum_address(address_bytes)


def build_bundle(nonce: int,
                 to: str,
                 block_number: str,
                 gas_tokens: list,
                 weth_amount_buy: int,
                 weth_amount_sell: int,
                 weth_amount_contract: int,
                 token_amount: int,
                 contract_router,
                 token_address: str,
                 miner_bribe: int):
    block_number = hex(block_number)[2:]
    weth_amount_hex = hex(int(weth_amount_buy))[2:]
    token_amount_hex = hex(token_amount)[2:]
    # Buy tx
    buy = {'value': 0,
           'gas': 150000,
           'gasPrice': 0,
           'nonce': nonce,  # int(w3.eth.getTransactionCount(acct.address)),
           'to': to,
           'data': '0x{buy_byte}' +
                   block_number +
                   '0' * (28 - len(weth_amount_hex)) + weth_amount_hex +
                   '0' * (28 - len(token_amount_hex)) + token_amount_hex +
                   contract_router.address[2:] +
                   "{gas_tokens}"}
    # signed_transaction_buy = ETH_ACCOUNT_FROM.sign_transaction(buy)
    token_amount_hex = hex(token_amount - 1)[2:]
    weth_amount_hex = hex(int(weth_amount_sell))[2:]
    weth_amount_contract = hex(int(weth_amount_contract))[2:]
    sell = {'value': 0,
            'gas': 150000,
            'gasPrice': miner_bribe,
            'nonce': nonce + 1,  # w3.eth.getTransactionCount(acct.address),
            'to': to,
            'data': '0x{sell_byte}' +
                    block_number +
                    '0' * (28 - len(weth_amount_hex)) + weth_amount_hex +
                    '0' * (28 - len(token_amount_hex)) + token_amount_hex +
                    contract_router.address[2:] +
                    token_address[2:] +
                    '0' * (28 - len(weth_amount_contract)) + weth_amount_contract +
                    "{gas_tokens}"}
    # signed_transaction_sell = ETH_ACCOUNT_FROM.sign_transaction(sell)

    return buy, sell


def get_optimal_bundle(block_number_max,
                       block_target,
                       gas_tokens,
                       bin_,
                       expected_tokens,
                       token_supplies,
                       contract_router,
                       params,
                       ETH_ACCOUNT_FROM,
                       weth_contract,
                       t,
                       n_gas_tokens_range,
                       bribe_pct,
                       ):

    l = []
    tim = time.time()
    target_tx = rlp.encode([int(t[i], 16) if isinstance(t[i], str) and t[i][:2] == '0x' else int(t[i]) for i in
                            ['nonce', 'gasPrice', 'gas', 'to', 'value',
                             'input', 'v', 'r', 's']]).hex()
    r = []
    buy, sell = build_bundle(w3.eth.getTransactionCount(ETH_ACCOUNT_FROM.address),
                             my_contract.address,
                             block_number_max,
                             gas_tokens,
                             int(bin_[0]),
                             int(bin_[1]),
                             weth_contract.functions.balanceOf(my_contract.address).call() -
                             int(bin_[0]) + int(bin_[1]) - 1,
                             int(expected_tokens),
                             contract_router,
                             token_supplies[w3.toChecksumAddress(params['path'][-1])].address,
                             0)
    buy_template = buy['data']
    sell_template = sell['data']
    if contract_router.functions.token0().call() == weth_contract.address:
        buy_sell_dict = {0: ['08', '09'], 1: ['08', '09'], 2: ['08', '09'], 3: ['01', '02']}
    else:
        buy_sell_dict = {0: ['07', '0a'], 1: ['07', '0a'], 2: ['07', '0a'], 3: ['00', '03']}
    print('Pre simulation time: ', time.time() - tim)
    gas_price = int(w3.eth.fee_history(1, 'latest').baseFeePerGas[0])
    for i in range(n_gas_tokens_range):
        print('Block number', w3.eth.blockNumber)
        print('Block target', block_target)
        buy['data'] = buy_template.format(buy_byte=buy_sell_dict[i][0], gas_tokens="".join(gas_tokens[:i]))
        sell['data'] = sell_template.format(sell_byte=buy_sell_dict[i][1], gas_tokens="".join(gas_tokens[i:i * 2]))
        buy['gasPrice'] = gas_price
        sell['gasPrice'] = gas_price
        signed_transaction_buy = ETH_ACCOUNT_FROM.sign_transaction(buy)
        signed_transaction_sell = ETH_ACCOUNT_FROM.sign_transaction(sell)

        bundle = [
            {
                "signed_transaction": signed_transaction_buy.rawTransaction
            },
            {
                "signed_transaction": hexbytes.HexBytes(target_tx)
            },
            {
                "signed_transaction": signed_transaction_sell.rawTransaction,
            },
        ]
        tim2 = time.time()
        result = w3.flashbots.simulate(bundle, block_tag=block_target)
        if 'error' in result['results'][2].keys():
            print('errored')
            return l, r
        r.append(result)
        print('Simulation call: ', time.time() - tim2)

        l = [result['results'][0]['gasUsed'],
             result['results'][2]['gasUsed'] if 'error' not in result['results'][2].keys() else 0,
             i]
    print('Simulation took: ', time.time() - tim)
    gas_price = int(w3.eth.fee_history(1, 'latest').baseFeePerGas[-1])
    print('Gas price: ', gas_price)
    profit = bin_[1] - bin_[0]
    first_tx_price = gas_price
    last_tx_price = int((profit * bribe_pct - l[0] * gas_price) / l[1])
    if last_tx_price > first_tx_price:
        print('Potential profit: ', profit)
        print('Base fee: ', sum(l[:2]) * gas_price)
        print('Miner bribe: ', profit * bribe_pct - sum(l[:2]) * gas_price)
        print("The real shit!")
        buy['data'] = buy_template.format(buy_byte=buy_sell_dict[0][0], gas_tokens="")
        sell['data'] = sell_template.format(sell_byte=buy_sell_dict[0][1], gas_tokens="")
        buy['gasPrice'] = first_tx_price
        sell['gasPrice'] = last_tx_price
        signed_transaction_buy = ETH_ACCOUNT_FROM.sign_transaction(buy)
        signed_transaction_sell = ETH_ACCOUNT_FROM.sign_transaction(sell)
        bundle = [
            {
                "signed_transaction": signed_transaction_buy.rawTransaction
            },
            {
                "signed_transaction": hexbytes.HexBytes(target_tx)
            },
            {
                "signed_transaction": signed_transaction_sell.rawTransaction,
            },
        ]
        print('Preparation time: ', time.time() - tim)
        result = list(
            map(lambda x: w3.flashbots.send_bundle(bundle, target_block_number=block_target + x), range(1, 3)))

        print('Simulation time: ', time.time() - tim)
        bal_before = weth_contract.functions.balanceOf(my_contract.address).call(block_identifier=block_target - 1)
        bal_after = weth_contract.functions.balanceOf(my_contract.address).call(block_identifier=w3.eth.blockNumber)
        profit = bal_after - bal_before
        print("Balance before", bal_before)
        print("Balance after", bal_after)
        print("Profit: ", profit)
    return l, r


def expected_return_fees(token_pool, weth_pool, value, fee=997, pct=1):
    return (value * fee * token_pool / (weth_pool * 1000 + value * fee)) * pct


def calculate_frontrun_return(my_eth, target_eth, token_pool, weth_pool, div=10 ** 18, fee=997, pct=1):
    a1 = expected_return_fees(token_pool, weth_pool, my_eth, fee, pct)
    a2 = expected_return_fees(token_pool - a1, weth_pool + my_eth, target_eth, fee, pct)

    return (
    my_eth / div, expected_return_fees(weth_pool + my_eth + target_eth, token_pool - a2 - a1, a1, fee, pct) / div,
    a2 / div) if div else (
        my_eth, expected_return_fees(weth_pool + my_eth + target_eth, token_pool - a2 - a1, a1, fee, pct), a2)


def binary_search(target_eth, token_pool, weth_pool, out_min, error_margin, upper=5, lower=0, pct=1):
    if upper > lower:
        mid = (upper + lower) / 2
        my_eth, profit_eth, target_tokens = calculate_frontrun_return(mid * 10 ** 18, target_eth,
                                                                      token_pool, weth_pool, False, pct=pct)
        if abs(upper - lower) * 10 ** 18 < error_margin:
            print(upper)
            if target_tokens < out_min:
                return calculate_frontrun_return(lower * 10 ** 18, target_eth, token_pool, weth_pool, False, pct=pct)
            else:
                return my_eth, profit_eth, target_tokens

        if target_tokens < out_min:
            return binary_search(target_eth, token_pool, weth_pool, out_min, error_margin, mid, lower, pct=pct)
        else:
            return binary_search(target_eth, token_pool, weth_pool, out_min, error_margin, upper, mid, pct=pct)
    return False


def optimal_bid(r0, vx):
    return -(1000 / 997) * r0 + 997000 / 5991 * vx + 10 / 5991 * (-179730 * r0 * vx + 9999820270 * vx ** 2) ** (0.5)


class UniswapFrontRunner(object):

    def __init__(self, frontrun_contracts, frontrun_addresses):
        self.finished = False
        # accounts = send_request({'method': 'eth_accounts', 'params': []})
        # if len(accounts) != 1:
        #     raise Exception('You should have exactly one address activated. ' +
        #                     'Got {0} instead.'.format(accounts))
        self.address = "123"  # accounts[0]
        self.transaction_cache = []
        self.frontrun_contracts = frontrun_contracts
        self.frontrun_addresses = frontrun_addresses
        self.counter = 0
        self.conn = sql.connect('main_db.db')

        # self.loop = asyncio.get_event_loop()

    def get_ticks(self):
        return asyncio.run(self.async_frontrun2())

    async def async_frontrun2(self):
        uri = "wss://api.blocknative.com/v0"
        async with websockets.connect(uri) as ws:
            res = await ws.send(json.dumps({'timeStamp': str(dt.datetime.now().isoformat()),
                                            # 'dappId': '24f5031e-358e-4b47-9147-23f64a68cb94',
                                            # 'dappId': 'a7787354-2599-4940-940c-35c2f4fadcb6',
                                            # 'dappId': 'cbc0af03-ed9e-4bb3-951d-2c1f428da483',
                                            'dappId': '48e1b25e-eb10-4e26-8a45-5eaf27f2e9a7',
                                            'version': '1',
                                            'blockchain': {
                                                'system': 'ethereum',
                                                'network': 'main'},
                                            'categoryCode': 'initialize',
                                            'eventCode': 'checkDappId'}))
            print(res)
            subscribe_msg = {
                'timeStamp': str(dt.datetime.now().isoformat()),
                # 'dappId': '24f5031e-358e-4b47-9147-23f64a68cb94',
                # 'dappId': 'a7787354-2599-4940-940c-35c2f4fadcb6',
                # 'dappId': 'cbc0af03-ed9e-4bb3-951d-2c1f428da483',
                'dappId': '48e1b25e-eb10-4e26-8a45-5eaf27f2e9a7',
                "categoryCode": "configs",
                'version': '1',
                'blockchain': {
                    'system': 'ethereum',
                    'network': 'main'},
                "eventCode": "put",
                "config": {
                    "scope": '0x7a250d5630b4cf539739df2c5dacb4c659f2488d',
                    "filters": [{"_join": "OR", "terms": [{"contractCall.methodName": "swapExactETHForTokens"},
                                                          {"contractCall.methodName": "swapETHForExactTokens"}]},
                                {"value": {"gt": 500000000000000000}}
                                ],
                    "abi": abi,
                    "watchAddress": True
                }
            }
            res2 = await ws.send(json.dumps(subscribe_msg))
            self.nonce = w3.eth.getTransactionCount(ETH_ACCOUNT_FROM.address)
            self.gas_tokens = []  # [mk_contract_address(my_contract.address, i)[2:] for i in range(176, 258) if w3.eth.getCode(mk_contract_address(my_contract.address, i)).hex() != '0x']
            self.pct_bribe = .98

            while True:
                t = await ws.recv()
                data = json.loads(t)
                if 'event' not in data.keys() or 'transaction' not in data['event'].keys():
                    continue
                t = data['event']['transaction']

                if t[u'to'].lower() == uniswap_address:
                    try:
                        value = int(t[u'value'])
                        method, params = uniswap_contract.decode_function_input(t[u'input'])
                        if data['event']['contractCall']['methodName'] in ['swapExactETHForTokens',
                                                                           'swapETHForExactTokens', ]:

                            l = list(map(lambda x: d[x], params['path']))
                            params['path'].remove(WETH_ERC20_TOKEN)
                            e = c[w3.toChecksumAddress(params['path'][-1])][1].call()
                            token_pool = c[w3.toChecksumAddress(params['path'][-1])][0].call()
                            if method.fn_name == 'swapExactETHForTokens':
                                bin_ = binary_search(value, token_pool, e, params['amountOutMin'],
                                                     10 ** 10, 100, 0, pct=1)
                            else:
                                bin_ = binary_search(value, token_pool, e, params['amountOut'],
                                                     10 ** 10, 100, 0, pct=1)
                            bin_ = (bin_[0], bin_[1] - 10000000, bin_[2])
                            if bin_ == False or bin_[1] - bin_[0] < t['gas'] * int(t['gasPrice']):
                                if method.fn_name != 'swapExactETHForTokens':
                                    print(method.fn_name)
                                continue
                            elif bin_[0] > 10 * 10 ** 18:
                                print('Not enough wETH in contract')
                                continue
                            print('')
                            print('Uniswap')
                            print(' --> '.join(l), t[u'hash'], dt.datetime.utcnow())
                            print(r'https://etherscan.io/tx/' + t[u'hash'], value / 10 ** 18)
                            print(method.fn_name)

                            print(dt.datetime.now())
                            print(r'Token: https://www.dextools.io/app/uniswap/pair-explorer/' +
                                  str(c[params['path'][-1]][0]).split("'")[1])
                            print('ETH in reserve: ', e / 10 ** 18)
                            print('Ratio: ', e / token_pool)
                            print('ETH reserve increase by {}%'.format(round(100 * value / e, 2)))
                            print('Expected tokens: ', expected_return_fees(token_pool, e, value))
                            # print('Optimal bid: ', optimal_bid(e, value)/10**18)

                            # df_search_100 = pd.DataFrame([calculate_frontrun_return(i * 10 ** 18, value, token_pool, e, div=10 ** 18, fee=990) for i in
                            #                           [i * 0.01 for i in range(50, 1000)]])
                            # df_search_100 = df_search_100[df_search_100[2] > params['amountOutMin'] / 10 ** 18]

                            print('Optimal bid 0.3% ')
                            print(list(map(lambda x: x / 10 ** 18, bin_)) if bin_ else 'Slippage set too low')
                            expected_tokens = int(expected_return_fees(token_pool, e, bin_[0], fee=997, pct=1))
                            print('Tokens: ', expected_tokens)
                            contract_router = w3.eth.contract(
                                w3.toChecksumAddress(c[w3.toChecksumAddress(params['path'][-1])][0].args[0]),
                                abi=uniswap_pair_abi)
                            contract_token = w3.eth.contract(w3.toChecksumAddress(params['path'][-1]), abi=erc_20_abi)
                            bribe = self.pct_bribe if contract_token.functions.balanceOf(
                                my_contract.address).call() > 0 else .99
                            print('Bribe: ', bribe)

                            block = w3.eth.blockNumber
                            l2, r = get_optimal_bundle(block + 5,
                                                       block,
                                                       self.gas_tokens,
                                                       bin_,
                                                       expected_tokens,
                                                       token_supplies,
                                                       contract_router,
                                                       params,
                                                       ETH_ACCOUNT_FROM,
                                                       weth_contract,
                                                       t,
                                                       n_gas_tokens_range=1,
                                                       bribe_pct=bribe)
                            print(l2)
                            # result.wait()
                            # receipts = result.receipts()
                            # print('RawTx: ', rlp.encode([int(t[i], 16) for i in
                            #                              ['nonce', 'gasPrice', 'gas', 'to', 'value',
                            #                               'input', 'v', 'r', 's']]).hex())
                            # gt_i = 0
                            # while w3.eth.getCode(mk_contract_address(my_contract.address, i)).hex() != '0x':
                            #     gt_i += 1
                            #     if gt_i > 100:
                            #         break
                            tim = time.time()
                            print('Block number: ', w3.eth.blockNumber)
                            self.gas_tokens = [mk_contract_address(my_contract.address, i)[2:] for i in range(176, 258)
                                               if w3.eth.getCode(
                                    mk_contract_address(my_contract.address, i)).hex() != '0x']

                            print('Gas tokens generate time: ', time.time() - tim)
                            self.nonce = w3.eth.getTransactionCount(ETH_ACCOUNT_FROM.address)
                            print('RawTx: ', rlp.encode(
                                [int(t[i], 16) if isinstance(t[i], str) and t[i][:2] == '0x' else int(t[i]) for i in
                                 ['nonce', 'gasPrice', 'gas', 'to', 'value',
                                  'input', 'v', 'r', 's']]).hex())
                            print('Max slippage: ',
                                  params['amountOutMin'] / 10 ** 18 if 'amountOutMin' in params.keys() else params[
                                      'amountOut'])

                            self.weth_reserve = e
                            self.token_reserve = token_pool
                            # print('10ETH without fees and gas would net a {} return'.format(
                            #     round(calculate_frontrun_return(10 ** 19, value, token_pool, e) / 10 ** 18, 2) - 10))
                            # print('2ETH without fees and gas would net a {} return'.format(
                            #     round(calculate_frontrun_return(2 * 10 ** 18, value, token_pool, e) / 10 ** 18, 2) - 2))
                            # print('New Ratio: ', )
                        gas_price = int(t[u'gasPrice'])
                        print('Gas price: ', gas_price / 10 ** 9)
                        self.counter += 1
                        if gas_price / 10 ** 9 < 100:
                            # print('G as too low, skipping')
                            continue
                        print('Seems legit, writing to db...')
                        t['time_utc'] = dt.datetime.utcnow()
                        print('Estimate tx time: ',
                              int(EtherScan.get_time_estimate(int(t[u'gasPrice']), etherscan_key)['result']) / 60)
                        try:
                            if w3.eth.getTransaction(t[u'hash'])[u'blockHash'] == None:
                                print('Still pending...')
                                t['pending'] = 'true'
                            else:
                                print('Already confirmed')
                                t['pending'] = 'false'
                        except:
                            time.sleep(0.1)
                            print('Error - probably private tx')
                            t['pending'] = 'error'
                        tx_sql = pd.DataFrame([t])
                        tx_sql.drop('type', 1).to_sql('transaction_stream',
                                                      index=False,
                                                      con=self.conn,
                                                      if_exists='append')


                    except KeyError as e:
                        # traceback.print_exc()
                        print(e)
                        # print('Coin not reqistered')
                    except Exception as e:
                        print(e)
                        traceback.print_exc()
                elif t[u'to'] == sushiswap_address:  # and int(t[u'value'], 16) >= 500000000000000000:
                    try:
                        value = int(t[u'value'])
                        method, params = sushiswap_contract.decode_function_input(t[u'input'])
                        if data['event']['contractCall']['methodName'] in ['swapExactETHForTokens',
                                                                           'swapETHForExactTokens', ]:

                            l = list(map(lambda x: d[x], params['path']))
                            params['path'].remove(WETH_ERC20_TOKEN)
                            e = c[w3.toChecksumAddress(params['path'][-1])][1].call()
                            token_pool = c[w3.toChecksumAddress(params['path'][-1])][0].call()
                            if method.fn_name == 'swapExactETHForTokens':
                                bin_ = binary_search(value, token_pool, e, params['amountOutMin'],
                                                     10 ** 10, 100, 0, pct=1)
                            else:
                                bin_ = binary_search(value, token_pool, e, params['amountOut'],
                                                     10 ** 10, 100, 0, pct=1)
                            bin_ = (bin_[0], bin_[1] - 10000000, bin_[2])
                            if bin_ == False or bin_[1] - bin_[0] < t['gas'] * int(t['gasPrice']):
                                if method.fn_name != 'swapExactETHForTokens':
                                    print(method.fn_name)
                                continue
                            elif bin_[0] > 2.7 * 10 ** 18:
                                print('Not enough wETH in contract')
                                continue
                            print('')
                            print('Sushiswap')
                            print(' --> '.join(l), t[u'hash'], dt.datetime.utcnow())
                            print(r'https://etherscan.io/tx/' + t[u'hash'], value / 10 ** 18)
                            print(method.fn_name)

                            print(dt.datetime.now())
                            print(r'Token: https://www.dextools.io/app/sushiswap/pair-explorer/' +
                                  str(c[params['path'][-1]][0]).split("'")[1])
                            print('ETH in reserve: ', e / 10 ** 18)
                            print('Ratio: ', e / token_pool)
                            print('ETH reserve increase by {}%'.format(round(100 * value / e, 2)))
                            print('Expected tokens: ', expected_return_fees(token_pool, e, value))
                            # print('Optimal bid: ', optimal_bid(e, value)/10**18)

                            # df_search_100 = pd.DataFrame([calculate_frontrun_return(i * 10 ** 18, value, token_pool, e, div=10 ** 18, fee=990) for i in
                            #                           [i * 0.01 for i in range(50, 1000)]])
                            # df_search_100 = df_search_100[df_search_100[2] > params['amountOutMin'] / 10 ** 18]

                            print('Optimal bid 0.3% ')
                            print(list(map(lambda x: x / 10 ** 18, bin_)) if bin_ else 'Slippage set too low')
                            expected_tokens = int(expected_return_fees(token_pool, e, bin_[0], fee=997, pct=1))
                            print('Tokens: ', expected_tokens)
                            contract_router = w3.eth.contract(
                                w3.toChecksumAddress(c[w3.toChecksumAddress(params['path'][-1])][0].args[0]),
                                abi=uniswap_pair_abi)
                            contract_token = w3.eth.contract(w3.toChecksumAddress(params['path'][-1]), abi=erc_20_abi)
                            bribe = self.pct_bribe if contract_token.functions.balanceOf(
                                my_contract.address).call() > 0 else .99
                            print('Bribe: ', bribe)
                            # print(df_search.iloc[-1].to_string() if not df_search.empty else 'Slippage set too low')
                            # print('2% deflationary token:')
                            # print(df_search_005.iloc[-1].to_string() if not df_search_005.empty else 'Slippage set too low')
                            # print('Optimal bid 1% ')
                            # print(df_search_100.iloc[-1].to_string() if not df_search.empty else 'Slippage set too low')
                            block = w3.eth.blockNumber
                            l2, opt, r = get_optimal_bundle(block + 5,
                                                            block,
                                                            self.gas_tokens,
                                                            bin_,
                                                            expected_tokens,
                                                            token_supplies,
                                                            contract_router,
                                                            params,
                                                            ETH_ACCOUNT_FROM,
                                                            weth_contract,
                                                            t,
                                                            n_gas_tokens_range=1,
                                                            bribe_pct=bribe)
                            print(l2, opt)
                            # result.wait()
                            # receipts = result.receipts()
                            # print('RawTx: ', rlp.encode([int(t[i], 16) for i in
                            #                              ['nonce', 'gasPrice', 'gas', 'to', 'value',
                            #                               'input', 'v', 'r', 's']]).hex())
                            # gt_i = 0
                            # while w3.eth.getCode(mk_contract_address(my_contract.address, i)).hex() != '0x':
                            #     gt_i += 1
                            #     if gt_i > 100:
                            #         break
                            tim = time.time()
                            print('Block number: ', w3.eth.block_number())
                            self.gas_tokens = [mk_contract_address(my_contract.address, i)[2:] for i in range(176, 258)
                                               if w3.eth.getCode(
                                    mk_contract_address(my_contract.address, i)).hex() != '0x']

                            print('Gas tokens generate time: ', time.time() - tim)
                            self.nonce = w3.eth.getTransactionCount(ETH_ACCOUNT_FROM.address)
                            print('RawTx: ',
                                  rlp.encode([int(t[i], 16) if isinstance(t[i], str) and t[i][:2] == '0x'
                                              else int(t[i]) for i in ['nonce', 'gasPrice', 'gas', 'to', 'value',
                                                                       'input', 'v', 'r', 's']]).hex())
                            print('Max slippage: ',
                                  params['amountOutMin'] / 10 ** 18 if 'amountOutMin' in params.keys() else params[
                                      'amountOut'])

                            self.weth_reserve = e
                            self.token_reserve = token_pool
                            # print('10ETH without fees and gas would net a {} return'.format(
                            #     round(calculate_frontrun_return(10 ** 19, value, token_pool, e) / 10 ** 18, 2) - 10))
                            # print('2ETH without fees and gas would net a {} return'.format(
                            #     round(calculate_frontrun_return(2 * 10 ** 18, value, token_pool, e) / 10 ** 18, 2) - 2))
                            # print('New Ratio: ', )
                        gas_price = int(t[u'gasPrice'])
                        print('Gas price: ', gas_price / 10 ** 9)
                        self.counter += 1
                        if gas_price / 10 ** 9 < 100:
                            # print('G as too low, skipping')
                            continue
                        print('Seems legit, writing to db...')
                        t['time_utc'] = dt.datetime.utcnow()
                        print('Estimate tx time: ',
                              int(EtherScan.get_time_estimate(int(t[u'gasPrice']), etherscan_key)['result']) / 60)
                        try:
                            if w3.eth.getTransaction(t[u'hash'])[u'blockHash'] == None:
                                print('Still pending...')
                                t['pending'] = 'true'
                            else:
                                print('Already confirmed')
                                t['pending'] = 'false'
                        except:
                            time.sleep(0.1)
                            print('Error - probably private tx')
                            t['pending'] = 'error'
                        tx_sql = pd.DataFrame([t])
                        tx_sql.drop('type', 1).to_sql('transaction_stream',
                                                      index=False,
                                                      con=self.conn,
                                                      if_exists='append')


                    except KeyError as e:
                        # traceback.print_exc()
                        print(e)
                        # print('Coin not reqistered')
                    except Exception as e:
                        print(e)
                        traceback.print_exc()


if __name__ == '__main__':
    frontrunner = UniswapFrontRunner(frontrun_addresses=['0xf6da21E95D74767009acCB145b96897aC3630BaD'],
                                     frontrun_contracts=competition)
    log('Front-running on address', frontrunner.address)

    while True:
        a = time.time()
        try:
            l = frontrunner.get_ticks()
        except Exception as e:
            print(f"Connection broken to feed, {str(e)}, retrying.")
