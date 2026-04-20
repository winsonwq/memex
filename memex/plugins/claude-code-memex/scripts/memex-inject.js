#!/usr/bin/env bun
/**
 * memex-inject.js
 * SessionStart hook: 读取 transcript，提取上下文，注入相关记忆
 *
 * Claude Code 传入 JSON via stdin，输出 {"context": "..."} 到 stdout
 */

import { readFileSync } from "node:fs";
import { basename } from "node:path";

const MEMEX_CMD = "memex";
const DEFAULT_LIMIT = 10;

// 从 transcript 提取关键信息用于 search
function extractContextFromTranscript(transcriptPath) {
  try {
    const content = readFileSync(transcriptPath, "utf-8");
    const lines = content.trim().split("\n");
    
    // 取最后几行 assistant 消息作为上下文
    const recentLines = lines.slice(-10);
    const contextParts = [];
    
    for (const line of recentLines) {
      try {
        const entry = JSON.parse(line);
        if (entry.type === "assistant" && entry.message?.content) {
          const text = entry.message.content.slice(0, 300);
          if (text) contextParts.push(text);
        }
      } catch {
        // skip invalid JSON
      }
    }
    
    return contextParts.join(" ").trim().slice(0, 500);
  } catch {
    return "";
  }
}

// 从 project 目录名提取项目名
function extractProjectName(cwd) {
  return basename(cwd || "default");
}

// 运行 memex 命令
async function runMemex(args) {
  const { stdout, exitCode } = await new Promise((resolve) => {
    const proc = Bun.spawn([MEMEX_CMD, ...args], {
      stdout: "pipe",
      stderr: "pipe",
    });
    
    let stdoutData = "";
    proc.stdout.on("data", (chunk) => { stdoutData += chunk.toString(); });
    
    proc.exited.then((code) => {
      resolve({ stdout: stdoutData, exitCode: code });
    });
  });
  
  if (exitCode !== 0) return null;
  return stdout.trim();
}

// 格式化记忆为可读文本
function formatMemories(data) {
  const { results } = data;
  if (!results || results.length === 0) return null;
  
  const lines = ["=== Relevant Memory ==="];
  for (const r of results) {
    const type = r.type || "memory";
    const content = r.content;
    const score = r.score ? ` (score: ${r.score.toFixed(2)})` : "";
    lines.push(`[${type}]${score} ${content}`);
  }
  lines.push("===================");
  return lines.join("\n");
}

// 输出 context JSON 到 stdout
function outputContext(text) {
  console.log(JSON.stringify({ context: text }));
  process.exit(0);
}

// 注入记忆
async function injectMemory(projectName, query) {
  if (!query) {
    query = `项目 ${projectName} 最近的记忆`;
  }
  
  const args = ["search", query, "--repo", "claude-code", "--limit", String(DEFAULT_LIMIT)];
  const result = await runMemex(args);
  
  if (result && result.startsWith("{")) {
    try {
      const data = JSON.parse(result);
      if (data.results && data.results.length > 0) {
        const memories = formatMemories(data);
        if (memories) {
          outputContext(memories);
          return;
        }
      }
    } catch {
      // 解析失败，忽略
    }
  }
  
  // 无相关记忆，正常退出
  process.exit(0);
}

// Main
async function main() {
  let input = "";
  process.stdin.on("data", (chunk) => { input += chunk.toString(); });
  
  await new Promise((resolve) => {
    process.stdin.on("end", resolve);
  });
  
  let hookInput;
  try {
    hookInput = JSON.parse(input.trim() || "{}");
  } catch {
    process.exit(0);
    return;
  }
  
  const { cwd = "" } = hookInput;
  const projectName = extractProjectName(cwd);
  const query = extractContextFromTranscript(hookInput.transcript_path || "");
  
  await injectMemory(projectName, query);
}

main().catch(() => process.exit(0));
