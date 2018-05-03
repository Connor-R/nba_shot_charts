SHELL=/bin/bash
source "/Users/connordog/.bash_profile"

cd ../scrapers
python scraper_playoff_shots.py
# python scraper_shots.py

wait

cd ../processing
python shots_Breakdown.py

wait

python shots_Distribution_Year.py
python shots_Distribution_Career.py

wait

python shots_Relative_Year.py

wait

python shots_Relative_Career.py

wait

python shot_skill_plus.py