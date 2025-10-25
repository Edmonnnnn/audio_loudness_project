module.exports = {
  apps: [
    {
      name: "lufs-web",
      script: "server.mjs",
      cwd: "/home/edmon/sites/lufs.bots-ai.net",
      env: { NODE_ENV: "production", PORT: "3002" },
      instances: 1,
      autorestart: true,
      max_restarts: 10,
      exp_backoff_restart_delay: 500
    }
  ]
};
