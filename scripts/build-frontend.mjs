import { build } from 'esbuild';

await build({
  entryPoints: ['frontend/herald-card.ts'],
  outfile: 'custom_components/herald/frontend/herald-card.js',
  bundle: true,
  format: 'esm',
  target: 'es2020',
  sourcemap: false,
  minify: false,
  legalComments: 'none',
});
