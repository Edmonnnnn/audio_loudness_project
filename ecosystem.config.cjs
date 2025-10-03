module.exports = {
  apps: [{
    name: "lufs",
    cwd: "/home/edmon/sites/lufs.bots-ai.net",
    script: "node",
    args: "server.mjs",
    env: { NODE_ENV: "production", HOST: "127.0.0.1", PORT: "8211" }
  }]
}
