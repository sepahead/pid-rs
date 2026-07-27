import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repo = process.cwd();
const evidenceDir = path.join(repo, "audit/evidence");
const stamp = "20260727T120200Z";
const stem = `fable5-ksg-rev4-settled-hostile-${stamp}`;
const promptPath = path.join(evidenceDir, `${stem}-prompt.md`);
const contextPath = path.join(evidenceDir, `${stem}-context.md`);
const receiptPath = path.join(evidenceDir, `${stem}-receipt.json`);
const oversizeReceiptPath = path.join(
  evidenceDir,
  `${stem}-oversize-negative-receipt.json`,
);
const indexPath = path.join(evidenceDir, `${stem}-responses.md`);
const runnerPath = fileURLToPath(import.meta.url);
const envPath = "/Users/torusprime/Development/sepahead-github/pid-rs/.env";

const keyOrder = [
  "ELEVENTH_ANTHROPIC_API_KEY",
  "TWELFTH_ANTHROPIC_API_KEY",
  "NINTH_ANTHROPIC_API_KEY",
  "TENTH_ANTHROPIC_API_KEY",
  "EIGT_ANTHROPIC_API_KEY",
];

const reviewRoles = [
  "Proof/SMT correspondence auditor: independently transcribe every theorem and attack premises, indexing, vacuity, models, proof trust, and mutations.",
  "Binary64 and compiled-refinement verifier: reconstruct the operation DAG and production dataflow; attack rounding, signed zero, association, counts, features, and backend parity.",
  "Statistical and primary-literature hostile reviewer: police estimands, support, formula conventions, theorem hypotheses, quantifiers, and every proposed transfer.",
  "Git/release/custody auditor: recompute the delta, hashes, generated projections, phase lifecycle, alternate-index assumptions, identity, and M1a/M1c chronology.",
  "Holistic mathematical red team and evolutionary-search designer: seek minimal exact counterexamples and mutation-resistant invariants while separating search from proof.",
  "Source-blind algebra auditor: derive the admissible domains, extrema, structural zeros, runtime image, and modular implications before comparing with repository claims.",
  "Checker-hostile formal-method engineer: design premise-deletion models, proof/certificate corruption attacks, independent evaluators, and separately encoded routes.",
  "Rust implementation adversary: follow every actual count and harmonic argument through KSG and Ehrlich callers under debug/release, serial/parallel, and brute/kd-tree profiles.",
  "Scientific-claims editor: locate every word that outruns its exact evidence, especially consistency, independence, sharpness, validation, universality, and publication readiness.",
  "Final synthesis skeptic: assume all prior reviewers share a hidden misconception; identify the strongest remaining single point of failure and a decisive test.",
];

const fullFiles = [
  "audit/evidence/codex-goal-prompt-2026-07-26.md",
  "audit/evidence/completion-handoff-2026-07-26-ksg-rev4.md",
  "audit/evidence/completion-active-resume.md",
  "audit/evidence/ksg-rev4-phase-path-policy.json",
  "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json",
  "claims/KSG-INTEGER-HARMONIC-001/claim-v4.md",
  "claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md",
  "claims/KSG-INTEGER-HARMONIC-001/routes-v4.md",
  "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md",
  "claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md",
  "claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md",
  "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md",
  "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md",
  "claims/KSG-INTEGER-HARMONIC-001/call-site-map.md",
  "claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-erratum-v2.md",
  "claims/KSG-INTEGER-HARMONIC-001/failures/decimal-reference-metric-conflation-v4.md",
  "claims/KSG-INTEGER-HARMONIC-001/failures/formal-seams-and-negative-controls-v2.md",
  "claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md",
  "claims/KSG-INTEGER-HARMONIC-001/failures/preclosure-audit-findings-v3.md",
  "crates/pid-core/src/stats.rs",
  "crates/pid-core/src/ksg.rs",
  "crates/pid-core/src/isx.rs",
  "crates/pid-core/src/pid3.rs",
  "crates/pid-core/tests/ksg.rs",
  "crates/pid-core/tests/isx.rs",
  "crates/pid-core/tests/ksg_report.rs",
  "crates/pid-core/tests/parallel_bit_identity.rs",
  "scripts/check-ksg-harmonic-exact-enclosure.py",
  "scripts/check-ksg-harmonic-modular-certificate.py",
  "scripts/check-ksg-harmonic-revision.py",
  "scripts/check-ksg-phase-isolation.py",
  "scripts/check-lean-ksg-integer-harmonic.py",
  "scripts/check-z3-ksg-integer-harmonic.py",
  "ecosystem-capabilities.json",
  "release-scope-1.0.json",
  "crates/pid-core/identity/software-identity-reference-v1.json",
];

const excerptFiles = [
  "README.md",
  "crates/pid-core/README.md",
  "METHODS.md",
  "ECOSYSTEM_CAPABILITIES.md",
  "RELEASE_SCOPE_1_0.md",
  "method-catalog.json",
  "audit/evidence/assurance-registry.json",
  "audit/evidence/task-dispositions.json",
  "AGENTS.md",
  "CHANGELOG.md",
  ".github/workflows/ci.yml",
  "justfile",
];

const excerptPattern =
  "KSG-INTEGER-HARMONIC|integer.harmonic|harmonic revision|ksg-harmonic|KSG harmonic|integration_no_go|integration NO-GO|open_integration_gates|assurance-registry|ecosystem";

const sha256 = (value) => createHash("sha256").update(value).digest("hex");
const run = (command, args) =>
  execFileSync(command, args, { cwd: repo, encoding: "utf8", maxBuffer: 64 << 20 });
const sanitize = (value) =>
  String(value)
    .replace(/sk-ant-[A-Za-z0-9_-]+/gu, "[REDACTED_API_KEY]")
    .replace(/[A-Za-z0-9_-]{80,}/gu, "[REDACTED_LONG_TOKEN]");
const numbered = (value) =>
  value
    .split(/\r?\n/u)
    .map((line, index) => `${String(index + 1).padStart(6, " ")} ${line}`)
    .join("\n");

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

const changedPaths = () => {
  const tracked = run("git", ["diff", "--name-only", "--diff-filter=ACMRTUXB", "HEAD"])
    .split(/\r?\n/u)
    .filter(Boolean);
  const untracked = run("git", ["ls-files", "--others", "--exclude-standard"])
    .split(/\r?\n/u)
    .filter(Boolean);
  const generatedOutputPaths = new Set([
    path.relative(repo, contextPath),
    path.relative(repo, receiptPath),
    path.relative(repo, oversizeReceiptPath),
    path.relative(repo, indexPath),
  ]);
  return [...new Set([...tracked, ...untracked])]
    .filter(
      (relative) =>
        !generatedOutputPaths.has(relative) &&
        !relative.startsWith(`audit/evidence/${stem}-response-r`),
    )
    .sort();
};

const buildContext = async () => {
  const head = run("git", ["rev-parse", "HEAD"]).trim();
  const headTree = run("git", ["rev-parse", "HEAD^{tree}"]).trim();
  const status = run("git", ["status", "--short", "--branch", "--untracked-files=all"]);
  const diffCheck = run("git", ["diff", "--check"]);
  const paths = changedPaths();
  const manifest = [];
  for (const relative of paths) {
    const bytes = await readFile(path.join(repo, relative));
    manifest.push({ path: relative, bytes: bytes.length, sha256: sha256(bytes) });
  }

  const parts = [
    "# Exact KSG revision-4 hostile-review context\n\n",
    "This context was generated before API calls. Line numbers are one-based render aids.\n",
    "The manifest covers every tracked modification and untracked file, while the full-text\n",
    "selection is intentionally narrower and declared below. Omission from full text is not\n",
    "evidence that a path is correct.\n\n",
    "## Git state\n\n```text\n",
    `HEAD ${head}\nHEAD tree ${headTree}\n`,
    status,
    "```\n\n",
    "## Diff check\n\n```text\n",
    diffCheck || "clean\n",
    "```\n\n",
    "## Complete changed-path byte manifest\n\n```json\n",
    `${JSON.stringify(manifest, null, 2)}\n`,
    "```\n\n",
  ];

  for (const relative of fullFiles) {
    const value = await readFile(path.join(repo, relative), "utf8");
    parts.push(
      `## Full file: ${relative}\n\n`,
      `SHA-256: \`${sha256(value)}\`; bytes: ${Buffer.byteLength(value, "utf8")}\n\n`,
      "```text\n",
      numbered(value),
      "\n```\n\n",
    );
  }

  for (const relative of excerptFiles) {
    let excerpt = "";
    try {
      excerpt = run("rg", ["-n", "-C", "14", excerptPattern, relative]);
    } catch (error) {
      if (error?.status !== 1) throw error;
    }
    const value = await readFile(path.join(repo, relative));
    parts.push(
      `## Pattern excerpt: ${relative}\n\n`,
      `Whole-file SHA-256: \`${sha256(value)}\`; bytes: ${value.length}\n\n`,
      "```text\n",
      excerpt || "[no matching excerpt]\n",
      "```\n\n",
    );
  }

  const context = parts.join("");
  await writeFile(contextPath, context, { mode: 0o644 });
  return { context, manifest, head, headTree, status, diffCheck };
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

let priorOversizeReceipt = null;
try {
  const priorReceiptBytes = await readFile(receiptPath);
  const priorReceipt = JSON.parse(priorReceiptBytes.toString("utf8"));
  if (
    Array.isArray(priorReceipt.attempts) &&
    priorReceipt.attempts.some(
      (attempt) =>
        typeof attempt.message === "string" &&
        attempt.message.includes("prompt is too long"),
    )
  ) {
    await writeFile(oversizeReceiptPath, priorReceiptBytes, { mode: 0o644 });
    priorOversizeReceipt = {
      path: path.relative(repo, oversizeReceiptPath),
      sha256: sha256(priorReceiptBytes),
      context_sha256: priorReceipt.context_sha256 ?? null,
      context_bytes: priorReceipt.context_bytes ?? null,
      attempts: priorReceipt.attempts,
      disposition:
        "retained fail-closed context-budget negative; no model response was produced",
    };
  }
} catch (error) {
  if (error?.code !== "ENOENT") throw error;
}

const prompt = await readFile(promptPath, "utf8");
const runner = await readFile(runnerPath);
const env = parseEnv(await readFile(envPath, "utf8"));
const generated = await buildContext();
const context = generated.context;
const attempts = [];
const responses = [];
const terminalAliases = new Set();
const transientCounts = new Map();
const successfulCounts = new Map();
const startedAt = new Date();
const maxRounds = 12;

const writeReceipt = async () => {
  const receipt = {
    schema: "pid-rs/fable5-settled-hostile-receipt",
    schema_revision: 1,
    advisory_only: true,
    started_at_utc: startedAt.toISOString(),
    updated_at_utc: new Date().toISOString(),
    model_requested: "claude-fable-5",
    max_tokens_per_attempt: 128000,
    thinking: { type: "adaptive" },
    output_config: { effort: "max" },
    maximum_rounds_safety_bound: maxRounds,
    prior_oversize_negative: priorOversizeReceipt,
    prompt_path: path.relative(repo, promptPath),
    prompt_sha256: sha256(prompt),
    context_path: path.relative(repo, contextPath),
    context_sha256: sha256(context),
    context_bytes: Buffer.byteLength(context, "utf8"),
    context_changed_path_manifest: generated.manifest,
    runner_path: path.relative(repo, runnerPath),
    runner_sha256: sha256(runner),
    head: generated.head,
    head_tree: generated.headTree,
    initial_status_sha256: sha256(generated.status),
    initial_diff_check_sha256: sha256(generated.diffCheck),
    attempted_aliases: keyOrder,
    terminal_aliases: [...terminalAliases],
    attempts,
    responses,
  };
  await writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, {
    mode: 0o644,
  });
};

for (let round = 0; round < maxRounds; round += 1) {
  let attemptedThisRound = 0;
  for (let index = 0; index < keyOrder.length; index += 1) {
    const alias = keyOrder[index];
    if (terminalAliases.has(alias)) continue;
    const apiKey = env[alias];
    const role = reviewRoles[(round * keyOrder.length + index) % reviewRoles.length];
    if (!apiKey) {
      attempts.push({ round: round + 1, alias, role, outcome: "missing" });
      terminalAliases.add(alias);
      await writeReceipt();
      continue;
    }

    attemptedThisRound += 1;
    process.stdout.write(`round ${round + 1} attempt ${alias}\n`);
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
            { type: "text", text: `\n\n<exact-candidate-context>\n${context}\n</exact-candidate-context>` },
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
      const count = (transientCounts.get(alias) ?? 0) + 1;
      transientCounts.set(alias, count);
      attempts.push({
        round: round + 1,
        alias,
        role,
        outcome: "transport_error",
        message: sanitize(error),
      });
      if (count >= 3) terminalAliases.add(alias);
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
        // Retain only the bounded, sanitized prefix above.
      }
      const creditExhausted = /credit balance is too low|insufficient credit/iu.test(message);
      const outcome = creditExhausted ? "credit_exhausted" : `http_${response.status}`;
      attempts.push({
        round: round + 1,
        alias,
        role,
        outcome,
        message: sanitize(message),
        request_id: requestId,
      });
      if (creditExhausted || response.status === 401 || response.status === 403) {
        terminalAliases.add(alias);
      } else {
        const count = (transientCounts.get(alias) ?? 0) + 1;
        transientCounts.set(alias, count);
        if (count >= 3) terminalAliases.add(alias);
      }
      await writeReceipt();
      continue;
    }

    try {
      const streamed = await readStreamedMessage(response);
      const successNumber = (successfulCounts.get(alias) ?? 0) + 1;
      successfulCounts.set(alias, successNumber);
      const responsePath = path.join(
        evidenceDir,
        `${stem}-response-r${round + 1}-a${index + 1}.md`,
      );
      await writeFile(responsePath, streamed.visibleText, { mode: 0o644 });
      const record = {
        round: round + 1,
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
      attempts.push({ round: round + 1, alias, role, outcome: "success" });
      responses.push(record);
    } catch (error) {
      const count = (transientCounts.get(alias) ?? 0) + 1;
      transientCounts.set(alias, count);
      attempts.push({
        round: round + 1,
        alias,
        role,
        outcome: "stream_error",
        message: sanitize(error),
      });
      if (count >= 3) terminalAliases.add(alias);
    }
    await writeReceipt();
  }
  if (attemptedThisRound === 0 || terminalAliases.size === keyOrder.length) break;
}

const indexSections = [
  "# Fable 5 Max KSG revision-4 settled-hostile responses\n\n",
  "These responses are retained as advisory attack input, not evidence or proof. Each allegation\n",
  "requires independent adjudication. Agreement among calls is a correlated model observation.\n\n",
];
for (const response of responses) {
  indexSections.push(
    `## Round ${response.round}: ${response.alias}\n\n`,
    `- Role: ${response.role}\n`,
    `- Response: \`${response.response_path}\`\n`,
    `- Visible SHA-256: \`${response.visible_text_sha256}\`\n`,
    `- Stop reason: \`${response.stop_reason}\`\n\n`,
  );
}
await writeFile(indexPath, indexSections.join(""), { mode: 0o644 });
await writeReceipt();
process.stdout.write(
  `completed ${responses.length} successful advisory calls; terminal aliases ${terminalAliases.size}/${keyOrder.length}\n`,
);
