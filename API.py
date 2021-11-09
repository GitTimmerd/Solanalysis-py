import datetime
import time
import requests
import json
import pandas as pd

from solana.rpc.api import Client as SolanaClient


class Sonar():
    def __init__(self):
        self.API_URL = 'https://sonar-backend-production-2.herokuapp.com/latest_data'
        self._fetch_data()
        return

    def unpack(self):
        self._unpack_tokens()
        self._unpack_prices()

    def _fetch_data(self):
        r = requests.get(self.API_URL)
        self.data = json.loads(r.text)

    def _unpack_tokens(self):
        tokens = pd.DataFrame(self.data['tokens'].values())
        tokens['type'] = 'token'
        self.tokens = tokens

    def _unpack_prices(self):
        prices = pd.DataFrame(self.data['prices'].values())
        prices.rename(columns={'value': 'price'}, inplace=True)
        self.prices = prices

    def _unpack_pool(self):
        """
        This one is not done yet.
        Pretty vague data.
        """

    def _unpack_farm(self):
        """
        This one is not done yet.
        Pretty vague data.
        """

class SolanaAPIWrapper:
    def __init__(self, endpoint):
        self.client = SolanaClient(endpoint)
        self.MAX_REQUESTS = 10
        self.REQUESTS_TIME_FRAME = 5  # seconds
        self.num_requests = 0
        self.start_time = datetime.datetime.now()

    def _enforce_api_limit(self):
        elapsed_seconds = (datetime.datetime.now() - self.start_time).seconds
        if elapsed_seconds > self.REQUESTS_TIME_FRAME:
            self.start_time = datetime.datetime.now()
            self.num_requests = 0
        elif self.num_requests >= self.MAX_REQUESTS:
            sleeping_time = self.REQUESTS_TIME_FRAME - elapsed_seconds
            print(f'Request limit breached. Sleeping {sleeping_time} seconds.')
            time.sleep(sleeping_time)
            self.num_requests = 0
            self.start_time = datetime.datetime.now()

        self.num_requests = self.num_requests + 1

    def get_confirmed_signature_for_address2(self, *args, **kwargs):
        self._enforce_api_limit()
        return self.client.get_confirmed_signature_for_address2(*args, **kwargs)

    def get_confirmed_transaction(self, *args, **kwargs):
        self._enforce_api_limit()
        return self.client.get_confirmed_transaction(*args, **kwargs)

    def get_balance(self, *args):
        self._enforce_api_limit()
        return self.client.get_balance(*args)
