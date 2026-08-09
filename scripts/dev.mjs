import { spawn } from "node:child_process";

const build = spawn(process.execPath, ["scripts/build.mjs"], {
  stdio: "inherit",
});

build.on("exit", (code) => {
  if (code !== 0) process.exit(code ?? 1);

  const server = spawn("npx", ["serve", "dist", "--listen", "3000"], {
    stdio: "inherit",
  });

  server.on("exit", (serverCode) => process.exit(serverCode ?? 0));
});
