git add .
git commit -m "Update script/schedule"
git push
launchctl unload ~/Library/LaunchAgents/com.boto3lab.example.plist
launchctl load  ~/Library/LaunchAgents/com.boto3lab.example.plist
