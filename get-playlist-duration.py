#!/opt/homebrew/opt/python@3.9/libexec/bin/python

from googleapiclient.discovery import build
import isodate
import os
import json

# Replace with your own API key and playlist ID
API_KEY=os.environ['RAJARAMANMYTHILI_YOUTUBE_API_KEY']
PLAYLIST_ID = 'PLdBTiOEoG70n_aTSZgIGi3pOtyO7D2Tky'
VIDEOS_JSON_FILE = '/Users/rajaramaniyer/rajaramanmythili.github.io/playlist.json'

def get_list_of_playlist():
    # Build the YouTube service
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    # Fetch the playlist items
    next_page_token = None
    with open(VIDEOS_JSON_FILE, "w", encoding="UTF-8") as write_file:
        write_file.write("[")

    while True:
        playlist_request = youtube.playlists().list(
            part='snippet,contentDetails',
            maxResults=50,  # Max results per page
            pageToken=next_page_token,
            channelId='UCLbwWE1OTFQyfXT7O3u6pbw'
        )
        playlist_response = playlist_request.execute()

        with open(VIDEOS_JSON_FILE, "a", encoding="UTF-8") as write_file:
            for item in playlist_response['items']:
                write_file.write('{"playlistId":"%s","title":"%s","publishedAt":"%s","thumbnail":"%s"},' % (item['id'], item['snippet']['title'], item['snippet']['publishedAt'], item['snippet']['thumbnails']['default']['url']))

        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break

    with open(VIDEOS_JSON_FILE, "a", encoding="UTF-8") as write_file:
        write_file.write("]")

def get_playlist_videos_duration(playlist_id):
    # Usage
    # durations = get_playlist_videos_duration(API_KEY, PLAYLIST_ID)
    # total_duration_seconds = sum(durations)
    # total_duration_minutes = total_duration_seconds / 60
    # print(f"Total duration: {total_duration_minutes:.2f} minutes")

    # Build the YouTube service
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    # Fetch the playlist items
    next_page_token = None
    video_durations = []

    while True:
        # Request the playlist items
        playlist_request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,  # Max results per page
            pageToken=next_page_token
        )
        playlist_response = playlist_request.execute()

        with open(VIDEOS_JSON_FILE, "a", encoding="UTF-8") as write_file:
            json.dump(playlist_response, write_file, indent=2)

        video_ids = []
        for item in playlist_response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        # Request the video details
        video_request = youtube.videos().list(
            part='contentDetails',
            id=','.join(video_ids)
        )
        video_response = video_request.execute()

        for item in video_response['items']:
            duration = item['contentDetails']['duration']
            duration_seconds = isodate.parse_duration(duration).total_seconds()
            video_durations.append(duration_seconds)

        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break

    return video_durations

get_list_of_playlist()
