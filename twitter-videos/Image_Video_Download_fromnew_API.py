import tweepy           # To consume Twitter's API
import pandas as pd     # To handle data
import numpy as np      # For number computing
import csv
# For plotting and visualization:
from IPython.display import display
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from urllib.request import urlopen ,URLError, HTTPError,Request
import urllib.error
import urllib
import glob 
from glob import glob
import argparse
import shutil
import requests
from bs4 import BeautifulSoup
import json
import urllib.parse
import m3u8
from pathlib import Path
import re
import ffmpeg
import os
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}



def download(video_url):
    video_player_url_prefix = 'https://twitter.com/i/videos/tweet/'
    video_host = ''
    output_dir = './output'

    # Parse the tweet ID
    video_url = video_url.split('?', 1)[0]
    tweet_user = video_url.split('/')[3]
    tweet_id = video_url.split('/')[5]

    # Grab the video client HTML
    video_player_url = video_player_url_prefix + tweet_id
    video_player_response = requests.get(video_player_url)

    # Get the JS file with the Bearer token to talk to the API.
    js_file_soup = BeautifulSoup(video_player_response.text, 'html.parser')
    js_file_url = js_file_soup.find('script')['src']
    js_file_response = requests.get(js_file_url)

    # Pull the bearer token out
    bearer_token_pattern = re.compile('Bearer ([a-zA-Z0-9%-])+')
    bearer_token = bearer_token_pattern.search(js_file_response.text)
    bearer_token = bearer_token.group(0)

    # Talk to the API to get the m3u8 URL
    api_string = 'https://api.twitter.com/1.1/videos/tweet/config/' + tweet_id + '.json'
    player_config = requests.get(api_string, headers={'Authorization': bearer_token})
    m3u8_url_get = json.loads(player_config.text)
    try:
        m3u8_url_get = m3u8_url_get['track']['playbackUrl']
        # Get m3u8
        m3u8_response = requests.get(m3u8_url_get, headers = {'Authorization': bearer_token})
        m3u8_url_parse = urllib.parse.urlparse(m3u8_url_get)
        video_host = m3u8_url_parse.scheme + '://' + m3u8_url_parse.hostname

        m3u8_parse = m3u8.loads(m3u8_response.text)

        if m3u8_parse.is_variant and len(m3u8_parse.playlists) > 1:
            playlist = m3u8_parse.playlists[len(m3u8_parse.playlists)-1]
            resolution = str(playlist.stream_info.resolution[0]) + 'x' + str(playlist.stream_info.resolution[1])
            resolution_file = Path('/media/nano/Nanoyotta/Maplytiks_Social/Events/CSK_Training_Camp/Twitter/') / Path(tweet_id + '.mp4')
            if not os.path.exists(resolution_file):
                # print('[+] Downloading ' + tweet_id)

                playlist_url = video_host + playlist.uri
                ts_m3u8_response = requests.get(playlist_url)
                ts_m3u8_parse = m3u8.loads(ts_m3u8_response.text)

                ts_list = []
                for ts_uri in ts_m3u8_parse.segments.uri:
                    ts_list.append(video_host + ts_uri)

                # Convert TS to MP4
                ts_streams = [ ffmpeg.input(str(_)) for _ in ts_list ]
                ffmpeg.concat(*ts_streams).output(str(resolution_file), strict= -2,loglevel='error').overwrite_output().run()
                print('[+] Downloaded non embded' + tweet_id)
            else :
                    print ("This  video file is already exists")
    except ffmpeg.Error as e:
        print ("ffmpeg error with this tweet",tweet_id)
        print("ffmpeg error")
        print(e)


    except:
        error_response = json.loads(player_config.text)
        if error_response['errors'][0]['code'] == 88:
            with open('./twitter_video_fails.txt', 'a') as f:
                f.write(api_string+"\n")



def get_image_video_url_from_tweet(tweet):
    images_and_videos_links =[]  
    if "retweeted_status" in tweet:
        if tweet["retweeted_status"]["truncated"]:

            if "extended_tweet" in tweet["retweeted_status"] and 'extended_entities' in tweet["retweeted_status"]['extended_tweet'].keys():
                medias = tweet["retweeted_status"]["extended_tweet"]['extended_entities']['media']
            else:
                medias="NaN"
        else:
            if "extended_entities" in tweet["retweeted_status"] and 'media' in tweet["retweeted_status"]['extended_entities'].keys():
                medias = tweet["retweeted_status"]['extended_entities']['media']
            else:
                medias ="NaN"
    
    elif "quoted_status" in tweet:
        if tweet["quoted_status"]["truncated"]:

            if "extended_tweet" in tweet["quoted_status"] and 'extended_entities' in tweet["quoted_status"]['extended_tweet'].keys():
                medias = tweet["quoted_status"]["extended_tweet"]['extended_entities']['media']
            else:
                medias="NaN"
        else:
            if "extended_entities" in tweet["quoted_status"] and 'media' in tweet["quoted_status"]['extended_entities'].keys():
                medias = tweet["quoted_status"]['extended_entities']['media']
            else:
                medias ="NaN"
    else:
        if tweet["truncated"]:
            if "extended_tweet" in tweet and 'extended_entities' in tweet['extended_tweet'].keys():
                medias = tweet["extended_tweet"]['extended_entities']['media']
            else:
                medias ="NaN"
        else:
            if "extended_entities" in tweet and 'media' in tweet['extended_entities'].keys():
                medias = tweet['extended_entities']['media']
            else:
                medias ="NaN"
    try:
        if medias!= "NaN":
            for media in medias:
                if media['type'] in {"video" , "animated_gif"}:
                    videos = media["video_info"]["variants"]
                    bitrate = 0
                    index = 0
                    for i in range(0, len(videos)):
                        if videos[i]['content_type'] == 'video/mp4':
                            br = int(videos[i]['bitrate'])
                            if br > bitrate:
                                bitrate = br
                                index = i
                    images_and_videos_links.append(videos[index]['url'])          
                elif (media['type'] not in {'video' , "animated_gif"} and media['expanded_url'].split('/')[6] =='video'):
                    videos = media['expanded_url']
                    videos_spt =videos.split('/video')[0]
                    images_and_videos_links.append(videos_spt)
                else :
                    images_url = media["media_url"]
                    images_and_videos_links.append(images_url)

        else:
            images_and_videos_links =[]

    except AttributeError:
        pass
    return images_and_videos_links

def download_images_videos_to_local_dir(tweet):
    images_and_videos_links =get_image_video_url_from_tweet(tweet)
    if "retweeted_status" in tweet.keys():
        tweetid = tweet["retweeted_status"]["id"]
        print ("This is a retweet",tweetid)
        
    else:
        tweetid= tweet["id"]
    
    if not  len(images_and_videos_links) ==0:
        for count,media_link in enumerate(images_and_videos_links):
            print ("This is the media link",media_link)
            try:
                if os.path.basename(media_link)==str(tweetid):
                    download(media_link)

                elif (os.path.splitext(media_link))[1] in [".jpg",".png"] :    
                    req = Request(media_link ,headers=headers)
                    rsp = urlopen(req)
                    image_file_name ='/media/nano/Nanoyotta/Maplytiks_Social/Events/CSK_Training_Camp/Twitter/'+'/' + str(tweetid)+ '_' +str(count) +str((os.path.splitext(media_link))[1])
                    if not os.path.exists(image_file_name):
                        with open(image_file_name,'wb') as f:
                            f.write(rsp.read())
                        print ("Downloaded images",tweetid)
                    else: 
                        print ("This  image file is already exists")
                    	

                else:    
                    req = Request(media_link ,headers=headers)
                    rsp = urlopen(req)
                    video_file_name ='./CSK_Training_Camp/Twitter/'+'/' + str(tweetid)+ '_'+ str(count)+'.mp4'
                    if not os.path.exists(video_file_name):
                        # print ("Downloading non nonebedded  video",tweetid)
                        with open(video_file_name,'wb') as f:
                            f.write(rsp.read())
                        print ("Downloaded embded video",tweetid)
                    else :
                        print ("This  video file is already exists")
            except urllib.error.URLError as e:
                if hasattr(e,'code'):
                    print (e.code)
                if hasattr(e,'reason'):
                    print (e.reason)
            except urllib.error.HTTPError as e:
                if hasattr(e,'code'):
                    print(e.code)
                if hasattr(e,'reason'):
                    print(e.reason)
                print('HTTPError!!!')


def write_tweets(tweets, filename):
    ''' Function that appends tweets to a file. '''

    with open(filename, 'a') as f:
        for tweet in tweets:
            json.dump(tweet, f)
            f.write('\n')


def find_unique_tweets(unique_tweet_ids,all_tweets):
    unique_tweets =[]
    for current_tweet in all_tweets:

        if str(current_tweet['id'])  not in unique_tweet_ids:
            unique_tweets.append(current_tweet)

            
    return unique_tweets

def collect_tweets(tweet_files):
    
    all_tweets =[]
    for file in tweet_files:
        with open(file, 'r') as f:
            for j ,line in enumerate(f.readlines()):
                try:
                    all_tweets.append(json.loads(line))
                except ValueError:
                    print ("{} failed the JSON load".format(line))
    return all_tweets


if __name__ == '__main__':
    
    tweet_path = "./CSK_Training_Camp/Twitter/"         
   
    tweet_files = glob(tweet_path +"/" +"*.json")
    for file in tweet_files:
        with open(file, 'r') as f:
            for j ,line in enumerate(f.readlines()):
                try:
                    # tweet_id =(os.path.splitext(line))[0].split("/")[7]
                    # tweet_remain_ids.append(tweet_id)
                    # print (line.split("/")[7])
                    download_images_videos_to_local_dir(json.loads(line)) 
                    
                except ValueError:
                    print ("{} failed the JSON load".format(line)) 
    # unique_tweets = find_unique_tweets(tweet_remain_ids,all_tweets)
    # write_tweets(unique_tweets,tweet_remain_filepath)
	                
#https://api.twitter.com/1.1/videos/tweet/config/1041280536646434816.json
