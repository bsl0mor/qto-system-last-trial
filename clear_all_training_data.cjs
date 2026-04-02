#!/usr/bin/env node

/**
 * CLEAR ALL TRAINING PROJECTS FROM DATABASE
 * 
 * WARNING: This will permanently delete all 104 training projects
 * Make sure you have a backup if needed
 */

"use strict";

const mysql = require("mysql2/promise");
require("dotenv").config();

function parseDatabaseUrl(url) {
  const match = url.match(/^mysql:\/\/([^:]+):([^@]+)@([^:/]+):?(\d+)?\/([^?]+)/);
  return {
    host: match[3],
    port: parseInt(match[4] ?? "3306"),
    user: decodeURIComponent(match[1]),
    password: decodeURIComponent(match[2]),
    database: match[5],
    ssl: { rejectUnauthorized: false },
  };
}

(async () => {
  let conn = null;
  try {
    const cfg = parseDatabaseUrl(process.env.DATABASE_URL);
    conn = await mysql.createConnection(cfg);

    console.log("\n🔴 WARNING: DELETING ALL TRAINING PROJECTS");
    console.log("=" .repeat(80));

    // Get count before deletion
    const [before] = await conn.query("SELECT COUNT(*) as count FROM training_projects");
    console.log(`\nProjects before: ${before[0].count}\n`);

    if (before[0].count === 0) {
      console.log("✅ Database is already empty\n");
      process.exit(0);
    }

    // Delete all training projects
    console.log("Deleting training_projects...");
    const [result1] = await conn.execute("DELETE FROM training_projects");
    console.log(`✅ Deleted ${result1.affectedRows} training projects`);

    // Delete all learned patterns
    console.log("Deleting learned_patterns...");
    const [result2] = await conn.execute("DELETE FROM learned_patterns WHERE projectType IN ('g', 'g1', 'g2', 'g1service')");
    console.log(`✅ Deleted ${result2.affectedRows} learned patterns`);

    // Verify empty
    const [after] = await conn.query("SELECT COUNT(*) as count FROM training_projects");
    console.log(`\nProjects after: ${after[0].count}`);
    console.log("\n🟢 DATABASE CLEARED SUCCESSFULLY\n");

    await conn.end();

  } catch (err) {
    console.error("❌ ERROR:", err.message);
    process.exit(1);
  }
})();
