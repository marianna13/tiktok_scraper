import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import os
import shutil
import time
import random
from multiprocessing.pool import ThreadPool


class TikTokScraper:

    def __init__(
        self,
        num_process: int = 5,
        random_seed: int = 13
    ):
        """
        num_process: number of parallel processes
        random_seed: intilize random generator to randomly choose TikTok tags
        """

        self.num_process = num_process
        random.seed(random_seed)

    def __call__(
        self,
        seed_tags: list = None,
        num_pages_per_url: int = 10,
        data_path: str = 'META.csv'
    ) -> None:
        """
        seed_tags: list of tags to start scraping from (uses tags from for you page if not provided)
        num_pages_per_url: number of iterations per tag (on each iteration extracts new tag from page and crawls data for this tag)
        data_path: path to 
        """

        data_dir = 'TMP'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        if not seed_tags:
            tiktok_foryou = 'https://www.tiktok.com/foryou'
            seed_tags = self._get_data(tiktok_foryou, for_you=True)
        else:
            seed_tags = ['/tag/'+tag for tag in seed_tags]

        URLs = ['https://www.tiktok.com' +
                url for url in seed_tags]

        N = len(URLs)
        print(f'Crawl for {N} tags with {num_pages_per_url} pages per tag...')
        s = time.time()
        with ThreadPool(self.num_process) as p:
            p.starmap(
                self._save_data,
                [(url, i, data_dir, num_pages_per_url) for url, i in zip(URLs, range(len(URLs)))])
        fs = [pd.read_csv(f'{data_dir}/{f}') for f in os.listdir(data_dir)]
        df = pd.concat(fs)
        if data_path.endswith('.csv'):
            df.to_csv(data_path, index=False)
        elif data_path.endswith('.parquet'):
            df.to_parquet(data_path, index=False)
        elif data_path.endswith('.xlsx'):
            df.to_excel(data_path, index=False)
        else:
            df.to_csv(data_path+'.csv', index=False)

        shutil.rmtree(data_dir)
        e = time.time()
        print(f'Done in {round(e-s, 2)} seconds')

    def _get_data(self, URL: str, for_you: bool = False):
        """
        URL: TikTok tag page
        for_you: whether the URL is for you TikTok page
        """
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'referer': 'https://www.google.com/',
            'accept-language': 'en-US,en;q=0.9,',
            'cookie': 'prov=6bb44cc9-dfe4-1b95-a65d-5250b3b4c9fb; _ga=GA1.2.1363624981.1550767314; __qca=P0-1074700243-1550767314392; notice-ctt=4%3B1550784035760; _gid=GA1.2.1415061800.1552935051; acct=t=4CnQ70qSwPMzOe6jigQlAR28TSW%2fMxzx&s=32zlYt1%2b3TBwWVaCHxH%2bl5aDhLjmq4Xr',
        }
        try:
            res = requests.get(URL, headers=headers)
            soup = res.content

            html = BeautifulSoup(soup, 'html.parser')
            topics = list(set([a['href'].split('?')[0] for a in html.find_all(
                'a', {'class': 'tiktok-q3q1i1-StyledCommonLink ejg0rhn4'}) if a['href'].lower() != URL.replace('https://www.tiktok.com', '').lower() and '/tag' in a['href']]))

            if for_you:
                return topics

            divs = html.find_all(
                'div', {'class': 'tiktok-yz6ijl-DivWrapper e1cg0wnj1'})

            urls = [d.find('a')['href'] for d in divs]

            topic = random.choice(topics)
            descriptions = [
                d.find('img')['alt'] for d in divs]
            usernames = [url.replace('https://', '').split('/')[1]
                         for url in urls]
            return usernames, urls, descriptions, topic

        except Exception as err:
            print(f"Couldn't crawl linkd for URL {URL}. error message: {err}")
            return [], [], [], None

    def _save_data(
            self,
            URL: str,
            st: int,
            output_dir: str,
            num_pages_per_url: int
    ):
        """
        URL: TikTok tag page
        st: number of thread
        output_dir: temp dir to save data
        num_pages_per_url: number of iterations per tag (on each iteration extracts new tag from page and crawls data for this tag)
        """
        data = {
            'USERNAME': [],
            'DESCRIPTION': [],
            'VIDEO_URL': [],
            'TOPIC': []
        }
        usernames, urls, descriptions, topic = self._get_data(URL)
        data['DESCRIPTION'].extend(descriptions)
        data['USERNAME'].extend(usernames)
        data['VIDEO_URL'].extend(urls)
        prev_topic = URL.split('/')[-1].replace('?lang=en', '')
        data['TOPIC'].extend([prev_topic]*len(urls))

        for _ in tqdm(range(num_pages_per_url)):
            if topic:
                url = 'https://www.tiktok.com'+topic.replace('?lang=en', '')
                prev_topic = topic
                usernames, urls, descriptions, topic = self._get_data(url)
                data['DESCRIPTION'].extend(descriptions)
                data['USERNAME'].extend(usernames)
                data['VIDEO_URL'].extend(urls)
                prev_topic = url.split('/')[-1].replace('?lang=en', '')
                data['TOPIC'].extend([prev_topic]*len(urls))

        pd.DataFrame(data).drop_duplicates(subset='VIDEO_URL').to_csv(
            f'{output_dir}/tmp_{st}.csv', index=False)
