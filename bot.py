# -*- coding: utf-8 -*-
import redis
import os
import telebot
# import some_api_lib
# import ...

import requests
from bs4 import BeautifulSoup as soup


class ServerResponseError(Exception):
    pass


# Example of your code beginning
#           Config vars
token = os.environ['TELEGRAM_TOKEN']
some_api_token = os.environ['SOME_API_TOKEN']
#             ...

# If you use redis, install this add-on https://elements.heroku.com/addons/heroku-redis
r = redis.from_url(os.environ.get("REDIS_URL"))

#       Your bot code below
# bot = telebot.TeleBot(token)
# some_api = some_api_lib.connect(some_api_token)
#              ...

def reddit_crawler(max_subreddits=5, max_thread_pages=1, starting_url=None):
    '''params
        max_subreddits      Maximum number of subreddits to process. Default: 5.
        starting_url        User custom URL. Make sure it contains "old.reddit.com/r/trendingsubreddits"
                            Default: None
        
        Reddit Crawler script. Search subreddits (limitted to 5, by default) with minimum of 5k upvotes, based on the (latest URL, by default) Trending Subreddits available.
    '''
        
    # Validate user starting_url
    if starting_url:
        pattern = 'old.reddit.com/r/trendingsubreddits'
        
        if pattern not in starting_url:
            raise ServerResponseError("Invalid custom starting URL.")
        
        if not starting_url.startswith('http'):
            starting_url = 'https://' + starting_url
            
    
    # Add real user agent
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0'
    
    # Limit how many pages to process.
    # By default, it's just a portion of the first page (5 // 125 == 0)
    # Max number of subreddits per page is 125
    max_subr_pages = (max_subreddits // 125) + 1

    flag = True
    # Loop based on user input, default: 1
    for page in range(max_subr_pages):
        
        # ===== STARTING TRENDING SUBREDDITS PAGE ========
        
        # Collect all subreddit urls
        if page == 0:
            
            # If user did not input a custom starting_url
            if starting_url == None:
                # First page
                starting_url = 'https://old.reddit.com/r/trendingsubreddits/'
                
            response = requests.get(starting_url, headers = {'User-agent': user_agent})
            
        else:
            # Subsequent pages
            url = trendings_page.find('span', {'class':'next-button'}).a.get('href')
            
            # Halt looping if there are no more next pages
            if not url:
                flag = False
                break
            
            response = requests.get(url, headers = {'User-agent': user_agent})

        if not response.ok:
            raise ServerResponseError('An error has occurred. Response code: ' + response.status_code)
            
        # Parse and store html response
        trendings_page = soup(response.text, 'lxml')
        

        # ============ LIMIT NUMBER OF SUBREDDITS TO SEARCH (default: 5) ============
        
        # If last iteration
        if page == max_subr_pages -1:
            a_tags = trendings_page.find_all('a', {'class': 'bylink'}, limit=max_subreddits)
        
        # Otherwise number of threads is still higher than 125 (the max value per page)
        else:
            a_tags = trendings_page.find_all('a', {'class': 'bylink'})

        # Store only valid urls
        # i.e. 'https://old.reddit.com/r/trendingsubreddits/comments/a13eio/trending_subreddits_for_20181128_rstarwars/'
        valid_subr_urls = []
        for tag in a_tags:
            valid_subr_urls.append(tag.attrs.get('href'))
        
        
        # ======== CHILD PAGE WITH 5 SUBREDDITS LINKS EACH =========
        
        # Collect all the individual thread html pages
        threads_list = []
        for i in range(len(valid_subr_urls)):
            
            thread = valid_subr_urls[i]

            response = requests.get(thread, headers = {'User-agent': user_agent})
            if not response.ok:
                raise ServerResponseError("There was a response error." + response.status_code)
            
            threads_list.append(soup(response.text, 'lxml'))
            
        print('Hold your horses!!\nWorking...\n')

            
        # ========= LIMIT NUMBER OF THREADS TO PROCESS (default: 1 -> Skips loop) ===========
        
        # Extract all <strong> tags from each page, each containing <a> thread url
        strong_tag_list = []
        for i in range(len(threads_list)):
            strong_tag_list.append(threads_list[i].find_all('strong'))
            
                
        # Extract all <a> from each <strong>
        url = 'https://old.reddit.com'
        subreddits = []
        for strong_tag in strong_tag_list:
            
            # strong_tag (list): most of length 6. Max of 11
            for a_tag in strong_tag:
                
                if a_tag.a:
                    
                    # Build full thread url > "https://old.reddit.com" + "/r/nasa"
                    subreddits.append(url + a_tag.a.text)
        
        
        # ======= INDIVIDUAL SUBREDDIT PAGE ==========
        
        # Get upvotes, subreddit, thread title, comments link and thread link
        
        subr_page = []
        for subr in subreddits:

            response = requests.get(subr, headers = {'User-agent': user_agent})
            if not response.ok:
                raise ServerResponseError("There was a response error." + response.status_code)
            
            subr_page.append(soup(response.text, 'lxml'))
            
            # Deal with extra pages
            for page in range(max_thread_pages-1):
                
                next_url = subr_page[-1].find('span', {'class': 'next-button'}).a.get('href')
                
                response = requests.get(next_url, headers = {'User-agent': user_agent})
                if not response.ok:
                    raise ServerResponseError("There was a response error." + response.status_code)
                
                subr_page.append(soup(response.text, 'lxml'))
        
        
        # Filter threads with upvotes higher than 5k
        upvotes = []
        top_matter = []
        for thread in subr_page:
            
            upvotes.append(thread.find_all('div', {'class': 'likes'}))
            top_matter.append(thread.find_all('div', {'class': 'top-matter'}))
            
        stats = {}
        stats['upvotes'] = []
        stats['subreddit'] = []
        stats['title'] = []
        stats['comments_url'] = []
        stats['thread_url'] = []
        for k in range(len(upvotes)):
            for i in range(len(upvotes[k])):
                
                # Filter by upvotes
                curr = upvotes[k][i].attrs.get('title')
                
                # Make sure curr is not None and it's above 5k
                if curr and int(curr) >= 5000: 
                    stats['upvotes'].append(curr)
                    
                    # comments_url = top_matter[k][i].find('li', {'class':'first'}).a.attrs.get('href')
                    # comments_url = top_matter[k][i].find('ul', {'class':'flat-list'}).li.a.get('href')
                    comments_url = top_matter[k][i].find('a', {'class':"bylink comments may-blank"}).attrs.get('href')
                    
                    c = comments_url.find('/comments/')
                    thread_url = comments_url[:c]
                    
                    thread_title = top_matter[k][i].p.text
                    t = thread_title.rfind(' (')
                    
                    subreddit_name = thread_url[25:]
                    
                    # Get all the remaining info
                    stats['subreddit'].append(subreddit_name)
                    stats['title'].append(thread_title[:t])
                    stats['comments_url'].append(comments_url)
                    stats['thread_url'].append(thread_url[:c])

        
        # Output gathered information
        for k in range(len(stats['upvotes'])):
            print('Upvotes: ' + stats['upvotes'][k])
            print('Subreddit: ' + stats['subreddit'][k])
            print('Thread Title: ' + stats['title'][k])
            print('Comments URL: ' + stats['comments_url'][k])
            print('Thread URL: ' + stats['thread_url'][k] + '\n')
        
        return
    

if __name__ == "__main__":
    reddit_crawler()