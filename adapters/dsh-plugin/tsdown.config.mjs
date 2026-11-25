export default [
  {
    entry: { index: "src/index.ts" },
    outDir: "lib",
    format: "esm",
    platform: "node",
    target: "es2024",
    fixedExtension: false,
    clean: true,
    dts: false,
  },
  {
    entry: { client: "src/client/index.tsx" },
    outDir: "lib",
    format: "cjs",
    platform: "browser",
    target: "es2022",
    clean: false,
    dts: false,
    deps: {
      neverBundle: ["react", "react-dom", "react/jsx-runtime"],
    },
    outputOptions: {
      entryFileNames: "client.js",
      banner: 'window.__ModuleLoader__.load({ id: "dsh-skynet-prompt", factory: (require) => {',
      footer: "return module.exports; } });",
      intro: "var module = { exports: {} }; var exports = module.exports;",
    },
  },
]
