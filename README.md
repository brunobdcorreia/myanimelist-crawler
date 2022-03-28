# MyAnimeList crawler
## A simple crawler using Selenium that scrapes info from the animes in the 'Top Anime' section of the MyAnimeList website.
This utility crawler gets the following information on each anime shown in the 'Top Anime' section on the MAL website:
- Anime name
- Anime score
- Anime popularity rank
- Studio that made the anime
- Number of episodes
- Genres
- Theme(s)
- Demographic

After finishing its crawl, it exports all the info to a dataframe in a .csv file.

This is really barebones at the moment, here's some of the stuff still left to do:
1. Make the Crawler multithreaded: since it currently scrapes one page at a time, it runs __very__ slowly.
2. Refactor the code.
