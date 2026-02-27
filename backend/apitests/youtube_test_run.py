# Gets the YouTube videos, playlists, and channels based on the search keyword. 

# all imports
from testdb_operations import save_video_to_db, save_comments_to_db
from googleapiclient.discovery import build
from google import genai
from google.genai import types
 
# Arguments that need to passed to the build function
DEVELOPER_KEY = "AIzaSyAsxHBbNUV36SfPDDdwTCVw2xObCuVKXLk" 
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
 
# creating Youtube Resource Object
youtube_object = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                                        developerKey = DEVELOPER_KEY)

# creating a client object for Gemini 3 Flash
client = genai.Client(api_key="AIzaSyDTnU1EHq6EIuM1e5Xx7rzMff24P_2nbkE")

# Function to get video comments
def get_video_comments(video_id, max_results=20):
    try:
        video_comments = youtube_object.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=max_results,
            textFormat="plainText"
        ).execute()
        
        comments = []
        for item in video_comments['items']:
            thread_id = item['id']  
            top_comment = item['snippet']['topLevelComment']
            snippet = top_comment['snippet']
            
            comments.append({
                "comment_id": top_comment['id'],  
                "thread_id": thread_id,            
                "author": snippet["authorDisplayName"],
                "author_channel_id": snippet.get("authorChannelId", {}).get("value"),  # real authorChannelId
                "text": snippet["textDisplay"],
                "likes": snippet["likeCount"],
                "published_at": snippet["publishedAt"],
                "updated_at": snippet["updatedAt"],
                "total_reply_count": item['snippet']['totalReplyCount']
            })
            
        return comments
        
    except Exception as e:
        print(f"Could not retrieve comments: {e}")
        return []
    
# Function to get video statistics (views, likes, comments)
def get_video_statistics(video_id):
    try:
        video_statistics = youtube_object.videos().list(part = "statistics", id = video_id).execute()
        if video_statistics['items']:
            stats = video_statistics['items'][0]['statistics']
            return {
                "views": stats.get("viewCount", 0),
                "likes": stats.get("likeCount", 0),
                "commentCount": stats.get("commentCount", 0)
            }

    except Exception as e:
        print(f"Could not retrieve statistics: {e}")
        return {'views': '0', 'likes': '0', 'comments': '0'}

# Function to send video link to Gemini 3 Flash and get transcript summary/opinions
def transcribe(video_url):
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=types.Content(
            parts=[
                types.Part(
                    file_data=types.FileData(file_uri=video_url)
                ),
                types.Part(text=f"You are a video content analyst. Given the YouTube video link, extract and summarize the main opinions and points made by the creator. Focus on: overall sentiment, key points, and any conclusions or verdicts mentioned."
                )
            ]
        )
    )
    print(response.text)

# Function to search YouTube based on a keyword and retrieve videos, playlists, channels, comments, and transcripts
def youtube_search_keyword(query, max_results):
     
    # calling the search.list method to retrieve youtube search results
    search_keyword = youtube_object.search().list(q = query, part = "id, snippet", order = "viewCount", type = "video",
                                               maxResults = max_results).execute()
     
    # extracting the results from search response
    results = search_keyword.get("items", [])
 
    # empty list to store video, channel, playlist metadata
    videos = []
    playlists = []
    channels = []
     
    # extracting required info from each result object
    for result in results:
        # video result object
        if result['id']['kind'] == "youtube#video":
            video_id = result["id"]["videoId"]
            stats = get_video_statistics(video_id)
            videos.append("% s (% s) (% s) (% s) (Likes: % s) (Views: %s) (Comment Count: %s)" % (result["snippet"]["title"],
                            video_id, result['snippet']['description'],
                            result['snippet']['thumbnails']['default']['url'], stats["likes"], stats["views"], stats["commentCount"]))

        # playlist result object
        elif result['id']['kind'] == "youtube#playlist":
            playlists.append("% s (% s) (% s) (% s)" % (result["snippet"]["title"],
                                 result["id"]["playlistId"],
                                 result['snippet']['description'],
                                 result['snippet']['thumbnails']['default']['url']))

        # channel result object
        elif result['id']['kind'] == "youtube#channel":
            channels.append("% s (% s) (% s) (% s)" % (result["snippet"]["title"],
                                   result["id"]["channelId"], 
                                   result['snippet']['description'], 
                                   result['snippet']['thumbnails']['default']['url']))
    
    print("Channels:\n", "\n".join(channels), "\n")
    print("Playlists:\n", "\n".join(playlists), "\n")   
    print("Videos:\n", "\n".join(videos), "\n")
    
    # Get comments for each video
    print("=" * 60)
    print("Comments for each video:")
    print("=" * 60)
    
    # Loop through each video result and retrieve comments
    for result in results:
        if result['id']['kind'] == "youtube#video":
            video_id = result["id"]["videoId"]
            video_title = result["snippet"]["title"]
            
            print(f"Comments for video: {result['snippet']['title']} (ID: {video_id})")
            print("-" * 60)
            
            comments = get_video_comments(video_id, max_results=5)
            
            if comments: 
                for i, comment in enumerate(comments, 1):
                    print(f"\n{i}Author: {comment['author']}")
                    print(f"Comment: {comment['text']}")
                    print(f"Likes: {comment['likes']}")
                    print(f"Published at: {comment['published_at']}")
                    print("-" * 40)
            else:
                print("No comments found or could not retrieve comments.")
    
    # Get transcript summary for each video using Gemini 3 Flash
    for result in results:
        if result['id']['kind'] == "youtube#video":
            video_id = result["id"]["videoId"]
            video_title = result["snippet"]["title"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            print("URL: " + video_url + "\n" + "Video Title: " + video_title)
            
            transcribe(video_url)
 
# Driver Code
if __name__ == "__main__":
    query = 'Danny Gonzalez'
    youtube_search_keyword(query, max_results = 1)