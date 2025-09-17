import { createClient } from "@/hooks/utils";
import { StreamConfig } from "./streamWorker.types";

// Since workers can't directly access the client SDK, you'll need to recreate/import necessary parts
const ctx: Worker = self as any;

ctx.addEventListener("message", async (event: MessageEvent<StreamConfig>) => {
  try {
    const { threadId, assistantId, input, modelName, modelConfigs } =
      event.data;

    console.log("🌐 RECEIVED WORKER MESSAGE:", {
      threadId,
      assistantId,
      input,
      modelName,
    });

    const client = createClient();

    console.log("📡 MAKING LANGGRAPH API CALL:", {
      threadId,
      assistantId,
      streamMode: "events",
      config: {
        configurable: {
          customModelName: modelName,
          modelConfig: modelConfigs[modelName as keyof typeof modelConfigs],
        },
      },
    });

    const stream = client.runs.stream(threadId, assistantId, {
      input: input as Record<string, unknown>,
      streamMode: "events",
      config: {
        configurable: {
          customModelName: modelName,
          modelConfig: modelConfigs[modelName as keyof typeof modelConfigs],
        },
      },
    });

    console.log("📡 LANGGRAPH STREAM STARTED");

    for await (const chunk of stream) {
      console.log("📦 RECEIVED CHUNK FROM LANGGRAPH:", chunk);
      // Serialize the chunk and post it back to the main thread
      ctx.postMessage({
        type: "chunk",
        data: JSON.stringify(chunk),
      });
    }

    console.log("✅ WORKER STREAM COMPLETED");
    ctx.postMessage({ type: "done" });
  } catch (error: any) {
    console.error("❌ WORKER ERROR:", error.message);
    ctx.postMessage({
      type: "error",
      error: error.message,
    });
  }
});
