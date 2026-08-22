import { build } from 'esbuild'
import { mkdirSync, copyFileSync } from 'node:fs'
await build({entryPoints:['src/chat.ts'],bundle:true,minify:true,format:'iife',target:'es2020',outfile:'dist/chat.js',legalComments:'none'})
mkdirSync('../backend/app/static/widget',{recursive:true})
copyFileSync('dist/chat.js','../backend/app/static/widget/chat.js')
