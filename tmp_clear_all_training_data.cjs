"use strict";
const fs = require("fs");
const path = require("path");
const mysql = require("./node_modules/.pnpm/mysql2@3.20.0_@types+node@20.19.37/node_modules/mysql2/promise");

function loadEnv() {
  try {
    const raw = fs.readFileSync(".env", "utf8");
    for (const line of raw.split("\n")) {
      const [k, ...vParts] = line.trim().split("=");
      if (k && !k.startsWith("#")) {
        const v = vParts.join("=").trim().replace(/^["']|["']$/g, "");
        if (!process.env[k]) process.env[k] = v;
      }
    }
  } catch { }
}

function parseDatabaseUrl(url) {
  const match = url.match(/^mysql:\/\/([^:]+):([^@]+)@([^:/]+):?(\d+)?\/([^?]+)/);
  if (!match) throw new Error("Invalid DATABASE_URL");
  return {
    host: match[3],
    port: parseInt(match[4] ?? "3306"),
    user: decodeURIComponent(match[1]),
    password: decodeURIComponent(match[2]),
    database: match[5],
    ssl: { rejectUnauthorized: false },
  };
}

loadEnv();

(async () => {
  console.log("=== DELETE ALL TRAINING DATA ===\n");
  const pool = await mysql.createPool(parseDatabaseUrl(process.env.DATABASE_URL));
  const conn = await pool.getConnection();

  console.log("Deleting learned_patterns for g/g1/g2/g1service...");
  const [delPatterns] = await conn.query(
    'DELETE FROM learned_patterns WHERE projectType IN ("g", "g1", "g2", "g1service")'
  );
  console.log(`  Deleted ${delPatterns.affectedRows} patterns`);

  console.log("Deleting training_projects for g/g1/g2/g1service...");
  const [delProjects] = await conn.query(
    'DELETE FROM training_projects WHERE projectType IN ("g", "g1", "g2", "g1service")'
  );
  console.log(`  Deleted ${delProjects.affectedRows} projects\n`);

  const [patterns] = await conn.query("SELECT COUNT(*) as cnt FROM learned_patterns");
  const [projects] = await conn.query("SELECT COUNT(*) as cnt FROM training_projects");

  console.log("After cleanup:");
  console.log(`  learned_patterns: ${patterns[0].cnt}`);
  console.log(`  training_projects: ${projects[0].cnt}`);

  await pool.end();
  console.log("\nDONE");
})();
