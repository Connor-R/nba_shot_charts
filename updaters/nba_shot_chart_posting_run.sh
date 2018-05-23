SHELL=/bin/bash
source "/Users/connordog/.bash_profile"


DOW=$(date +%u)
HOUR=$(date +"%H")


if [[ "$DOW" == "3" && "$HOUR" == "15" ]]; then

    cd ../charting/ && python chart_bot_team.py

else

    cd ../charting/ && python chart_bot.py

fi