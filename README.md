# NBA Shot Charts

A python script made to create shot charts for any NBA player season or career (from 1996 to present).

These charts are primarily an extension from the work of [Dan Vatterott](http://www.danvatterott.com/) and [Savvas Tjortjoglou](http://www.savvastjortjoglou.com). I made an attempt to combine my favorite aspects of other shot charts on the internet (primarily from: [Kirk](https://www.instagram.com/kirkgoldsberry/) [Goldsberry](https://fivethirtyeight.com/contributors/kirk-goldsberry/), [Buckets (by Peter Beshai)](http://buckets.peterbeshai.com/app/#/playerView/201935_2015), [BallR (by Todd Schneider)](http://toddwschneider.com/posts/ballr-interactive-nba-shot-charts-with-r-and-shiny/), and [Swish (by Austin Clemens)](http://www.austinclemens.com/shotcharts/)) into one image, while also adding some additional features I thought would be nice in order to better distinguish the strengths and weaknesses of a player.

To run this code, download the script and player_list and put them in a directory and change the directory path in the script to your directory. To call a single player you can run the following command: `python shot_charts.py --player_name 'Zach Randolph' --player_id 2216 --start_year 2001 --end_year 2017`, but the player_id, start_year, and end_year arguments are only necessary if the player isn’t in the player_list already. Otherwise, the script will find the values in the list and run for the player’s whole career. If you wish to run every player in the script, you can just run: `python shot_charts.py` from your directory. 

Two lesser noticed features of these charts are the following:
* Each chart’s name will save under the template `shot_charts_Firstname_Lastname_Season_eFG.png`
* The color of the Player Name and Zone Frequencies key is the corresponding color to their overall eFG% for the season (e.g., if a player’s eFG% for a year was 100%, their name and key would be dark red, while if their eFG% was 0%, then those colors would be light yellow).

If you're interested in seeing more charts, I created a [twitter bot](https://twitter.com/NBAChartBot) that posts a pseudo-random player/season shot chart every hour.

If you would like to report a bug, request a specific player chart, or contact me for any other reason, my contact information is at the bottom of [my personal github.io page](http://connor-r.github.io/).


