
from pymongo import MongoClient
import nltk
from src.utils import DATABASE_NAME, MONGO_URI, embed_text_using_jina_model

nltk.download('punkt_tab')

fruits = [
    {"name": "Apple", "color": "Red", "weight": 150, "description": "A sweet red fruit", "attributes": ["crunchy", "juicy"], "whenToAvoid": "When overripe"},
    {"name": "Banana", "color": "Yellow", "weight": 120, "description": "A soft yellow fruit", "attributes": ["sweet", "soft"], "whenToAvoid": "When too ripe"},
    {"name": "Orange", "color": "Orange", "weight": 130, "description": "A citrus fruit with a tangy flavor", "attributes": ["juicy", "citrusy"], "whenToAvoid": "When too dry"},
    {"name": "Grapes", "color": "Purple", "weight": 50, "description": "Small round fruits that grow in bunches", "attributes": ["sweet", "tart"], "whenToAvoid": "When shriveled"},
    {"name": "Mango", "color": "Yellow", "weight": 200, "description": "A tropical fruit with a sweet flavor", "attributes": ["sweet", "tropical"], "whenToAvoid": "When too soft"},
    {"name": "Pineapple", "color": "Brown", "weight": 900, "description": "A tropical fruit with a spiky exterior", "attributes": ["tropical", "sweet"], "whenToAvoid": "When too ripe"},
    {"name": "Strawberry", "color": "Red", "weight": 15, "description": "A small red fruit with seeds on the outside", "attributes": ["sweet", "juicy"], "whenToAvoid": "When mushy"},
    {"name": "Blueberry", "color": "Blue", "weight": 1, "description": "A small blue fruit that is sweet and tangy", "attributes": ["tart", "sweet"], "whenToAvoid": "When shriveled"},
    {"name": "Watermelon", "color": "Green", "weight": 5000, "description": "A large fruit with a green rind and red flesh", "attributes": ["refreshing", "juicy"], "whenToAvoid": "When overripe"},
    {"name": "Peach", "color": "Pink", "weight": 150, "description": "A soft fruit with a fuzzy skin", "attributes": ["sweet", "juicy"], "whenToAvoid": "When too soft"},
    {"name": "Kiwi", "color": "Brown", "weight": 75, "description": "A small brown fruit with green flesh", "attributes": ["tart", "sweet"], "whenToAvoid": "When too soft"},
    {"name": "Papaya", "color": "Orange", "weight": 500, "description": "A tropical fruit with orange flesh", "attributes": ["sweet", "tropical"], "whenToAvoid": "When too ripe"},
    {"name": "Cherry", "color": "Red", "weight": 5, "description": "A small red fruit with a pit", "attributes": ["sweet", "tart"], "whenToAvoid": "When overripe"},
    {"name": "Pear", "color": "Green", "weight": 180, "description": "A sweet fruit with a smooth skin", "attributes": ["sweet", "juicy"], "whenToAvoid": "When too soft"},
    {"name": "Plum", "color": "Purple", "weight": 70, "description": "A small round fruit with a pit", "attributes": ["sweet", "tart"], "whenToAvoid": "When overripe"},
    {"name": "Coconut", "color": "Brown", "weight": 1500, "description": "A hard-shelled fruit with a sweet water inside", "attributes": ["tropical", "refreshing"], "whenToAvoid": "When too dry"},
    {"name": "Lemon", "color": "Yellow", "weight": 100, "description": "A sour citrus fruit", "attributes": ["sour", "tart"], "whenToAvoid": "When too dry"},
    {"name": "Lime", "color": "Green", "weight": 50, "description": "A small green citrus fruit", "attributes": ["sour", "tart"], "whenToAvoid": "When too dry"},
    {"name": "Pomegranate", "color": "Red", "weight": 300, "description": "A fruit with a tough outer skin and juicy seeds inside", "attributes": ["tart", "sweet"], "whenToAvoid": "When too dry"},
]




# Safeguard for max token estimation (~3.5 words/token)




def generate_fruit_text(fruit):
    return f"{fruit['name']} is a {fruit['color']} fruit weighing {fruit['weight']} grams. " \
           f"It is described as: {fruit['description']}. " \
           f"Attributes include: {', '.join(fruit['attributes'])}. " \
           f"When to avoid: {fruit['whenToAvoid']}."



def main():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    fruits_collection = db["fruits"]

    documents = []

    for fruit in fruits:
        input_text = generate_fruit_text(fruit)
        embedding = embed_text_using_jina_model(input_text)

        documents.append({
            **fruit,
            "text": input_text,
            "embedding": embedding
        })

    # Clear and insert
    fruits_collection.delete_many({})
    fruits_collection.insert_many(documents)

    print(f"✅ Inserted {len(documents)} fruits with embeddings.")

if __name__ == "__main__":
    main()
