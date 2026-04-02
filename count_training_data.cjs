const fs = require('fs');
const path = require('path');

const csv = fs.readFileSync('B:\\work\\projects estimation\\projects\\projects_boq_calc_report.csv', 'utf8');
const lines = csv.split('\n').slice(1); // skip header

let withBOQ = 0;
let withCalc = 0;
let withBoth = 0;
const bothProjects = [];

for (const line of lines) {
  if (!line.trim()) continue;
  const hasBOQ = line.includes('"True"') && line.split(',')[2] === '"True"';
  const hasCalc = line.includes('"True"') && line.split(',')[3] === '"True"';
  if (hasBOQ) withBOQ++;
  if (hasCalc) withCalc++;
  if (hasBOQ && hasCalc) {
    withBoth++;
    // Extract path & name
    const match = line.match(/"([^"]+)","([^"]+)"/);
    if (match) {
      bothProjects.push({ path: match[1], name: match[2] });
    }
  }
}

console.log(`Total lines: ${lines.length}`);
console.log(`Projects with BOQ: ${withBOQ}`);
console.log(`Projects with Calculation: ${withCalc}`);
console.log(`Projects with BOTH: ${withBoth}`);
console.log('\nFirst 20 projects with both:');
bothProjects.slice(0, 20).forEach((p, i) => {
  console.log(`${i + 1}. ${p.name} => ${p.path}`);
});
