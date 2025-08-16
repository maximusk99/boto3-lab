# boto3-lab

Small Boto3 automation lab for macOS with a LaunchAgent schedule.

## Quick start
```bash
# Create and activate a virtual env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Materialize a real LaunchAgent from the template
sed "s|__HOME__|$HOME|g" launchagent/com.boto3lab.example.template.plist \
  > ~/Library/LaunchAgents/com.boto3lab.example.plist

# Load and start the job (runs daily at 09:00; RunAtLoad starts once now)
launchctl unload ~/Library/LaunchAgents/com.boto3lab.example.plist 2>/dev/null || true
launchctl load  ~/Library/LaunchAgents/com.boto3lab.example.plist
launchctl start com.boto3lab.example

# Check logs
tail -n 50 ~/Library/Logs/boto3lab.out.log
tail -n 50 ~/Library/Logs/boto3lab.err.log
