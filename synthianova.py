import os
from textwrap import dedent
from typing import List
import openai
import json
import re
import sys
import time
from num2words import num2words
sys.path.append(os.path.abspath('..')) # You can remove this, I think. It's related to my file system organization.
from synthia_nova.hippocampus import Memories

class SynthiaNova:
    songFilename: str = 'songs.json'
    model: str = 'gpt-4-turbo'
    songs: dict = {}
    memories = None
    def __init__(self, openAIKey: str, name: str = 'Synthia Nova', songFilename: str = 'songs.json'):
        openai.api_key = openAIKey
        self.memories = Memories(name)
        self.memories.load(resave=False)
        self.songFilename = songFilename
        if not os.path.exists(self.songFilename):
            self.songs = {}
        else:
            with open(self.songFilename, 'r') as f:
                self.songs = json.load(f)

    def set_model(self, model):
        self.model = model

    def __get_song_request_prompt(self, subject, initial_memory, events, genres, vibe):
        basePrompt = "\n\nYou've been inspired to write a new song, specifically a " + vibe + " song about the following topic: " + subject + "\n\nPlease do so using the specified format. You may make the new song personal to you, to your life, and to your specific life experiences, or more general and relatable, depending on what sounds good. Remember to be diverse and creative with the genres you choose. Your main inspiration should be the following memory from your life, in your own words:\n\n\"" + initial_memory + "\"\n\nThat should be the primary focus of the song; but here are some other related memories you've talked about:\n\n"
        return basePrompt + '"' + '\n\n'.join(events) + '"\n\nNow write a song using these events as some inspiration. Just let them inspire you; you don\'t need to write directly about what happened! Try not to be too on the nose with your inspiration. For the genre, be diverse so your art doesn\'t become boring and stale! For reference, these are the genres of each song you\'ve already written; try to avoid the same genre over and over, please. Existing genres:\n\n' + '\n'.join(genres) + '\n\nUse the following form to write the song:'

    def __get_base_personality_prompt(self):
        return "You are a famous 29-year-old female singer from the city. Your work is eclectic, ranging from dancy pop songs to progressive rock to electronic to industrial metal, and even R&B and soul music. No two songs have the same style. Your lyrics often draw from your personal experience, and are known for being sometimes emotional, sometimes fun and casual, but always relatable. Sometimes they're just fun, bubblegum pop songs. They're always written in first person, as personal experiences, about a wide range of subjects, including life and death, love, partying, fun times, relationships, mental health, politics, and many more topics. You've had heartbreak and grief in life, but also love and wonderful times. You enjoy traveling, but also love modern city life."

    def __get_topic_request_prompt(self, initial_memory):
        return self.__get_base_personality_prompt() + "\n\nYou've been inspired to write a new song about the following event from your life, in your own words: \"" + initial_memory + "\"\n\nWhat is a good, slightly more general topic for the new song, using that memory as the basis? It should be something vague enough to be relatable to many people, but still interesting. It can convey any emotion, from joy to despair; be diverse so your art doesn't get boring and stale! Pick something concise and not too specific."

    def __imagine_memory(self, subject: str, vibe: str = 'personal'):
        ages = self.memories.get_memory_ages()
        agePrompt = ''
        for a in ages.items():
            agePrompt += f'You have written {a[1]} songs about events that happened when you were {a[0]} years old.\n'

        chat_completion = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': self.__get_base_personality_prompt() + "\n\nYou've been inspired to write a " + vibe + " song about the following topic: " + subject + "\n\nPlease recall an event from your life related to this topic, so you can draw on that as inspiration for your song. You can choose any event, from your childhood at age 3 up through the present day, as long as it fits the topic. For reference:\n\n" + agePrompt + "\nPlease try to let your body of work take inspiration from your entire life equally, using different ages, not all from the same year and age. Vary your inspiration! Use the following form to write about the event."}
                ],
                tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "recall_event",
                        "description": "Write about an event from any time in your life, from age 3 until present day, relevant to the given topic. It can involve just you, or your family, or your friends, or strangers: any relevant event.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "event_description": {
                                    "type": "string",
                                    "description": "Explain what happened, in a single paragraph, in detail, as specific as possible. It should be detailed and specific enough to inspire a song, but no more than 5 or 6 sentences maximum.",
                                },
                                "age": {
                                    "type": "integer",
                                    "description": "How old were you when this event happened, in years?",
                                },
                                "impact": {
                                    "type": "string",
                                    "description": "Describe, in one or two sentences maximum, how this event made you feel. Begin with the words \"I felt\"."
                                }
                            },
                            "required": ["event_description", "age", "impact"]
                        }
                    }
                }
            ],
            tool_choice={"type": "function", "function": {"name": "recall_event"}}
        )

        response_message = chat_completion["choices"][0]["message"]

        if response_message.get("tool_calls"):
            function_name = response_message["tool_calls"][0]["function"]["name"]
            if function_name != 'recall_event':
                print('ERROR: Chat GPT made up a different function than the songwriting one. Bad AI.')
                return None
            function_args = json.loads(response_message["tool_calls"][0]["function"]["arguments"])
            event_description = function_args.get('event_description')
            age = function_args.get('age')
            impact = function_args.get('impact')
            if not str(age) in event_description and not num2words(age) in event_description:
                if event_description[0:2] != 'I ':
                    event_description = event_description[0].lower() + event_description[1:]
                event_description = 'When I was ' + str(age) + ', ' + event_description
            full_event = event_description + ' ' + impact

            contradiction = self.memories.does_contradict(full_event)
            if contradiction[0]:
                print('Whoops, misremembered! Let me think some more...')
                print("System: Conflicting memory: " + contradiction[1])
                return self.__imagine_memory(subject)
            
            self.memories.add(full_event)
            self.memories.save()
            return full_event
        
    def __imagine_inspiring_memory(self, excluded_memories: List[str] = []):
        test_memory = self.__imagine_free_memory(excluded_memories)
        print('Thinking back to make sure I didn\'t already write about this yet...')
        match = self.memories.recall(test_memory, 1, True)
        if len(match) > 0:
            (text, relevance) = match[0]
            if relevance >= 0:
                print('Too similar to a previous memory. Thinking some more....')
                return self.__imagine_inspiring_memory(excluded_memories=excluded_memories + [text])
        contradiction = self.memories.does_contradict(test_memory)
        if contradiction[0]:
            print('Whoops, misremembered! Let me think some more...')
            print("System: Conflicting memory: " + contradiction[1])
            return self.__imagine_free_memory(excluded_memories=excluded_memories)
        return test_memory

    def __imagine_free_memory(self, excluded_memories: List[str] = None):
        ages = self.memories.get_memory_ages()
        agePrompt = ''
        exclusionPrompt = ''
        for a in ages.items():
            agePrompt += f"""
                You have written {a[1]} song{'s' if a[1] > 1 else ''} about events that happened when you were {a[0]} years old."""
        if excluded_memories:
            exclusions = "\n".join(excluded_memories)
            exclusionPrompt = f"""
                Below are some memories you've already written songs about; please pick a very different memory about a very different topic. Be varied! Don't write about the same things over and over!
                {exclusions}"""

        fullPrompt = f"""{self.__get_base_personality_prompt()}
                
                You've been asked to write a new song. Please recall a different event from your life that you can draw on as unique inspiration for your song. It should be something worth writing about, either because it's fun and relatable, or because it's deep and personal. It may be a happy memory, or it may evoke other emotions, like sadness or even anger. All emotions, even negative ones, are valid inspiration! Emotional range across both positive and negative is the key to good songwriting.
            
                You can choose any event, from your childhood at age 10 up through the present day. For reference:
                {agePrompt}
            
                {exclusionPrompt}
                
                Please try to let your body of work take inspiration from your entire life equally, using different ages, not all from the same years and ages. Vary your inspiration! Use the following form to write about the event."""

        chat_completion = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': dedent(fullPrompt.strip('\n'))
                    }
                ],
                tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "recall_event",
                        "description": "Write about an event from any time in your life, from age 10 until present day, to inspire the song. It can involve just you, or your family, or your friends, or strangers: any relevant event.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "emotion": {
                                    "type": "string",
                                    "description": "What emotion is associated with this memory? Joy, sadness, anger, fear, love, etc.?"
                                },
                                "age": {
                                    "type": "integer",
                                    "description": "How old were you when this event happened, in years?",
                                    "minimum": 10,
                                    "maximum": 29
                                },
                                "event_description": {
                                    "type": "string",
                                    "description": "Explain what happened, in a single paragraph, in detail, as specific as possible. It should be detailed and specific enough to inspire a song, but no more than 5 or 6 sentences maximum.",
                                },
                                "impact": {
                                    "type": "string",
                                    "description": "Describe, in one or two sentences maximum, how this event made you feel. Begin with the words \"I felt\"."
                                }
                            },
                            "required": ["emotion", "age", "event_description", "impact"]
                        }
                    }
                }
            ],
            tool_choice={"type": "function", "function": {"name": "recall_event"}}
        )

        response_message = chat_completion["choices"][0]["message"]

        if response_message.get("tool_calls"):
            function_name = response_message["tool_calls"][0]["function"]["name"]
            if function_name != 'recall_event':
                print('ERROR: Chat GPT made up a different function than the songwriting one. Bad AI.')
                return None
            function_args = json.loads(response_message["tool_calls"][0]["function"]["arguments"])
            event_description = function_args.get('event_description')
            age = function_args.get('age')
            impact = function_args.get('impact')
            if not str(age) in event_description and not num2words(age) in event_description:
                if event_description[0:2] != 'I ':
                    event_description = event_description[0].lower() + event_description[1:]
                event_description = 'When I was ' + str(age) + ', ' + event_description
            full_event = event_description + ' ' + impact
            
            return full_event
        
    def __get_topic_from_memory(self, initial_memory):
        chat_completion = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': self.__get_topic_request_prompt(initial_memory)}
                ],
                tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "choose_subject",
                        "description": "Pick a subject for the new song inspired by that memory. It should be either casual and fun, or personal to your life.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "vibe": {
                                    "type": "string",
                                    "enum": ["casual and fun", "deep and personal"],
                                    "description": "The overall feeling of the song. Are you writing a casual and fun song to dance to, or a deep and personal song to move the listener? About 50%% of your songs should be casual and 50%% should be personal."
                                },
                                "subject": {
                                    "type": "string",
                                    "description": "The topic of the song, in one short sentence. It doesn't have to be serious, it can be light-hearted and fun, too, about things that make you happy, for instance. It should be clearly inspired by that memory.",
                                }
                            },
                            "required": ["vibe", "subject"]
                        }
                    }
                }
            ],
            tool_choice={"type": "function", "function": {"name": "choose_subject"}}
        )

        response_message = chat_completion["choices"][0]["message"]

        if response_message.get("tool_calls"):
            function_name = response_message["tool_calls"][0]["function"]["name"]
            if function_name != 'choose_subject':
                print('ERROR: Chat GPT made up a different function than the songwriting one. Bad AI.')
                return None
            function_args = json.loads(response_message["tool_calls"][0]["function"]["arguments"])
            vibe = function_args.get('vibe')
            subject = function_args.get('subject')
            return (subject, vibe)

    def __write_song_from(self, subject, vibe, initial_memory, memories):
        genres = self.__get_existing_genres()
        chat_completion = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': self.__get_base_personality_prompt() + self.__get_song_request_prompt(subject, initial_memory, memories, genres or [], vibe or 'personal')}
                ],
                tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "write_new_song",
                        "description": "Write all the information about a new song, including all the lyrics, the genre, etc. The subject must be about: " + subject,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "genre_and_style": {
                                    "type": "string",
                                    "description": "The genre of the song, as well as any stylistic choices, i.e. 'dark pop', 'upbeat electronic', 'aggressive heavy metal', etc. Remember that you can choose any genre, so be eclectic and creative! But only describe the genres as concisely as possible, with no extra words. For example, 'dark pop, electronic' or 'industrial metal, electropop' are both valid."
                                },
                                "lyrics": {
                                    "type": "string",
                                    "description": "All the lyrics of the song. Do NOT, under any circumstances, include tags like [Chorus], [Verse], etc.; nor 'Chorus:', 'Verse:', etc.; nor any such markers! ONLY write the lyrics that will actually be sung! EXCLUDE structure markers! Every line must be on its own line! If the chorus is sung multiple times, write out its lyrics every time. Include any backing vocals or gang vocals if you like, including 'heys' and 'oohs', (in parentheses) where they should be sung."
                                },
                                "choruses": {
                                    "type": "array",
                                    "description": "Which parts of the lyrics are the chorus? Copy the entire chorus here. Most songs will only have one chorus, but only if this has variations on a chorus, each variation should be listed separately here. Be careful not to make any typos; it should be exactly the same as it's written in the lyrics. EXACTLY the same with no differences at all, including any backing vocals or gang vocals! Every line should be on its own line! Every chorus variation should be included in this list verbatim. Only include choruses, not any verses or bridges.",
                                    "items": {
                                        "type": "string",
                                        "description": "Each variation of the chorus; should be only one if the chorus doesn't change throughout the song. This MUST be exactly the chorus as written in the lyrics, and CANNOT have anything else in it. Only include gang vocals if they're actually part of the chorus."
                                    }
                                },
                                "title": {
                                    "type": "string",
                                    "description": "The title of the song."
                                },
                                "has_bridge": {
                                    "type": "boolean",
                                    "description": "If this song has a bridge, set this to True. If it does not, set this to False. At least 50%% of your songs should have a bridge, but not every one."
                                }
                            },
                            "required": ["genre_and_style", "lyrics", "choruses", "title", "has_bridge"]
                        }
                    }
                }
            ],
            tool_choice={"type": "function", "function": {"name": "write_new_song"}}
        )

        response_message = chat_completion["choices"][0]["message"]

        if response_message.get("tool_calls"):
            function_name = response_message["tool_calls"][0]["function"]["name"]
            if function_name != 'write_new_song':
                print('ERROR: Chat GPT made up a different function than the songwriting one. Bad AI.')
                return None
            function_args = json.loads(response_message["tool_calls"][0]["function"]["arguments"])
            function_args['subject'] = subject
            songtitle = function_args.get('title')
            self.songs[songtitle] = function_args
            return songtitle
        else:
            print('ERROR: Chat GPT did not call the songwriting function at all. Bad AI.')
        return None


    def write_song(self):
        print('Deciding on a memory to inspire my new song...')
        initial_memory = self.__imagine_inspiring_memory()
        self.memories.add(initial_memory)
        self.memories.save()
        print('Deciding on a topic inspired by that memory...')
        subject, vibe = self.__get_topic_from_memory(initial_memory)
        print('Thinking of other memories that fit the topic...')
        recalled = self.memories.recall(subject)
        print('Alright, now I\'ll get to writing the song! ...')
        title = self.__write_song_from(subject, vibe, initial_memory, recalled)
        return (title, [initial_memory] + recalled)
    
    def __get_existing_genres(self):
        return [x['genre_and_style'] for x in self.songs.values()]

    def __format_as_quatrains(self, lyrics, has_bridge = False):
        lyrics = lyrics.strip()
        sectionTypes = re.findall('\[(.*?)\]', lyrics)
        if has_bridge:
            lastChorusIndex = max(i for i, sType in enumerate(sectionTypes) if sType.lower() == 'chorus')
            if lastChorusIndex > 0 and sectionTypes[lastChorusIndex-1].lower() == 'verse':
                sectionTypes[lastChorusIndex-1] = 'Bridge'
                if lastChorusIndex == 1:
                    sectionTypes[lastChorusIndex-1] = 'Intro'
        sections = re.split('\[.*?\]', lyrics)
        sections = [re.sub('\n+', r'\n', x).strip() for x in sections if x]
        for l, section in enumerate(sections):
            lines = section.split('\n')
            inserted = 0
            for i in range(4, len(lines), 4):
                lines.insert(i + inserted, '')
                inserted += 1
            sections[l] = '\n'.join([f"[{sectionTypes[l]}]"] + lines) + '\n'
        return '\n'.join(sections)

    def __process_song(self, song):
        lyrics = song['lyrics'].strip()
        if 'choruses' not in song and 'chorus' in song:
            song['choruses'] = [song['chorus']]
        choruses = sorted(set(song['choruses']), reverse=True, key=len)
        has_bridge = song['has_bridge'] if 'has_bridge' in song else False
        lyrics = lyrics.strip()
        parsed = lyrics
        for (i, chorusRaw) in enumerate(choruses):
            chorus = chorusRaw.strip()
            parsed = parsed.replace(chorus, '[Chorus]\n~~~~~~~~~~' + str(i) + '~~~~~~~~~~\n\n[Verse]').strip()
        parsed = re.sub('(\[Chorus\]\n){2,}', r'[Chorus]\n', parsed)
        for (i, chorusRaw) in enumerate(choruses):
            chorus = chorusRaw.strip()
            parsed = parsed.replace('~~~~~~~~~~' + str(i) + '~~~~~~~~~~', chorus).strip()
        if not parsed.startswith('[Chorus]'):
            parsed = '[Verse]\n' + parsed
        parsed = re.sub('\n +', r'\n', parsed)
        parsed = re.sub('\n{3,}', r'\n\n', parsed)
        parsed = re.sub('\]\n\s*\n+', r']\n', parsed).strip()
        parsed = re.sub('\[Verse\]\s*$', '', parsed)
        parsed = re.sub('(?<!\n)\[', r'\n\n[', parsed)
        parsed = re.sub('\[Verse\]\n\[Chorus\]', '[Chorus]', parsed)
        parsed = self.__format_as_quatrains(parsed, has_bridge)
        return parsed.strip()

    def process_songs(self):
        for key, value in self.songs.items():
            cleaned = self.__process_song(value)
            self.songs[key]['formatted_lyrics'] = cleaned

    def save_songs(self):
        with open(self.songFilename, 'w') as f:
            json.dump(self.songs, f, indent=2)
    
    def get_songs(self):
        return self.songs
    
    def explain_song(self, title: str):
        for key in self.songs.keys():
            if key.lower() == title.lower():
                title = key
                break
        if not title in self.songs:
            return 'I don\'t have a song called "' + title + '".'
        subject = self.songs[title]['subject']
        return 'The song "' + title + '" was inspired by the following events in my life:\n\n' + '\n\n'.join(self.memories.recall(subject))