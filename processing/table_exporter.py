import argparse
from time import time
import csv
import os

from py_db import db
db = db("nba_shots")

def initiate():
    start_time = time()

    print "\nexporting to .csv"

    for statType in ('Player', 'Team', 'PlayerCareer'):
        for rangeType in ('Reg', 'Pre', 'Post'):
            print '\t', statType, rangeType
            if statType == 'PlayerCareer':
                isCareer=True
                dataType = 'Player'
            else:
                isCareer=False
                dataType = statType
            export_table(dataType, rangeType, isCareer=isCareer)

    end_time = time()
    elapsed_time = float(end_time - start_time)
    print "\n\nNBA table_exporter.py"
    print "time elapsed (in seconds): " + str(elapsed_time)
    print "time elapsed (in minutes): " + str(elapsed_time/60.0)

def export_table(dataType, rangeType, isCareer):

    if dataType == "Player":
        qry_join = "JOIN players pl USING (player_id) WHERE 1"
        fname = "fname"
        lname = "lname"

    elif dataType == "Team":
        qry_join = "JOIN teams t USING (team_id) WHERE LEFT(season_id,4) > start_year AND LEFT(season_id,4) <= end_year"
        fname = "city"
        lname = "tname"

    if isCareer is False:
        careerText = ""

        qry = """SELECT
        CONCAT(%s, ' ', %s) as 'Name',
        season_type as 'Season Type',
        %s_id as 'NBA ID',
        season_id as 'Year(s)',
        b.games as 'Games', 
        b.makes as 'FG',
        b.attempts as 'FGA',
        b.points as 'Points',
        ROUND(efg*100,1) as 'EFG_Perc',
        ROUND(efg_plus,1) as 'EFG+',
        ROUND(PAA,1) as 'PAA',
        ROUND(PAA_per_game,1) as 'PAA/Game',
        ROUND(PAR,1) as 'PAR',
        ROUND(PAR_per_game,1) as 'PAR/Game',
        ROUND(ShotSkillPlus,1) as 'ShotSkill+',
        AttemptsPerGame_percentile as 'Volume Percentile',
        EFG_percentile as 'EFG Percentile',
        PAAperGame_percentile as 'PAA/Game Percentile',
        PARperGame_percentile as 'PAR/Game Percentile',
        shotSkill_percentile as 'ShotSkill Percentile'
        FROM shots_%s_Relative_Year r
        JOIN shots_%s_Distribution_Year d USING (%s_id, season_id, season_type, shot_zone_basic, shot_zone_area)
        JOIN shots_%s_Breakdown b USING (%s_id, season_id, season_type, shot_zone_basic, shot_zone_area)
        JOIN shot_skill_plus_%s_Year s USING (%s_id, season_id, season_type)
        JOIN percentiles_%s_Year p USING (%s_id, season_id, season_type)
        %s
        AND shot_zone_basic = 'all'
        AND season_type = '%s';"""

        query = qry % (fname, lname, dataType, dataType, dataType, dataType, dataType, dataType, dataType, dataType, dataType, dataType, qry_join, rangeType)

        # raw_input(query)

    elif isCareer is True:
        careerText = "_Career"

        qry = """SELECT
        CONCAT(fname, ' ', lname) as 'Name',
        season_type as 'Season Type',
        player_id as 'NBA ID',
        season_id as 'Year(s)',
        b.games as 'Games', 
        b.makes as 'FG',
        b.attempts as 'FGA',
        b.points as 'Points',
        ROUND(efg*100,1) as 'EFG_Perc',
        ROUND(efg_plus,1) as 'EFG+',
        ROUND(PAA,1) as 'PAA',
        ROUND(PAA_per_game,1) as 'PAA/Game',
        ROUND(PAR,1) as 'PAR',
        ROUND(PAR_per_game,1) as 'PAR/Game',
        ROUND(ShotSkillPlus,1) as 'ShotSkill+',
        AttemptsPerGame_percentile as 'Volume Percentile',
        EFG_percentile as 'EFG Percentile',
        PAAperGame_percentile as 'PAA/Game Percentile',
        PARperGame_percentile as 'PAR/Game Percentile',
        shotSkill_percentile as 'ShotSkill Percentile'
        FROM shots_player_Relative_Career r
        JOIN shots_player_Distribution_Career d USING (player_id, season_id, season_type, shot_zone_basic, shot_zone_area)
        JOIN(
            SELECT 
            player_id, season_type, shot_zone_basic, shot_zone_area,
            SUM(games) AS games,
            SUM(attempts) AS attempts,
            SUM(makes) AS makes,
            SUM(points) AS points
            FROM shots_player_Breakdown
            GROUP BY player_id, season_type, shot_zone_area, shot_zone_basic, season_type
        ) b USING (player_id, season_type, shot_zone_basic, shot_zone_area)
        JOIN shot_skill_plus_player_Career s USING (player_id, season_id, season_type)
        JOIN percentiles_player_Career p USING (player_id, season_id, season_type)
        JOIN players pl USING (player_id)
        WHERE shot_zone_basic = 'all'
        AND season_type = '%s';"""

        query = qry % (rangeType)

    # raw_input(query)
    res = db.query(query)

    file_name = "%s_%s%s" % (dataType, rangeType, careerText)
    csv_title = "/Users/connordog/Dropbox/Desktop_Files/Work_Things/CodeBase/Python_Scripts/Python_Projects/nba_shot_charts/csvs/leaderboards/%s.csv" % (file_name)
    csv_file = open(csv_title, "wb")
    append_csv = csv.writer(csv_file)
    csv_header = ["Name", "Season Type", "NBA ID", "Year(s)", "Games", "FG", "FGA", "FG Points", "EFG%", "EFG+", "PAA", "PAA/Game", "PAR", "PAR/Game", "ShotSkill+", "Volume Percentile", "EFG Percentile", "PAA/Game Percentile", "PAR/Game Percentile", "ShotSkill Percentile"]
    append_csv.writerow(csv_header)

    for row in res:
        row = list(row[0:])
        for i, val in enumerate(row):
            if type(val) in (str,):
                row[i] = "".join([l if ord(l) < 128 else "" for l in val])
        append_csv.writerow(row)


if __name__ == "__main__":     
    parser = argparse.ArgumentParser()

    args = parser.parse_args()
    
    initiate()

