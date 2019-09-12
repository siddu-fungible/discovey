from fun_global import get_current_time
from pymongo import MongoClient


class MongoDbManager():
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.fun_test

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


if __name__ == "__main__":
    m = MongoDbManager()
    collection1 = "t1"
    collection = m.get_collection(collection1)
    for i in range(100):
        post_data = {'date': get_current_time()}
        collection.insert_one(post_data)

