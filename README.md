# celebration-scraper

Scrape all upcoming films and showtimes from the celebration cinema movie theater.

URL: https://www.celebrationcinema.com/cinemas/celebration-cinema-crossroads

## Setup

1. `python3 -m venv ./.venv`
2. `source ./.venv/bin/activate`

## Usage

### Mode 1 — what's playing this weekend?

```
python cinema.py --days fri sat sun --no-times
```

```
Friday, May 16
--------------
  Animal Farm  [1h 36m]
  Mortal Kombat II  [1h 56m]
  Project Hail Mary  [2h 36m]
  The Devil Wears Prada 2  [2h 0m]
  ...

Saturday, May 17
----------------
  Animal Farm  [1h 36m]
  Mortal Kombat II  [1h 56m]
  ...
```

### Mode 2 — showtimes for a specific movie

```
python cinema.py --movie "mortal kombat" --days fri sat sun
```

```
Mortal Kombat II  [1h 56m]
  Friday, May 16
    12:05 PM (2D)  1:05 PM (IMAX 2D)  2:50 PM (2D)  5:35 PM (2D)  8:20 PM (2D)  9:50 PM (IMAX 2D)
  Saturday, May 17
    12:05 PM (2D | Open Captioning)  1:15 PM (IMAX 2D)  2:50 PM (2D)  5:35 PM (2D)  8:20 PM (2D)  9:40 PM (IMAX 2D)
  Sunday, May 18
    12:05 PM (2D)  1:05 PM (IMAX 2D)  2:50 PM (2D)  5:35 PM (2D)  8:20 PM (2D)  9:50 PM (IMAX 2D)
```

## Options

| Flag | Description |
|---|---|
| `--days` | `today` `tomorrow` `mon` `tue` `wed` `thu` `fri` `sat` `sun` |
| `--weeks` | How many weeks out to look (default: `1`) |
| `--movie` | Case-insensitive substring match on title |
| `--no-times` | Hide showtimes, show titles only |

## Data source

The site is built in Angular. All movie data is embedded in a stringified JSON object in the `ng-init` attribute of a div:

```html
<div class="cinema-movie-detail" ng-controller="MovieController as mvm" ng-cloak ng-init="init({&quot;calendarDates&quot;:&quot;STRINGIFIED_JSON&quot;,&quot;data&quot;:&quot;STRINGIFIED_JSON&quot;,&quot;films&quot;:&quot;STRINGIFIED_JSON&quot;,&quot;cinemas&quot;:&quot;STRINGIFIED_JSON&quot;},[{&quot;ID&quot;:&quot;007-381022&quot;,&quot;TicketsSellingFast&quot;:true,&quot;ShowSoldOut&quot;:false}]);selectedTab=mvm.getTodaysSelectedTab()">
```

Once it's parsed, the data model looks like this. Abbreviated each field down to a couple of elements for brevity. Dates include at least the next 2 weeks of showtimes.

```json
{
  "calendarDates": [
    {
      "Text": "Today",
      "Moment": "2026-05-14T00:00:00",
      "ID": 0
    },
    {
      "Text": "Tomorrow",
      "Moment": "2026-05-15T00:00:00",
      "ID": 1
    },
    {
      "Text": "Sat 5/16",
      "Moment": "2026-05-16T00:00:00",
      "ID": 2
    }
  ],
  "data": [
    {
      "TicketsOnSale": "0001-01-01T00:00:00",
      "currentShowtimes": [
        {
          "TicketsOnSale": "0001-01-01T00:00:00",
          "ReleaseDate": "Released: May 7th",
          "RunTime": "1h 56m",
          "StartTime": "2026-05-14T17:35:00-04:00",
          "Date": "2026-05-14",
          "Title": "003-400834",
          "PriceGroupCode": null,
          "SalesChannels": null,
          "SessionAttributesNames": "AD,CC",
          "ConceptAttributesNames": "",
          "VistaID": "003-400834",
          "SessionID": "400834",
          "ScreenName": null,
          "ScreenNumber": null,
          "CinemaOperatorCode": null,
          "FormatCode": "2D",
          "FormatHOPK": "",
          "SoldoutStatus": "",
          "TypeCode": "",
          "ScheduledFilmId": "HO00010293",
          "EventId": "",
          "hasDeal": false,
          "hasEvent": false,
          "EventName": "",
          "AllowChildAdmits": false,
          "AllowComplimentaryTickets": false,
          "AllowTicketSales": false,
          "HasDynamicallyPricedTicketsAvailable": false,
          "Showtime": "2026-05-14T17:35:00-04:00",
          "DateTime": "2026-05-14T17:35:00-04:00",
          "SeatsAvailable": 73.0,
          "FilmID": "HO00010293",
          "CinemaID": "003",
          "__DetailUrl": null,
          "TicketsSellingFast": false,
          "ShowSoldOut": false,
          "DetailUrl": "/Booking/003-400834",
          "OverrideShowtimeIcon": null,
          "OverrideShowtimeIconDescription": null,
          "OverrideShowtimeIconKey": null,
          "OverrideShowtimeIconDescriptionKey": null,
          "OverrideShowtimeIconKeyOrder": 0
        },
      ],
      "Title": "Mortal Kombat II",
      "Showtime": [
        {
          "Date": "2026-05-14",
          "Showtime": "2026-05-14T17:35:00-04:00",
          "RunTime": "1h 56m",
          "FormatCode": "2D",
          "SessionID": "400834",
          "DetailUrl": "/Booking/003-400834",
          "SeatsAvailable": 73.0,
          "TicketsSellingFast": false,
          "ShowSoldOut": false
        }
      ],
      "RunTime": "1h 56m",
      "ReleaseDate": "Released: May 7th",
      "Img": "",
      "Genres": "Action, Adventure, Fantasy",
      "Rating": "R",
      "Summary": "From New Line Cinema comes the latest high-stakes installment in the blockbuster video game franchise in all its brutal glory, Mortal Kombat II. This time, the fan favorite champions—now joined by Johnny Cage himself—are pitted against one another in the ultimate, no-holds barred, gory battle to defeat the dark rule of Shao Kahn that threatens the very existence of the Earthrealm and its defenders.\n\nKarl Urban stars as Johnny Cage, alongside Adeline Rudolph, Jessica McNamee, Josh Lawson, Ludi Lin, Mehcad Brooks, Tati Gabrielle, Lewis Tan, Damon Herriman, with Chin Han, Tadanobu Asano as Lord Raiden, Joe Taslim as Bi-Han, and Hiroyuki Sanada as Hanzo Hasashi and Scorpion.\n\nDirector Simon McQuoid returns to helm the follow up to his explosive 2021cinematic adventure, from a screenplay by Jeremy Slater, based on the videogame created by Ed Boon and John Tobias. The film is produced by Todd Garner, E. Bennett Walsh, James Wan, Toby Emmerich and Simon McQuoid, and executive produced by Michael Clear, Judson Scott, Jeremy Slater, Ed Boon and Lawrence Kasanoff.\n\nJoining McQuoid behind the camera are director of photography Stephen F. Windon, production designer Yohei Taneda, editor Stuart Levy and costume designer Cappi Ireland, with casting by Rich Delia and music by Benjamin Wallfisch. New Line Cinema Presents an Atomic Monster/Broken Road Production, a Fireside Films Production, Mortal Kombat II. ",
      "Director": "Simon McQuoid",
      "Cast": "Karl Urban, Mehcad Brooks, Hiroyuki Sanada, Josh Lawson, Jessica  McNamee, Joe Taslim, Ludi Lin, Tati Gabrielle, Martyn Ford, Adeline Rudolph, CJ Bloomfield, Tadanobu  Asano",
      "FilmDetailUrl": "/Films/detail/Mortal-Kombat-II",
      "ShowtimeDetailUrl": "/Booking/003-400834",
      "TrailerUrl": "https://www.youtube.com/watch?v=b24oG7qCwp4",
      "FilmId": "HO00010293",
      "Sessions": {
        "2026-05-14": [
          {
            "TicketsOnSale": "0001-01-01T00:00:00",
            "ReleaseDate": "Released: May 7th",
            "RunTime": "1h 56m",
            "StartTime": "2026-05-14T17:35:00-04:00",
            "Date": "2026-05-14",
            "Title": "003-400834",
            "PriceGroupCode": null,
            "SalesChannels": null,
            "SessionAttributesNames": "AD,CC",
            "ConceptAttributesNames": "",
            "VistaID": "003-400834",
            "SessionID": "400834",
            "ScreenName": null,
            "ScreenNumber": null,
            "CinemaOperatorCode": null,
            "FormatCode": "2D",
            "FormatHOPK": "",
            "SoldoutStatus": "",
            "TypeCode": "",
            "ScheduledFilmId": "HO00010293",
            "EventId": "",
            "hasDeal": false,
            "hasEvent": false,
            "EventName": "",
            "AllowChildAdmits": false,
            "AllowComplimentaryTickets": false,
            "AllowTicketSales": false,
            "HasDynamicallyPricedTicketsAvailable": false,
            "Showtime": "2026-05-14T17:35:00-04:00",
            "DateTime": "2026-05-14T17:35:00-04:00",
            "SeatsAvailable": 73.0,
            "FilmID": "HO00010293",
            "CinemaID": "003",
            "__DetailUrl": null,
            "TicketsSellingFast": false,
            "ShowSoldOut": false,
            "DetailUrl": "/Booking/003-400834",
            "OverrideShowtimeIcon": null,
            "OverrideShowtimeIconDescription": null,
            "OverrideShowtimeIconKey": null,
            "OverrideShowtimeIconDescriptionKey": null,
            "OverrideShowtimeIconKeyOrder": 0
          },
          {
            "TicketsOnSale": "0001-01-01T00:00:00",
            "ReleaseDate": "Released: May 7th",
            "RunTime": "1h 56m",
            "StartTime": "2026-05-14T20:20:00-04:00",
            "Date": "2026-05-14",
            "Title": "003-400835",
            "PriceGroupCode": null,
            "SalesChannels": null,
            "SessionAttributesNames": "AD,CC",
            "ConceptAttributesNames": "",
            "VistaID": "003-400835",
            "SessionID": "400835",
            "ScreenName": null,
            "ScreenNumber": null,
            "CinemaOperatorCode": null,
            "FormatCode": "2D",
            "FormatHOPK": "",
            "SoldoutStatus": "",
            "TypeCode": "",
            "ScheduledFilmId": "HO00010293",
            "EventId": "",
            "hasDeal": false,
            "hasEvent": false,
            "EventName": "",
            "AllowChildAdmits": false,
            "AllowComplimentaryTickets": false,
            "AllowTicketSales": false,
            "HasDynamicallyPricedTicketsAvailable": false,
            "Showtime": "2026-05-14T20:20:00-04:00",
            "DateTime": "2026-05-14T20:20:00-04:00",
            "SeatsAvailable": 71.0,
            "FilmID": "HO00010293",
            "CinemaID": "003",
            "__DetailUrl": null,
            "TicketsSellingFast": false,
            "ShowSoldOut": false,
            "DetailUrl": "/Booking/003-400835",
            "OverrideShowtimeIcon": null,
            "OverrideShowtimeIconDescription": null,
            "OverrideShowtimeIconKey": null,
            "OverrideShowtimeIconDescriptionKey": null,
            "OverrideShowtimeIconKeyOrder": 0
          },
          {
            "TicketsOnSale": "0001-01-01T00:00:00",
            "ReleaseDate": "Released: May 7th",
            "RunTime": "1h 56m",
            "StartTime": "2026-05-14T21:00:00-04:00",
            "Date": "2026-05-14",
            "Title": "003-402783",
            "PriceGroupCode": null,
            "SalesChannels": null,
            "SessionAttributesNames": "2nd,AD,CC",
            "ConceptAttributesNames": "",
            "VistaID": "003-402783",
            "SessionID": "402783",
            "ScreenName": null,
            "ScreenNumber": null,
            "CinemaOperatorCode": null,
            "FormatCode": "2D",
            "FormatHOPK": "",
            "SoldoutStatus": "",
            "TypeCode": "",
            "ScheduledFilmId": "HO00010293",
            "EventId": "",
            "hasDeal": false,
            "hasEvent": false,
            "EventName": "",
            "AllowChildAdmits": false,
            "AllowComplimentaryTickets": false,
            "AllowTicketSales": false,
            "HasDynamicallyPricedTicketsAvailable": false,
            "Showtime": "2026-05-14T21:00:00-04:00",
            "DateTime": "2026-05-14T21:00:00-04:00",
            "SeatsAvailable": 34.0,
            "FilmID": "HO00010293",
            "CinemaID": "003",
            "__DetailUrl": null,
            "TicketsSellingFast": false,
            "ShowSoldOut": false,
            "DetailUrl": "/Booking/003-402783",
            "OverrideShowtimeIcon": null,
            "OverrideShowtimeIconDescription": null,
            "OverrideShowtimeIconKey": null,
            "OverrideShowtimeIconDescriptionKey": null,
            "OverrideShowtimeIconKeyOrder": 0
          },
          {
            "TicketsOnSale": "0001-01-01T00:00:00",
            "ReleaseDate": "Released: May 7th",
            "RunTime": "1h 56m",
            "StartTime": "2026-05-14T21:45:00-04:00",
            "Date": "2026-05-14",
            "Title": "003-400804",
            "PriceGroupCode": null,
            "SalesChannels": null,
            "SessionAttributesNames": "AD,CC,IMAX",
            "ConceptAttributesNames": "",
            "VistaID": "003-400804",
            "SessionID": "400804",
            "ScreenName": null,
            "ScreenNumber": null,
            "CinemaOperatorCode": null,
            "FormatCode": "IMAX 2D",
            "FormatHOPK": "",
            "SoldoutStatus": "",
            "TypeCode": "",
            "ScheduledFilmId": "HO00010293",
            "EventId": "",
            "hasDeal": false,
            "hasEvent": true,
            "EventName": "IMAX",
            "AllowChildAdmits": false,
            "AllowComplimentaryTickets": false,
            "AllowTicketSales": false,
            "HasDynamicallyPricedTicketsAvailable": false,
            "Showtime": "2026-05-14T21:45:00-04:00",
            "DateTime": "2026-05-14T21:45:00-04:00",
            "SeatsAvailable": 274.0,
            "FilmID": "HO00010293",
            "CinemaID": "003",
            "__DetailUrl": null,
            "TicketsSellingFast": false,
            "ShowSoldOut": false,
            "DetailUrl": "/Booking/003-400804",
            "OverrideShowtimeIcon": null,
            "OverrideShowtimeIconDescription": null,
            "OverrideShowtimeIconKey": null,
            "OverrideShowtimeIconDescriptionKey": null,
            "OverrideShowtimeIconKeyOrder": 0
          }
        ]
      },
      "Cinemas": null,
      "Dates": null,
      "Formats": null
    }
  ],
  "dates": [
    "2026-05-14",
    "2026-05-15",
    "2026-05-16"
  ],
  "films": {
    "HO00010340": {
      "Title": "Karuppu",
      "Director": "RJ Balaji",
      "Cast": "Prakash Raj, Yogi Babu, TRISHA  KRISHNAN, Swasika Vijay, Indrans , Kaali Venkat, Mansoor Ali Khan, RJ Balaji, Suriya ",
      "Summary": "A lawyer becomes possessed by a deity and battles injustice affecting marginalized communities.",
      "HOFilmCode": "HO00010340",
      "Rating": "NR",
      "TrailerUrl": "https://www.youtube.com/watch?v=Llss1aRo8tw",
      "ReleaseDate": "Released: May 13th",
      "Duration": "2h 36m",
      "CoverPhoto": "http://www.celebrationcinema.com/images/default-source/movie-posters/ho00010340.jpg?Status=Master&sfvrsn=9533f063_0",
      "BackgroundPhoto": "http://www.celebrationcinema.com/images/default-source/movie-backgrounds/ho00010340.jpg?Status=Master&sfvrsn=cc2cd531_0",
      "Genres": "Action, Thriller",
      "DetailUrl": "/Films/detail/Karuppu",
      "ReleaseDateDT": "2026-05-13T20:00:00-04:00",
      "TicketsOnSale": "0001-01-01T00:00:00"
    }
  },
  "cinemas": {
    "011": {
      "Title": "Getty Drive-In",
      "LocationName": "Getty Drive-In",
      "Address": "920 E Summit Ave",
      "Address2": "Muskegon, MI 49444",
      "GoogleMapUrl": "43.1967,-86.2227",
      "VistaID": "011",
      "PhoneNumber": null,
      "LocationPhoto": null,
      "DetailUrl": "/cinemas/Getty-Drive-In"
    }
  }
}
```
