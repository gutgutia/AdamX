from apify_client import ApifyClient
from googleapiclient.discovery import build
from dotenv import load_dotenv
import json
import os

from readability import Document
import requests

load_dotenv()


APIFY_API_KEY = os.getenv('APIFY_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Set up the YouTube API client
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Initialize the ApifyClient with your API token
client = ApifyClient(APIFY_API_KEY)

def get_user_choice():
    options = ["Google Search", "YouTube", "Webpage", "Article", "G2", "Others"]
    print("What data do you want to process?")
    for i, option in enumerate(options, start=1):
        print(f"{i}. {option}")
    
    choice = input("Please enter the number of your choice: ")
    try:
        choice_int = int(choice)
        if 1 <= choice_int <= len(options):
            return options[choice_int - 1]
        else:
            print("Invalid choice. Please enter a number from the list.")
            return get_user_choice()
    except ValueError:
        print("Invalid input. Please enter a number.")
        return get_user_choice()

def get_article(url):
    response = requests.get(url)
    doc = Document(response.text)
    article = doc.summary()

    filename = 'article.html'
    # Determine the desktop path
    desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')
    file_path = os.path.join(desktop_path, filename)

    print("Saving article...") 
    # save article as a html file
    with open(file_path, 'w') as file:
        file.write(article)

    print(f"Article has been saved to {file_path}")
    
    return article

# Ignore this function
def get_screenshot_2(url):

    # Prepare the Actor input with the provided URL
    run_input = {
        "urls": [
            {"url": url},
        ],
        "pageLoadTimeoutSecs": 60,
        "pageMaxRetryCount": 2,
        "waitUntil": "load",
        "viewportWidth": 1200,
        "viewportHeight": 900,
        "delaySecs": 0,
        "imageType": "jpeg",
    }

    # Run the Actor and wait for it to finish
    run = client.actor("xDM69LgSdy3tscbqS").call(run_input=run_input)

    # Fetch and return the first screenshot URL from the run's dataset
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        screenshotUrl = item.get('screenshot').get('url')
        #return item.get('screenshotUrl')

    return screenshotUrl

def get_screenshot(url): # Use ApiFY screenshot actor
    # Prepare the Actor input
    run_input = {
        "urls": [{ "url": url }],
        "waitUntil": "load",
        "delay": 5000,
        "viewportWidth": 1280,
        "scrollToBottom": True,
        "delayAfterScrolling": 2500,
        "waitUntilNetworkIdleAfterScroll": True,
        "waitUntilNetworkIdleAfterScrollTimeout": 30000,
        "proxy": { "useApifyProxy": True },
        "selectorsToHide": "",
    }

    # Run the Actor and wait for it to finish
    run = client.actor("rGCyoaKTKhyMiiTvS").call(run_input=run_input)

    # Fetch and print Actor results from the run's dataset (if there are any)
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        screenshotUrl = item.get('screenshotUrl')

    return screenshotUrl

def scrape_googlesearch(searchTerm):

    # Prepare the Actor input
    run_input = {
        "queries": searchTerm,
        "resultsPerPage": 20,
        "maxPagesPerQuery": 1,
        "languageCode": "",
        "mobileResults": False,
        "includeUnfilteredResults": False,
        "saveHtml": False,
        "saveHtmlToKeyValueStore": False,
    }

    # Run the Actor and wait for it to finish
    run = client.actor("nFJndFXA5zjCTuudP").call(run_input=run_input)

    results = []
    
    # Fetch and print Actor results from the run's dataset (if there are any)
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        #print(item)
        for result in item.get('paidResults', []) + item.get('organicResults', []):
            results.append({
                "title": result.get("title"),
                "url": result.get("url"),
                "displayedUrl": result.get("displayedUrl"),
                "description": result.get("description"),
                "type": result.get("type")
            })

        url = item.get('searchQuery').get('url')
        print(url)

    results = json.dumps(results, indent=2)

    filename = "google_search_results_" + searchTerm.replace(" ", "+") + ".txt"

    # Determine the desktop path
    desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')
    file_path = os.path.join(desktop_path, filename)
    
    # Write the results to a .txt file on the desktop
    with open(file_path, 'w') as file:
        file.write(results)
    
    print(f"Results have been saved to {file_path}")

    return results, url

# Ignore this function
'''
def scrape_youtube(searchTerm):

    # Prepare the Actor input
    run_input = {
        "searchKeywords": searchTerm,
        "maxResults": 20,
        "maxResultsShorts": 20,
        "maxResultStreams": 20,
        "startUrls": [],
        "subtitlesLanguage": "en",
        "subtitlesFormat": "srt",
    }

    # Run the Actor and wait for it to finish
    run = client.actor("h7sDV53CddomktSi5").call(run_input=run_input)

    # Fetch and print Actor results from the run's dataset (if there are any)
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        print(item)

    base_url = "https://www.youtube.com/results?search_query="
    formatted_search_term = searchTerm.replace(" ", "+")
    url = base_url + formatted_search_term

    return url
'''

# Search for videos on YouTube
def scrape_youtube_2(search_term, max_results=20):
    
    request = youtube.search().list(
        q=search_term,
        part='snippet',
        type='video',
        maxResults=max_results
    )
    response = request.execute()
    
    videos = []
    for item in response.get('items', []):
        video_id = item['id']['videoId']
        video_data = {
            'channelName': item['snippet']['channelTitle'],
            'title': item['snippet']['title'],
            'description': item['snippet']['description'],
            'videoId': item['id']['videoId'],
            'publishTime': item['snippet']['publishTime'],
            'thumbnails': item['snippet']['thumbnails']['default']['url'],
            'url': f'https://www.youtube.com/watch?v={video_id}'  # Constructing the YouTube URL
        }
        videos.append(video_data)
    
    videos = json.dumps(videos, indent=2)

    formatted_search_term = search_term.replace(" ", "+")
    filename = "youtube_search_results_" + formatted_search_term + ".txt"

    # Determine the desktop path
    desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')
    file_path = os.path.join(desktop_path, filename)
    
    # Write the results to a .txt file on the desktop
    with open(file_path, 'w') as file:
        file.write(videos)
    
    print(f"Results have been saved to {file_path}")


    base_url = "https://www.youtube.com/results?search_query="
    url = base_url + formatted_search_term

    return videos, url


def main():
    results = []
    
    choice = get_user_choice()

    if(choice == "Google Search" or choice == "YouTube"):
        searchTerm = input("Enter the search term: ")

    print("\nGetting data...")
    if(choice == "Google Search"):
        results, url = scrape_googlesearch(searchTerm)
    elif(choice == "YouTube"):
        videos, url = scrape_youtube_2(searchTerm)
        print(videos)
    elif(choice == "Webpage"):
        url = input("Enter the URL: ")
    elif(choice == "G2"):
        url = input("Enter the URL: ")
    elif(choice == "Article"):
        url = input("Enter the URL: ")
        article = get_article(url)
    elif(choice == "Others"):
        url = input("Enter the URL: ")
        
    print("\nGetting screenshot...")
    screenShotURL = get_screenshot(url)
    print(screenShotURL)

main()