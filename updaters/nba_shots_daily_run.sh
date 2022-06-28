SHELL=/bin/bash
source "/Users/connordog/.bash_profile"

# Years defined as the starting year for a season (e.g. 2017 is for the 2017/18 season)
startYear=2021
endYear=2021
lastNgames=15
shortType="Post" #Pre/Post/AS/Reg

python ../scrapers/scraper_shots.py --start_year "$startYear" --end_year "$endYear" --lastNgames "$lastNgames" --short_type "$shortType"

wait

python ../processing/shots_Breakdown.py --start_year "$startYear" --end_year "$endYear" 

wait

python ../processing/shots_Distribution_Year.py --start_year "$startYear" --end_year "$endYear" 
python ../processing/shots_Distribution_Career.py

wait

python ../processing/shots_Relative_Year.py --start_year "$startYear" --end_year "$endYear" 

wait

python ../processing/shots_Relative_Career.py

wait

python ../processing/shot_skill_plus.py

wait

python ../processing/percentiles.py --start_year "$startYear" --end_year "$endYear" 

wait

bash nba_shots_tables_run.sh

wait

cd ../charting
python nba_shot_charts.py --player_name "YESTERDAY"
python nba_team_charts.py --min_start "$startYear"

# # wait
# # Run every offseason
# cd ../charting
# python nba_shot_charts.py --player_name "LASTYEAR"


wait

printf "\n\nNBA SHOTS DAILY RUN COMPLETED\n\n"
