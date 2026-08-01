// emit-manifest.ts — Composition manifest'ini üret ve public/ klasörüne yaz.
// Docker build context: remotion/  — bu script yalnızca remotion/ içindeki dosyaları okur.
// Çalıştırma: npx tsx scripts/emit-manifest.ts  (prebuild adımı)
import { writeFileSync, mkdirSync } from "fs"
import { resolve } from "path"
import { SCENE_REGISTRY } from "../src/registry"

// eslint-disable-next-line @typescript-eslint/no-var-requires
const pkg = require("../package.json") as { dependencies: { remotion: string } }
const remotionVersion: string = pkg.dependencies.remotion

const manifest = {
  generated_at: new Date().toISOString(),
  remotion_version: remotionVersion,
  compositions: Object.entries(SCENE_REGISTRY).map(([id, c]) => ({
    id,
    aspect:     c.aspect,
    components: c.components,
    required:   c.required,
  })),
}

const outDir = resolve(__dirname, "../public")
mkdirSync(outDir, { recursive: true })
writeFileSync(resolve(outDir, "compositions.json"), JSON.stringify(manifest, null, 2))
console.log(`[manifest] ${manifest.compositions.length} composition yazıldı → public/compositions.json`)
