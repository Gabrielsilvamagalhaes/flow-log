import IORedis from "ioredis";

export const redis = new IORedis({
  port: 6379,
  host: "localhost",
  maxRetriesPerRequest: null,
});
