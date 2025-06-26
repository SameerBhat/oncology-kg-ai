import { encoding_for_model } from "tiktoken";
import { MongoClient } from "mongodb";

// Setup tokenizer for the correct model
const enc = encoding_for_model("text-embedding-3-small");

// MongoDB connection setup
const MONGO_URI = "mongodb://localhost:27017/oncopro";
const DATABASE_NAME = "oncopro";

async function main() {
  const client = new MongoClient(MONGO_URI);
  try {
    await client.connect();
    const db = client.db(DATABASE_NAME);
    const nodesCollection = db.collection("nodes");

    const nodes = await nodesCollection.find({}).toArray();
    console.log("Total nodes:", nodes.length);

    let totalTokens = 0;

    for (const node of nodes) {
      const { richText = "", text = "", attributes = [], links = [] } = node;

      const combined = [richText, text, ...attributes, ...links].join("\n\n");

      const tokens = enc.encode(combined);
      totalTokens += tokens.length;
    }

    console.log("Total token count across all nodes:", totalTokens);
  } catch (err) {
    console.error("Error:", err);
  } finally {
    await client.close();
  }
}

main();
