import json

from main import DatabaseManager


def read_seed_data():
    with open('seed.json', 'r') as file:
        data = json.load(file)
    return data


def use_database_to_insert_data(database_manager):
    data = read_seed_data()
    for item in data:
        database_manager.insert_data(item['name'], item['keywords'])


if __name__ == "__main__":
    db_manager = DatabaseManager("agents")
    if not db_manager.check_collection():
        db_manager.create_collection()

    use_database_to_insert_data(db_manager)
