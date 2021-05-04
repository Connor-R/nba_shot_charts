SHELL=/bin/bash
source "/Users/connordog/.bash_profile"


DOW=$(date +%u)
HOUR=$(date +"%H")


if { [ "$DOW" -eq "1" ] || [ "$DOW" -eq "3" ] || [ "$DOW" -eq "5" ]; } && [ "$HOUR" == "15" ]; then

    pkill -f chart_bot_team.py && printf "\n\nkillingbot\n\n"

else

    pkill -f chart_bot.py && printf "\n\nkillingbot\n\n"

fi


wait

printf "\n\nBOT TERMINATED\n\n"
