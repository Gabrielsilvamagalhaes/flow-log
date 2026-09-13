import { Queue } from "bullmq";
import { redis } from "./server/config/redis";
import { cleanAllJobsFromQueue } from "./service/clean-jobs";
import { JobTypes } from "./shared/enums/jobs-types";
import { QueueNames } from "./shared/enums/queue-names";

// const connection = await getRedisConnection();

const testQueue = new Queue(QueueNames.TestQueue, {
  connection: redis,
});

const initJobs = async () => {
  await cleanAllJobsFromQueue(testQueue);

  const quicklyJob = await testQueue.add(JobTypes.QuicklyJob, {
    message: "Job rápido iniciado",
    apiToken: "TEST-API-TOKEN",
    password: "TEST-DB-PASSWORD",
  });

  const slowlyJob = await testQueue.add(JobTypes.SlowlyJob, {
    message: "Job lento iniciado",
  });

  const errorJob = await testQueue.add(
    JobTypes.ErrorJob,
    {
      message: "Job de erro iniciado",
    },
    {
      attempts: 3,
      backoff: {
        type: "exponential",
        delay: 5000,
      },
    },
  );

  const delayJob = await testQueue.add(
    JobTypes.DelayJob,
    {
      message: "Job com delay iniciado",
    },
    { delay: 10000 },
  );

  console.info("Jobs iniciados com sucesso!");

  // Close connections
  await testQueue.close();
  await redis.quit();
};

await initJobs();
