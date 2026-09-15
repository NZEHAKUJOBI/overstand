import mongoose from "mongoose";

/**
 * Mongoose connection, cached across hot reloads in development and reused for
 * the lifetime of the process in production. Render runs a long-lived Node
 * server, so one pooled connection per instance is exactly what we want.
 *
 * Never import this from `middleware.ts` — that runs on the Edge runtime,
 * where the MongoDB driver cannot run.
 */

type ConnectionCache = {
  conn: typeof mongoose | null;
  promise: Promise<typeof mongoose> | null;
};

const globalForMongoose = globalThis as unknown as {
  _mongooseCache?: ConnectionCache;
};

const cache: ConnectionCache = globalForMongoose._mongooseCache ?? {
  conn: null,
  promise: null,
};

globalForMongoose._mongooseCache = cache;

export async function connectDb(): Promise<typeof mongoose> {
  if (cache.conn) return cache.conn;

  const uri = process.env.MONGODB_URI;
  if (!uri) {
    throw new Error(
      "MONGODB_URI is not set. Copy .env.example to .env.local and provide a MongoDB connection string.",
    );
  }

  if (!cache.promise) {
    cache.promise = mongoose
      .connect(uri, {
        // Fail fast with a clear error rather than hanging a page render.
        serverSelectionTimeoutMS: 10_000,
        maxPoolSize: 10,
      })
      .catch((error) => {
        // Clear the promise so the next request retries instead of reusing
        // a permanently rejected one.
        cache.promise = null;
        throw error;
      });
  }

  cache.conn = await cache.promise;
  return cache.conn;
}
