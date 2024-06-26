import os

from dotenv import load_dotenv
from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection, model
from sentence_transformers import SentenceTransformer

load_dotenv()


class DatabaseManager:
    def __init__(self, collection_name):
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.collection_name = collection_name
        self.connect_to_milvus()

    @staticmethod
    def connect_to_milvus():
        connections.connect("default", uri=os.environ.get("MILVUS_URI"), token=os.environ.get("MILVUS_TOKEN"))

    def check_collection(self):
        return utility.has_collection(self.collection_name)

    def create_collection(self):
        fields = [
            FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100),
            FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="keywords", dtype=DataType.ARRAY, element_type=DataType.VARCHAR, max_capacity=100,
                        max_length=100),
            FieldSchema(name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=384)
        ]
        schema = CollectionSchema(fields, "Database collection where context of agents will be stored.")
        return Collection(self.collection_name, schema)

    def insert_data(self, name, keywords):
        embeddings = self.generate_embeddings(keywords)

        entities = [
            [name],  # field name
            [keywords],  # field keywords
            [embeddings]  # field embeddings
        ]

        collection = Collection(self.collection_name)
        collection.insert(entities)

        collection.flush()
        self.create_index()

    def generate_embeddings(self, keywords):
        return self.embedding_model.encode(", ".join(keywords))

    def create_index(self):
        index = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 128}
        }
        collection = Collection(self.collection_name)
        collection.create_index(field_name="embeddings", index_params=index)

    def similarity_search(self, keywords):
        collection = Collection(self.collection_name)
        collection.load()
        vector_to_search = self.generate_embeddings(keywords)
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        return collection.search([vector_to_search], "embeddings", search_params, limit=3, output_fields=["name"])


if __name__ == "__main__":
    db_manager = DatabaseManager("agents")
    if not db_manager.check_collection():
        db_manager.create_collection()

    result = db_manager.similarity_search(["hotel", "car"])

    for res in result:
        for obj in res:
            print(obj.entity.get("name"))
