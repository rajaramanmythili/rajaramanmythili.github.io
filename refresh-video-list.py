#!/opt/homebrew/opt/python@3.9/libexec/bin/python

import requests
import json
from collections import Counter
import os
import re

API_KEY=os.environ['RAJARAMANMYTHILI_YOUTUBE_API_KEY']
VIDEOS_JSON_FILE = '/Users/rajaramaniyer/rajaramanmythili.github.io/videos.json'

def list_videos():
    f = open('/Users/rajaramaniyer/rajaramanmythili.github.io/data.json', 'r', encoding="UTF-8")
    videos_json = json.load(f)
    f.close()
    # videos_json format is: { "12" : { "videoId": "123", "title": "title", "publishedAt": "2021-01-01T00:00:00Z" }, "11" : { "videoId": "123", "title": "title", "publishedAt": "2021-01-01T00:00:00Z" } }
    # List videos that are not having Srimad Bhagavatam or Yugala Shathakam in title
    for key in videos_json:
        if 'title' in videos_json[key]:
            title = videos_json[key]['title']
            if not re.search(r'(^Srimad Bhagavatham|^Govinda Shatakam|^Radhika Shatakam|^Raghava Shatakam|^Yugala Shatakam)', title, re.IGNORECASE):
                print(title)

def get_video_json():
    f = open(VIDEOS_JSON_FILE, 'r', encoding="UTF-8")
    videos_json = json.load(f)
    f.close()
    return videos_json

def refresh_videos_list():
    # The API endpoint
    url = "https://www.googleapis.com/youtube/v3/playlistItems?playlistId=UULbwWE1OTFQyfXT7O3u6pbw&key="+API_KEY+"&part=snippet&maxResults=50"

    response = requests.get(url)
    response_json = response.json()

    videos_json = get_video_json()
    items_to_add = 0
    if 'items' in videos_json:
        for item in response_json['items']:
            if item['id'] == videos_json['items'][0]['id']:
                break
            items_to_add += 1
    else:
        items_to_add = len(response_json['items'])
    if items_to_add == 0:
        print('videos.json is Already upto date.')
        response_json = videos_json
    else:
        if items_to_add < len(response_json['items']):
            for num in reversed(range(items_to_add)):
                videos_json['items'].insert(0, response_json['items'][num])
            videos_json['pageInfo']['totalResults'] = response_json['pageInfo']['totalResults']
            response_json = videos_json
        else:
            next_response_json = response_json
            while 'nextPageToken' in next_response_json:
                print(json.dumps(next_response_json))
                response = requests.get(url + "&pageToken=" + next_response_json['nextPageToken'])
                next_response_json = response.json()
                for item in next_response_json['items']:
                    response_json['items'].append(item)
        # end
        response_json['pageInfo']['resultsPerPage'] = len(response_json['items'])
        with open(VIDEOS_JSON_FILE, "w", encoding="UTF-8") as write_file:
            json.dump(response_json, write_file, indent=2)
    print("Total %d videos" % len(response_json['items']))

def update_data_json():
    f = open(VIDEOS_JSON_FILE,'r',encoding="UTF-8")
    response_json = json.loads(f.read())
    f.close()
    json_data = {}
    i=len(response_json['items'])
    for item in response_json['items']:
        json_data[i] = {
            'videoId': item['snippet']['resourceId']['videoId'], 
            'title': item['snippet']['title'],
            'publishedAt': item['snippet']['publishedAt']
        }
        i-=1
        #print(item['snippet']['title'])
        #print(item['snippet']['description'])
        #print(item['snippet']['playlistId'])
        #print(item['snippet']['publishedAt'])
        #print(item['snippet']['thumbnails']['default']['url'])
        #print(item['snippet']['resourceId']['videoId'])

    j = open('/Users/rajaramaniyer/rajaramanmythili.github.io/data.json','w',encoding="UTF-8")
    j.write(json.dumps(json_data, indent=2))
    j.close()

refresh_videos_list()
update_data_json()
#list_videos()
