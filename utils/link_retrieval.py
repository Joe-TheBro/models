"""
Requests youtube URLs from waldo api that meet requirements
Validates fetched URLs, and saves them to a csv file
"""
import argparse
import json
import os
import re

import pandas as pd
import requests
import validators

# Setup command line arguments
parser = argparse.ArgumentParser(description="Get URL's from API and store them locally")
parser.add_argument("-e", "--endpoint", help='Target URL On Server', required=False,
                    default="https://waldo.vision/api/trpc/urls", type=str)
parser.add_argument("-k", "--key", help='API Key', required=False,
                    default=(os.environ.get("WALDO_API_KEY")), type=str)
parser.add_argument("-o", "--output", help='Folder To Store Output', required=True, type=str)
parser.add_argument("-r", "--requirements", help='Specfications for links retrieved',
                    default='{"minReviews": 25, "rating": 90}', required=False, type=str)

args = vars(parser.parse_args())

def is_valid_youtube_url(url):
    """Checks via regex if URL is a valid youtube link"""
    regex = (
            r'https?://(?:www\.)?(?:youtube|youtu|youtube-nocookie|music'
            r'\.youtube|gaming\.youtube|studio\.youtube|content\.googleapis|googlevideo)'
            r'\.(?:com|be)/(?:watch\?v=|embed/|v/|.+\?v=)?([^\&=%\?]+)'
            )
    return bool(re.match(regex, url))

def parse_data(data):
    """
    Convert the data to a pandas DataFrame. If you find a better solution, please fix.
    Were expecting data that looks like this:
    {"page": 0,
    "totalPages": 100,
    "gameplay": [{"uuid": "38r8hnf80ew-35uhehrfnjea-wryhghjvsdk",
                  "ytUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                {"uuid": "38r8hnf80ew-35uhehrfnjea-wryhghjvsdk",
                 "ytUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}]
    }
    """

    response_dataframe = pd.DataFrame(data)
    response_list = response_dataframe['gameplay'].tolist()
    response_dataframe = pd.DataFrame(columns=['uuid','url'])
    for obj in response_list:
        obj_dataframe = pd.DataFrame(obj, index=[0])
        obj_dataframe.rename(columns={"ytUrl": "url"}, inplace=True)
        response_dataframe = pd.concat([response_dataframe, obj_dataframe], ignore_index=True)

    # Filter out duplicate links
    response_dataframe.drop_duplicates(subset=["url"], inplace=True)

    # Validate the URLs
    valid_urls = []
    for url in response_dataframe["url"]:
        if (validators.url(url) and is_valid_youtube_url(url)):
            valid_urls.append(url)
    return valid_urls

def main(requirements):
    """
    Pulls URLs from the DB that meet the criteria in the requirements argument

    Example requirements
    {
        "minReviews": 25,
        "rating": 90,
    }
    """

    endpoint = args['endpoint']
    params = {
        "auth_token": args['key'],
        "requirements": requirements
    }
    params_json = json.dumps(params)
    # Make the API request and retrieve the data
    response = requests.get(endpoint, params=params_json, timeout=10)
    data = response.json()
    valid_urls = parse_data(data)
    # Make output directory if it doesn't exist
    download_dir = args['output']
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    # Save the downloaded links to a file
        valid_urls_df = pd.DataFrame(valid_urls)
        valid_urls_df.to_csv((os.path.join(download_dir + "links.csv")),
                            index=True, columns=["uuid","url"])

if __name__ == "__main__":
    main(dict(args['requirements']))
