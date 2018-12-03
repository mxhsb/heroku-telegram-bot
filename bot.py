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
# r = redis.from_url(os.environ.get("REDIS_URL"))

#       Your bot code below
bot = telebot.TeleBot(token)
# some_api = some_api_lib.connect(some_api_token)
#              ...

import requests
from bs4 import BeautifulSoup as soup


def crawler(subr_input, max_thread_pages=2):
    '''params
        subreddits          Subreddits string separated by ';'
        max_thread_pages    Number of thread pages to process. Default: 2
        
        Reddit Crawler script. Search for subreddits with minimum of 5k upvotes.
        Get upvotes, subreddit, thread title, comments link and thread link.
    '''
    
    if not subr_input:
        raise Exception("Invalid list input.")
        
    # Add real user agent
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0'
    
    subr_input = subr_input.split(';')
    # Build list urls
    url = 'https://old.reddit.com/r/'
    subreddits = []
    for subr in subr_input:
        subreddits.append(url + subr)
    
    print("Hold your horses!!\n")
    
    subr_page = []
    for subr in subreddits:

        response = requests.get(subr, headers = {'User-agent': user_agent})
        if not response.ok:
            raise ServerResponseError("There was a response error." + response.status_code)
        
        subr_page.append(soup(response.text, 'lxml'))
        
        # Deal with extra pages
        for page in range(max_thread_pages-1):
            
            next_url = subr_page[-1].find('span', {'class': 'next-button'}).a.get('href')
            
            if next_url is None:
                print("Page limit reached for "+ subr_input[subr] +" on page number: "+ page +".")
                return
            
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
    
    if not stats.get('upvotes'):
        print("Sorry. Based on your input there are no threads with 5k upvotes or higher. Try increasing how much pages to process (default: 2).")
        return

    
    # Output gathered information
    for k in range(len(stats['upvotes'])):
        print('Upvotes: ' + stats['upvotes'][k])
        print('Subreddit: ' + stats['subreddit'][k])
        print('Thread Title: ' + stats['title'][k])
        print('Comments URL: ' + stats['comments_url'][k])
        print('Thread URL: ' + stats['thread_url'][k] + '\n')
    
    return
    

# reddit_crawler('space;nasa')

# https://api.telegram.org/bot730157765:AAFtEqAFS2K_rbhv1JhxDL5bohpgmkC7KYM/getme

# https://api.telegram.org/bot730157765:AAFtEqAFS2K_rbhv1JhxDL5bohpgmkC7KYM/sendMessage?chat_id=666175175,&text=TestReply

if __name__ == "__main__":
    crawler()