// scripts/update-manifest.js
const fs = require("fs");
const path = require("path");

const version = process.argv[2];
const manifestPath = path.resolve("custom_components", "beaglecam", "manifest.json");

const manifest = JSON.parse(fs.readFileSync(manifestPath));
manifest.version = version;
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));

console.log(`✔ Updated manifest.json to version ${version}`);
