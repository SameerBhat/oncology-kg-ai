import { MongoClient } from "mongodb";
import OpenAI from "openai";
import dotenv from "dotenv";

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// const MONGO_URI = process.env.DATABASE_URI;
const MONGO_URI = "mongodb://localhost:27017"; // replace with your MongoDB URI
const DATABASE_NAME = "testvectors";

const fruits = [
  { name: "Apple", color: "Red", weight: 150, description: "A sweet red fruit", attributes: ["crunchy", "juicy"], whenToAvoid: "When overripe" },
  { name: "Banana", color: "Yellow", weight: 120, description: "A soft yellow fruit", attributes: ["sweet", "soft"], whenToAvoid: "When too ripe" },
  { name: "Orange", color: "Orange", weight: 130, description: "A citrus fruit with a tangy flavor", attributes: ["juicy", "citrusy"], whenToAvoid: "When too dry" },
  { name: "Grapes", color: "Purple", weight: 50, description: "Small round fruits that grow in bunches", attributes: ["sweet", "tart"], whenToAvoid: "When shriveled" },
  { name: "Mango", color: "Yellow", weight: 200, description: "A tropical fruit with a sweet flavor", attributes: ["sweet", "tropical"], whenToAvoid: "When too soft" },
  { name: "Pineapple", color: "Brown", weight: 900, description: "A tropical fruit with a spiky exterior", attributes: ["tropical", "sweet"], whenToAvoid: "When too ripe" },
  { name: "Strawberry", color: "Red", weight: 15, description: "A small red fruit with seeds on the outside", attributes: ["sweet", "juicy"], whenToAvoid: "When mushy" },
  { name: "Blueberry", color: "Blue", weight: 1, description: "A small blue fruit that is sweet and tangy", attributes: ["tart", "sweet"], whenToAvoid: "When shriveled" },
  { name: "Watermelon", color: "Green", weight: 5000, description: "A large fruit with a green rind and red flesh", attributes: ["refreshing", "juicy"], whenToAvoid: "When overripe" },
  { name: "Peach", color: "Pink", weight: 150, description: "A soft fruit with a fuzzy skin", attributes: ["sweet", "juicy"], whenToAvoid: "When too soft" },
  { name: "Kiwi", color: "Brown", weight: 75, description: "A small brown fruit with green flesh", attributes: ["tart", "sweet"], whenToAvoid: "When too soft" },
  { name: "Papaya", color: "Orange", weight: 500, description: "A tropical fruit with orange flesh", attributes: ["sweet", "tropical"], whenToAvoid: "When too ripe" },
  { name: "Cherry", color: "Red", weight: 5, description: "A small red fruit with a pit", attributes: ["sweet", "tart"], whenToAvoid: "When overripe" },
  { name: "Pear", color: "Green", weight: 180, description: "A sweet fruit with a smooth skin", attributes: ["sweet", "juicy"], whenToAvoid: "When too soft" },
  { name: "Plum", color: "Purple", weight: 70, description: "A small round fruit with a pit", attributes: ["sweet", "tart"], whenToAvoid: "When overripe" },
  { name: "Coconut", color: "Brown", weight: 1500, description: "A hard-shelled fruit with a sweet water inside", attributes: ["tropical", "refreshing"], whenToAvoid: "When too dry" },
  { name: "Lemon", color: "Yellow", weight: 100, description: "A sour citrus fruit", attributes: ["sour", "tart"], whenToAvoid: "When too dry" },
  { name: "Lime", color: "Green", weight: 50, description: "A small green citrus fruit", attributes: ["sour", "tart"], whenToAvoid: "When too dry" },
  { name: "Pomegranate", color: "Red", weight: 300, description: "A fruit with a tough outer skin and juicy seeds inside", attributes: ["tart", "sweet"], whenToAvoid: "When too dry" },
];

async function main() {
  const client = new MongoClient(MONGO_URI);

  try {
    await client.connect();
    const db = client.db(DATABASE_NAME);
    const fruitsCollection = db.collection("fruits");

    const documents = [];

    for (const fruit of fruits) {
      const inputText = `${fruit.name} is a ${fruit.color} fruit weighing ${fruit.weight} grams. It is described as: ${fruit.description}. Attributes include: ${fruit.attributes.join(", ")}. When to avoid: ${fruit.whenToAvoid}.`;
      const embeddingResponse = await openai.embeddings.create({
        model: "" +
            "", // or "text-embedding-ada-002"
        input: inputText,
      });

      const embedding = embeddingResponse.data[0].embedding;

      documents.push({
        ...fruit,
        embedding,
      });
    }

    await fruitsCollection.deleteMany({});
    await fruitsCollection.insertMany(documents);

    console.log(`Inserted ${documents.length} fruits with embeddings.`);
  } catch (err) {
    console.error("Error:", err);
  } finally {
    await client.close();
  }
}

main();
