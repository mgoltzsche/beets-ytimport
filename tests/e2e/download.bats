#!/usr/bin/env bats

YTDIR=/data/ytimport

assertDirExists() {
	if [ ! -d "$1" ]; then
		echo "ERROR: Directory not found: $1" >&2
		DIR="$(dirname "$1")"
		printf "Found files:\n%s" "$(ls -la "$DIR")" >&2
		return 1
	fi
}

# Args: FILE TAG VALUE
assertTag() {
	if [ ! -f "$1" ]; then
		echo "ERROR: File not found: $1" >&2
		DIR="$(dirname "$1")"
		printf "Found files:\n%s" "$(ls -la "$DIR")" >&2
		return 1
	fi
	ffprobe -v quiet -show_format -show_streams -print_format json "$1" | jq -e --arg k "$2" --arg v "$3" --arg f "$1" 'if .format.tags[$k]==$v or .streams[0].tags[$k]==$v then true else error("file "+$f+"\nUnexpected "+$k+" tag value:\n  "+(.format.tags[$k])+"\nexpects:\n  "+$v) end' >/dev/null
}

@test 'download track from youtube' {
	# 'Cabal' from 'Marcus Intalex (Thema)'
	beet ytimport --no-import https://www.youtube.com/watch?v=7VwubS2kBYU
	FILE="$YTDIR/singles/Marcus Intalex - Cabal [7VwubS2kBYU].opus"
	assertTag "$FILE" title 'Cabal'
	assertTag "$FILE" artist 'Marcus Intalex'
	assertTag "$FILE" album 'Cabal'
	assertTag "$FILE" album_artist 'Marcus Intalex'
	assertTag "$FILE" comment 'https://www.youtube.com/watch?v=7VwubS2kBYU Cabal'
	assertTag "$FILE" yt_source 'youtube.com'
}

@test 'import track' {
	# 'Cabal' from 'Marcus Intalex (Thema)'
	beet ytimport -q https://youtu.be/7VwubS2kBYU
	[ "$(beet ls Cabal)" = 'Marcus Intalex - Cabal - Cabal' ]
	[ "$(beet info Cabal -f '$genre | $yt_source')" = 'Drum And Bass | youtube.com' ]
}

@test 'download track and clean artist' {
	# 'Exchange' from 'Colyn - Topic'
	beet ytimport --no-import https://www.youtube.com/watch?v=b7rzFFJ6gso
	FILE="$YTDIR/singles/Colyn - Exchange [b7rzFFJ6gso].opus"
	assertTag "$FILE" title 'Exchange'
	assertTag "$FILE" artist 'Colyn'
	assertTag "$FILE" album 'Resolve'
	assertTag "$FILE" album_artist 'Colyn'
}

@test 'download track and derive artist from title' {
	# '07.  Lemon D - Deep Space'
	beet ytimport --no-import https://www.youtube.com/watch?v=_3pzM2GoSvU
	FILE="$YTDIR/singles/Lemon D - Deep Space [_3pzM2GoSvU].opus"
	assertTag "$FILE" title 'Deep Space'
	assertTag "$FILE" artist 'Lemon D'
	assertTag "$FILE" album_artist 'Lemon D'
}

@test 'download track and use title as is' {
	# 'STEPART & PUPAJIM : "Non Stop" (Playground LP - Stand High Records)' from 'STAND HIGH PATROL'
	beet ytimport --no-import https://www.youtube.com/watch?v=9HtLHY7cREA
	FILE="$YTDIR"'/singles/STAND HIGH PATROL - STEPART & PUPAJIM - _Non Stop_ (Playground LP - Stand High Records) [9HtLHY7cREA].opus'
	assertTag "$FILE" title 'STEPART & PUPAJIM : "Non Stop" (Playground LP - Stand High Records)'
	assertTag "$FILE" artist 'STAND HIGH PATROL'
	assertTag "$FILE" album_artist 'STAND HIGH PATROL'
}

@test 'download and split compilation' {
	# 'Tour De Manège Vol.4 : The Wizards (Full Album)' from 'Tour De Manège'
	beet ytimport --no-import https://www.youtube.com/watch?v=pKgJppNfR1g
	DIR="$YTDIR/albums/Tour De Manege - Tour De Manege Vol 4 - The Wizards (Full Album) [pKgJppNfR1g]"
	assertDirExists "$DIR"
	FILE="$DIR/13 - Dee La Kream - It s Yours.opus"
	assertTag "$FILE" title "It's Yours"
	assertTag "$FILE" artist 'Dee La Kream'
	assertTag "$FILE" album 'Tour De Manège Vol.4 : The Wizards'
	assertTag "$FILE" album_artist 'Tour De Manège'
	assertTag "$FILE" track '13/28'
	FILE="$DIR/19 - Slivanoe - Persistant Dreams.opus"
	assertTag "$FILE" title 'Persistant Dreams'
	assertTag "$FILE" artist 'Slivanoé'
	assertTag "$FILE" album 'Tour De Manège Vol.4 : The Wizards'
	assertTag "$FILE" album_artist 'Tour De Manège'
	assertTag "$FILE" track '19/28'
}

@test 'download and split album with year in title' {
	# 'THE SELECTER - Too Much Pressure [FULL ALBUM] 1980 (LYRICS added in the comment section)'
	beet ytimport --no-import https://www.youtube.com/watch?v=lutwqvQq5t8
	DIR="$YTDIR/albums/THE SELECTER - Too Much Pressure [FULL ALBUM] 1980 (LYRICS added in the comment section) [lutwqvQq5t8]"
	assertDirExists "$DIR"
	FILE="$DIR/09 - Too Much Pressure.opus"
	assertTag "$FILE" title 'Too Much Pressure'
	assertTag "$FILE" artist 'THE SELECTER'
	assertTag "$FILE" album 'Too Much Pressure'
	assertTag "$FILE" album_artist 'THE SELECTER'
	assertTag "$FILE" track '9/14'
	assertTag "$FILE" date 1980
}

@test 'ignore long track without chapters' {
	# 'Panda Dub - Black Bamboo - Full Album'
	beet ytimport --no-import --max-length-nochapter 600 https://www.youtube.com/watch?v=dJCdqz6EuSM
	! ls -laR "$YTDIR" | grep -iq 'Bamboo'
}

@test 'download track from soundcloud' {
	# 'Chris.SU - Mercury [C4C Recordings]'
	beet ytimport --no-import 'https://soundcloud.com/chrissuofficial/mercury?si=84a62ed3a35640a6913edd5ef19cfa9b&utm_source=clipboard&utm_medium=text&utm_campaign=social_sharing'
	FILE="$YTDIR/singles/Chris SU - Mercury [C4C Recordings] [547755837].mp3"
	assertTag "$FILE" title 'Mercury [C4C Recordings]'
	assertTag "$FILE" artist 'Chris.SU'
	assertTag "$FILE" album_artist 'Chris.SU'
	assertTag "$FILE" yt_source 'soundcloud.com'
}

@test 'reimport track' {
	# 'Cabal' from 'Marcus Intalex (Thema)'
	beet modify -y title:Cabal title=Changed
	! beet ls title:Cabal
	beet ytimport --reimport https://www.youtube.com/watch?v=7VwubS2kBYU
	beet ls title:Cabal
}

@test 'truncate long file name' {
	# 'Le Monstre du Lockdown (feat. Vitess, Oden & Fatzo, Jeff The Fool, Marwan Sabb)' by 'Herr Krank, Deborah Aime La Bagarre, Vitess, Oden & Fatzo, Jeff The F...'
	beet ytimport --no-import https://www.youtube.com/watch?v=WxX7Pl2Y988
	FILE="$YTDIR/singles/Herr Krank Deborah Aime La Bagarre Vitess Oden & Fatzo Jeff The F - Le Monstre du Lockdown (feat Vitess Oden & Fatzo Jeff The Fool Marwan Sabb) [WxX7Pl2Y988].opus"
	assertTag "$FILE" title 'Le Monstre du Lockdown (feat. Vitess, Oden & Fatzo, Jeff The Fool, Marwan Sabb)'
	assertTag "$FILE" artist 'Herr Krank, Deborah Aime La Bagarre, Vitess, Oden & Fatzo, Jeff The F...'
}

@test 'strip trailing dot from title' {
	# 'Open Cage.' by 'Daso'
	beet ytimport --no-import https://www.youtube.com/watch?v=3shC0WBqdrU
	FILE="$YTDIR/singles/Daso - Open Cage [3shC0WBqdrU].opus"
	assertTag "$FILE" title 'Open Cage'
	assertTag "$FILE" artist 'Daso'
}
