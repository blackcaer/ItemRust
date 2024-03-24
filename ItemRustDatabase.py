import os
from datetime import datetime

import jsonpickle

from ItemRustDatabaseRecord import ItemRustDatabaseRecord


class ItemRustDatabase:
    def __init__(self, filename):
        self.filename = filename
        self.records: dict[str, ItemRustDatabaseRecord] = {}

    def is_empty(self):
        return len(self.records) == 0

    def load_database(self):
        """ Load self.records from file"""
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as file:
                data = jsonpickle.decode(file.read())
            self.records = data
        else:
            print(f"File '{self.filename}' does not exist.")

    def save_database(self):
        """ Save self.records to file"""
        if self.records is not None and not self.is_empty():
            print("Saving database")
            with open(self.filename, 'w') as f:
                # json.dump(obj_to_save, f)
                json_data = jsonpickle.encode(self.records)
                f.write(json_data)
        else:
            print("Not saving database - empty")

    def update_record(self, itemrust):
        """ Replace previous record with new one or create new record"""
        print("Updating db for " + itemrust.name)
        self.records[itemrust.name] = ItemRustDatabaseRecord(itemrust)

    def delete_record(self, name):
        """ Delete record with given name whether it exists or not"""
        self.records.pop(name, None)

    def has_actual_record(self, name):
        """ If the item in the database and has not expired"""
        has_actual_record = bool(name in self.records and not self._is_record_expired(name))
        print(name + " has_actual_record: " + str(has_actual_record))
        return has_actual_record

    def _is_record_expired(self, name):
        """ Is record with given name expired.
        Raises AttributeError if name is not in database."""
        """def calc_expiry_date():
            item = self.records[name]
            timestamp = item.timestamp
            now = datetime.now()
            value = item.
            pass
"""

        if name not in self.records:
            raise AttributeError("Key '" + name + "' is not in database")
        record = self.records[name]

        is_record_expired = bool(record.calc_expiry_date() < datetime.now())

        # is_record_expired = bool(self.records[name].timestamp < (datetime.now() - timedelta(hours=22)))
        print("" + name + " isexpired: " + str(is_record_expired))
        if is_record_expired:
            return True
        return False

    def assign_data_to(self, itemrust):
        """ Assigns data from database to itemrust.
        Raises AttributeError if itemrust is not in database"""
        print("assign data to " + itemrust.name)
        if itemrust.name not in self.records:
            raise AttributeError("Key '" + itemrust.name + "' is not in database")
        self.records[itemrust.name].assign_data_to(itemrust)
