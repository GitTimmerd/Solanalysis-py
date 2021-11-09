import pandas as pd

from API import SolanaAPIWrapper, Sonar
from wallet import get_tokens, modify_token_dataframe

LPs = {'SOL-IVN': 'JGhNs5r7YNnJokzzXZWE3REKV8x4GiUvn2xSg7XGg59'}
SOLANA_API_LINK = "https://api.mainnet-beta.solana.com"
sol_api = SolanaAPIWrapper(SOLANA_API_LINK) # This is my own wrapper around it to control API requests
sonar = Sonar()
sonar.unpack()

# df_token contains the current balance of an LP
# Need additional function to fetch historical balance as time series
df_token = get_tokens(LPs['SOL-IVN'])
df_token = modify_token_dataframe(df_token, sonar)