from base64 import b64decode
from base58 import b58decode
import pandas as pd
import numpy as np
import spl.token._layouts as layouts


def decode_byte_string(byte_string: str, encoding: str = "base64") -> bytes:
    """Decode a encoded string from an RPC Response."""
    b_str = str.encode(byte_string)
    if encoding == "base64":
        return b64decode(b_str)
    if encoding == "base58":
        return b58decode(b_str)
    raise NotImplementedError(f"{encoding} decoding not currently supported.")

def parse_token_data(_token_data):
    token_data = layouts.ACCOUNT_LAYOUT.parse(decode_byte_string(_token_data))
    return token_data

def get_signature_for_address(sol_client, address, start_time, end_time, include_error=False) -> pd.DataFrame:
    """
    :param sol_client:
    :param address:
    :param start_time:
    :param end_time:
    :param include_error:
    :return:
    """
    start_time = pd.Timestamp(start_time)
    end_time = pd.Timestamp(end_time)
    start_time_unix = (start_time - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
    end_time_unix = (end_time - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')

    if start_time < pd.Timestamp('2021-03-31 00:00:00'):
        print(
            'Warning! Timestamps before March 2021 may cause some errors on the blockTime of the get_confirmed_signature call')

    before_sig = None
    cnt = 0
    result = []
    while 1 > 0:
        list_signatures = sol_client.get_confirmed_signature_for_address2(address, before=before_sig)
        # If there is no data available, stop:
        if len(list_signatures['result']) == 0:
            break
        else:
            # Save the oldest signature in case we want to query the next batch of signatures
            before_sig = list_signatures['result'][-1]['signature']

        # If the latest blockTime is a NoneType, it is before March 2021 and we need to make a fix for this
        # Probably by running the signature through another API call to see the time from there
        if list_signatures['result'][-1]['blockTime'] is None:
            result = result + list_signatures['result']
            continue

        # If the latest time available is below the start_time, we should not append anything, and stop the loop.
        if list_signatures['result'][0]['blockTime'] < start_time_unix:
            break

        # If the oldest time available is above the end_time, we should not append anything, and continue with the next X signatures
        if list_signatures['result'][-1]['blockTime'] > end_time_unix:
            # Go to next signatures
            _ = 1
        else:
            # Append it
            result = result + list_signatures['result']
            # Go to next signatures

    # Then finally, we change it into a dataframe and delete the times that are outside our interval.
    df = pd.DataFrame(result)
    df = df.loc[(df['blockTime'] >= start_time_unix) & (df['blockTime'] <= end_time_unix)]

    if include_error is False:
        df = df.loc[pd.isnull(df['err'])]

    return df


def parse_transaction(tx, _sig, _mint=None):
    """
    :param tx: Transaction dictionary resulting from Client.get_confirmed_transaction()
    :param _sig: Signature of the transaction
    :param _mint: Redundant
    :return: _d: Dictionary of parsed transaction
    """
    # Parsing the SOL balances of the tx in a dataframe so it is easier to analyse
    _solana_balances = []
    _solana_balances.append(tx['result']['meta']['preBalances'])
    _solana_balances.append(tx['result']['meta']['postBalances'])
    _solana_balances.append(tx['result']['transaction']['message']['accountKeys'])
    df_solana_balances = pd.DataFrame(np.array(_solana_balances).T, columns=['pre_balance', 'post_balance', 'pubkey'])
    df_solana_balances['post_balance'] = df_solana_balances['post_balance'].astype(float) / 1000000000
    df_solana_balances['pre_balance'] = df_solana_balances['pre_balance'].astype(float) / 1000000000
    df_solana_balances['change'] = df_solana_balances['post_balance'] - df_solana_balances['pre_balance']

    # Parsing other information in dictionary (BETA)
    # Dont have all the knowledge about the transactions yet so some things are shortcuts
    _d = {}
    # _d['amount'] = ((tx['result']['meta']['preBalances'][0] - tx['result']['meta']['postBalances'][0])/1000000000)
    _d['sig'] = _sig
    _d['minter'] = _mint
    _d['amt_addresses'] = len(df_solana_balances)  # Amt of addresses involved in tx
    _d['amt_involved_tx'] = len(
        df_solana_balances.loc[abs(df_solana_balances['change']) > 0])  # Amt of addresses transacting SOL in tx
    _d['sol_received'] = df_solana_balances.loc[
        df_solana_balances['change'] > 0, 'change'].sum()  # Total SOL received in the tx
    _d['sol_sent'] = df_solana_balances.loc[
        df_solana_balances['change'] < 0, 'change'].sum()  # Total SOL spent in the tx

    # Tokens are still in beta
    if len(tx['result']['meta']['postTokenBalances']) > 0:
        _d['tokens_involved'] = True
    else:
        _d['tokens_involved'] = False

    # If the transacting addresses are just two, we can assume it is just a SOL transfer.
    # As no token addresses are involved and no additional parties
    # (We might be wrong here)
    _d['sender'] = None
    _d['receiver'] = None
    _d['amount'] = np.nan
    if _d['amt_involved_tx'] == 2:
        _d['amount'] = _d['sol_sent']
        if len(df_solana_balances.loc[df_solana_balances['change'] > 0]) > 0:
            _d['receiver'] = df_solana_balances.loc[df_solana_balances['change'] > 0, 'pubkey'].values[0]

        if len(df_solana_balances.loc[df_solana_balances['change'] < 0]) > 0:
            _d['sender'] = df_solana_balances.loc[df_solana_balances['change'] < 0, 'pubkey'].values[0]

    return _d
