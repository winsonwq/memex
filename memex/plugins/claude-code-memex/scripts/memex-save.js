#!/usr/bin/env bun
/**
 * memex-save.js
 * PostToolUse / SessionEnd: 保存观察到 memex
 */

import { readFileSync } from "node:fs";

const MEMEX_CMD = "memex";
const REPO = "claude-code";
const isSessionEnd = process.argv.includes("--session-end");

// 从工具输入提取关键信息
function extractContent(toolName, toolInput) {
  if (toolName === "Bash") return toolInput?.command || null;
  if (toolName === "Edit") return `修改 ${toolInput?.file_path || toolInput?.file}: ${(toolInput?.old_string || "").slice(0, 50)}`;
  if (toolName === "Write") return `写入 ${toolInput?.file_path || toolInput?.file}`;
  if (toolName === "Read") return `读取 ${toolInput?.file_path || toolInput?.file}`;
  return null;
}

// 保存记忆
async function saveMemory(content) {
  return new Promise((resolve) => {
    const args = ["save", "--type", "journal", "--content", `"${content.replace(/"/g, '\\"')}"`, "--repo", REPO];
    const proc = Bun.spawn([MEMEX_CMD, ...args], { stdout: "pipe", stderr: "pipe" });
    proc.exited.then(() => resolve({ success: proc.exitCode === 0 }));
  });
}

// SessionEnd: 从 transcript 提取摘要
async function handleSessionEnd(transcriptPath) {
  try {
    const content = readFileSync(transcriptPath, "utf-8");
    const lines = content.trim().split("\n");
    const prompts = [];
    const actions = [];

    for (const line of lines.slice(-50)) {
      try {
        const e = JSON.parse(line);
        if (e.type === "user" && e.message?.content) prompts.push(e.message.content.slice(0, 80));
        if (e.type === "assistant" && e.message?.content) {
          const a = e.message.content;
          if (a.includes("创建") || a.includes("修改") || a.includes("执行")) actions.push(a.slice(0, 60));
        }
      } catch {}
    }

    const summary = [];
    if (prompts.length) summary.push(`用户: ${prompts[prompts.length - 1]}`);
    if (actions.length) summary.push(`操作: ${[...new Set(actions)].slice(-3).join("; ")}`);
    
    if (summary.length) await saveMemory(`会话摘要: ${summary.join(" | ")}`);
  } catch {}
}

// PostToolUse
async function handlePostToolUse(toolName, toolInput) {
  const content = extractContent(toolName, toolInput);
  if (content) await saveMemory(content);
}

// Main
async function main() {
  let input = "";
  process.stdin.on("data", (c) => { input += c.toString(); });
  await new Promise((r) => { process.stdin.on("end", r); });

  try {
    const { tool_name, tool_input, transcript_path } = JSON.parse(input.trim() || "{}");
    if (isSessionEnd) await handleSessionEnd(transcript_path);
    else if (tool_name) await handlePostToolUse(tool_name, tool_input);
  } catch {}

  process.exit(0);
}

main().catch(() => process.exit(0));
