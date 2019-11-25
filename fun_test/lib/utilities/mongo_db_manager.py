from fun_global import get_current_time, is_development_mode
from pymongo import MongoClient
import pymongo.errors



class MongoDbManager():
    if not is_development_mode():
        DEFAULT_HOST = "127.0.0.1"
    else:
        DEFAULT_HOST = "integration.fungible.local"
    DEFAULT_PORT = 27017

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.client = MongoClient(host=host, port=port)
        self.db = self.client.fun_test

    def test_connection(self):
        result = False
        try:
            info = self.client.server_info()
            result = True
        except pymongo.errors.ServerSelectionTimeoutError:
            print("server is down.")
        return result

    def collection_exists(self, collection_name):
        return collection_name in self.db.list_collection_names()

    def create_collection(self, collection_name):
        if not self.collection_exists(collection_name):
            collection = self.db[collection_name]
        else:
            collection = self.db[collection_name]
        return collection

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def delete_one(self, collection_name, query):
        result = None
        try:
            collection = self.get_collection(collection_name=collection_name)
            if collection:
                collection.delete_one(query)
                result = True
        except pymongo.errors.ServerSelectionTimeoutError:
            raise Exception("ServerSelectionTimeoutError")
        except Exception as ex:
            print ("delete_one exception: {}".format(str(ex)))
        return result

    def insert_one(self, collection_name, *args, **kwargs):
        result = None
        try:
            collection = self.get_collection(collection_name=collection_name)
            if collection:
                data_dict = kwargs
                collection.insert_one(data_dict)
                result = True
        except pymongo.errors.ServerSelectionTimeoutError:
            raise Exception("ServerSelectionTimeoutError")
        except Exception as ex:
            print ("insert_one exception: {}".format(str(ex)))
        return result

    def find_one_and_update(self, collection_name, key, *args, **kwargs):
        result = None
        try:
            collection = self.get_collection(collection_name=collection_name)
            update_dict = kwargs
            if collection:
                collection.find_one_and_update(key,
                                               {"$set": update_dict},
                                               upsert=True)
        except pymongo.errors.ServerSelectionTimeoutError:
            raise Exception("ServerSelectionTimeoutError")
        except Exception as ex:
            print ("insert_one exception: {}".format(str(ex)))
        return result

    def collections_count(self):
        return len(self.get_all_collection_names())

    def get_all_collection_names(self):
        return self.db.collection_names()

    def drop_collection(self, collection):
        collection.drop()

if __name__ == "__main2__":
    m = MongoDbManager()
    collection1 = "t1"
    collection = m.get_collection(collection1)
    for i in range(100):
        post_data = {'date': get_current_time()}
        collection.insert_one(post_data)


if __name__ == "__main__":
    m = MongoDbManager()
    m.test_connection()

