import { Queue } from "bullmq";
import { redis } from "./server/config/redis";
import { JobTypes } from "./shared/enums/jobs-types";

// const connection = await getRedisConnection();

const testQueue = new Queue("test-queue", {
  connection: redis,
});

const initJobs = async () => {
  const quicklyJob = await testQueue.add(JobTypes.QuicklyJob, {
    mesage: "Job 1 rápido iniciado",
  });

  console.log(quicklyJob.data);
  // await testQueue.add(JobTypes.QuicklyJob, { mesage: "Job 2 rápido iniciado" });

  console.info("Jobs iniciados com sucesso!");
};

await initJobs();
