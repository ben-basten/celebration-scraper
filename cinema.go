package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
	"sort"
	"strings"
	"time"

	htmlparse "golang.org/x/net/html"
)

const siteURL = "https://www.celebrationcinema.com/cinemas/celebration-cinema-crossroads"

var userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

var dayNameToWeekday = map[string]time.Weekday{
	"sun": time.Sunday,
	"mon": time.Monday,
	"tue": time.Tuesday,
	"wed": time.Wednesday,
	"thu": time.Thursday,
	"fri": time.Friday,
	"sat": time.Saturday,
}

// ---------------------------------------------------------------------------
// Data types
// ---------------------------------------------------------------------------

type CalendarDate struct {
	Text   string `json:"Text"`
	Moment string `json:"Moment"`
	ID     int    `json:"ID"`
}

type Showtime struct {
	Date       string `json:"Date"`
	Showtime   string `json:"Showtime"`
	RunTime    string `json:"RunTime"`
	FormatCode string `json:"FormatCode"`
}

type Movie struct {
	Title    string     `json:"Title"`
	Showtime []Showtime `json:"Showtime"`
}

type InitData struct {
	CalendarDates []CalendarDate
	Movies        []Movie
}

// ---------------------------------------------------------------------------
// Fetching & parsing
// ---------------------------------------------------------------------------

func fetchHTML(url string) (string, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("User-Agent", userAgent)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return string(body), nil
}

var ngInitRe = regexp.MustCompile(`(?i)init\s*\(`)

func extractNgInit(pageHTML string) (string, error) {
	doc, err := htmlparse.Parse(strings.NewReader(pageHTML))
	if err != nil {
		return "", err
	}

	var found string
	var walk func(*htmlparse.Node)
	walk = func(n *htmlparse.Node) {
		if found != "" {
			return
		}
		if n.Type == htmlparse.ElementNode {
			for _, attr := range n.Attr {
				if attr.Key == "ng-init" && ngInitRe.MatchString(attr.Val) {
					found = attr.Val
					return
				}
			}
		}
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			walk(c)
		}
	}
	walk(doc)

	if found == "" {
		return "", fmt.Errorf("could not find ng-init attribute with init() call")
	}
	return found, nil
}

// extractBracketObject extracts the first top-level {...} from s starting at
// the first '{', respecting nested braces and JSON strings.
func extractBracketObject(s string) (string, error) {
	start := strings.Index(s, "{")
	if start < 0 {
		return "", fmt.Errorf("no '{' found")
	}

	depth := 0
	inString := false
	escape := false

	for i := start; i < len(s); i++ {
		ch := s[i]
		if escape {
			escape = false
			continue
		}
		if ch == '\\' && inString {
			escape = true
			continue
		}
		if ch == '"' {
			inString = !inString
			continue
		}
		if inString {
			continue
		}
		if ch == '{' {
			depth++
		} else if ch == '}' {
			depth--
			if depth == 0 {
				return s[start : i+1], nil
			}
		}
	}
	return "", fmt.Errorf("unmatched '{' in string")
}

func parseInitData(ngInit string) (*InitData, error) {
	objStr, err := extractBracketObject(ngInit)
	if err != nil {
		return nil, fmt.Errorf("extracting init object: %w", err)
	}

	// The outer object has string values that are themselves JSON-encoded.
	var raw map[string]string
	if err := json.Unmarshal([]byte(objStr), &raw); err != nil {
		return nil, fmt.Errorf("unmarshaling init object: %w", err)
	}

	calJSON, ok := raw["calendarDates"]
	if !ok {
		return nil, fmt.Errorf("no calendarDates field")
	}
	dataJSON, ok := raw["data"]
	if !ok {
		return nil, fmt.Errorf("no data field")
	}

	var calDates []CalendarDate
	if err := json.Unmarshal([]byte(calJSON), &calDates); err != nil {
		return nil, fmt.Errorf("parsing calendarDates: %w", err)
	}

	var movies []Movie
	if err := json.Unmarshal([]byte(dataJSON), &movies); err != nil {
		return nil, fmt.Errorf("parsing data: %w", err)
	}

	return &InitData{CalendarDates: calDates, Movies: movies}, nil
}

func fetchData() (*InitData, error) {
	fmt.Fprintln(os.Stderr, "Fetching", siteURL, "...")
	pageHTML, err := fetchHTML(siteURL)
	if err != nil {
		return nil, err
	}
	ngInit, err := extractNgInit(pageHTML)
	if err != nil {
		return nil, err
	}
	return parseInitData(ngInit)
}

// ---------------------------------------------------------------------------
// Day resolution
// ---------------------------------------------------------------------------

type DayPair struct {
	ISO      string // "2026-05-16"
	CalLabel string // "Today", "Tomorrow", "Sat 5/16", etc.
}

func resolveDays(requested []string, calDates []CalendarDate, weeks int) ([]DayPair, error) {
	today := time.Now().Format("2006-01-02")
	cutoff := time.Now().AddDate(0, 0, weeks*7).Format("2006-01-02")

	calByDate := map[string]string{}
	var available []string
	for _, cd := range calDates {
		iso := cd.Moment[:10]
		calByDate[iso] = cd.Text
	}
	for iso := range calByDate {
		if iso >= today && iso <= cutoff {
			available = append(available, iso)
		}
	}
	sort.Strings(available)

	todayISO := ""
	if len(available) > 0 {
		todayISO = available[0]
	}

	matched := map[string]string{}
	for _, token := range requested {
		t := strings.ToLower(token)
		switch t {
		case "today":
			if todayISO != "" {
				matched[todayISO] = calByDate[todayISO]
			}
		case "tomorrow":
			if len(available) > 1 {
				matched[available[1]] = calByDate[available[1]]
			}
		default:
			wd, ok := dayNameToWeekday[t]
			if !ok {
				fmt.Fprintf(os.Stderr, "Warning: unknown day %q (use today/tomorrow/mon/tue/wed/thu/fri/sat/sun)\n", token)
				continue
			}
			for _, iso := range available {
				dt, _ := time.Parse("2006-01-02", iso)
				if dt.Weekday() == wd {
					matched[iso] = calByDate[iso]
					break
				}
			}
		}
	}

	var pairs []DayPair
	for _, iso := range available {
		if label, ok := matched[iso]; ok {
			pairs = append(pairs, DayPair{ISO: iso, CalLabel: label})
		}
	}
	return pairs, nil
}

func allDays(calDates []CalendarDate, weeks int) []DayPair {
	today := time.Now().Format("2006-01-02")
	cutoff := time.Now().AddDate(0, 0, weeks*7).Format("2006-01-02")

	var pairs []DayPair
	for _, cd := range calDates {
		iso := cd.Moment[:10]
		if iso >= today && iso <= cutoff {
			pairs = append(pairs, DayPair{ISO: iso, CalLabel: cd.Text})
		}
	}
	sort.Slice(pairs, func(i, j int) bool { return pairs[i].ISO < pairs[j].ISO })
	return pairs
}

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

func fmtTime(iso string) string {
	// Showtimes are timezone-aware: "2026-05-16T17:35:00-04:00"
	t, err := time.Parse(time.RFC3339, iso)
	if err != nil {
		// fallback: strip offset and parse as local
		if len(iso) >= 19 {
			t, _ = time.ParseInLocation("2006-01-02T15:04:05", iso[:19], time.Local)
		}
	}
	return t.Format("3:04 PM")
}

func fmtDayLabel(iso, calLabel string) string {
	t, _ := time.Parse("2006-01-02", iso)
	base := t.Format("Monday, January 2")
	if calLabel == "Today" || calLabel == "Tomorrow" {
		return fmt.Sprintf("%s  (%s)", base, calLabel)
	}
	return base
}

func isFuture(iso string) bool {
	t, err := time.Parse(time.RFC3339, iso)
	if err != nil {
		return true // don't filter if we can't parse
	}
	return t.After(time.Now())
}

func shortLabel(iso, calLabel string) string {
	if calLabel == "Today" {
		return "today"
	}
	if calLabel == "Tomorrow" {
		return "tmrw"
	}
	t, _ := time.Parse("2006-01-02", iso)
	return strings.ToLower(t.Format("Mon"))
}

// ---------------------------------------------------------------------------
// Mode 1: movies by day
// ---------------------------------------------------------------------------

func modeDays(movies []Movie, pairs []DayPair, hideTimes bool) {
	for _, dp := range pairs {
		type entry struct {
			title     string
			runtime   string
			showtimes []Showtime
		}
		var dayMovies []entry

		for _, m := range movies {
			var sts []Showtime
			for _, s := range m.Showtime {
				if len(s.Date) >= 10 && s.Date[:10] == dp.ISO && isFuture(s.Showtime) {
					sts = append(sts, s)
				}
			}
			if len(sts) == 0 {
				continue
			}
			sort.Slice(sts, func(i, j int) bool { return sts[i].Showtime < sts[j].Showtime })
			runtime := ""
			if len(sts) > 0 {
				runtime = sts[0].RunTime
			}
			dayMovies = append(dayMovies, entry{m.Title, runtime, sts})
		}

		if len(dayMovies) == 0 {
			continue
		}
		sort.Slice(dayMovies, func(i, j int) bool { return dayMovies[i].title < dayMovies[j].title })

		heading := fmtDayLabel(dp.ISO, dp.CalLabel)
		fmt.Println(heading)
		fmt.Println(strings.Repeat("-", len(heading)))
		for _, e := range dayMovies {
			line := "  " + e.title
			if e.runtime != "" {
				line += "  [" + e.runtime + "]"
			}
			fmt.Println(line)
			if !hideTimes {
				var parts []string
				for _, s := range e.showtimes {
					parts = append(parts, fmt.Sprintf("%s (%s)", fmtTime(s.Showtime), s.FormatCode))
				}
				fmt.Println("    " + strings.Join(parts, "  "))
			}
		}
		fmt.Println()
	}
}

// ---------------------------------------------------------------------------
// Mode 2: showtimes by movie
// ---------------------------------------------------------------------------

func modeMovie(movies []Movie, query string, pairs []DayPair, hideTimes bool) {
	q := strings.ToLower(query)
	daySet := map[string]string{}
	for _, dp := range pairs {
		daySet[dp.ISO] = dp.CalLabel
	}

	var orderISO []string
	for _, dp := range pairs {
		orderISO = append(orderISO, dp.ISO)
	}

	found := false
	for _, m := range movies {
		if !strings.Contains(strings.ToLower(m.Title), q) {
			continue
		}

		byDate := map[string][]Showtime{}
		for _, s := range m.Showtime {
			d := ""
			if len(s.Date) >= 10 {
				d = s.Date[:10]
			}
			if _, ok := daySet[d]; ok && isFuture(s.Showtime) {
				byDate[d] = append(byDate[d], s)
			}
		}
		if len(byDate) == 0 {
			continue
		}
		found = true

		runtime := ""
		for _, s := range m.Showtime {
			if s.RunTime != "" {
				runtime = s.RunTime
				break
			}
		}

		title := m.Title
		if runtime != "" {
			title += "  [" + runtime + "]"
		}
		fmt.Println(title)

		for _, iso := range orderISO {
			sts, ok := byDate[iso]
			if !ok {
				continue
			}
			sort.Slice(sts, func(i, j int) bool { return sts[i].Showtime < sts[j].Showtime })
			fmt.Println("  " + fmtDayLabel(iso, daySet[iso]))
			if !hideTimes {
				var parts []string
				for _, s := range sts {
					parts = append(parts, fmt.Sprintf("%s (%s)", fmtTime(s.Showtime), s.FormatCode))
				}
				fmt.Println("    " + strings.Join(parts, "  "))
			}
		}
		fmt.Println()
	}

	if !found {
		fmt.Printf("No movies found matching %q.\n", query)
	}
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

var (
	daysFlag    string
	weeksFlag   int
	movieFlag   string
	noTimes     bool
	versionFlag bool
)

var Version = "dev"

func main() {
	flag.StringVar(&daysFlag, "days", "", "Comma separated days: today tomorrow mon tue wed thu fri sat sun")
	flag.IntVar(&weeksFlag, "weeks", 1, "How many weeks out to look (default: 1)")
	flag.StringVar(&movieFlag, "movie", "", "Movie title search (case-insensitive substring match)")
	flag.BoolVar(&noTimes, "no-times", false, "Hide showtimes, show titles only")
	flag.BoolVar(&versionFlag, "v", false, "Show version")
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, `Usage: cinema [options]

Examples:
  cinema --days "fri sat sun" --no-times
  cinema --days "fri sat sun"
  cinema --movie "mortal kombat" --days "fri sat sun"
  cinema --weeks 2

Options:
`)
		flag.PrintDefaults()
	}
	flag.Parse()

	if versionFlag {
		fmt.Println(Version)
		return
	}

	data, err := fetchData()
	if err != nil {
		fmt.Fprintln(os.Stderr, "Error:", err)
		os.Exit(1)
	}

	var pairs []DayPair
	if daysFlag != "" {
		// Accept both space and comma separated
		tokens := strings.FieldsFunc(daysFlag, func(r rune) bool { return r == ',' || r == ' ' })
		pairs, err = resolveDays(tokens, data.CalendarDates, weeksFlag)
		if err != nil || len(pairs) == 0 {
			fmt.Fprintln(os.Stderr, "None of the requested days are available in the schedule.")
			os.Exit(1)
		}
	} else {
		pairs = allDays(data.CalendarDates, weeksFlag)
	}

	fmt.Println()

	switch {
	case movieFlag != "":
		modeMovie(data.Movies, movieFlag, pairs, noTimes)
	default:
		modeDays(data.Movies, pairs, noTimes)
	}
}
