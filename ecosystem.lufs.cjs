module.exports = {
  apps: [{
    name: "lufs-next",
    cwd: "/home/edmon/sites/lufs.bots-ai.net",
    script: "node",
    args: "server.mjs",         // или: "node_modules/next/dist/bin/next", args: "start -p 3001"
    env: { NODE_ENV: "production", PORT: "3001" },
    out_file: "logs/out.log",
    error_file: "logs/err.log",
    max_restarts: 5,
    restart_delay: 2000
  }]
}
