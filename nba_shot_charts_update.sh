# Shell script to re-create all shot_charts and push to repository

python nba_shot_charts.py

git add *
git commit -m "weekly update"
git push