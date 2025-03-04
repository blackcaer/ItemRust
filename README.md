# ItemRust Repository

The *ItemRust* repository is a helper package for working with Rust items on the Steam Market. It provides functionalities to fetch, store, and manage item data, including prices, price history, and sales offers. 
The package supports asynchronous operations for better performance and implements logic to determine data expiration based on item value. It was designed for my other Steam-related projects so I don't have to repeat that logic in every one of them.


**Disclaimer: This is an older project, so the code may be messy and lacks full documentation—but it was a valuable learning experience in data scraping and market analysis.**


## Key Features:
- **Asynchronous API Requests**: Efficiently fetch data from the Steam Market using asynchronous calls.
- **Item Data Management**: Store, update, and retrieve item information with automatic expiration handling.
- **Custom Expiration Logic**: Data freshness is controlled by item value, with the option to expire data on specific days (e.g., Fridays).
- **Database Handling**: Persistent storage of item records using JSON-based serialization.

## File Overview:

### `itemrust.py`
- Core module for interacting with the Steam Market API.
- Handles asynchronous HTTP requests and error management.
- Provides methods to fetch prices, offers, and other item-related data (some functions are placeholders for future implementations).

### `itemrustdatabase.py`
- Manages the item database.
- Supports synchronous and asynchronous saving/loading of item records.
- Handles record updates, deletions, and expiration checks.

### `itemrustdatabaserecord.py`
- Defines the structure of an item record in the database.
- Stores item attributes (e.g., prices, sales history) and calculates the expiration date based on value.
- Allows data transfer between the database and item objects.

### `result.py`
- Utility class to standardize API responses.
- Stores success status, returned data, and error messages.

