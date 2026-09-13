import type { Queue } from "bullmq";

export const cleanAllJobsFromQueue = async (queue: Queue) => {
  // Remove all jobs from the queue
  await queue.obliterate({ force: true });

  console.info("All jobs been removed");
};
