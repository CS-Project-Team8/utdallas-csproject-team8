import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from db_routes import load_llm_output, get_movie_data_for_llm

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

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
      "claim": "<specific statement or message made by the trailer>",
      "source": "<either transcript or comment>",
      "sentiment": "<either positive, negative, or neutral>"       
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
"""

REVIEW_PROMPT = """
You are an expert movie analyst that specializes in intelligence from movie studios and streaming companies. You will be given data 
from a movie review video posted by an independent YouTube reviewer channel. This channel and its video are not associated with an
official movie studio and represent authentic public reaction of a movie or studio. This data will be in the form of the video transcript
and comments. Your job is to analyze this content and return a structured JSON object with insights. Do not return anything else. 
Do not include any explanation or text outside of the JSON object. If a field cannot be determined from the provided data, use null.

You must return the following JSON structure exactly:

{
  "movie": "<name of the specific movie being discussed>",
  "video_type": "review",
  "key_takeaways": [
    "<concise string about main topics from the review regarding the movie>",
    ...
  ],
  "claims": [
    {
      "claim": "<specific factual or opinion statement made by the reviewer or commenters>",
      "source": "<either transcript or comment>",
      "sentiment": "<either positive, negative, or neutral>"
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
    "summary": "<1-2 sentences describing the overall tone of the reviewer>"
  },
  "top_words": [
    {
      "word": "<single word drawn from transcripts>",
      "sentiment": "<either positive, negative, or mixed>",
      "count": <integer of how often the word appears>
    },
    ...
  ],
  "mood_signals": [
    {
      "mood": "<single mood like Excitement, Nostalgia, Disappointment, etc>",
      "percentage": <integer from 0-100, estimate how strongly this mood is present across reviews>
    },
    ...
  ],
  "creator_risk": {
    "risk_score": <integer from 1-10>,
    "risk_level": "<either low, moderate, or high>",
    "summary": "<2-3 sentences about what this reviewer's reception suggests about franchise or content strategy risk>"
  }
}

Guidelines:
- Claims are a factual statement made in the trailer. Narratives are high-level stories or themes connected by multiple claims.
- Focus claims on what the reviewer is actually saying about the film. Focus on their thoughts, feelings, and voice.
- Extract 3-5 key takeaways, 4-6 claims, and 1-3 narratives.
- Extract exactly 5 moods for mood_signals, each scored individually.
- Key takeaways should be points a studio executive may need to know about public reaction to the movie.
- There should be a total of 10 expressive words in top_words, taken directly from the most common sentiment words in the transcript
"""

COMMENTS_PROMPT = """
You are an expert movie analyst that specializes in intelligence from movie studios and streaming companies. You will be given data
in the form of the JSON object with a YouTube video's transcript analysis and the comments on that video. These comments are not associated 
with an official movie studio and represent authentic public reaction of a movie or studio that the YouTube video is about. Your job is to 
analyze this content and return a structured JSON object with insights. Do not return anything else. Do not include any explanation or text 
outside of the JSON object. If a field cannot be determined from the provided data, use null.

You must return the following JSON structure exactly:

{
  "movie": "<name of the specific movie being discussed>",
  "claims": [
    {
      "claim": "<specific factual or opinion statement made by the comments>",
      "sentiment": "<either positive, negative, or neutral>"
    },
    ...
  ],
  "sentiment_breakdown": {
    "overall_sentiment": "<either positive, negative, or mixed>",
    "average_sentiment_score": <number between -1.0 and 1.0>,
    "positive_pct": <integer from 0-100>,
    "negative_pct": <integer from 0-100>,
    "neutral_pct": <integer from 0-100>,
    "summary": "<1-2 sentences describing the audience reaction to this video>"
  },
  "top_words": [
    {
      "word": "<single impactful word used in the comments>",
      "sentiment": "<either positive, negative, or mixed>"
    },
    ...
  ],
  "mood_signals": [
    {
      "mood": "<single mood like Excitement, Nostalgia, Disappointment, etc>",
      "percentage": <integer from 0-100, estimating how strongly this mood is present in the comments>
    },
    ...
  ],
  "agreeability": "<either mostly_agrees, mostly_disagrees, mixed>",
  "video_alignment": "<2-3 sentences describing where the audience aligns with the reviewer's opinion>"
}

Guidelines:
- Focus on the comments' reactions. Highlight if they are agreeing/disagreeing with the review or adding their own opinion.
- Extract 3-5 claims from the comments.
- There should be a total of 10 expressive words in top_words, taken directly from the most common sentiment words in the transcript and comments
- Extract exactly 5 moods for mood_signals, each scored individually.
- In sentiment_breakdown, positive_pct, negative_pct, and neutral_pct should all sum to 100.
"""

VIDEO_PROMPT = """
You are an expert movie analyst that specializes in intelligence from movie studios and streaming companies. You will be given two JSON
analysis objects for a single YouTube video: a Transcript Analysis that focuses on what the video creator has said, and a Comments
Analysis that focuses on how the audience reacted to the video. Your job is to combine these into a single unified report. Do not return
anything else. Do not include any explanation or text outside of the JSON object. If a field cannot be determined from the provided data, 
use null.

You must return the following JSON structure exactly:

{
  "movie": "<name of the specific movie>",
  "video_type": "<trailer or review>",
  "key_takeaways": [
    "<concise insight synthesized from both the video and audience reaction>",
    ...
  ],
  "claims": [
    {
      "claim": "<specific factual or opinion statement made by the transcript and comments>",
      "source": "<transcript or comment>",
      "sentiment": "<either positive, negative, or mixed>"
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
    "summary": "<1-2 sentences describing the overall tone of the reviewer>"
  },
  "top_words": [
    {
      "word": "<single impactful word from transcript or comments>",
      "sentiment": "<either positive, negative, or mixed>"
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
- Synthesize both sources, highlighting where the video and audience agree or disagree.
- Extract 3-6 key takeaways, 4-8 combined claims, and 2-4 narratives.
- audience_vs_video captures the difference between the video's message and public reaction.
- There should be a total of 10 expressive words in top_words, taken directly from the most common sentiment words in the transcript and comments
- Extract exactly 5 moods for mood_signals, each scored individually.
- In sentiment_breakdown, positive_pct, negative_pct, and neutral_pct should all sum to 100.
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
"""

# clean up input given by user to make it easier for llm to understand
def clean_comments_input(transcript, comments):
    # for c in comments:
    #     formatter = "\n- "
    #     cleaned_comments = formatter.join(c)
    cleaned_comments = "\n- " + "\n- ".join(comments)
    
    cleaned_input = f"""
    VIDEO TRANSCRIPT ANALYSIS:
    {json.dumps(transcript, indent=2)}

    VIEWER COMMENTS:
    {cleaned_comments}
    """
    
    return cleaned_input

def clean_video_input(transcript, comments):
    cleaned_input = f"""
    TRANSCRIPT ANALYSIS:
    {json.dumps(transcript, indent=2)}

    COMMENTS ANALYSIS:
    {json.dumps(comments, indent=2)}
    """
    
    return cleaned_input

# also need to clean input given to aggregation prompt
def clean_aggregation_input(trailer_result, review_results):
    cleaned_input = "TRAILER INSIGHTS:\n"
    cleaned_input += json.dumps(trailer_result, indent=4)
    
    # separate a json object for each review video
    for i, review in enumerate(review_results, 1):
        cleaned_input += f"\n\nREVIEW VIDEO {i} INSIGHTS:\n"
        cleaned_input += json.dumps(review, indent=4)
        
    return cleaned_input

# defining llm model and message so don't have to repeat
def _call_llm(system_prompt, user_content):
    response = client.chat.completions.create(
        # model="openai/gpt-oss-120b",
        model = "llama-3.3-70b-versatile", # changed the model to handle more requests
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

# analyze transcript only (trailer or review)
def analyze_transcript(transcript, video_type):
    if video_type == "trailer":
        system_prompt = TRAILER_PROMPT
    else:
        system_prompt = REVIEW_PROMPT

    return _call_llm(system_prompt, transcript)
    # response = client.chat.completions.create(
    #     model="openai/gpt-oss-120b",
    #     messages=[
    #         {"role": "system", "content": system_prompt},
    #         {"role": "user", "content": transcript}
    #     ],
    #     temperature=0.3,
    #     max_completion_tokens=2048,
    #     stream=False
    # )

    # return response.choices[0].message.content

# analyze comments for a video transcript
def analyze_comments(transcript_result, comments):
    user_input = clean_comments_input(transcript_result, comments)

    return _call_llm(COMMENTS_PROMPT, user_input)
    # response = client.chat.completions.create(
    #     model="openai/gpt-oss-120b",
    #     messages=[
    #         {"role": "system", "content": COMMENTS_PROMPT},
    #         {"role": "user", "content": user_input}
    #     ],
    #     temperature=0.3,
    #     max_completion_tokens=2048,
    #     stream=False
    # )

    # return response.choices[0].message.content

# analyzes a single video (either trailer or review) based on transcript + comments
def analyze_video(transcript, comments, video_type):
    transcript_result_raw = analyze_transcript(transcript, video_type)
    transcript_result = _parse_json(transcript_result_raw, "transcript analysis")
    
    
    comments_result_raw = analyze_comments(transcript_result, comments)
    comments_result = _parse_json(comments_result_raw, "comments_analysis")

    user_input = clean_video_input(transcript_result, comments_result)
    raw = _call_llm(VIDEO_PROMPT, user_input)
    
    return _parse_json(raw, "video analysis")

    # response = client.chat.completions.create(
    #     model="openai/gpt-oss-120b",
    #     messages=[
    #         {"role": "system", "content": VIDEO_PROMPT},
    #         {"role": "user", "content": user_input}
    #     ],
    #     temperature=0.3,
    #     max_completion_tokens=2048,
    #     stream=False
    # )

    # raw_response = response.choices[0].message.content
    # return raw_response # <---- may need to change when integrating to postgresql db

# combines insights from trailer + reviews for a full analysis report
def aggregate_analysis(trailer_result, review_results):
    user_input = clean_aggregation_input(trailer_result, review_results)
    
    raw = _call_llm(AGGREGATION_PROMPT, user_input)
    return _parse_json(raw, "aggregation analysis")

    # response = client.chat.completions.create(
    #     model="openai/gpt-oss-120b",
    #     messages=[
    #         {"role": "system", "content": AGGREGATION_PROMPT},
    #         {"role": "user", "content": user_input}
    #     ],
    #     temperature=0.3,
    #     max_completion_tokens=2048,
    #     stream=False
    # )

    # raw_response = response.choices[0].message.content
    # return raw_response # <---- may need to change when integrating to postgresql db


# full llm pipeline
# NOTE: do we want to save each analysis to DB for later use? if so we need to modify this
def run_llm(trailer, reviews):    
    # analyze trailer  
    print("Analyzing Trailer")
    trailer_result = analyze_video(trailer["transcript"], trailer["comments"], "trailer")

    # analyze reviews
    review_results = []
    for i, review in enumerate(reviews, 1):
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
    trailer, reviews = get_movie_data_for_llm(movie_id)
    print(f"  Found trailer + {len(reviews)} review(s)")
 
    result = run_llm(trailer, reviews)
 
    print("Saving to DB...")
    load_llm_output(run_id, movie_id, result)
    return result
  
# main   
if __name__ == "__main__":
    RUN_ID   = "26d2d07a-9dcd-4777-acf0-e338251b039b"
    MOVIE_ID = "94c045de-0426-423f-b22a-fd13c9c0e23c"
 
    result = run_llm_for_movie(RUN_ID, MOVIE_ID)
    print("Final aggregated analysis:")
    print(json.dumps(result, indent=2))
 
# if __name__ == "__main__":
#   RUN_ID = "b3e214fa-475f-49b5-8743-dd2fee36aee4"
#   MOVIE_ID = "4fc3ba49-a378-41f2-aa02-41bbb0136ffd"
  
#   trailer = {
#     "transcript": "There was an idea. To bring together a group of remarkable people. To see if we could become something more. So when they needed us, we could fight the battles. That they never could. could. In time, you will know what it's like to lose. To feel so desperately that you're right, yet to fail all the same. Dread it. Run from it. Destiny still arrives Evacuate the city. Engage all defenses. And get this man a shield. Fun isn't something one considers when balancing the universe. But this... does put a smile on my face. Who the hell are you guys?",
#     "comments": [
#       "I love this movie, a LOT. But being honest, Infinity War is still the best Avengers movie so far, the best MCU movie, is Winter Soldier.",
#       "I wonder if the Doomsday trailer would match the level of infinity war...",
#       "The fact that they showed Thanos actually winning in the trailer told me this was going to be different.",
#       "I've never felt dread watching a Marvel trailer before. This one actually scared me.",
#       "Thanos throwing a moon at Iron Man is the most unhinged thing I've ever seen in a superhero movie.",
#       "The shot of all the heroes in Wakanda gave me chills I still haven't recovered from.",
#       "Marvel really said let's make the villain the main character and it worked perfectly.",
#       "This trailer made me realize how long we've been waiting for this moment.",
#       "The Children of Thanos look terrifying. Finally some real threats in this universe.",
#       "I watched this trailer like 30 times the day it dropped.",
#       "The music choice here is so different from every other Marvel trailer. It feels massive.",
#       "Tony's face when he realizes how outmatched they are is the best acting in any Marvel trailer.",
#       "We really thought they were all going to make it out okay. We were so naive.",
#       "The way they hid so much of the actual plot and still made it the most hyped movie ever is insane.",
#       "Cap showing up in Wakanda with a beard after two years felt like seeing an old friend.",
#       "Thanos actually feeling like a real character in this trailer and not just a CGI villain was unexpected.",
#       "This is the trailer that made me go back and rewatch every single Marvel movie before release."
#     ]
#   }

#   reviews = [
#       {
#       "transcript": """Hey everyone, welcome back to the channel.

#   Today we're talking about Avengers: Infinity War, and I want to be upfront — I've seen this movie twice now, and I still don't fully know how to process it.

#   Let me start with what makes this film unlike anything Marvel has done before. This is not an Avengers movie in the traditional sense. This is a Thanos movie. He is the protagonist. He has the clearest arc, the most screen time, and the most compelling motivation of anyone in the film. That is an extraordinary creative decision for a franchise that has spent ten years building toward this moment, and it almost entirely pays off.

#   Josh Brolin's performance as Thanos is the backbone of this entire film. What could have been a generic world-ending villain is instead a character who genuinely believes he is saving the universe. His logic is flawed and horrifying, but it is internally consistent. When he talks about balance and sacrifice, you understand where he's coming from even as you completely reject it. That moral complexity is rare in blockbuster filmmaking.

#   The film's structure is genuinely unusual. Rather than building toward a climax where the heroes win, Infinity War spends its entire runtime dismantling them. Every time the Avengers get close to stopping Thanos, something goes wrong. Someone makes an emotional decision over a tactical one. And the movie never punishes those decisions in a cheap way — it treats them as tragic but human.

#   The Guardians of the Galaxy integration is one of the best things about this film. Putting Thor with the Guardians is comedic genius, but it also gives Thor some of his best character work in the entire franchise. His grief over Asgard, over his brother, over everything he's lost — it gives the humor real weight.

#   Wakanda as the setting for the final battle was a smart choice. It grounds the cosmic scale of the conflict in something tactile and real. The battle itself is spectacular, though I'll admit it sometimes becomes difficult to track amid so many characters and so much action.

#   Doctor Strange's decision to give up the Time Stone is the scene I keep coming back to. He tells Tony it was the only way, and in the moment it feels like a betrayal. But knowing what comes next, it reframes everything. That single line carries the entire weight of the sequel on its back.

#   And then there's the ending.

#   I don't think any mainstream blockbuster has ever ended the way Infinity War ends. Heroes turning to dust one by one. No reversal. No last minute save. Just loss. The theater I was in was completely silent for the entire credits sequence. People didn't know how to react because nothing had prepared them for a Marvel movie to end with the villain winning.

#   Spider-Man's scene is devastating in a way that still gets me. Unlike the others who simply fade, he's scared. He knows what's happening and he doesn't want to go. It's the most human moment in the film.

#   My criticisms are few but worth noting. Some of the smaller character groupings feel rushed — there are so many moving parts that certain storylines don't get the breathing room they deserve. The film also leans heavily on prior knowledge of all the characters, which is part of the design but can make it feel dense to anyone who hasn't kept up.

#   But those are minor complaints against something genuinely ambitious. Infinity War is a film that trusts its audience to handle darkness and ambiguity. It doesn't reassure you that everything will be okay. It sits with failure, grief, and consequence in a way that superhero films almost never do.

#   It's not a complete story — it was never designed to be. But as the first half of something much larger, it is one of the most confident and emotionally devastating blockbusters ever made.

#   Thanks for watching. Let me know in the comments whether you think Thanos was right.""",

#       "comments": [
#           "The silence in my theater after the snap was the most surreal movie experience I've ever had.",
#           "Thanos is genuinely one of the best written villains in any superhero movie ever made.",
#           "You're right that this is basically a Thanos movie and I think that's exactly why it works.",
#           "Spider-Man's scene destroyed me. I was not prepared for that at all.",
#           "The Doctor Strange line at the end recontextualized the entire movie for me on rewatch.",
#           "I think the Wakanda battle is slightly overlong but everything before it is perfect.",
#           "Thor's arc in this movie is massively underappreciated. He loses everything and still shows up.",
#           "The fact that the villain actually wins is still something I don't think Marvel will ever top.",
#           "Gamora's death hit harder than most of the snap deaths for me. That scene was brutal.",
#           "I disagree that some storylines felt rushed — I thought the pacing was actually impressive given how many characters are in this.",
#           "The Guardians and Thor scenes are so funny but then you remember what's at stake and it hits different.",
#           "Best MCU movie for me personally. Nothing else comes close to what this film was willing to do.",
#           "Strange giving up the stone felt like a betrayal the first time. Second viewing completely changed how I saw it.",
#           "The ending still makes me angry in the best way possible. They really just let the villain win.",
#           "This review nailed the Thanos analysis. Most people reduce him to just a big purple guy but he's way more than that."
#       ]
#     }
#   ]

#   raw_result = run_llm(trailer, reviews)
#   print("Final Aggregated Analysis:")
#   print(raw_result)

#   try:
#       result = json.loads(raw_result)
#   except json.JSONDecodeError:
#       print("LLM did not return valid JSON:")
#       print(raw_result)
#       exit(1)

#   print("Saving to DB")
#   load_llm_output(RUN_ID, MOVIE_ID, result)