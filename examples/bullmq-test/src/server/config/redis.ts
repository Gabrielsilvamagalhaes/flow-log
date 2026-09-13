import IORedis from "ioredis";

export const getRedisConfig = (): { port: number; host: string } => {
  const portString = process.env.REDIS_PORT ?? 6379;
  const host = process.env.REDIS_HOST ?? "localhost";
  const port = Number(portString);

  if (Number.isNaN(port)) throw new Error("REDIS_PORT must be a number");

  return { port, host };
};

const { port, host } = getRedisConfig();

export const redis = new IORedis({
  port,
  host,
  maxRetriesPerRequest: null,
});
