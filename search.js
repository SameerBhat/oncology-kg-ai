import { MongoClient } from "mongodb";
import OpenAI from "openai";
import dotenv from "dotenv";
dotenv.config();
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const query = "green rind";

const embeddingResponse = await openai.embeddings.create({
  model: "text-embedding-3-small", // or "text-embedding-ada-002"
  input: query,
});

const queryEmbedding = embeddingResponse.data[0].embedding;

const MONGO_URI = process.env.DATABASE_URI;
const DATABASE_NAME = "testvectors";

const client = new MongoClient(MONGO_URI); // use your Atlas URI

await client.connect();
const db = client.db(DATABASE_NAME);

const results = await db.collection("fruits").aggregate([
  {
    $vectorSearch: {
      index: "fruits_vector_index",
      path: "embedding",
      queryVector: queryEmbedding,
      similarity: "cosine",
      limit: 5,
      numCandidates: 100  // ← must be present
    }
  }
]).toArray();

console.log("Top Results:", results);

await client.close();