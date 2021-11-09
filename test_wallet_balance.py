from API import Sonar
from wallet import show_account_balance, get_tokens, modify_token_dataframe
import pandas as pd

test_address = '2fc9pAo8sjeaPfBG4fzTUDXvJXq2dm8MDRpatNenYG4r' # Random address from solana explorer


sonar = Sonar()
sonar._unpack_tokens()
sonar._unpack_prices()

show_account_balance(test_address)
df_tokens = get_tokens(test_address)

df_wallet = df_tokens[['pubkey','mint','amount','delegated_amount','delegate']].merge(sonar.tokens[['_id','symbol','decimals','address','type']],left_on=['mint'],right_on=['address'],how='left').sort_values('symbol')
df_wallet = df_wallet.merge(sonar.prices[['address','price']],how='left').sort_values('amount', ascending=False)
df_wallet['value'] = df_wallet['amount'] / (10**df_wallet['decimals']) * df_wallet['price']
df_wallet = df_wallet.sort_values('value', ascending=False)
df_wallet = modify_token_dataframe(df_tokens, sonar)

print(df_wallet.head(5))
