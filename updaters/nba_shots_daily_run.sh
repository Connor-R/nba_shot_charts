SHELL=/bin/bash
source "/Users/connordog/.bash_profile"

# Years defined as the starting year for a season (e.g. 2017 is for the 2017/18 season)
startYear=2018
endYear=2018
lastNgames=10
shortType="Pre" #Pre/Post/AS/Reg

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

python ../charting/nba_shot_charts.py --player_name "YESTERDAY"

wait

# Run every offseason
# python ../charting/nba_shot_charts.py --player_name "LASTYEAR"

