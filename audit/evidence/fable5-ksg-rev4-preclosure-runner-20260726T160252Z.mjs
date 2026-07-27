import { createHash } from "node:crypto";
import { execFile as execFileCallback } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const repo = process.cwd();
const stem = "fable5-ksg-rev4-preclosure-20260726T160252Z";
const evidenceDir = path.join(repo, "audit/evidence");
const promptPath = path.join(evidenceDir, `${stem.replace("-20260726T160252Z", "")}-prompt-20260726T160252Z.md`);
const contextPath = path.join(evidenceDir, `${stem}-context.md`);
const responsePath = path.join(evidenceDir, `${stem}-response.md`);
const receiptPath = path.join(evidenceDir, `${stem}-receipt.json`);
const runnerPath = fileURLToPath(import.meta.url);
const envPath = "/Users/torusprime/Development/sepahead-github/pid-rs/.env";

const expectedHead = "118e1de6a2d6d2ae33fe7bdc224736257e42a83f";
const expectedOriginMain = "118e1de6a2d6d2ae33fe7bdc224736257e42a83f";
const artifacts = [
  ["claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json", "29fc9f78122d85e2852890bbfba1849729c1d1016c074ed7071a4f3dd52dc8a3"],
  ["claims/KSG-INTEGER-HARMONIC-001/claim-v4.md", "f3438abbb5fa97df4f27940358b2b8e2244a7ac94ca9b03bb82c5772142e048b"],
  ["claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md", "28a4a5b885799a95f4450c241797886fd6a607abbbbb59bafd15db3195afd521"],
  ["claims/KSG-INTEGER-HARMONIC-001/routes-v4.md", "e14c3a54c81f84208f42b241b04d0feda3f32d0b1e62a32396c9e161ef5aa951"],
  ["claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md", "e14654f5b27273fefc0f9395f105c2e549ee4a281122579e722b47dc96e6d97d"],
  ["claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md", "d7c87b91e8bd4b43d86d08361f0b73df48f4d6ecb97d459f48ecb506f7f3d3e5"],
  ["claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md", "61e81c0812978ad8d806a7ab836a103d26b52061094bbb38d8ca3c3460834b11"],
  ["claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md", "0e9a04456a6d60ed151e5bd764e5a08060c83024c1731311234907a1db2e805d"],
  ["claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md", "45813b90cc15c6880ca9df83419851a7bb80adb4100963ff4c2322493d4eb905"],
  ["claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md", "04335c39cdbd409bd987805b3dc0d540bb5514d19d807a08940286d43770ca3c"],
  ["claims/KSG-INTEGER-HARMONIC-001/failures/preclosure-audit-findings-v3.md", "565e18922514123942dd4d241c2d677be27101c3402f6fb594dc699641eae071"],
  ["claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md", "062d51b03cbcfbfee9a16cba1e29ba3cb83480e6e48e603788828f917b08db25"],
  ["claims/KSG-INTEGER-HARMONIC-001/certificates/ksg-harmonic-modular-certificate-v1.json", "ae4645c3c9db7e8ad39d74edb1093114aeefc99d9ca9f41285ffffaeab277102"],
  ["audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean", "32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4"],
  ["audit/formal/z3-ksg-harmonic/ksg-local-bound-v4.smt2", "33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31"],
  ["scripts/check-lean-ksg-integer-harmonic.py", "eb57ba3632ba3d2a811c971b20ab5bda2d3b3e0cd26fe69662cc39dbf25504d4"],
  ["scripts/check-lean-ksg-integer-harmonic-self-test.py", "80e37d202acdc7fe9a5118601c693131e74bd8384c3e3ac712c8f0e617b92f3e"],
  ["scripts/check-z3-ksg-integer-harmonic.py", "c52618848f3331892bcb34b151a1e51674e7f493fbad71c48b160ff40fbf2d19"],
  ["scripts/check-z3-ksg-integer-harmonic-self-test.py", "241a23c903c5087dadc91b31d6fd332fc57f9d94ad46b62709290f25082cb07e"],
  ["scripts/check-ksg-harmonic-modular-certificate.py", "561f6c2fe25b5b54fd87f1c5b210b5cca55afda75b3b139ba5078269166aa755"],
  ["scripts/check-ksg-harmonic-modular-certificate-self-test.py", "c6376ab07d714a7d732568d589e73e01377cffdbcf163340e9866dfadda7eac4"],
  ["scripts/check-ksg-harmonic-revision.py", "286388468a3866f2a447ba6e01a62d0d34c0e0a5efe6dad3172977726d39ea46"],
  ["scripts/check-ksg-harmonic-revision-self-test.py", "cc048f2bd7518ff6309a416af1952a8be77ff8c0e31a030e2e4db4e09e874943"],
  ["crates/pid-core/src/stats.rs", "a8fc8a6792c1f1406caf45301b2d8eb47dadbe9058673535c249646df475acb2"],
  ["crates/pid-core/src/ksg.rs", "0f5109dda054a0222ed796209b10d22196348eddac76d8d53dd78b4e03a95250"],
  ["crates/pid-core/src/isx.rs", "ad2bf59da32433f866313d339889084050bff21e0b672589019260df8ff690d5"],
  ["crates/pid-core/src/pid3.rs", "f1f9d18b73312fb2e25e725382e65edf42bdaecd73d611d7dffc943221b2bfcd"],
  ["crates/pid-core/tests/ksg.rs", "544192cac6c00957e1e05a4cc320c069453060eb1fe676131f83b155c1ee6daa"],
  ["crates/pid-core/tests/isx.rs", "10b40cfc2b37243a28ae38d32917e803094d37e90549a993961a53eeeefd537d"],
  ["crates/pid-core/tests/ksg_report.rs", "724c1fad3ce11ce14b789efda0edccfe96a6f3334d077cad075dd667683b0f44"],
  ["crates/pid-core/tests/parallel_bit_identity.rs", "611a31e1b76536b1b1b712cdbd7713dc5caad24f354b0c507e2779bbf8f3cb28"],
];

const keyOrder = [
  "ELEVENTH_ANTHROPIC_API_KEY",
  "TWELFTH_ANTHROPIC_API_KEY",
  "NINTH_ANTHROPIC_API_KEY",
  "TENTH_ANTHROPIC_API_KEY",
  "EIGT_ANTHROPIC_API_KEY",
];

const sha256 = (value) => createHash("sha256").update(value).digest("hex");
const sanitize = (value) =>
  String(value)
    .replace(/sk-ant-[A-Za-z0-9_-]+/gu, "[REDACTED_API_KEY]")
    .replace(/[A-Za-z0-9_-]{80,}/gu, "[REDACTED_LONG_TOKEN]");

const parseEnv = (text) => {
  const result = {};
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
    result[key] = value;
  }
  return result;
};

const gitText = async (...args) => {
  const result = await execFile("git", args, {
    cwd: repo,
    encoding: "utf8",
    maxBuffer: 16 * 1024 * 1024,
  });
  if (result.stderr !== "") {
    throw new Error(`git ${args.join(" ")} failed: ${result.stderr}`);
  }
  return result.stdout.trim();
};

const head = await gitText("rev-parse", "HEAD");
const originMain = await gitText("rev-parse", "origin/main");
if (head !== expectedHead || originMain !== expectedOriginMain) {
  throw new Error(`Git anchor changed: HEAD=${head}, origin/main=${originMain}`);
}

const prompt = await readFile(promptPath, "utf8");
const runner = await readFile(runnerPath);
const manifest = [];
const sections = [
  "# Exact retained context for Fable 5 Max KSG revision-4 review\n\n",
  `HEAD and origin/main at launch: \`${head}\`.\n\n`,
  "The listed artifacts are exact UTF-8 bytes. Unlisted repository state is outside this review.\n",
];

for (const [relative, expected] of artifacts) {
  const bytes = await readFile(path.join(repo, relative));
  const actual = sha256(bytes);
  if (actual !== expected) {
    throw new Error(`artifact mismatch for ${relative}: expected ${expected}, got ${actual}`);
  }
  const artifactText = bytes.toString("utf8");
  if (Buffer.from(artifactText, "utf8").compare(bytes) !== 0) {
    throw new Error(`artifact is not exact UTF-8: ${relative}`);
  }
  manifest.push({ path: relative, sha256: actual, bytes: bytes.length });
  sections.push(
    `\n## Artifact: \`${relative}\`\n\nSHA-256: \`${actual}\`\n\n`,
    "```text\n",
    artifactText,
    artifactText.endsWith("\n") ? "" : "\n",
    "```\n",
  );
}

const context = sections.join("");
await writeFile(contextPath, context, { mode: 0o644 });

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
          text: `\n\n<exact-retained-context>\n${context}\n</exact-retained-context>`,
        },
      ],
    },
  ],
};

const readStream = async (response) => {
  const decoder = new TextDecoder();
  const rawDigest = createHash("sha256");
  let pending = "";
  let visibleText = "";
  let responseId = null;
  let responseModel = null;
  let stopReason = null;
  let usage = null;

  const event = (text) => {
    const data = text
      .split(/\r?\n/u)
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart());
    if (data.length === 0) return;
    const payload = JSON.parse(data.join("\n"));
    if (payload.type === "message_start") {
      responseId = payload.message?.id ?? responseId;
      responseModel = payload.message?.model ?? responseModel;
      usage = payload.message?.usage ?? usage;
    } else if (payload.type === "content_block_start" && payload.content_block?.type === "text") {
      visibleText += payload.content_block.text ?? "";
    } else if (payload.type === "content_block_delta" && payload.delta?.type === "text_delta") {
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
      const text = pending.slice(0, match.index);
      pending = pending.slice(match.index + match[0].length);
      event(text);
    }
  }
  pending += decoder.decode();
  if (pending.trim()) event(pending);
  return {
    visibleText,
    responseId,
    responseModel,
    stopReason,
    usage,
    rawSha256: rawDigest.digest("hex"),
  };
};

const env = parseEnv(await readFile(envPath, "utf8"));
const attempts = [];
let completed = null;
const startedAt = new Date().toISOString();

for (const alias of keyOrder) {
  const apiKey = env[alias];
  if (!apiKey) {
    attempts.push({ alias, outcome: "missing" });
    continue;
  }
  process.stdout.write(`attempt ${alias}\n`);
  try {
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const raw = await response.text();
      let requestId = null;
      let message = raw;
      try {
        const parsed = JSON.parse(raw);
        requestId = parsed.request_id ?? null;
        message = parsed.error?.message ?? raw;
      } catch {
        // Retain sanitized non-JSON error text.
      }
      attempts.push({
        alias,
        outcome: "http_error",
        status: response.status,
        requestId,
        message: sanitize(message),
      });
      continue;
    }
    completed = await readStream(response);
    attempts.push({
      alias,
      outcome: "completed",
      responseId: completed.responseId,
      model: completed.responseModel,
    });
    break;
  } catch (error) {
    attempts.push({ alias, outcome: "transport_or_stream_error", message: sanitize(error) });
  }
}

const finishedAt = new Date().toISOString();
if (completed) {
  await writeFile(responsePath, completed.visibleText, { mode: 0o644 });
}

const receipt = {
  schema: "pid-rs/external-hostile-review-receipt",
  schema_revision: 1,
  status: completed ? "completed_advisory" : "unavailable_all_configured_keys",
  model_requested: "claude-fable-5",
  effort: "max",
  max_tokens: 128000,
  started_at: startedAt,
  finished_at: finishedAt,
  head,
  origin_main: originMain,
  prompt: { path: path.relative(repo, promptPath), sha256: sha256(prompt) },
  context: { path: path.relative(repo, contextPath), sha256: sha256(context) },
  runner: { path: path.relative(repo, runnerPath), sha256: sha256(runner) },
  response: completed
    ? {
        path: path.relative(repo, responsePath),
        sha256: sha256(completed.visibleText),
        raw_stream_sha256: completed.rawSha256,
        response_id: completed.responseId,
        response_model: completed.responseModel,
        stop_reason: completed.stopReason,
        usage: completed.usage,
      }
    : null,
  artifact_manifest: manifest,
  attempts,
  boundary:
    "External model output is advisory falsification input. It is not proof, custody, or independent evidence for a shared premise.",
};
await writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, { mode: 0o644 });

if (!completed) {
  throw new Error("all configured Anthropic aliases were unavailable; sanitized receipt written");
}
process.stdout.write(
  `completed ${completed.responseModel} ${completed.responseId}; response SHA-256 ${sha256(completed.visibleText)}\n`,
);
