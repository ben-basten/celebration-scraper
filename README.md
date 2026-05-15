# celebration-scraper

Scrape all upcoming films and showtimes from the celebration cinema movie theater.

URL: https://www.celebrationcinema.com/cinemas/celebration-cinema-crossroads

The site is built in Angular, and all of the movie data is included in a stringified JSON object in the Angular `ng-init` function.

The data size is very large, so here is a truncated example of what the data looks like:

```html
<div class="cinema-movie-detail" ng-controller="MovieController as mvm" ng-cloak ng-init="init({&quot;calendarDates&quot;:&quot;STRINGIFIED_JSON&quot;,&quot;data&quot;:&quot;STRINGIFIED_JSON&quot;,&quot;films&quot;:&quot;STRINGIFIED_JSON&quot;,&quot;cinemas&quot;:&quot;STRINGIFIED_JSON&quot;},[{&quot;ID&quot;:&quot;007-381022&quot;,&quot;TicketsSellingFast&quot;:true,&quot;ShowSoldOut&quot;:false}]);selectedTab=mvm.getTodaysSelectedTab()">
```
