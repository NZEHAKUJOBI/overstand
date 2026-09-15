/**
 * Runs a local MongoDB for development, so you can work without installing one.
 * Data is kept in .mongo-data, so it survives restarts.
 *
 *   npm run mongo:dev        # leave running in its own terminal
 *
 * Point .env.local at it:
 *   MONGODB_URI=mongodb://127.0.0.1:27017/anchor
 *
 * This is a development convenience only — production uses the MONGODB_URI
 * configured on Render.
 */
import { mkdirSync } from "node:fs";
import { MongoMemoryServer } from "mongodb-memory-server";

const PORT = Number(process.env.MONGO_DEV_PORT ?? 27017);
const DB_PATH = ".mongo-data";

mkdirSync(DB_PATH, { recursive: true });

const mongo = await MongoMemoryServer.create({
  instance: { port: PORT, dbName: "anchor", dbPath: DB_PATH, storageEngine: "wiredTiger" },
});

console.log(`\n  MongoDB listening on ${mongo.getUri("anchor")}`);
console.log(`  Data directory: ${DB_PATH}`);
console.log("  Press Ctrl+C to stop.\n");

async function shutdown() {
  await mongo.stop();
  process.exit(0);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

await new Promise(() => {});
