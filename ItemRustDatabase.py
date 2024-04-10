import os
from datetime import datetime

import jsonpickle
import json

from ItemRustDatabaseRecord import ItemRustDatabaseRecord
import asyncio

class ItemRustDatabase:
    def __init__(self, filename, do_not_expire=False):
        """

        :param filename: name of the database file
        :type filename: str
        :param do_not_expire: No record in the database will be treated as expired, useful for testing
        :type do_not_expire: bool
        """
        self.filename = filename
        self.do_not_expire = do_not_expire
        self.records: dict[str, ItemRustDatabaseRecord] = {}

    def is_empty(self):
        return not self.records

    def load_database(self):
        """ Load self.records from file. Returns True if loaded db, False if error or empty db."""
        if not os.path.exists(self.filename):
            print(f"File '{self.filename}' does not exist.")
            return False

        with open(self.filename, 'r') as file:
            data = file.read()
            if not data:
                print(f"File '{self.filename}' is empty")
                return False

            try:
                jsondata = jsonpickle.decode(data)
            except json.decoder.JSONDecodeError as e:
                print(f"Error while decoding json data from {self.filename}:\n",e)
                return False

        self.records = jsondata
        return True

    def save_database(self):
        """ Save self.records to file"""
        if not self.is_empty():
            print("Saving database")
            with open(self.filename, 'w') as f:
                json_data = jsonpickle.encode(self.records)
                f.write(json_data)
            print("Database saved")
        else:
            print("Not saving database - empty")
    async def save_database_async(self):
        """ Save self.records to file asynchronously"""
        if not self.is_empty():
            print("Saving database async")
            async with open(self.filename, 'w') as f:
                json_data = jsonpickle.encode(self.records)
                await f.write(json_data)
            print("Database saved")
        else:
            print("Not saving database - empty")

    def update_record(self, itemrust):
        """ Replace previous record with new one or create new record"""
        print("Updating db record of: " + itemrust.name)
        self.records[itemrust.name] = ItemRustDatabaseRecord(itemrust)

    def delete_record(self, name):
        """ Delete record with given name whether it exists or not"""
        self.records.pop(name, None)

    def has_record(self, name):
        return name in self.records

    def has_actual_record(self, name):
        """ If the item in the database and has not expired"""
        has_actual_record = bool(self.has_record(name) and not self.is_record_expired(name))
        #print(name + " has_actual_record: " + str(has_actual_record))
        return has_actual_record

    def is_record_expired(self, name):
        """ Is record with given name expired.
        Raises AttributeError if name is not in database."""

        if not self.has_record(name):
            raise AttributeError("Key '" + name + "' is not in database")

        if self.do_not_expire:
            print(name + " isexpired: False (do_not_expire mode turned ON)")
            return False

        record = self.records[name]
        is_record_expired = bool(record.calc_expiry_date() < datetime.now())

        print(name + " isexpired: " + str(is_record_expired))

        if is_record_expired:
            return True
        return False

    def assign_data_to(self, itemrust):
        """ Assigns data from database to itemrust.
        Raises AttributeError if itemrust is not in database"""

        #print("assigning data to " + itemrust.name)
        if not self.has_record(itemrust.name):
            raise AttributeError("Key '" + itemrust.name + "' is not in database")

        self.records[itemrust.name].assign_data_to(itemrust)
