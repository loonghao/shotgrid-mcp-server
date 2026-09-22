import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

// The MCP Apps host renders `ui://` resources inside a CSP-restricted iframe that
// denies subresource loads by default, so every script and style must be inlined
// into a single HTML document. `viteSingleFile()` does that inlining; the result
// is committed to `src/shotgrid_mcp_server/apps/dashboard/index.html` so the
// Python runtime never needs Node.
export default defineConfig({
  plugins: [viteSingleFile()],
  build: {
    target: "es2020",
    outDir: "../src/shotgrid_mcp_server/apps/dashboard",
    emptyOutDir: true,
    cssCodeSplit: false,
    // Inline every asset: the sandboxed iframe has no origin to fetch from.
    assetsInlineLimit: Number.MAX_SAFE_INTEGER,
    chunkSizeWarningLimit: Number.MAX_SAFE_INTEGER,
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
      },
    },
  },
});
