from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from concurrent import futures
import pandas as pd
import re

# This variable defines how many pages from the 'top anime' page will be crawled.
NUM_PAGES = 3

# Instantiate the browser and open up MAL's top 50 anime.
options = Options()
options.headless = True
browser = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)
url = 'https://myanimelist.net/topanime.php'
browser.get(url)

# Create lists for various info about the anime.
anime_links = []
anime_name_by_anime = []
anime_score_by_anime = []
anime_pop_rank_by_anime = []
studio_by_anime = []
num_episodes_per_anime = []
anime_genres_by_anime = []
anime_themes_by_anime = []
anime_demographic_by_anime = []

try:
    for number_of_animes in range(50, (NUM_PAGES * 50) + 50, 50):
        prev_url = browser.current_url

        # Get scores and links to each anime's individual page.
        results = browser.find_element(By.CLASS_NAME, 'detail')
        animes = results.find_elements(By.XPATH, '//a[contains(@id, "area")]')
        scores = results.find_elements(By.XPATH, '//span[contains(@class, "score-label")]')

        # Store each anime's link and name in their respective lists
        for anime in animes:
            anime_links.append(anime.get_attribute("href"))

        anime_links = list(dict.fromkeys(anime_links))

        for link in anime_links:
            browser.get(link)

            # Get the content wrapper in the middle of the screen.
            content_wrapper = browser.find_element(By.XPATH, '//div[contains(@class, "wrapper")]')

            anime_name = content_wrapper.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div[1]/div/div[1]/div/h1/strong').text

            anime_score = content_wrapper.find_element(By.XPATH, '//div[contains(@class, "score-label")]').text

            anime_pop_rank = content_wrapper.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div[2]/table/tbody/tr/td[2]/div[1]/table/tbody/tr[1]/td/div[1]/div[1]/div[1]/div[1]/div[2]/span[2]/strong').text

            anime_studio = content_wrapper.find_element(By.XPATH, '//span[contains(@class, "information studio author")]')
            studio_name = anime_studio.find_element(By.TAG_NAME, 'a').text

            # Get the WebElement for the Information panel on the left side of the page:
            leftside = browser.find_element(By.XPATH, '//div[contains(@class, "leftside")]')

            anime_info = leftside.find_elements(By.XPATH, '//div[contains(@class, "spaceit_pad")]')

            num_episodes = None
            anime_genres = []
            anime_themes = []
            anime_demographic = 'None'
            
            for index, info in enumerate(anime_info):
                info = str(info.text).split(': ')

                if len(info) > 1:
                    info_category = info[0]
                    info_content = info[1]

                    if info_category == 'Episodes':               
                        num_episodes = int(info_content)
                    elif info_category == 'Genres':
                        for genre in info_content.split(', '):
                            anime_genres.append(genre)
                    elif info_category == 'Theme' or info_category == 'Themes':
                        for theme in info_content.split(', '):
                            anime_themes.append(theme)
                    elif info_category == 'Demographic':
                        anime_demographic = info[1]

            anime_name_by_anime.append(anime_name)
            anime_score_by_anime.append(anime_score)
            anime_pop_rank_by_anime.append(anime_pop_rank)
            studio_by_anime.append(studio_name)
            num_episodes_per_anime.append(num_episodes)
            anime_genres_by_anime.append(anime_genres)
            anime_themes_by_anime.append(anime_themes)
            anime_demographic_by_anime.append(anime_demographic)

            # Debug stuff
            # print(anime_name, anime_score, anime_pop_rank, studio_name, num_episodes, anime_genres, anime_themes, anime_demographic)

            # Go back to the previous url.
            browser.get(prev_url)

        # Go to page containing the next 50 animes.
        browser.get(url + '?limit=' + str(number_of_animes))

except Exception as e:
    print(e)
    
finally:
    # Create a dict with names and scores so we can use it to create a dataframe.
    anime_score_dict = {
        'Name': anime_name_by_anime, 
        'Score' : anime_score_by_anime,
        'Popularity Rank' : anime_pop_rank_by_anime,
        'Studio' : studio_by_anime,
        'Num. of episodes' : num_episodes_per_anime,
        'Genres' : anime_genres_by_anime,
        'Theme(s)' : anime_themes_by_anime,
        'Demographic' : anime_demographic_by_anime
    }

    # Create a df and save it to a .csv file.
    anime_df = pd.DataFrame.from_dict(anime_score_dict)
    anime_df.to_csv('animes.csv')

    browser.close()
