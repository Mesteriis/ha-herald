import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync, gunzipSync } from "node:zlib";
import { build } from "esbuild";

const root = fileURLToPath(new URL("../", import.meta.url));
const target = "custom_components/herald/frontend/herald-card.js";
const checkOnly = process.argv.includes("--check");
const result = await build({
  absWorkingDir: root,
  entryPoints: ["frontend/index.js"],
  bundle: true,
  format: "esm",
  platform: "browser",
  target: "es2020",
  legalComments: "eof",
  write: false,
  banner: { js: "// Generated from frontend/index.js by npm run build. Do not edit." },
});
const bundle = Buffer.from(result.outputFiles[0].contents);
const outputs = new Map([
  [target, bundle],
  [`${target}.gz`, gzipSync(bundle, { level: 9 })],
]);

for (const [relativePath, contents] of outputs) {
  const path = join(root, relativePath);
  if (checkOnly) {
    let current;
    try {
      current = readFileSync(path);
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    // Deflate output differs between Node/zlib versions. Verify the payload,
    // rather than treating equivalent compression as a stale frontend.
    const matches = relativePath.endsWith(".gz")
      ? current && gunzipSync(current).equals(bundle)
      : current?.equals(contents);
    if (!matches) {
      throw new Error(`${relativePath} is stale or missing. Run npm run build and commit both generated files.`);
    }
  } else {
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, contents);
  }
}
console.log(checkOnly ? "Frontend bundle and gzip match the source." : "Built frontend bundle and gzip.");
