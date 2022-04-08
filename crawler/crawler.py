from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from concurrent import futures

import bs4 as bs
import pandas as pd
import time
import datetime

# This variable defines how many pages from the 'top anime' page will be crawled.
NUM_PAGES = 3
URL = 'https://myanimelist.net/topanime.php'

def get_browser():
    options = Options()
    options.headless = True
    browser = webdriver.Firefox(executable_path=GeckoDriverManager().install())
    print('Succesfully created browser.')
    return browser

def get_links(url):
    anime_links = []
    browser = get_browser()
    browser.get(url)
    results = browser.find_element(By.CLASS_NAME, 'detail')
    animes = results.find_elements(By.XPATH, '//a[contains(@id, "area")]')

    for anime in animes:
        anime_links.append(anime.get_attribute("href"))

    anime_links = list(dict.fromkeys(anime_links))

    ###############
    #### DEBUG ####
    ###############
    print('Got the following links:')
    for link in anime_links:
        print(link)
    return anime_links

def scrape_info(link):

    print('Called scrape_info() with link: ' + link)
    time.sleep(5)
    browser = get_browser()
    browser.get(link)

    # Get the content wrapper in the middle of the screen.
    content_wrapper = browser.find_element(By.XPATH, '//div[contains(@class, "wrapper")]')

    anime_name = content_wrapper.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div[1]/div/div[1]/div/h1/strong').text

    anime_rank = content_wrapper.find_element(By.XPATH, '//span[contains(@class, "numbers-ranked")]').text

    anime_score = float(content_wrapper.find_element(By.XPATH, '//div[contains(@class, "score-label")]').text)

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
    
    for info in anime_info:
        info = str(info.text).split(': ')

        if len(info) > 1:
            info_category = info[0]
            info_content = info[1]

            if info_category == 'Episodes':
                # Some anime have 'Unkown' number of episodes, since they are currently running or haven't been released yet
                # If that's the case, we'll consider the number of episodes as 0.
                if info_content == 'Unknown':
                    num_episodes = 0

                # Else just get the number of episodes normally.
                num_episodes = int(info_content)
            elif info_category == 'Genres':
                for genre in info_content.split(', '):
                    anime_genres.append(genre)
            elif info_category == 'Theme' or info_category == 'Themes':
                for theme in info_content.split(', '):
                    anime_themes.append(theme)
            elif info_category == 'Demographic':
                anime_demographic = info[1]

    # Debug stuff
    print(anime_name, anime_rank, anime_score, anime_pop_rank, studio_name, num_episodes, anime_genres, anime_themes, anime_demographic)
    current_url = browser.current_url
    browser.close()
    print('Closed browser for ' + current_url)
    return anime_name, anime_rank, anime_score, anime_pop_rank, studio_name, num_episodes, anime_genres, anime_themes, anime_demographic

def crawl(NUM_PAGES, url):
    anime_links = []
    anime_name_by_anime = []
    anime_rank_by_anime = []
    anime_score_by_anime = []
    anime_pop_rank_by_anime = []
    studio_by_anime = []
    num_episodes_per_anime = []
    anime_genres_by_anime = []
    anime_themes_by_anime = []
    anime_demographic_by_anime = []

    browser = get_browser()
    browser.get(url)

    try:
        for number_of_animes in range(50, (NUM_PAGES * 50) + 50, 50):

            if len(anime_links) > 0:
                anime_links.clear()

            anime_links = get_links(browser.current_url)

            for url in anime_links:
                print(url)

            with futures.ThreadPoolExecutor() as executor:
                future_results = { 
                    url : executor.submit(scrape_info, url) for url in anime_links 
                }

                for url, future in future_results.items():
                    try:
                        result = future.result()
                        anime_name_by_anime.append(result[0])
                        anime_rank_by_anime.append(result[1])
                        anime_score_by_anime.append(result[2])
                        anime_pop_rank_by_anime.append(result[3])
                        studio_by_anime.append(result[4])
                        num_episodes_per_anime.append(result[5])
                        anime_genres_by_anime.append(result[6])
                        anime_themes_by_anime.append(result[7])
                        anime_demographic_by_anime.append(result[8])

                    except Exception as err:
                        print('url {:0} generated an exception: {:1}'.format(url, err))

            # Wait until the start of the next hour so we don't exhaust our request limit.
            delta = datetime.timedelta(hours=1)
            current_time = datetime.datetime.now()
            next_hour = (current_time + delta).replace(microsecond=0, second=0, minute=2)
            seconds = (next_hour - current_time).seconds
            time.sleep(seconds)

            # Go to page containing the next 50 animes.
            browser.get(url + '?limit=' + str(number_of_animes))

        browser.close()

    except Exception as e:
        # Create a dict with names and scores so we can use it to create a dataframe.
        anime_score_dict = {
        'Name': anime_name_by_anime, 
        'Score' : anime_score_by_anime,
        'Score Rank' : anime_rank_by_anime,
        'Popularity Rank' : anime_pop_rank_by_anime,
        'Studio' : studio_by_anime,
        'Num. of episodes' : num_episodes_per_anime,
        'Genres' : anime_genres_by_anime,
        'Theme(s)' : anime_themes_by_anime,
        'Demographic' : anime_demographic_by_anime
    }

        # Create a df and save it to a .csv file.
        anime_df = pd.DataFrame.from_dict(anime_score_dict)
        anime_df.to_csv(r'../data/animes.csv')
        print(e.with_traceback)

if __name__ == '__main__':
    crawl(NUM_PAGES, URL)