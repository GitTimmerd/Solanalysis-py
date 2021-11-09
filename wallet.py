import pandas as pd

from API import SolanaAPIWrapper
from solanahelper import parse_token_data
from solana.rpc.api import Client as SolanaClient
from solana.rpc.types import TokenAccountOpts
from solana.publickey import PublicKey

SOLANA_API_LINK = "https://api.mainnet-beta.solana.com"
sol_api = SolanaAPIWrapper(SOLANA_API_LINK) # This is my own wrapper around it to control API requests

def show_account_balance(address):
    sol_balance = sol_api.client.get_balance(address)['result']['value'] / (10**9)
    print(f'{address} has {sol_balance} SOL in his wallet')


def get_tokens(address):
    _opt = TokenAccountOpts(program_id='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
    tokens = sol_api.client.get_token_accounts_by_owner(address, opts=_opt)
    list_d = []
    for _token in tokens['result']['value']:
        deserialized_data = parse_token_data(_token['account']['data'][0])
        for _x, _y in deserialized_data.items():
            if isinstance(_y, bytes):
                deserialized_data[_x] = PublicKey(_y).__str__()
        _d = {}
        _d['pubkey'] = _token['pubkey']
        _d['mint'] = deserialized_data['mint']
        #_d['owner'] = deserialized_data['owner'] # Owner is already defined by the wallet pubkey in the input.
        _d['amount'] = deserialized_data['amount']
        _d['delegate_option'] = deserialized_data['delegate_option']
        _d['delegate'] = deserialized_data['delegate']
        _d['state'] = deserialized_data['state']
        _d['is_native_option'] = deserialized_data['is_native_option']
        _d['is_native'] = deserialized_data['is_native']
        _d['delegated_amount'] = deserialized_data['delegated_amount']
        _d['close_authority_option'] = deserialized_data['close_authority_option']
        _d['close_authority'] = deserialized_data['close_authority']
        list_d.append(_d)

    return pd.DataFrame(list_d)

def modify_token_dataframe(df_token, sonar):

    _df = df_token.merge(sonar.tokens.rename(columns={'address':'mint'})[['mint', 'symbol']], how='left')
    _df = _df.merge(sonar.prices.rename(columns={'address':'mint'})[['mint', 'type', 'decimals', 'price']], how='left')
    _df['value'] = _df['amount'] / 10**_df['decimals'] * _df['price']
    _df.sort_values('value',ascending=0, inplace=True)
    return _df







