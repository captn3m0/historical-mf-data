#!/bin/bash
set -euo pipefail
# Data is often backfilled, but not very often.
# We default to checking last 90 days
# But on every Sunday, go back a year.
# Returns a 1-7, 1=Mon
if [ "$(date +%u)" -eq 7 ]; then
	d=$(date -I -d '-365 days')
else
	d=$(date -I -d '-90 days')
fi

# On the first of every month, go back to starting of the dataset
if [ "$(date +%d)" -eq 1 ]; then
	d='2005-12-31'
fi
echo "Starting date is $d"

# Loop till we reach tomorrow, so it does run for today
# Every date is refetched, since AMFI backfills old data.
while [ "$d" != "$(date -I -d '+1 day')" ]; do
	echo "Fetching $d"
	df=$(date '+%d-%b-%Y' -d "$d")
	out="data/$(date '+%Y/%m/%d' -d "$d").csv"
	mkdir -p "$(dirname "$out")"
	tmp=$(mktemp)
	wget --output-document="$tmp" --quiet --tries=3 --waitretry=5 \
		"https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?frmdt=$df"
	if head -c 12 "$tmp" | grep -q '^Scheme Code'; then
		mv "$tmp" "$out"
	elif grep -qi '<html' "$tmp" && [ ! -e "$out" ]; then
		# AMFI serves an HTML page for dates it has no data for
		rm "$tmp"
	else
		echo "ERROR: unexpected response for $d ($(wc -c < "$tmp") bytes)" >&2
		exit 1
	fi
	d=$(date -I -d "$d + 1 day")
done
