import platform
import requests
import os
import urllib.parse
import unicodedata
import re
import dotenv
import subprocess

if os.path.isfile('.env.local'):
    config = dotenv.dotenv_values('.env.local')
elif os.path.isfile('.env'):
    config = dotenv.dotenv_values('.env')
else:
    print('No .env file found.')
    exit(0)

TWITCH_API = 'https://api.twitch.tv'
TWITCH_CLIENT_ID = config['TWITCH_CLIENT_ID']

def slugify(value, allow_unicode=False) -> str:
    """
    https://github.com/django/django/blob/f0fa2a3b49797f1e9830e2a0d2072119093b4452/django/utils/text.py#L400

    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = (
            unicodedata.normalize('NFKD', value)
            .encode('ascii', 'ignore')
            .decode('ascii')
        )
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

def get_m3u8_url(vod_metadata: dict) -> str:
    split_url = urllib.parse.urlsplit(vod_metadata['animated_preview_url'])
    split_path = split_url.path.split('/')

    return f'{split_url.scheme}://{split_url.netloc}/{split_path[1]}/chunked/index-dvr.m3u8'

def get_full_output_path(vod_metadata: dict, output_path: str) -> str:
    title = vod_metadata['title']
    game = vod_metadata['game']
    created_at = vod_metadata['created_at']
    channel = vod_metadata['channel']['name']

    file_name = slugify(f'{channel}-{game}-{created_at}-{title}')

    if platform.system() == 'Windows':
        return f'{output_path}\\{file_name}.mp4'
    
    return f'{output_path}/{file_name}.mp4'

def download_vod(input: str, output: str):
    subprocess.check_call(args=f'ffmpeg -i "{input}" -c copy -bsf:a aac_adtstoasc "{output}"', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=True)

def main():
    output_path = input('VOD output path: ').rstrip('/\\')
    vods_urls = input('Twitch VODs URLs (separated by comma): ')
    vods_urls = vods_urls.split(',')

    headers = {
        'client-id': TWITCH_CLIENT_ID,
        'accept': 'application/vnd.twitchtv.v5+json'
    }

    for url in vods_urls:
        vod_url = url.split('?')[0] # Remove all query parameters
        vod_id = vod_url.split('/')[-1]

        r = requests.get(url=f'{TWITCH_API}/kraken/videos/{vod_id}', headers=headers)
        if r.status_code == 200:
            vod_metadata = r.json()

            m3u8_url = get_m3u8_url(vod_metadata)
            full_output_path = get_full_output_path(vod_metadata, output_path)

            print(f'Downloading {vod_url}')
            download_vod(m3u8_url, full_output_path)

if __name__ == '__main__':
    main()
