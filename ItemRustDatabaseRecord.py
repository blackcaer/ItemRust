from datetime import datetime, timedelta


class ItemRustDatabaseRecord:
    """ Encapsulates data of ItemRust for ItemRustDatabase class"""

    def __init__(self, itemrust):
        self.name = None
        self.iteminfo = None
        self.price_sm = None
        self.pricehistory_sm = None
        self.sale_offers_sm = None
        self.price_sp = None
        self.pricehistory_sp = None
        self.sales_histogram_sp = None
        self.timestamp: datetime = None

        self.value = None

        self.hash_name = None

        self.save_data(itemrust)

    def save_data(self, itemrust):
        if not itemrust.all_success:
            raise RuntimeError("Itemrust all_success is false")

        self.name = itemrust.name
        self.iteminfo = itemrust.iteminfo

        self.price_sm = itemrust.price_sm
        self.pricehistory_sm = itemrust.pricehistory_sm
        self.sale_offers_sm = itemrust.sale_offers_sm

        self.price_sp = itemrust.price_sp
        self.pricehistory_sp = itemrust.pricehistory_sp
        self.sales_histogram_sp = itemrust.sales_histogram_sp

        self.hash_name = itemrust.hash_name
        self.value = itemrust.calc_value()  # TODO what if calc_value err? how to handle expiry date?

        self.timestamp = itemrust.timestamp

    def assign_data_to(self, itemrust):
        itemrust.fromDB = True

        itemrust.name = self.name
        itemrust.iteminfo = self.iteminfo

        itemrust.price_sm = self.price_sm
        itemrust.pricehistory_sm = self.pricehistory_sm
        itemrust.sale_offers_sm = self.sale_offers_sm

        itemrust.price_sp = self.price_sp
        itemrust.pricehistory_sp = self.pricehistory_sp
        itemrust.sales_histogram_sp = self.sales_histogram_sp

        itemrust.hash_name = self.hash_name

        itemrust.timestamp = self.timestamp

        itemrust.all_success = True
        itemrust.calc_phsm_values()

    def calc_expiry_date(self, min_expiry_time=2, high_value=2.5, max_expiry_time=7, low_value=1.5,
                         expire_on_friday=True):
        """ Calculates item's data expiry date based on its value. Higher value = shorted expiration time.
        :param min_expiry_time: Days to expiration for items with >= high_value
        :type min_expiry_time: float
        :param high_value: Items with >= values will have max_expiry_time days to expiration
        :type high_value: float
        :param max_expiry_time: Days to expiration for items with <= low_value
        :type max_expiry_time:float
        :param low_value: Items with <= values will have min_expiry_time days to expiration
        :type low_value:float
        :param expire_on_friday: If True, expires item on 00:00 of next Friday (itemstore update)
        :type expire_on_friday:float
        :return: Date of item's expiration
        :rtype: datetime

        """
        if high_value < low_value:
            raise ValueError("low_value cannot be greater than high_value")
        if max_expiry_time < min_expiry_time:
            raise ValueError("min_expiry_time cannot be greater than max_expiry_time")

        val = self.value

        if val <= low_value:
            expiry_time_days = max_expiry_time
        elif val >= high_value:
            expiry_time_days = min_expiry_time
        else:
            # Calculate expiry time days by scaling time proportionally to value between low and high value
            mtp = (val - low_value) / (high_value - low_value)
            expiry_time_days = min_expiry_time + mtp * (max_expiry_time - min_expiry_time)

        expiry_date = self.timestamp + timedelta(days=expiry_time_days)

        if expire_on_friday:
            day = self.timestamp + timedelta(days=1)
            while day.weekday() != 4:
                day += timedelta(days=1)

            friday_expiration = day.replace(hour=0, minute=0, second=0, microsecond=0)

            if expiry_date > friday_expiration:
                expiry_date = friday_expiration

        return expiry_date
