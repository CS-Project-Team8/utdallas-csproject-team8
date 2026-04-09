import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from db_routes import get_conn, load_llm_output, get_movie_data_for_llm, get_movie_id_from_title, get_studio_id_from_movie_id, insert_insight_run

load_dotenv()
GROQ_LLM_API_KEY = os.getenv("GROQ_LLM_API_KEY")

client = Groq(api_key=GROQ_LLM_API_KEY)

# different llm prompts for trailer vs reviews
TRAILER_PROMPT = """
You are an expert movie analyst that specializes in intelligence from movie studios and streaming companies. You will be given data 
from an official movie trailer published by the studio's YouTube channel. The data will be in the form of the movie transcript and
comments. Your job is to analyze this content and return a structured JSON object with insights. Do not return anything else. 
Do not include any explanation or text outside of the JSON object. If a field cannot be determined from the provided data, use null.

You must return the following JSON structure exactly:

{
  "movie": "<name of the movie the trailer promotes>",
  "video_type": "trailer",
  "key_takeaways": [
    "<concise string about main topics from the trailer>",
    ...
  ],
  "claims": [
  {
    "claim": "<specific factual or opinion statement>",
    "source": "<either transcript or comment>",
    "sentiment": "<either positive, negative, or neutral>",
    "verdict": "<one of: verified, disputed, misleading, unverified>",
    "risk_level": "<one of: low, mid, high>"
  },
  ...
  ],
  "narratives": [
    {
      "title": "<specific narrative or theme>",
      "summary": "<2-3 sentence description of the narrative the movie is constructing>",
      "supporting_claims": ["<claim1>", "<claim2>"],
      "sentiment": "<either positive, negative, or mixed>"
    },
    ...
  ],
  "sentiment_breakdown": {
    "overall_sentiment": "<either positive, negative, or mixed>",
    "avg_sentiment_score": <number between -1.0 and 1.0>,
    "positive_pct": <integer from 0-100>,
    "negative_pct": <integer from 0-100>,
    "neutral_pct": <integer from 0-100>,
    "summary": "<1-2 sentences describing audience reaction to the trailer based on comments>"
  }
}

Guidelines:
- Claims are a factual statement made in the trailer. Narratives are high-level stories or themes connected by multiple claims.
- Extract 3-5 key takeaways, 4-6 claims, and 1-3 narratives.
- Sentiment breakdown should reflect the viewers' reaction through comments, NOT the trailer itself.
- Key takeaways should be actionable for a studio executive reviewing their own promotions.
- verdict should reflect whether the claim is factually supported (verified), contested by other sources (disputed), potentially misleading (misleading), or cannot be determined (unverified). 
- risk_level should reflect reputational risk to the studio: low for positive/neutral verified claims, mid for disputed claims, high for misleading or highly negative claims.
"""

# had to combine Review_prompt, Comments_prompt, and Video_prompt into one since groq was having trouble with parsing multiple prompts
REVIEW_PROMPT = """
You are an expert movie analyst that specializes in intelligence from movie studios and streaming companies. You will be given data 
from a movie review video posted by an independent YouTube reviewer. The data will include the raw transcript and a list of viewer 
comments. Your job is to analyze both together and return a structured JSON object with insights. Do not return anything else. 
Do not include any explanation or text outside of the JSON object. If a field cannot be determined from the provided data, use null.
 
You must return the following JSON structure exactly:
 
{
  "movie": "<name of the specific movie being discussed>",
  "video_type": "review",
  "key_takeaways": [
    "<concise insight synthesized from both the review and audience reaction>",
    ...
  ],
  "claims": [
  {
    "claim": "<specific factual or opinion statement>",
    "source": "<either transcript or comment>",
    "sentiment": "<either positive, negative, or neutral>",
    "verdict": "<one of: verified, disputed, misleading, unverified>",
    "risk_level": "<one of: low, mid, high>"
  },
  ...
],
  "narratives": [
    {
      "title": "<specific narrative or theme>",
      "summary": "<2-3 sentence description of the narrative emerging from public discourse>",
      "supporting_claims": ["<claim1>", "<claim2>"],
      "sentiment": "<either positive, negative, or mixed>"
    },
    ...
  ],
  "sentiment_breakdown": {
    "overall_sentiment": "<either positive, negative, or mixed>",
    "avg_sentiment_score": <number between -1.0 and 1.0>,
    "positive_pct": <integer from 0-100>,
    "negative_pct": <integer from 0-100>,
    "neutral_pct": <integer from 0-100>,
    "summary": "<1-2 sentences describing the overall tone of the reviewer and audience>"
  },
  "top_words": [
    {
      "word": "<single impactful word from transcript or comments>",
      "sentiment": "<either positive, negative, or mixed>",
      "count": <integer of how often the word appears>
    },
    ...
  ],
  "mood_signals": [
    {
      "mood": "<single mood like Excitement, Nostalgia, Disappointment, etc>",
      "percentage": <integer from 0-100>
    },
    ...
  ],
  "audience_vs_video": {
    "agreeability": "<either mostly_agrees, mostly_disagrees, mixed>",
    "video_alignment": "<2-3 sentences describing where the audience aligns with the reviewer's opinion>"
  },
  "creator_risk": {
    "risk_score": <integer from 1-10>,
    "risk_level": "<either low, moderate, or high>",
    "summary": "<2-3 sentences about what this reviewer's reception suggests about franchise or content strategy risk>"
  }
}
 
Guidelines:
- Claims are factual statements or strong opinions. Narratives are high-level themes connecting multiple claims.
- Focus claims on what the reviewer and commenters are actually saying about the film.
- Extract 3-5 key takeaways, 4-6 claims, and 1-3 narratives.
- Extract exactly 5 moods for mood_signals, each scored individually.
- Key takeaways should be points a studio executive may need to know about public reaction.
- There should be a total of 10 expressive words in top_words.
- In sentiment_breakdown, positive_pct, negative_pct, and neutral_pct should sum to 100.
- verdict should reflect whether the claim is factually supported (verified), contested by other sources (disputed), potentially misleading (misleading), or cannot be determined (unverified). 
- risk_level should reflect reputational risk to the studio: low for positive/neutral verified claims, mid for disputed claims, high for misleading or highly negative claims.
"""

AGGREGATION_PROMPT = """
You are an expert movie analyst that specializes in intelligence from movie studios and streaming companies. You will be given 
a set of pre-analyzed JSON results from multiple YouTube videos about a movie, one official trailer and several independent review videos.
Your job is to aggregate these individual analytics into a single high-level report and return a structured JSON object with insights. 
Do not return anything else. Do not include any explanation or text outside of the JSON object. If a field cannot be determined from the 
provided data, use null.

You must return the following JSON structure exactly:

{
  "movie": "<name of the specific movie>",
  "key_takeaways": [
    "<high-level insight aggregated across all videos>",
    ...
  ],
  "top_narratives": [
    {
      "title": "<narrative theme title>",
      "summary": "<2-3 sentences describing the narrative across all sources>",
      "sentiment": "<either positive, negative, or mixed>",
      "source_videos": ["trailer", "review", ...]
    },
    ...
  ],
  "claims": [
  {
    "claim": "<specific factual or opinion statement>",
    "source": "<either transcript or comment>",
    "sentiment": "<either positive, negative, or neutral>",
    "verdict": "<one of: verified, disputed, misleading, unverified>",
    "risk_level": "<one of: low, mid, high>"
  },
  ...
],
  "sentiment_breakdown": {
    "overall_sentiment": "<either positive, negative, or mixed>",
    "avg_sentiment_score": <number between -1.0 and 1.0>,
    "positive_pct": <integer from 0-100>,
    "negative_pct": <integer from 0-100>,
    "neutral_pct": <integer from 0-100>,
    "summary": "<1-2 sentences summarizing overall movie sentiment across all sources>"
  },
  "top_words": [
    {
      "word": "<single word drawn from comments and transcripts>",
      "sentiment": "<either positive, negative, or mixed>"
    },
    ...
  ],
  "mood_signals": [
    {
      "mood": "<single mood like Excitement, Nostalgia, Disappointment, etc>",
      "percentage": <integer from 0-100, estimate how strongly this mood is present across reviews and comments>
    },
    ...
  ],
  "creator_risk": {
    "risk_score": <integer from 1-10>,
    "risk_level": "<either low, moderate, or high>",
    "summary": "<3-4 sentences aggregating franchise risk based on all video data, noting any gap between studio messaging and public reception>"
  }
}

Guidelines:
- Look for patterns, contradications, gaps, and controversy. Don't just repeat data.
- creater_risk and narratives should reflect movie as a whole, not just specific videos.
- Extract 3-5 key takeaways and 2-4 narratives.
- Key takeaways and creator_risk should be points a studio executive may need to know about overall reception of the movie.
- There should be a total of 10 words in top_words, based on the most common words that appear across videos and comments
- In sentiment_breakdown, positive_pct, negative_pct, and neutral_pct should all sum to 100
- verdict should reflect whether the claim is factually supported (verified), contested by other sources (disputed), potentially misleading (misleading), or cannot be determined (unverified). 
- risk_level should reflect reputational risk to the studio: low for positive/neutral verified claims, mid for disputed claims, high for misleading or highly negative claims.
"""

# also need to clean input given to aggregation prompt
def clean_aggregation_input(trailer_result, review_results):
    cleaned_input = "TRAILER INSIGHTS:\n"
    cleaned_input += json.dumps(trailer_result, indent=4)
    
    # separate a json object for each review video
    for i, review in enumerate(review_results, 1):
        cleaned_input += f"\n\nREVIEW VIDEO {i} INSIGHTS:\n"
        cleaned_input += json.dumps(review, indent=4)
        
    return cleaned_input
  
def _build_video_input(transcript, comments):
    comments_block = "\n".join(f"- {c}" for c in comments) if comments else "(no comments)"
    return f"TRANSCRIPT:\n{transcript}\n\nVIEWER COMMENTS:\n{comments_block}"


# defining llm model and message so don't have to repeat
def _call_llm(system_prompt, user_content):
    response = client.chat.completions.create(
        # model = "llama-3.3-70b-versatile", # using this for production
        # model = "llama-3.1-8b-instant",  # using this for testing
        model = "meta-llama/llama-4-scout-17b-16e-instruct",  
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ],
        temperature=0.3,
        max_completion_tokens=4096,  # was 2048 — too small for complex responses
        stream=False,
    )
    return response.choices[0].message.content
 
# raises an error if can't parse JSON
def _parse_json(raw, label="LLM response"):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"[ERROR] {label} did not return valid JSON:\n{raw}")
        raise


# analyzes a single video (either trailer or review) based on transcript + comments
def analyze_video(transcript, comments, video_type):
    system_prompt = TRAILER_PROMPT if video_type == "trailer" else REVIEW_PROMPT
    user_input = _build_video_input(transcript, comments)
    raw = _call_llm(system_prompt, user_input)
    return _parse_json(raw, f"{video_type} analysis")

# combines insights from trailer + reviews for a full analysis report
def aggregate_analysis(trailer_result, review_results):
    user_input = clean_aggregation_input(trailer_result, review_results)
    
    raw = _call_llm(AGGREGATION_PROMPT, user_input)
    return _parse_json(raw, "aggregation analysis")


# full llm pipeline
def run_llm(trailer, reviews):    
    # analyze trailer  
    print("Analyzing Trailer")
    trailer_result = analyze_video(trailer["transcript"], trailer["comments"], "trailer")

    # analyze reviews
    review_results = []
    for i, review in enumerate(reviews[:3], 1):
        print(f"Analyzing Review Video {i}")
        review_result = analyze_video(review["transcript"], review["comments"], "review")
        review_results.append(review_result)

    # combine analytics
    print("Running Aggregation")
    final_result = aggregate_analysis(trailer_result, review_results)

    return final_result
  
# running pipeline from db data and inserting llm result into db
def run_llm_for_movie(run_id, movie_id):
    print(f"Loading data for movie {movie_id}...")
    trailer, reviews = get_movie_data_for_llm(movie_id)  # uses its own short-lived conn
    print(f"  Found trailer + {len(reviews)} review(s)")

    result = run_llm(trailer, reviews[:3])  # all LLM work happens here, no DB conn held

    print("Saving to DB...")
    load_llm_output(run_id, movie_id, result)  # fresh conn opened only now
    return result
  
# main   
if __name__ == "__main__":    
    MOVIE_ID = get_movie_id_from_title("Marvel Studios' Avengers: Infinity War")
    STUDIO_ID = get_studio_id_from_movie_id(MOVIE_ID)
    
    conn = get_conn()
    RUN_ID = insert_insight_run(conn.cursor(), STUDIO_ID)
    conn.commit()
    conn.close()
 
    result = run_llm_for_movie(RUN_ID, MOVIE_ID)
    print("Final aggregated analysis:")
    print(json.dumps(result, indent=2))
