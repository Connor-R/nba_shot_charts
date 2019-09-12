SHELL=/bin/bash
source "/Users/connordog/.bash_profile"


DOW=$(date +%u)
HOUR=$(date +"%H")


if { [ "$DOW" -eq "1" ] || [ "$DOW" -eq "3" ] || [ "$DOW" -eq "5" ]; } && [ "$HOUR" == "15" ]; then

    cd ../charting/ && python chart_bot_team.py

else

    cd ../charting/ && python chart_bot.py

fi