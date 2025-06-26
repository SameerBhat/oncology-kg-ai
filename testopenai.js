import OpenAI from "openai";
import dotenv from 'dotenv';
dotenv.config();
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});
const MODEL = "text-embedding-3-small";
async function generateEmbeddings(text) {
  try {
    const response = await openai.embeddings.create({
      model: MODEL,
      input: text,
    });
    return response.data[0].embedding;
  } catch (error) {
    console.error("Error generating embeddings:", error);
    throw error;
  }
}

async function main() {
  const text = "Hello, world!";
  try {
    const embedding = await generateEmbeddings(text);
    console.log("Generated embedding:", embedding);
  } catch (error) {
    console.error("Error in main function:", error);
  }
}

main();
