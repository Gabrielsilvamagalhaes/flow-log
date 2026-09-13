import { type Job, Worker } from "bullmq";
import { redis } from "../server/config/redis";
import { JobTypes } from "../shared/enums/jobs-types";
import { QueueNames } from "../shared/enums/queue-names";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const worker = new Worker(
  QueueNames.TestQueue,
  async (job: Job) => {
    console.log(`Worker pegou o job: ${job.name}`);

    if (job.name === JobTypes.SlowlyJob) {
      console.info("Job lento caiu no setTimeout");
      await job.log("Job lento iniciado (etapa 1/3)");
      await sleep(10000);
      await job.log("Job lento em andamento (etapa 2/3)");
      await sleep(10000);
      await job.log("Job lento finalizando (etapa 3/3)");
      await sleep(10000);
    }

    if (job.name === JobTypes.ErrorJob) {
      console.error("Job de erro caiu na exceção");
      throw new Error("Job de erro");
    }
  },
  { connection: redis, autorun: false, concurrency: 4 },
);

worker.on("active", (job: Job) => {
  console.time(`Processing job ${job.id} of type ${job.name}`);
  console.info(`Job ativo: ${job.id} do tipo ${job.name}.`);
});

worker.on("failed", (job: Job | undefined, error: Error) => {
  console.error(
    `Falha no job ${job?.id} do tipo ${job?.name}. Tentativa ${job?.attemptsMade} Razão: ${job?.failedReason}. Stacktrace: ${error.stack}.`,
  );
});

worker.on("completed", (job: Job) => {
  console.timeEnd(`Processing job ${job.id} of type ${job.name}`);
  console.info(`Job ${job.id} do tipo ${job.name} concluído com sucesso.`);
});

worker.on("ready", () => {
  console.info("Worker pronto para processar jobs.");
});
