# NBA Shot Charts

## General Details
This project is licensed under the terms of the MIT license.

A python script made to create shot charts for any NBA player season or career (from 1996 to present).

These charts are primarily an extension from the work of [Dan Vatterott](http://www.danvatterott.com/) and [Savvas Tjortjoglou](http://www.savvastjortjoglou.com). I made an attempt to combine my favorite aspects of other shot charts on the internet (primarily from: [Kirk](https://www.instagram.com/kirkgoldsberry/) [Goldsberry](https://fivethirtyeight.com/contributors/kirk-goldsberry/), [Buckets (by Peter Beshai)](http://buckets.peterbeshai.com/app/#/playerView/201935_2015), [BallR (by Todd Schneider)](http://toddwschneider.com/posts/ballr-interactive-nba-shot-charts-with-r-and-shiny/), and [Swish (by Austin Clemens)](http://www.austinclemens.com/shotcharts/)) into one image, while also adding some additional features I thought would be nice in order to better distinguish the strengths and weaknesses of a player.

To run this code, download the script and player_list and put them in a directory and change the directory path in the script to your directory. To call a single player you can run the following command: `python nba_shot_charts_v1.py --player_name "Zach Randolph"`. If you wish to run every player in the script, you can just run: `python shot_charts_v1.py` from your directory (this will take multiple days to complete). 

Two lesser noticed features of these charts are the following:
* Each chart’s name will save under the template `shot_charts_Firstname_Lastname_Season_eFG.png`
* The color of the Player Name and Zone Frequencies key is the corresponding color to their overall eFG% for the season (e.g., if a player’s eFG% for a year was 100%, their name and key would be dark red, while if their eFG% was 0%, then those colors would be light yellow).

If you're interested in seeing more charts, I created a twitter bot ([@NBAChartBot](https://twitter.com/NBAChartBot)) that posts a pseudo-random player/season shot chart every 3 hours.

If you would like to report a bug, request a copy of the data, or contact me for any other reason, my contact information is at the bottom of [my personal github.io page](http://connor-r.github.io/).


### March 4, 2017 Update
I'm changing the code structure a bit. I've added scrapers and some post-processing scripts so I can store/manipulate the shot data a little bit easier in a MySQL database. I'm leaving the original chart generator (`nba_shot_charts_v1.py`) and chart bot script (`chart_bot_v1.py`), but will eventually add a v2 of both of this scripts, using the MySQL db instead of re-scraping nba.com each time. Part of the reason I'm changing the structure is to help facilitate a few longer term goals of these charts:
- [ ] Speeding up the process of generating a chart (querying the database is faster than scraping the web)
- [ ] Generating team shot charts similar to how we current generate player charts.
- [ ] Calculating some form of a similarity score, to see which players/teams have the most similar distribution and shot making ability from some pre-defined zones
- [x] Creating some form of an era-adjustment, to be able to more accurately compare charts from players from different seasons (think of how a player like Ray Allen's shot chart may differ if his career started in 2015, or how a player like Patrick Beverley's may have differed if his career started in 1990).