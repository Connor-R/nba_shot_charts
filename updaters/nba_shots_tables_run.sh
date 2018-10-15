SHELL=/bin/bash
source "/Users/connordog/.bash_profile"

updateDate=$( date +"%b %d, %Y" )

python ../processing/table_exporter.py

wait

cd ~/Dropbox/Desktop_Files/Work_Things/CodeBase/Python_Scripts/Python_Projects/nba_shot_charts/csvs/leaderboards/

csvtotable Player_Post_Career.csv /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Player_Post_Career.html -c "NBA Leaderboards - Player Postseason by Career (Last Updated $updateDate)" -vs 15 -o
python /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/google_analytics_appender.py --file_path "/Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Player_Post_Career.html"

csvtotable Player_Post.csv /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Player_Post.html -c "NBA Leaderboards - Player Postseason by Season (Last Updated $updateDate)" -vs 15 -o
python /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/google_analytics_appender.py --file_path "/Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Player_Post.html"

csvtotable Player_Pre_Career.csv /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Player_Pre_Career.html -c "NBA Leaderboards - Player Preseason by Career (Last Updated $updateDate)" -vs 15 -o
python /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/google_analytics_appender.py --file_path "/Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Player_Pre_Career.html"

csvtotable Player_Pre.csv /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Player_Pre.html -c "NBA Leaderboards - Player Preseason by Season" -vs 15 -o
python /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/google_analytics_appender.py --file_path "/Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Player_Pre.html"

csvtotable Player_Reg_Career.csv /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Player_Reg_Career.html -c "NBA Leaderboards - Player Regular Season by Career (Last Updated $updateDate)" -vs 15 -o
python /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/google_analytics_appender.py --file_path "/Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Player_Reg_Career.html"

csvtotable Player_Reg.csv /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Player_Reg.html -c "NBA Leaderboards - Player Regular Season by Season (Last Updated $updateDate)" -vs 15 -o
python /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/google_analytics_appender.py --file_path "/Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Player_Reg.html"

csvtotable Team_Post.csv /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Team_Post.html -c "NBA Leaderboards - Team Postseason by Season (Last Updated $updateDate)" -vs 15 -o
python /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/google_analytics_appender.py --file_path "/Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Team_Post.html"

csvtotable Team_Pre.csv /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Team_Pre.html -c "NBA Leaderboards - Team Preseason by Season (Last Updated $updateDate)" -vs 15 -o
python /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/google_analytics_appender.py --file_path "/Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Team_Pre.html"

csvtotable Team_Reg.csv /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Team_Reg.html -c "NBA Leaderboards - Team Regular Season by Season (Last Updated $updateDate)" -vs 15 -o
python /Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/google_analytics_appender.py --file_path "/Users/connordog/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/Tables/NBA_leaderboards/Team_Reg.html"



wait

cd ~/Dropbox/Desktop_Files/Work_Things/connor-r.github.io/
git add Tables/NBA_leaderboards/*
git commit -m "NBA leaderboards update"
git push

wait 

cd ~/Dropbox/Desktop_Files/Work_Things/CodeBase/Python_Scripts/Python_Projects/nba_shot_charts/
git add csvs/leaderboards/*
git commit -m "NBA leaderboards update"
git push
