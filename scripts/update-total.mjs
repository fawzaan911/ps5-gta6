import { appendFileSync, writeFileSync } from "node:fs";

const secretKey = process.env.MOYASAR_SECRET_KEY;
const siteUrl = process.env.SITE_URL;

function setOutput(name, value) {
  if (process.env.GITHUB_OUTPUT) appendFileSync(process.env.GITHUB_OUTPUT, `${name}=${value}\n`);
}

if (!secretKey) {
  console.log("MOYASAR_SECRET_KEY is not set; the page will use collectedAmount from config.js.");
  setOutput("changed", "false");
  process.exit(0);
}

const auth = "Basic " + Buffer.from(secretKey + ":").toString("base64");
let page = 1;
let totalHalalas = 0;

while (page) {
  const res = await fetch(`https://api.moyasar.com/v1/payments?page=${page}`, {
    headers: { Authorization: auth },
  });
  if (!res.ok) throw new Error(`Moyasar API error ${res.status}: ${await res.text()}`);

  const body = await res.json();
  for (const p of body.payments) {
    if ((p.status === "paid" || p.status === "captured") && p.currency === "SAR") {
      totalHalalas += p.amount - (p.refunded || 0);
    }
  }
  page = body.meta?.next_page || null;
}

const collected = totalHalalas / 100;
writeFileSync("data.json", JSON.stringify({ collected, updatedAt: new Date().toISOString() }));
console.log(`Collected: ${collected} SAR`);

let previous = null;
try {
  const res = await fetch(new URL("data.json", siteUrl), { cache: "no-store" });
  if (res.ok) previous = (await res.json()).collected;
} catch {}

setOutput("changed", previous === collected ? "false" : "true");
