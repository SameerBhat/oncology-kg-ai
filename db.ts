#!/usr/bin/env ts-node

import { Command } from "commander";
import { MongoClient } from "mongodb";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();
const program = new Command();

// Hardcoded MongoDB URIs
const localUri = "mongodb://localhost:27017/jina4";
const prodUri =
  process.env.PROD_DATABASE_URI + "/jina4" ||
  "mongodb://localhost:27017/myProdDB";

console.log(`Using prod URI: ${prodUri}`);
// Extract database name
const dbName = (() => {
  try {
    const lastPart = localUri.split("/").pop();
    return lastPart?.split("?")[0] || "";
  } catch {
    console.error("❌ Could not parse DB name from URI");
    process.exit(1);
  }
})();

const backupDir = path.join(process.cwd(), "backup_databases");

// Utility to run shell commands
function runProcess(cmd: string, args: string[]): Promise<void> {
  return new Promise((resolve, reject) => {
    const proc = spawn(cmd, args, { stdio: "inherit" });
    proc.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${cmd} exited with code ${code}`));
    });
  });
}

// Sync prod DB → local DB
// Sync prod DB → local DB
async function syncDatabase(): Promise<void> {
  if (!fs.existsSync(backupDir)) fs.mkdirSync(backupDir);
  const timestamp = new Date().toISOString().replace(/:/g, "-");

  // const localBackup = path.join(
  //   backupDir,
  //   `${dbName}-${timestamp}-local.archive`
  // );
  const prodBackup = path.join(
    backupDir,
    `${dbName}-${timestamp}-prod.archive`
  );

  // console.log(`💾 Backing up local DB to ${localBackup}`);
  // await runProcess("mongodump", [
  //   `--uri=${localUri}`,
  //   `--archive=${localBackup}`,
  //   "--gzip",
  // ]);

  console.log(`⬇️ Dumping prod DB to ${prodBackup}`);
  await runProcess("mongodump", [
    `--uri=${prodUri}`,
    `--archive=${prodBackup}`,
    "--gzip",
  ]);

  console.log(`♻️ Restoring prod DB into local`);
  await runProcess("mongorestore", [
    `--uri=${localUri}`,
    `--archive=${prodBackup}`,
    "--gzip",
  ]);

  console.log("✅ Sync complete.");
}

program
  .command("sync")
  .description("Backup local DB and replace it with prod DB")
  .action(() => syncDatabase().catch(console.error));

program.parse(process.argv);
