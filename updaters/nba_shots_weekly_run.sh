SHELL=/bin/bash
source "/Users/connordog/.bash_profile"

cd ../scrapers
python scraper_players.py
python scraper_teams.py

wait

cd ../charting
python nba_shot_charts.py
