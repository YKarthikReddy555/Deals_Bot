module.exports = {
  apps: [
    {
      name: 'cyber-bot-engine',
      script: 'ultimate_bot.py',
      interpreter: 'python3',
      restart_delay: 5000,
      env: {
        NODE_ENV: 'production',
      }
    },
    {
      name: 'admin-dashboard',
      script: 'dashboard.py',
      interpreter: 'python3',
      restart_delay: 5000,
      env: {
        NODE_ENV: 'production',
      }
    },
    {
      name: 'public-website',
      script: 'website.py',
      interpreter: 'python3',
      restart_delay: 5000,
      env: {
        NODE_ENV: 'production',
      }
    }
  ]
};
