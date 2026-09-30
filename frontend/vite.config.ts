import { existsSync } from "node:fs";
import { resolve } from "node:path";

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";


function normalizeBasePath(value: string | undefined): string {
  if (!value || value === "/") {
    return "/";
  }

  return `/${value.replace(/^\/+|\/+$/g, "")}/`;
}


export default defineConfig(({ mode }) => {
  const environment = loadEnv(mode, process.cwd(), "");
  const demoMode = environment.VITE_DEMO_MODE || "api";

  if (demoMode !== "api" && demoMode !== "static") {
    throw new Error("VITE_DEMO_MODE must be either 'api' or 'static'.");
  }

  return {
    base: normalizeBasePath(environment.VITE_BASE_PATH),
    resolve: {
      alias:
        demoMode === "static"
          ? {
              "./lib/demoDataSource": resolve(process.cwd(), "src/lib/staticDemoDataSource.ts"),
            }
          : {},
    },
    plugins: [
      react(),
      {
        name: "validate-static-showcase-assets",
        apply: "build",
        buildStart() {
          if (demoMode === "static" && !existsSync(resolve(process.cwd(), "public/showcase/manifest.json"))) {
            this.error(
              "Static showcase assets are missing. Run 'PYTHONPATH=src python -m demo.export_showcase' from the repository root before building.",
            );
          }
        },
      },
    ],
  };
});
