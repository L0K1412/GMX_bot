from requests import get, post
#import pandas as pd
from datetime import datetime
import pytz
import time
from bs4 import BeautifulSoup

# input API Key
API_KEY = "LU3LdU4ChI1TnCpKsHpPlvqVIs5Agcb8"
HEADER = {"x-dune-api-key" : API_KEY}

# Simplifying URL generation
BASE_URL = "https://api.dune.com/api/v1/"

# Label database
label = {
    "0xe8c19db00287e3536075114b2576c70773e039bd": "Andrew Kang (@Rewkang)",
    "0x284101246f8bb2a7e876a0b0feed776c8ea02474": "Func (@func_anon)",
    "0xfd93b5134839e6c5c7d1ccb9ab852c137a52d161": "Emperor (@EmperorBTC)",
    "0xd92f6d0c7c463bd2ec59519aeb59766ca4e56589": "im🔥.eth",
    "0xc292eafd5422a9c961cc2630cbddf04c93db33bd": "mh001.eth",
    "0xd4ad5d62dce1a8bf661777a5c1df79bd12ac8f1d": "🤓 Smart LP on Nansen"
}

def checkNone(num):
    if num is None:
        return 0
    return num

def format_number(num):
    if num is None:
        return f'None'
    elif num >= 10**9 or num <= -10**9:
        return f"{num / 10**9:.2f}b"
    elif num >= 10**6 or num <= -10**6:
        return f"{num / 10**6:.2f}m"
    elif num >= 10**3 or num <= -10**3:
        return f"{num / 10**3:.2f}k"
    else:
        return f"{num:.2f}"
    
def format_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    link = soup.find('a')

    if link:
        href = link['href']
        text = link.text

        if '/tx/' in href:
            if 'arbiscan.io' in href:
                return f'<a href="{href}" target="_blank">View on Arbiscan</a>'
            else:
                return f'<a href="{href}" target="_blank">View on Snowtrace</a>'
        else:
            if text in label:
                return f'<a href="{href}" target="_blank">{label[text]}</a>'
            else:
                return f'<a href="{href}" target="_blank">{text[:9]}</a>'

    return html
    
def timestamp_to_readable(ts, timezone="Asia/Singapore", format="%Y-%m-%d %H:%M:%S"):
    # https://en.wikipedia.org/wiki/List_of_tz_database_time_zones Asia/Ho_Chi_Minh, Asia/Singapore, America/Los_Angeles
    tz = pytz.timezone(timezone)
    return datetime.fromtimestamp(ts, tz=tz).strftime(format)

def readable_to_timestamp(str, format="%Y-%m-%d %H:%M:%S.%f UTC"):
    tz = pytz.timezone('Etc/GMT')
    dt = datetime.strptime(str, format)
    dt = tz.localize(dt)
    return dt.timestamp()

def make_api_url(module, action, ID):
    """
    We shall use this function to generate a URL to call the API.
    """

    url = BASE_URL + module + "/" + ID + "/" + action

    return url

# Wrapping API endpoints in functions

# execute query with no param or default params
def execute_query(query_id, engine="medium"):
    """
    Takes in the query ID and engine size.
    Specifying the engine size will change how quickly your query runs. 
    The default is "medium" which spends 10 credits, while "large" spends 20 credits.
    Calls the API to execute the query.
    Returns the execution ID of the instance which is executing the query.
    """

    url = make_api_url("query", "execute", query_id)
    params = {
        "performance": engine,
    }
    response = post(url, headers=HEADER, params=params)
    execution_id = response.json()['execution_id']

    return execution_id

# execute query with params
def execute_query_with_params(query_id, param_dict):
    """
    Takes in the query ID. And a dictionary containing parameter values.
    Calls the API to execute the query.
    Returns the execution ID of the instance which is executing the query.
    """

    url = make_api_url("query", "execute", query_id)
    response = post(url, headers=HEADER, json={"query_parameters" : param_dict})
    execution_id = response.json()['execution_id']

    return execution_id

def get_query_status(execution_id):
    """
    Takes in an execution ID.
    Fetches the status of query execution using the API
    Returns the status response object
    """

    url = make_api_url("execution", "status", execution_id)
    response = get(url, headers=HEADER)
    status = response.json()

    return status

def get_query_results(execution_id):
    """
    Takes in an execution ID.
    Fetches the results returned from the query using the API
    Returns the results response object
    """

    url = make_api_url("execution", "results", execution_id)
    response = get(url, headers=HEADER)

    return response

def cancel_query_execution(execution_id):
    """
    Takes in an execution ID.
    Cancels the ongoing execution of the query.
    Returns the response object.
    """

    url = make_api_url("execution", "cancel", execution_id)
    response = get(url, headers=HEADER)

    return response

def run_query(query_id):
    # Last transactions of address (Test query: 2619279)
    execution_id = execute_query(query_id,"medium")
    # print(execution_id)

    response_status = get_query_status(execution_id)
    
    # Check state of query
    while response_status["state"] != "QUERY_STATE_COMPLETED":
        # wait 30 seconds then check again
        time.sleep(120)
        response_status = get_query_status(execution_id)

    response_result = get_query_results(execution_id)
    array_data = list(response_result.json()['result']['rows'])
    
    # sort order of columns
    new_array_data =[]
    
    for item in array_data:
        if item['chain'] == 'MULTICHAIN':
            if item['action'] == 'Open':
                format_item = {
                    f"<b>[ALERT FOR TOP {item['#']} MUX {item['table']}]</b>: {format_html(item['wallet_address'])}\n"
                    f"⬆️📈 <b>OPEN: {item['position_side']} {item['token']}</b> at price ${format_number(item['cur_price'])}\n"
                    f"Margin size: ${format_number(item['running_total_size'])}\n"
                    f"Collateral size: ${format_number(item['running_total_col'])}\n"
                    f"Leverage: {format_number(item['lev'])}x\n"
                    f"Estimate PnL: ${format_number(item['pnl'])} ({checkNone(item['pnl_pct'])*100:.2f}%)\n\n"
                    
                    f"At {timestamp_to_readable(readable_to_timestamp(item['last_action']))} (UTC+8) | On {item['chain_action']}\n"
                    f"{item['evt_tx_hash']}\n\n"
                    
                    f"<b>INFO TRADER:</b>\n"
                    f"Total PnL: ${format_number(item['total_PnL'])}\n"
                    f"Total trade: {item['numTrade']} - Win: {item['win']} - Winrate: {item['winrate']*100:.2f}%\n"
                    f"------------------------------------------------------------"
                }
                new_array_data.append(format_item)
            elif item['action'] == 'Increase':
                format_item = {
                    f"<b>[ALERT FOR TOP {item['#']} MUX {item['table']}]</b>: {format_html(item['wallet_address'])}\n"
                    f"⬆️📈 <b>INCREASE: {item['position_side']} {item['token']}</b> at price ${format_number(item['cur_price'])}\n"
                    f"Margin size change: +${format_number(item['sizeDelta'])}\n"
                    f"At {timestamp_to_readable(readable_to_timestamp(item['last_action']))} (UTC+8) | On {item['chain_action']}\n"
                    f"{item['evt_tx_hash']}\n\n"
                    
                    f"<b>INFO CURRENT TRADE:</b>\n"
                    f"Margin size: ${format_number(item['running_total_size'])}\n"
                    f"Collateral size: ${format_number(item['running_total_col'])}\n"
                    f"Leverage: {format_number(item['lev'])}x\n"
                    f"Average price: ${format_number(item['avgPrice'])}\n"
                    f"Estimate PnL: ${format_number(item['pnl'])} ({checkNone(checkNone(item['pnl_pct']))*100:.2f}%)\n\n"
                    
                    f"<b>INFO TRADER:</b>\n"
                    f"Total PnL: ${format_number(item['total_PnL'])}\n"
                    f"Total trade: {item['numTrade']} - Win: {item['win']} - Winrate: {item['winrate']*100:.2f}%\n"
                    f"------------------------------------------------------------"
                }
                new_array_data.append(format_item)
            elif item['action'] == 'Decrease':
                format_item = {
                    f"<b>[ALERT FOR TOP {item['#']} MUX {item['table']}]</b>: {format_html(item['wallet_address'])}\n"
                    f"⬇️📉 <b>DECREASE: {item['position_side']} {item['token']}</b> at price ${format_number(item['cur_price'])}\n"
                    f"Margin size change: -${format_number(item['sizeDelta'])}\n"
                    f"At {timestamp_to_readable(readable_to_timestamp(item['last_action']))} (UTC+8) | On {item['chain_action']}\n"
                    f"{item['evt_tx_hash']}\n\n"
                    
                    f"<b>INFO CURRENT TRADE:</b>\n"
                    f"Margin size: ${format_number(item['running_total_size'])}\n"
                    f"Collateral size: ${format_number(item['running_total_col'])}\n"
                    f"Leverage: {format_number(item['cur_lev'])}x\n"
                    f"PnL: ${format_number(item['pnl'])} ({checkNone(item['pnl_pct'])*100:.2f}%)\n\n"
                    
                    f"<b>INFO TRADER:</b>\n"
                    f"Total PnL: ${format_number(item['total_PnL'])}\n"
                    f"Total trade: {item['numTrade']} - Win: {item['win']} - Winrate: {item['winrate']*100:.2f}%\n"
                    f"------------------------------------------------------------"
                }
                new_array_data.append(format_item)
            elif (item['action'] == 'Close' or item['action'] == 'Liquidated'):
                format_item = {
                    f"<b>[ALERT FOR TOP {item['#']} MUX {item['table']}]</b>: {format_html(item['wallet_address'])}\n"
                    f"⬇️📉 <b>{(item['action']).upper()}: {item['position_side']} {item['token']}</b> at price ${format_number(item['cur_price'])}\n"
                    f"PnL: ${format_number(item['pnl'])} ({checkNone(item['pnl_pct'])*100:.2f}%)\n\n"
                    f"At {timestamp_to_readable(readable_to_timestamp(item['last_action']))} (UTC+8) | On {item['chain_action']}\n"
                    f"{item['evt_tx_hash']}\n\n"
                    
                    f"<b>INFO TRADER:</b>\n"
                    f"Total PnL: ${format_number(item['total_PnL'])}\n"
                    f"Total trade: {item['numTrade']} - Win: {item['win']} - Winrate: {item['winrate']*100:.2f}%\n"
                    f"------------------------------------------------------------"
                }
                new_array_data.append(format_item)
        elif item['table'] == 'MARGIN SIZE':
            if item['action'] == 'Open':
                format_item = {
                    f"<b>[ALERT FOR TOP GMX {item['table']}]</b>: {format_html(item['wallet_address'])}\n"
                    f"⬆️📈 <b>OPEN: {item['position_side']} {item['token']}</b> at price ${format_number(item['cur_price'])}\n"
                    f"Margin size: ${format_number(item['sizeDelta'])}\n"
                    f"Collateral size: ${format_number(item['collatDelta'])}\n"
                    f"Leverage: {format_number(item['cur_lev'])}x\n"
                    f"Estimate PnL: ${format_number(item['PnL'])} ({checkNone(item['Pnl_pct'])*100:.2f}%)\n\n"
                    
                    f"At {timestamp_to_readable(readable_to_timestamp(item['last_action']))} (UTC+8) | On {item['chain']}\n"
                    f"{format_html(item['evt_tx_hash'])}\n"

                    f"------------------------------------------------------------"
                }
                new_array_data.append(format_item)
            elif item['action'] == 'Increase':
                format_item = {
                    f"<b>[ALERT FOR TOP GMX {item['table']}]</b>: {format_html(item['wallet_address'])}\n"
                    f"⬆️📈 <b>INCREASE: {item['position_side']} {item['token']}</b> at price ${format_number(item['cur_price'])}\n"
                    f"Margin size change: +${format_number(item['sizeDelta'])}\n"
                    f"Collateral size change: +${format_number(item['collatDelta'])}\n"
                    f"At {timestamp_to_readable(readable_to_timestamp(item['last_action']))} (UTC+8) | On {item['chain']}\n"
                    f"{format_html(item['evt_tx_hash'])}\n\n"
                    
                    f"<b>INFO CURRENT TRADE:</b>\n"
                    f"Margin size: ${format_number(item['running_total_size'])}\n"
                    f"Collateral size: ${format_number(item['running_col'])}\n"
                    f"Leverage: {format_number(item['cur_lev'])}x\n"
                    f"Average price: ${format_number(item['avgPrice'])}\n"
                    f"Estimate PnL: ${format_number(item['PnL'])} ({checkNone(item['Pnl_pct'])*100:.2f}%)\n"
                    
                    f"------------------------------------------------------------"
                }
                new_array_data.append(format_item)
            elif item['action'] == 'Decrease':
                format_item = {
                    f"<b>[ALERT FOR TOP GMX {item['table']}]</b>: {format_html(item['wallet_address'])}\n"
                    f"⬇️📉 <b>DECREASE: {item['position_side']} {item['token']}</b> at price ${format_number(item['cur_price'])}\n"
                    f"Margin size change: -${format_number(item['sizeDelta'])}\n"
                    f"Collateral size change: -${format_number(item['collatDelta'])}\n"
                    f"At {timestamp_to_readable(readable_to_timestamp(item['last_action']))} (UTC+8) | On {item['chain']}\n"
                    f"{format_html(item['evt_tx_hash'])}\n\n"
                    
                    f"<b>INFO CURRENT TRADE:</b>\n"
                    f"Margin size: ${format_number(item['running_total_size'])}\n"
                    f"Collateral size: ${format_number(item['running_col'])}\n"
                    f"Leverage: {format_number(item['cur_lev'])}x\n"
                    f"Average price: ${format_number(item['avgPrice'])}\n"
                    f"Estimate PnL: ${format_number(item['PnL'])} ({checkNone(item['Pnl_pct'])*100:.2f}%)\n"
                    
                    f"------------------------------------------------------------"
                }
                new_array_data.append(format_item)
            elif (item['action'] == 'Close' or item['action'] == 'Liquidated'):
                format_item = {
                    f"<b>[ALERT FOR TOP GMX {item['table']}]</b>: {format_html(item['wallet_address'])}\n"
                    f"⬇️📉 <b>{(item['action']).upper()}: {item['position_side']} {item['token']}</b> at price ${format_number(item['cur_price'])}\n"
                    f"Margin size: ${format_number(item['running_total_size'])}\n"
                    f"Collateral size: ${format_number(item['running_col'])}\n"
                    f"Leverage: {format_number(item['cur_lev'])}x\n"
                    f"Average price: ${format_number(item['avgPrice'])}\n"
                    f"PnL: ${format_number(item['PnL'])} ({checkNone(item['Pnl_pct'])*100:.2f}%)\n\n"
                    f"At {timestamp_to_readable(readable_to_timestamp(item['last_action']))} (UTC+8) | On {item['chain']}\n"
                    f"{format_html(item['evt_tx_hash'])}\n"
                    
                    f"------------------------------------------------------------"
                }
                new_array_data.append(format_item)
        else:
            if item['action'] == 'Open':
                format_item = {
                    f"<b>[ALERT FOR TOP {item['#']} GMX {item['table']}]</b>: {format_html(item['wallet_address'])}\n"
                    f"⬆️📈 <b>OPEN: {item['position_side']} {item['token']}</b> at price ${format_number(item['cur_price'])}\n"
                    f"Margin size: ${format_number(item['sizeDelta'])}\n"
                    f"Collateral size: ${format_number(item['collatDelta'])}\n"
                    f"Leverage: {format_number(item['cur_lev'])}x\n"
                    f"Estimate PnL: ${format_number(item['PnL'])} ({checkNone(item['Pnl_pct'])*100:.2f}%)\n\n"
                    
                    f"At {timestamp_to_readable(readable_to_timestamp(item['last_action']))} (UTC+8) | On {item['chain']}\n"
                    f"{format_html(item['evt_tx_hash'])}\n\n"
                    
                    f"<b>INFO TRADER:</b>\n"
                    f"Total PnL: ${format_number(item['total_PnL'])}\n"
                    f"Total trade: {item['numTrade']} - Win: {item['win']} - Winrate: {item['winrate']*100:.2f}%\n"
                    f"------------------------------------------------------------"
                }
                new_array_data.append(format_item)
            elif item['action'] == 'Increase':
                format_item = {
                    f"<b>[ALERT FOR TOP {item['#']} GMX {item['table']}]</b>: {format_html(item['wallet_address'])}\n"
                    f"⬆️📈 <b>INCREASE: {item['position_side']} {item['token']}</b> at price ${format_number(item['cur_price'])}\n"
                    f"Margin size change: +${format_number(item['sizeDelta'])}\n"
                    f"Collateral size change: +${format_number(item['collatDelta'])}\n"
                    f"At {timestamp_to_readable(readable_to_timestamp(item['last_action']))} (UTC+8) | On {item['chain']}\n"
                    f"{format_html(item['evt_tx_hash'])}\n\n"
                    
                    f"<b>INFO CURRENT TRADE:</b>\n"
                    f"Margin size: ${format_number(item['running_total_size'])}\n"
                    f"Collateral size: ${format_number(item['running_col'])}\n"
                    f"Leverage: {format_number(item['cur_lev'])}x\n"
                    f"Average price: ${format_number(item['avgPrice'])}\n"
                    f"Estimate PnL: ${format_number(item['PnL'])} ({checkNone(checkNone(item['Pnl_pct']))*100:.2f}%)\n\n"
                    
                    f"<b>INFO TRADER:</b>\n"
                    f"Total PnL: ${format_number(item['total_PnL'])}\n"
                    f"Total trade: {item['numTrade']} - Win: {item['win']} - Winrate: {item['winrate']*100:.2f}%\n"
                    f"------------------------------------------------------------"
                }
                new_array_data.append(format_item)
            elif item['action'] == 'Decrease':
                format_item = {
                    f"<b>[ALERT FOR TOP {item['#']} GMX {item['table']}]</b>: {format_html(item['wallet_address'])}\n"
                    f"⬇️📉 <b>DECREASE: {item['position_side']} {item['token']}</b> at price ${format_number(item['cur_price'])}\n"
                    f"Margin size change: -${format_number(item['sizeDelta'])}\n"
                    f"Collateral size change: -${format_number(item['collatDelta'])}\n"
                    f"At {timestamp_to_readable(readable_to_timestamp(item['last_action']))} (UTC+8) | On {item['chain']}\n"
                    f"{format_html(item['evt_tx_hash'])}\n\n"
                    
                    f"<b>INFO CURRENT TRADE:</b>\n"
                    f"Margin size: ${format_number(item['running_total_size'])}\n"
                    f"Collateral size: ${format_number(item['running_col'])}\n"
                    f"Leverage: {format_number(item['cur_lev'])}x\n"
                    f"Average price: ${format_number(item['avgPrice'])}\n"
                    f"Estimate PnL: ${format_number(item['PnL'])} ({checkNone(item['Pnl_pct'])*100:.2f}%)\n\n"
                    
                    f"<b>INFO TRADER:</b>\n"
                    f"Total PnL: ${format_number(item['total_PnL'])}\n"
                    f"Total trade: {item['numTrade']} - Win: {item['win']} - Winrate: {item['winrate']*100:.2f}%\n"
                    f"------------------------------------------------------------"
                }
                new_array_data.append(format_item)
            elif (item['action'] == 'Close' or item['action'] == 'Liquidated'):
                format_item = {
                    f"<b>[ALERT FOR TOP {item['#']} GMX {item['table']}]</b>: {format_html(item['wallet_address'])}\n"
                    f"⬇️📉 <b>{(item['action']).upper()}: {item['position_side']} {item['token']}</b> at price ${format_number(item['cur_price'])}\n"
                    f"Margin size: ${format_number(item['running_total_size'])}\n"
                    f"Collateral size: ${format_number(item['running_col'])}\n"
                    f"Leverage: {format_number(item['cur_lev'])}x\n"
                    f"Average price: ${format_number(item['avgPrice'])}\n"
                    f"PnL: ${format_number(item['PnL'])} ({checkNone(item['Pnl_pct'])*100:.2f}%)\n\n"
                    f"At {timestamp_to_readable(readable_to_timestamp(item['last_action']))} (UTC+8) | On {item['chain']}\n"
                    f"{format_html(item['evt_tx_hash'])}\n\n"
                    
                    f"<b>INFO TRADER:</b>\n"
                    f"Total PnL: ${format_number(item['total_PnL'])}\n"
                    f"Total trade: {item['numTrade']} - Win: {item['win']} - Winrate: {item['winrate']*100:.2f}%\n"
                    f"------------------------------------------------------------"
                }
                new_array_data.append(format_item)
        
    
    return new_array_data
        
def run_query_with_params():
    # Last transactions of address (Test query: 2619279)
    # initialize list params
    parameters = {"last_txs" : "10", "wallet_address" : "0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43"}
    execution_id = execute_query_with_params("2619279", parameters)
    # print(execution_id)

    response_status = get_query_status(execution_id)
    
    # Check state of query
    while response_status["state"] != "QUERY_STATE_COMPLETED":
        # wait 30 seconds then check again
        time.sleep(120)
        response_status = get_query_status(execution_id)

    response_result = get_query_results(execution_id)
    array_data = list(response_result.json()['result']['rows'])
    
    # sort order of columns
    new_array_data =[
        {f"*[ALERT FOR GMX]*: {item['amount']} {item['symbol']}\nFrom {item['from']}\nTo {item['to']}\nOn ethereum chain at {item['time']} (UTC+0)\nTransaction Hash: {item['tx_hash']}"}
        for item in array_data
    ]
    
    return new_array_data
    
# run query with default params
# a = run_query('2462605')

# print(a[0])
# run query with params
# run_query_with_params()