#!/bin/bash
# Starting date is 7 days ago
# which is reasonable lookup for "how old data can still be getting backfilled"
d=$(date -I -d '-90 days')
# Loop till we reach tomorrow, so it does run for today
while [ "$d" != $(date -I -d '+1 day') ]; do 
	if [ ! -f "data/$d" ]; then
		echo "Fetching $d"
		df=$(date '+%d-%b-%Y' -d "$d")
		year=$(date '+%Y' -d "$d")
		month=$(date '+%m' -d "$d")
		date=$(date '+%d' -d "$d")
		URL="https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?frmdt=$df"
		mkdir -p "data/$year/$month"
		wget --output-document="data/$year/$month/$date.csv" --quiet "$URL"
	fi
	d=$(date -I -d "$d + 1 day")
done
