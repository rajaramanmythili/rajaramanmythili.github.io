#!/opt/homebrew/opt/python@3.9/libexec/bin/python
"""
Push titles from data.json to YouTube (reverse of refresh-video-list.py).

Setup (one time):
  pip install google-api-python-client google-auth-oauthlib
  Google Cloud Console -> enable "YouTube Data API v3"
  -> Credentials -> Create OAuth client ID (type: Desktop app)
  -> download JSON and save as client_secret.json next to this script.
  (If the consent screen is in "Testing" mode, add your Google account as a test user.)

Usage:
  python push-titles-to-youtube.py            # dry run: shows what would change
  python push-titles-to-youtube.py --apply    # actually updates YouTube

Quota: videos.list = 1 unit per 50 videos, videos.update = 50 units each.
Default daily quota is 10,000 units => roughly 190 title updates per day.
Re-run the next day; already-updated videos are skipped automatically.
"""

import json
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

DATA_JSON_FILE = '/Users/rajaramaniyer/rajaramanmythili.github.io/data.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET = os.path.join(HERE, 'client_secret.json')
TOKEN_FILE = os.path.join(HERE, 'token.json')


def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)


def load_local_titles():
    with open(DATA_JSON_FILE, 'r', encoding='UTF-8') as f:
        data = json.load(f)
    return {v['videoId']: v['title'] for v in data.values()
            if 'videoId' in v and 'title' in v}


def fetch_remote_snippets(youtube, video_ids):
    snippets = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        resp = youtube.videos().list(part='snippet', id=','.join(batch)).execute()
        for item in resp.get('items', []):
            snippets[item['id']] = item['snippet']
    return snippets


def main():
    apply_changes = '--apply' in sys.argv

    local = load_local_titles()
    youtube = get_service()
    remote = fetch_remote_snippets(youtube, list(local.keys()))

    changes = []
    for vid, new_title in local.items():
        snippet = remote.get(vid)
        if snippet is None:
            print(f'SKIP (not found / not yours): {vid}')
            continue
        if snippet['title'] != new_title:
            changes.append((vid, snippet, new_title))

    print(f'{len(changes)} title(s) differ out of {len(local)} videos.\n')
    for vid, snippet, new_title in changes:
        print(f'{vid}\n  YouTube: {snippet["title"]}\n  Local  : {new_title}\n')

    if not apply_changes:
        print('Dry run only. Re-run with --apply to update YouTube.')
        return

    done = 0
    for vid, snippet, new_title in changes:
        # videos.update replaces the snippet, so resend the writable fields unchanged.
        body = {
            'id': vid,
            'snippet': {
                'title': new_title,
                'description': snippet.get('description', ''),
                'categoryId': snippet['categoryId'],
            }
        }
        if 'tags' in snippet:
            body['snippet']['tags'] = snippet['tags']
        if 'defaultLanguage' in snippet:
            body['snippet']['defaultLanguage'] = snippet['defaultLanguage']

        try:
            youtube.videos().update(part='snippet', body=body).execute()
            done += 1
            print(f'Updated {vid}: {new_title}')
        except HttpError as e:
            print(f'FAILED {vid}: {e}')
            if e.resp.status == 403 and b'quota' in e.content.lower():
                print('Quota exhausted. Run again tomorrow.')
                break

    print(f'\nUpdated {done} of {len(changes)} videos.')


main()
