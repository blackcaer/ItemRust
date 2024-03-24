import asyncio
import json
from datetime import datetime as dt, timedelta

import aiohttp

from ItemRustDatabase import ItemRustDatabase
from Result import Result


class ItemRust:
    API_URL = "https://rust.scmm.app/api/"
    API_ITEM_URL = API_URL + "item/"
    # application/json text/plain
    DEFAULT_HEADERS = {"accept": "application/json", "language": "English", "currency": "USD"}

    session: aiohttp.ClientSession = None
    database: ItemRustDatabase = None

    @classmethod
    def set_session(cls, session):
        cls.session = session

    @classmethod
    def set_database(cls, database):
        cls.database: ItemRustDatabase = database

    def __init__(self, name, quantity=1,price_rchshop=None):
        self.name = name
        self.hash_name = None
        self.price_rchshop: float = price_rchshop

        self.all_success = False

        self.iteminfo = None

        self.price_sm = None  # lowest offer
        self.pricehistory_sm = None
        self.sale_offers_sm = None

        self.price_sp = None
        self.pricehistory_sp = None
        self.sales_histogram_sp = None

        self.timestamp = None  # Timestamp of last all_success update
        self.fromDB = False

        if quantity < 0:
            raise AttributeError("Quantity cannot be less than zero.")
        self.quantity = quantity

        self.perday = None
        self.value = None
        self.value_single = None  # Value if quantity of an item were 1
        self.liqval = None
        self.liqval_single = None  # Liqval if quantity of an item were 1

    async def update_async(self):
        """ Update item data """
        print(self.name + " updating...")

        if self.database is None:
            raise RuntimeError("Database is not set")

        has_actual_record = self.database.has_actual_record(self.name)
        if has_actual_record:
            # Take data from db
            print("Reading data from DB for " + self.name)
            self.fromDB = True
            self.database.assign_data_to(self)

            return
        else:
            self.fromDB = False

        phsm = await self.get_pricehistory_sm_async(100)
        iteminfo = await self.get_item_info_async()  # TODO run concurrently
        # shsm = await self.get_sale_offers_sm_async()

        if phsm.success:
            self.pricehistory_sm = phsm.data

            print(f"Price history success ({self.name})")
        else:
            print(f"Price history errors ({self.name}): " + str(phsm.errors))

        """if shsm.success:
            self.sale_offers_sm = shsm.data
            print(f"Sales histogram success ({self.name})")

            if len(self.sale_offers_sm["items"]) > 0:
                self.price_sm = self.sale_offers_sm["items"][0]['price']
            else:
                print(f"Warning: shsm is empty ({self.name})")
        else:
            print(f"Sales histogram errors ({self.name}): " + str(shsm.errors))"""

        if iteminfo.success:
            self.iteminfo = iteminfo.data
            print(f"Item info success ({self.name})")
            self.price_sm = self.market_price("SteamCommunityMarket")
            self.price_sp = self.market_price("Skinport")
            if self.price_sm is None and phsm.success:
                # If there's no SteamCommunityMarket in iteminfo, happens sometimes
                self.price_sm = phsm.data[len(phsm.data) - 1]["median"] * 100  # Converting to standard format
                print(self.name + " no SteamCommunityMarket in iteminfo, assuming price_sm from price history")

            # Name with proper case
            self.hash_name = self.iteminfo["nameHash"].strip()

        else:
            print(f"Item info errors ({self.name}): " + str(iteminfo.errors))

        if phsm.success:
            self.calc_phsm_vals()

        if phsm.success and iteminfo.success:  # and shsm.success
            self.all_success = True
            self.timestamp = dt.now()
            print(self.name + " updated with status \nSUCCESS")
        else:
            self.all_success = False
            print(self.name + " updated with status \nFAILURE")

        if not has_actual_record and self.all_success:
            self.database.update_record(self)

        print()

    def market_price(self, market_type="SteamCommunityMarket"):
        """ Returns market price from market_type using SCMM API.
        Uses format 1234 (1234 == 12.34 USD)
        Return None if specified market_type is not found
        """
        if self.iteminfo is None:
            return None
        try:
            price = next(item["price"] for item in self.iteminfo["buyPrices"] if item["marketType"] == market_type)
        except StopIteration:
            return None
        return price

        # deprecated, use async version

    async def get_item_info_async(self):
        result = await self._get_json_async(self.API_ITEM_URL + self.name,
                                            params={},
                                            headers={})
        return result

    async def get_pricehistory_sm_async(self, max_days):
        """ GET steammarket pricehistory.
        Returns Result object with price history.
        max_days - The maximum number of days worth of sales history to return.
        Use -1 for all sales history.
        result.data: list[dict()]
        dict keys:
        "date": datetime object,
        "median": 0.0,
        "high": 0,
        "low": 0,
        "open": 0,
        "close": 0,
        "volume": 0
        """
        result = await self._get_json_async(self.API_ITEM_URL + self.name + "/sales",
                                            params={"maxDays": max_days},
                                            headers={})
        if result.success:
            for r in result.data:
                r['date'] = self._parse_date(r['date'])

        return result

    async def get_sale_offers_sm_async(self, count=100, start=0):
        """ GET steammarket sales histogram
        Returns Result object with sales histogram
        """
        result = await self._get_json_async(self.API_ITEM_URL + self.name + "/sellOrders",
                                            params={"start": start, "count": count},
                                            headers={})
        return result

    def calc_real_sales_sm(self, days_back=30):
        """ Calculate avg median price and volume on a specified number of days back.
         If item's sales history is shorter, returns data from the actual period of time
         Returns {'price': float, 'volume': int}"""
        rounded_time = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)

        start_date = rounded_time - timedelta(days=days_back)

        # TODO pamietaj ze volume moze byc do 100% zawyżony przy days_back=1 bo wlicza tez to co sie dzisiaj poki co sprzedalo
        filtered_data = [entry for entry in self.pricehistory_sm if entry["date"] >= start_date]

        median_sum = sum(entry["median"] * entry["volume"] for entry in filtered_data)
        volume_sum = sum(entry["volume"] for entry in filtered_data)

        avg_median = 0 if volume_sum == 0 else round(
            median_sum / volume_sum, 2)  # Price is given as cents (price = 100 = 1$)

        return {'price': avg_median, 'volume': int(volume_sum)}

    def calc_sales_extrapolated_sm(self, days_back=30):
        """ Calculate avg median price and volume for the certain period,
        If sales history is too short, extrapolate existing data for the whole period of time.
        If it's sales history is long enough, returns calc_sales_per_time_sm(days).
        Mainly for calculating average volume per time.
        Returns {'price': float, 'volume': int}
        If pricehistory_sm is None returns None """
        if self.pricehistory_sm is None:
            return None

        rounded_time = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
        oldest_record = self.pricehistory_sm[0]["date"]
        days_back_in_record = (rounded_time - oldest_record).days

        result = self.calc_real_sales_sm(days_back)
        if days_back_in_record >= days_back:  # Enough data
            return result

        today = self._today_frac()
        extrapolated_volume = result['volume'] * (days_back + today) / (days_back_in_record + today)
        result['volume'] = round(extrapolated_volume)

        return result

    def calc_liqval(self, quantity=None, MIN_LIQVAL_VALUE=0.01):
        """ Calculate liquidity value factor.
        Function made via graphic func creator (Desmos) to represent subjective liquidity value of an item
        based on it's.
        If quantity is set to None, defaults to self.quantity"""
        if quantity is None:
            quantity = self.quantity
        sales_ex = self.calc_sales_extrapolated_sm(days_back=30)
        if sales_ex is None:
            return None
        sold_per_day = sales_ex["volume"] / (30 + self._today_frac())

        w2 = 7
        k1 = 0.4
        k2 = 1 / (w2 - (1 / k1))
        c = 2.1
        d = 1.5
        m = 1.2
        n = 0.7
        o = 2

        def f1(x):
            return ((k1 * (x + 0.1)) ** (1 / c)) - 0.2

        def f2(x):
            return (k2 * (x - 1 / k1)) ** (1 / d) + 0.82

        def i(a):
            return 1 * ((a - 0.1) * m) ** (1 / n) + 1

        x = sold_per_day / 10.0  # Formula detail
        a = quantity / 10.0  # Formula detail

        if 0 < x < 1 / k1:
            func_evaluated = f1(x)
        elif 1 / k1 <= x:
            func_evaluated = f2(x)
        else:
            raise ValueError("Unsupported range")

        result = func_evaluated / i(a) ** (o / x)

        if result < MIN_LIQVAL_VALUE:
            result = MIN_LIQVAL_VALUE
        return result

    def calc_value(self, price_shop=None, quantity=None):
        """ Calculate combined value of an item. If price_shop is not None, returns
        value of an item modified by exchange factor.
        price_shop - [optional] price in shop in USD (i.e. 12.44)
        quantity - if quantity of items is set to None, defaults to self.quantity"""
        if quantity is None:
            quantity = self.quantity
        price_sm = self.price_sm / 100
        if price_shop is None:
            # We don't include price_rch in calculations
            exchange_factor = 1
        elif isinstance(price_shop, (int, float)) and price_shop > 0:
            exchange_factor = (price_sm / price_shop) ** 2  # Exchange factor
        else:
            raise AttributeError("price_rch has to be number greater than 0")

        liqval = self.calc_liqval(quantity=quantity)

        return round(exchange_factor * liqval * price_sm ** (1 / 2), 2)

    def calc_phsm_vals(self):
        # Some of it is dependent on previously fetched values (price_sm in value)
        self.perday = round(self.calc_sales_extrapolated_sm(30)["volume"] / 30, 2)
        self.value = self.calc_value(price_shop=None)
        self.value_single = self.calc_value(price_shop=None, quantity=1)
        self.liqval = self.calc_liqval()
        self.liqval_single = self.calc_liqval(quantity=1)

    # ========== Helper methods:

    async def _get_json_async(self, url, params=None, headers=None, cookies=None, attempts=1, delay_ms=1000):
        """ Makes GET request and parses it to json. Wrapper for error handling and multiple attempts"""
        # TODO: handle errors
        if params is None: params = {}
        if headers is None: headers = {}
        if cookies is None: cookies = {}
        errors = []

        for attempt in range(attempts):
            if attempt > 0:
                await asyncio.sleep(delay_ms / 1000)

            response = await self.session.get(url,
                                              params=params,
                                              headers={**self.DEFAULT_HEADERS, **headers},
                                              cookies={**cookies})
            if response.status == 200:
                json_result = json.loads(await response.text())
                return Result(json_result)
            elif response.status == 404:
                error = f"404: {response.reason}"
                errors.append(error)
                return Result(success=False, errors=errors)

            error = (f"Status code is not 200, status_code={response.status}, reason={response.reason}, "
                     f"attempt {attempt + 1}/{attempts}")
            errors.append(error)

        errors.append("Attempt limit reached")
        return Result(success=False, errors=errors)

    def _today_frac(self):
        # Fraction of today, matters with low values of days_back
        return round(dt.now().hour / 24, 2)

    def _parse_date(self, strdate):
        return dt.strptime(strdate, "%Y-%m-%dT%H:%M:%S")



    # ================================================= na kiedys:

    def get_price_sm(self):
        """ Current price sm (TODO'real price'?)"""
        pass

    def get_offers_sm(self):
        """ Nicely parsed get_sales_histogram?"""
        pass

    def get_price_sp(self):
        """ Current price sp ('real price'?)"""
        pass

    def get_pricehistory_sp(self):
        """  """
        pass

    def get_offers_sp(self):
        pass


