from etherscan import Etherscan
import json
from datetime import datetime
import calendar
import time
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from web3 import Web3
from uniswap import Uniswap



# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#Configure ethereum node
#web3 = Web3(Web3.HTTPProvider(https://mainnet.infura.io/v3/a2fad1a2e6324fc1a61897bf4b807b0e))
provider = "https://mainnet.infura.io/v3/a2fad1a2e6324fc1a61897bf4b807b0e"
version = 2

uniswap = Uniswap(address = None, private_key = None, version=version, provider = provider)
WRAPPED_ETHER = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
# How many blocks to search
BLOCK_LENGTH = 500

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    return render_template("layout.html")

@app.route("/eth")
def eth():
    eth = Etherscan("19ZZF2YPD4AF8X6E42C1NGFX9W32ZMWZV4")
    current_GMT = time.gmtime()

    # Store timestamp
    ts = calendar.timegm(current_GMT)
    print("timestamp: ", ts)
    

    # Get latest block
    currentBlock = int(eth.get_block_number_by_timestamp(timestamp = ts, closest = "before"))
    print("current block:", currentBlock)

    timeList =[]

    # Get list of the latest factory transactions
    internal_txs = eth.get_internal_txs_by_address(address = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f", startblock = currentBlock-BLOCK_LENGTH, endblock = currentBlock, sort = "desc")
    print("inern txs done")
    txHashList = []
    pairList = []

    # Loop through the list and find the transactions that creates contracts
    for tx in internal_txs:
        print(tx["type"])
        if tx["type"] == "create2":
            txHashList.append(tx["hash"])
            pairList.append(tx["contractAddress"])
            timeList.append(datetime.fromtimestamp(int(tx["timeStamp"])))
    print("append to first hashlist done")

    ethLiqList = []
    # Get the ETH in their liquidity pools
    for pair in pairList:
        start = time.time()
        try:
            ethLiq = int(eth.get_acc_balance_by_token_and_contract_address(contract_address = WRAPPED_ETHER, address = pair))
        except Exception as err:
            print(err)
            continue
        
        print("get_acc_balance_by_token_and_contract_address")
        end = time.time()
        print(end - start)
        
        print("liq assignment done")
        print(ethLiq/10**18)
        if ethLiq/10**18 < 0.01:
            ethLiqList.append(0)
        else:
            ethLiqList.append(ethLiq/10**18)


    print("length of liqlist: ", len(ethLiqList))
    contractList = []
    tokenDict = dict()

    # Get the contract from the transaction ID
    for tx in txHashList:
        start = time.time()
        receipttx = eth.get_proxy_transaction_receipt(txhash = tx)
        print("get_proxy_transaction_receipt")
        end = time.time()
        print(end - start)
        contractList.append(receipttx["contractAddress"])

    print("length of contractlist: ", len(contractList))

    x = 0

    # Check if the contracts exist and removes them from the dict if they do not
    for contract in contractList:
        print(contract)
        if contract != None:
            start = time.time()
            try:
                token = uniswap.get_token(address = contract)
            except Exception as err:
                print(err)
                continue
            print("uniswap.get_token")
            end = time.time()
            print(end - start)
            
            if token != None:
                print(token)
                tokenDict[x] = [contract, token.name,ethLiqList[x],timeList[x]]
                x+=1
            else:
                del ethLiqList[x]
                del timeList[x]
        else:
            del ethLiqList[x]
            del timeList[x]

    # Render the html
    return render_template("index.html", tokenDict = tokenDict)




