import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

client = Groq(api_key=API_KEY)

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
    "risk_level": "<one of: low, moderate, high>",
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
def clean_video_input(transcript, comments):
    for c in comments:
        formatter = "\n- "
        cleaned_comments = formatter.join(c)

    cleaned_input = f"""
    VIDEO TRANSCRIPT:
    {transcript}

    VIEWER COMMENTS:
    {cleaned_comments}
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

# analyzes a single video (either trailer or review) based on transcript + comments
def analyze_video(transcript, comments, video_type):
    if video_type == "trailer":
        system_prompt = TRAILER_PROMPT
    else: 
        system_prompt = REVIEW_PROMPT
        
    user_input = clean_video_input(transcript, comments)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",    # alt: llama-3.1-8b-instant
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.4,
        max_completion_tokens=2048,
        stream=False
    )

    raw_response = response.choices[0].message.content
    return raw_response # <---- may need to change when integrating to postgresql db

# combines insights from trailer + reviews for a full analysis report
def aggregate_analysis(trailer_result, review_results):
    user_input = clean_aggregation_input(trailer_result, review_results)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",    # alt: llama-3.1-8b-instant
        messages=[
            {"role": "system", "content": AGGREGATION_PROMPT},
            {"role": "user", "content": user_input}
        ],
        temperature=0.3,
        max_completion_tokens=2048,
        stream=False
    )

    raw_response = response.choices[0].message.content
    return raw_response # <---- may need to change when integrating to postgresql db

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


if __name__ == "__main__":
    trailer = {
        "transcript": "The world is changing. The world is changing. God, it seems like a thousand years ago, I fought my way out of that cave, became Iron Man, became Iron Man, realized I loved you. realized I loved you. realized I loved you. I know I said no more surprises, but I was really hoping to pull off one last one. but I was really hoping to pull off one last one. but I was really hoping to pull off one last one. The world has changed. None of us can go back. All we can do is our best. And sometimes the best that we can do... is to start over. I still hold these people to die. I keep telling everybody they should move on Some do And not us Even if there a small chance we owe this to everyone who's not in this room to try. We will. Whatever it takes. Whatever it takes. Whatever it takes. Whatever it takes. I like this one.",
        "comments": [
            "Back when Marvel had us by the throat with just a logo and a heartbeat sound. MCU was never the same after Endgame.",
            "I really miss this movie so much. That time when I watched this movie on theatres with full of people and the crowd went crazy during epic fights.",
            "THE CHILLS, THE HYPE, THE NOSTALGIA, THE CINEMA AUDIENCE, THIS MOVIE WAS TRULY A ONCE IN A LIFETIME EXPERIENCE."
        ]
    }

    reviews = [
      {
        "transcript": """Hey everyone, welcome back to the channel.
Today I want to talk about Avengers: Endgame — not just as a superhero movie, but as one of the most ambitious franchise finales ever attempted.

Coming off the emotional devastation of Infinity War, Endgame opens in a surprisingly quiet place. Instead of jumping straight into spectacle, the movie leans into grief, guilt, and the weight of failure. The surviving Avengers are scattered, emotionally exhausted, and for the first time in this series, genuinely unsure if being heroes is even enough anymore.

That opening tone is one of the film's smartest creative decisions. It immediately tells the audience that this isn't just another team-up movie. This is a story about consequences.

The first act is deliberately slow, and honestly, that's going to divide people. We spend a lot of time watching characters try to move on with their lives. Steve is running support groups. Natasha is barely holding the team together. Thor has completely collapsed under the weight of what he believes is his personal failure. For a blockbuster of this size, it's surprisingly introspective.

But that emotional groundwork is essential, because once the time-heist concept is introduced, the movie becomes something very different.

Rather than trying to top the cosmic scale of the previous film, Endgame turns inward. The plot is basically built around revisiting key moments from earlier movies, and that choice is extremely intentional. This is a celebration of everything the franchise has been building for over a decade. It rewards long-time viewers without fully locking out casual audiences.

What really stands out here is how character-driven the time travel sequences are. Each stop isn't just fan service. It's designed to resolve something emotionally unfinished for the characters involved. Tony confronting his father. Steve finally facing the life he gave up. Thor rediscovering what it actually means to be worthy. These moments carry more narrative weight than the mechanics of time travel itself.

And yes, the time travel rules are messy. The movie doesn't pretend to be hard science fiction. But the emotional logic is consistent, and that matters far more for a story like this.

Robert Downey Jr.'s performance as Tony Stark is easily one of the strongest parts of the film. Tony is no longer the reckless genius trying to prove himself. He's a father now. His motivation isn't saving the universe — it's protecting the small, fragile life he's finally built. That internal conflict gives real stakes to every decision he makes.

Chris Evans also delivers one of his most grounded performances as Steve Rogers. Steve's entire arc has always been about sacrifice. In this film, that idea is finally challenged. Instead of asking what he owes the world, the story asks what he owes himself.

The emotional climax of the movie doesn't come from an explosion or a punch. It comes from a choice.

And then, of course, there's the final battle.

This is pure cinematic spectacle. Portals opening across the battlefield. Heroes arriving from every corner of the franchise. The moment is designed to overwhelm you, and it absolutely succeeds. It's loud, chaotic, and unapologetically celebratory.

But what makes the battle work isn't just how big it is — it's how clearly it reflects the themes of the entire saga. The Avengers don't win because they're stronger. They win because they're finally united again, after years of division, trauma, and loss.

Thanos, as a villain, is slightly less nuanced here than in Infinity War. He's more of a traditional antagonist — focused on domination rather than philosophical justification. But that shift actually fits the story. In this film, the real conflict isn't ideological. It's personal. This is about undoing pain, not debating destiny.

One of the most powerful choices the movie makes is refusing to completely erase what was lost. Even after the snap is reversed, the emotional damage remains. People have lived with grief. Relationships have changed. Time has passed. The movie understands that you can't simply rewind trauma.

Tony's final act is not framed as heroism in the traditional sense. It's framed as acceptance. He finally stops trying to outthink every problem and instead makes the one decision that only he can make. The moment lands because the entire franchise has been quietly building toward it.

Steve's ending, on the other hand, is about something the series rarely allows its heroes: peace. After years of being defined by duty, he chooses a life for himself. It's not flashy, but it's deeply earned.

Ultimately, Avengers: Endgame works because it understands exactly what it is. It is a payoff film — and it embraces that responsibility completely.""",
        "comments": [
            "This was actually one of the best breakdowns of Endgame I've heard.",
            "Hot take but I still think the time travel stuff was way too convenient.",
            "Thor's arc in this movie is super underrated.",
            "This feels more like a film analysis than a hype review.",
            "This honestly feels like how Marvel should've ended things permanently."
        ]
      }
    ]

    result = run_llm(trailer, reviews)
    print("Final Aggregated Analysis:")
    print(result)
