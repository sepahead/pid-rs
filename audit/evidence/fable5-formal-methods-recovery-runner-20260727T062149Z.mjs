import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repo = process.cwd();
const evidenceDir = path.join(repo, "audit/evidence");
const stamp = "20260727T062149Z";
const stem = `fable5-formal-methods-recovery-${stamp}`;
const promptPath = path.join(evidenceDir, `${stem}-prompt.md`);
const receiptPath = path.join(evidenceDir, `${stem}-receipt.json`);
const indexPath = path.join(evidenceDir, `${stem}-responses.md`);
const runnerPath = fileURLToPath(import.meta.url);
const envPath =
  "/Users/torusprime/Development/sepahead-github/pid-rs/.env";

const keyOrder = [
  "ELEVENTH_ANTHROPIC_API_KEY",
  "TWELFTH_ANTHROPIC_API_KEY",
  "NINTH_ANTHROPIC_API_KEY",
  "TENTH_ANTHROPIC_API_KEY",
  "EIGT_ANTHROPIC_API_KEY",
];

const reviewRoles = [
  "Act as a proof-assistant and SMT correspondence auditor. Concentrate on theorem statements, semantic bridges, proof objects, trust bases, shared cuts, and mutations.",
  "Act as a floating-point and compiled-refinement verifier. Concentrate on Gappa/Flocq/SMT-FP/interval/Kani/CBMC possibilities, signed zero, association, overflow, and production dataflow.",
  "Act as a mathematical PID researcher centered on categorical Makkeh--Gutknecht--Wibral shared exclusions. Concentrate on exact algebra, lattice/event semantics, all 108 PID3 coordinates, and useful bounded frontier theorems.",
  "Act as a statistical-methods hostile reviewer. Concentrate on estimands, support, identifiability, finite-sample bounds, dependence, UQ, calibration, multiplicity, and non-transfer among PID objects.",
  "Act as a scientific-process, evolutionary-search, custody, and publication auditor. Concentrate on CEGIS/genetic discovery, negative-result retention, durable recovery, machine/human schema parity, and complete-detail PDF verification.",
];

const sha256 = (value) => createHash("sha256").update(value).digest("hex");
const sanitize = (value) =>
  String(value)
    .replace(/sk-ant-[A-Za-z0-9_-]+/gu, "[REDACTED_API_KEY]")
    .replace(/[A-Za-z0-9_-]{80,}/gu, "[REDACTED_LONG_TOKEN]");

const parseEnv = (text) => {
  const values = {};
  for (const rawLine of text.split(/\r?\n/u)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) continue;
    const split = line.indexOf("=");
    const key = line.slice(0, split).trim();
    let value = line.slice(split + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    values[key] = value;
  }
  return values;
};

const readStreamedMessage = async (response) => {
  const decoder = new TextDecoder();
  const rawDigest = createHash("sha256");
  let pending = "";
  let responseId = null;
  let responseModel = null;
  let stopReason = null;
  let usage = null;
  let visibleText = "";

  const processEvent = (eventText) => {
    const dataLines = eventText
      .split(/\r?\n/u)
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart());
    if (dataLines.length === 0) return;
    const payload = JSON.parse(dataLines.join("\n"));
    if (payload.type === "message_start") {
      responseId = payload.message?.id ?? responseId;
      responseModel = payload.message?.model ?? responseModel;
      usage = payload.message?.usage ?? usage;
    } else if (
      payload.type === "content_block_start" &&
      payload.content_block?.type === "text"
    ) {
      visibleText += payload.content_block.text ?? "";
    } else if (
      payload.type === "content_block_delta" &&
      payload.delta?.type === "text_delta"
    ) {
      visibleText += payload.delta.text ?? "";
    } else if (payload.type === "message_delta") {
      stopReason = payload.delta?.stop_reason ?? stopReason;
      usage = { ...(usage ?? {}), ...(payload.usage ?? {}) };
    } else if (payload.type === "error") {
      throw new Error(payload.error?.message ?? "streamed Anthropic error");
    }
  };

  for await (const chunk of response.body) {
    rawDigest.update(chunk);
    pending += decoder.decode(chunk, { stream: true });
    for (;;) {
      const match = pending.match(/\r?\n\r?\n/u);
      if (!match || match.index === undefined) break;
      const eventText = pending.slice(0, match.index);
      pending = pending.slice(match.index + match[0].length);
      processEvent(eventText);
    }
  }
  const finalChunk = decoder.decode();
  if (finalChunk) pending += finalChunk;
  if (pending.trim()) processEvent(pending);

  return {
    responseId,
    responseModel,
    stopReason,
    usage,
    visibleText,
    rawSha256: rawDigest.digest("hex"),
  };
};

const prompt = await readFile(promptPath, "utf8");
const runner = await readFile(runnerPath);
const env = parseEnv(await readFile(envPath, "utf8"));
const status = execFileSync("git", ["status", "--short", "--branch"], {
  cwd: repo,
  encoding: "utf8",
});
const head = execFileSync("git", ["rev-parse", "HEAD"], {
  cwd: repo,
  encoding: "utf8",
});
const attempts = [];
const responses = [];
const startedAt = new Date();

const writeReceipt = async () => {
  const receipt = {
    schema: "pid-rs/fable5-multi-review-receipt",
    schema_revision: 1,
    advisory_only: true,
    started_at_utc: startedAt.toISOString(),
    updated_at_utc: new Date().toISOString(),
    model_requested: "claude-fable-5",
    max_tokens_per_attempt: 128000,
    thinking: { type: "adaptive" },
    output_config: { effort: "max" },
    prompt_path: path.relative(repo, promptPath),
    prompt_sha256: sha256(prompt),
    runner_path: path.relative(repo, runnerPath),
    runner_sha256: sha256(runner),
    head: head.trim(),
    initial_status_sha256: sha256(status),
    attempted_aliases: keyOrder,
    attempts,
    responses,
  };
  await writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, {
    mode: 0o644,
  });
};

for (let index = 0; index < keyOrder.length; index += 1) {
  const alias = keyOrder[index];
  const apiKey = env[alias];
  const role = reviewRoles[index];
  if (!apiKey) {
    attempts.push({ alias, role, outcome: "missing" });
    await writeReceipt();
    continue;
  }

  process.stdout.write(`attempt ${alias}\n`);
  const request = {
    model: "claude-fable-5",
    max_tokens: 128000,
    stream: true,
    thinking: { type: "adaptive" },
    output_config: { effort: "max" },
    messages: [
      {
        role: "user",
        content: [
          { type: "text", text: prompt },
          {
            type: "text",
            text: `\n\n<assigned-independent-review-role>\n${role}\n</assigned-independent-review-role>`,
          },
        ],
      },
    ],
  };

  let response;
  try {
    response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify(request),
    });
  } catch (error) {
    attempts.push({
      alias,
      role,
      outcome: "transport_error",
      message: sanitize(error),
    });
    await writeReceipt();
    continue;
  }

  if (!response.ok) {
    const raw = await response.text();
    let message = raw.slice(0, 1000);
    let requestId = null;
    try {
      const parsed = JSON.parse(raw);
      message = parsed?.error?.message ?? message;
      requestId = parsed?.request_id ?? null;
    } catch {
      // Retain the bounded raw prefix above.
    }
    attempts.push({
      alias,
      role,
      outcome: `http_${response.status}`,
      message: sanitize(message),
      request_id: requestId,
    });
    await writeReceipt();
    continue;
  }

  try {
    const streamed = await readStreamedMessage(response);
    const responsePath = path.join(
      evidenceDir,
      `${stem}-response-${index + 1}.md`,
    );
    await writeFile(responsePath, streamed.visibleText, { mode: 0o644 });
    const record = {
      alias,
      role,
      outcome: "success",
      response_path: path.relative(repo, responsePath),
      response_id: streamed.responseId,
      model: streamed.responseModel,
      stop_reason: streamed.stopReason,
      usage: streamed.usage,
      raw_response_sha256: streamed.rawSha256,
      visible_text_sha256: sha256(streamed.visibleText),
      visible_text_bytes: Buffer.byteLength(streamed.visibleText, "utf8"),
    };
    attempts.push({ alias, role, outcome: "success" });
    responses.push(record);
  } catch (error) {
    attempts.push({
      alias,
      role,
      outcome: "stream_error",
      message: sanitize(error),
    });
  }
  await writeReceipt();
}

const indexSections = [
  "# Fable 5 Max formal-method and recovery advisory responses\n\n",
  "These model responses are retained as advisory attack input, not evidence or proof. Every\n",
  "recommendation requires independent adjudication against primary sources, exact derivation,\n",
  "formal or certificate semantics, compiled behavior, and the repository object firewall.\n\n",
];
for (const response of responses) {
  indexSections.push(
    `## ${response.alias}\n\n`,
    `- Role: ${response.role}\n`,
    `- Response: \`${response.response_path}\`\n`,
    `- Visible SHA-256: \`${response.visible_text_sha256}\`\n`,
    `- Stop reason: \`${response.stop_reason}\`\n\n`,
  );
}
await writeFile(indexPath, indexSections.join(""), { mode: 0o644 });
await writeReceipt();
process.stdout.write(
  `completed ${responses.length}/${keyOrder.length} successful Fable advisory attempts\n`,
);
