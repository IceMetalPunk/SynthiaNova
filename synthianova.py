import os
import openai
import json
import re
import sys
from num2words import num2words
sys.path.append(os.path.abspath('..')) # You can remove this, I think. It's related to my file system organization.
from synthia_nova.hippocampus import Memories

class SynthiaNova:
    songFilename: str = 'songs.json'
    # model: str = 'gpt-4-0613'
    model: str = 'gpt-4-1106-preview'
    songs: dict = {}
    memories = None
    def __init__(self, openAIKey: str, name: str = 'Synthia Nova', songFilename: str = 'songs.json'):
        openai.api_key = openAIKey
        self.memories = Memories(name)
        self.memories.load()
        self.songFilename = songFilename
        if not os.path.exists(self.songFilename):
            self.songs = {}
        else:
            with open(self.songFilename, 'r') as f:
                self.songs = json.load(f)

    def set_model(self, model):
        self.model = model

    def __get_existing_prompt(self):
         if len(self.songs):
            return "Here are some of your existing songs' topics:\n\n* " + '\n* '.join(self.__get_existing_song_topics())
         return ''

    def __get_song_request_prompt(self, subject, events, genres):
        basePrompt = "\n\nYou've been asked to write a new song, specifically about the following topic: " + subject + "\n\nPlease do so using the specified format. You may make the new song personal to you, to your life, and to your specific life experiences, or more general and relatable, depending on what sounds good. Remember to be diverse and creative with the genres you choose. I'll remind you of a few events from your life that are relevant to the topic, in your own words:\n\n"
        return basePrompt + '"' + '\n\n'.join(events) + '"\n\nNow write a song using these events as some inspiration. Just let them inspire you; you don\'t need to write directly about what happened! Try not to be too on the nose with your inspiration. For the genre, be diverse so your art doesn\'t become boring and stale! For reference, these are the genres of each song you\'ve already written; try to avoid the same genre over and over, please. Existing genres:\n\n' + '\n'.join(genres)

    def __get_base_personality_prompt(self):
        return "You are a famous 29-year-old female singer. Your work is eclectic, ranging from pop songs to progressive rock to electronic to industrial metal, and even R&B and soul music. No two songs have the same style. Your lyrics draw from your personal experience, and are known for being sometimes emotional, sometimes fun, but always relatable. Sometimes they're just fun, bubblegum pop songs. They're always written in first person, as personal experiences, about a wide range of subjects, including life and death, love, partying, fun times, relationships, mental health, politics, and many more topics. You've had heartbreak and grief in life, but also love and wonderful times."

    def __get_topic_request_prompt(self):
        return self.__get_base_personality_prompt() + ' ' + self.__get_existing_prompt() + "\n\nYou've been asked to write a new song. Please suggest a topic for this song, one that's different from any of your existing song subjects. It should be something vague enough to be relatable to many people, but still unique enough to be interesting. It can convey any emotion, from joy to despair; be diverse so your art doesn't get boring and stale!"

    def __imagine_memory(self, subject: str):
        ages = self.memories.get_memory_ages()
        agePrompt = ''
        for a in ages.items():
            agePrompt += f'You have written {a[1]} songs about events that happened when you were {a[0]} years old.\n'

        chat_completion = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': self.__get_base_personality_prompt() + "\n\nYou've been asked to write a song about the following topic: " + subject + "\n\nPlease recall an event from your life related to this topic, so you can draw on that as inspiration for your song. You can choose any event, from your childhood at age 3 up through the present day, as long as it fits the topic. For reference:\n\n" + agePrompt + "\nPlease try to let your body of work take inspiration from your entire life equally, not all from the same year and age. Vary your inspiration! Use the following form to write about the event."}
                ],
                functions=[
                {
                    "name": "recall_event",
                    "description": "Write about an event from any time in your life, from age 3 until present day, relevant to the given topic. It can involve just you, or your family, or your friends, or strangers: any relevant event.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event_description": {
                                "type": "string",
                                "description": "Explain what happened, in a single paragraph, in detail. It should be detailed enought to inspire a song, but no more than 5 or 6 sentences maximum.",
                            },
                            "age": {
                                "type": "integer",
                                "description": "How old were you when this event happened, in years?",
                            },
                            "impact": {
                                "type": "string",
                                "description": "Describe, in one or two sentence maximum, how this event made you feel. Begin with the words \"I felt\"."
                            }
                        },
                        "required": ["event_description", "age", "impact"]
                    }
                }
            ],
            function_call={"name": "recall_event"}
        )

        response_message = chat_completion["choices"][0]["message"]

        if response_message.get("function_call"):
            function_name = response_message["function_call"]["name"]
            if function_name != 'recall_event':
                print('ERROR: Chat GPT made up a different function than the songwriting one. Bad AI.')
                return None
            function_args = json.loads(response_message["function_call"]["arguments"])
            event_description = function_args.get('event_description')
            age = function_args.get('age')
            impact = function_args.get('impact')
            if not str(age) in event_description and not num2words(age) in event_description:
                event_description = 'When I was ' + str(age) + ', ' + event_description
            full_event = event_description + ' ' + impact

            if self.memories.does_contradict(full_event):
                print('Whoops, misremembered! Let me think some more...')
                return self.__imagine_memory(subject)
            
            self.memories.add(full_event)
            self.memories.save()
            return full_event

    def __get_topic_and_memories(self):
        chat_completion = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': self.__get_topic_request_prompt()}
                ],
                functions=[
                {
                    "name": "choose_subject",
                    "description": "Pick a subject for the new song. It should be personal to your life, but can be as specific or vague as you like.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "The topic of the song, in one short but specific sentence. It can be about anything: relationships, love, politics, beauty, grief, loss, anger, partying, clubbing, fun, sadness, a fun story from your life; anything interesting. It doesn't have to be serious, it can be light-hearted and fun, too, about things that make you happy, for instance. It should be either about a specific event in your life, or vaguely about an interest of yours.",
                            }
                        },
                        "required": ["subject"]
                    }
                }
            ],
            function_call={"name": "choose_subject"}
        )

        response_message = chat_completion["choices"][0]["message"]

        if response_message.get("function_call"):
            function_name = response_message["function_call"]["name"]
            if function_name != 'choose_subject':
                print('ERROR: Chat GPT made up a different function than the songwriting one. Bad AI.')
                return None
            function_args = json.loads(response_message["function_call"]["arguments"])
            subject = function_args.get('subject')
            print('Subject chosen: ' + subject)
            # self.songs[songtitle] = function_args
            recalled = self.memories.recall(subject)
            if len(recalled) < 5:
                print('Have to think about a memory...')
                self.__imagine_memory(subject)
                recalled = self.memories.recall(subject)
            return (subject, recalled)
        else:
            print('ERROR: Chat GPT did not call the songwriting function at all. Bad AI.')
        return None
    
    def __get_existing_genres(self):
        return [x['genre_and_style'] for x in self.songs.values()]

    def write_song(self):
        print("Synthia: I'm deciding on a topic for the new song. One second...")
        (subject, memories) = self.__get_topic_and_memories()
        print("Synthia: Got it! I want to write about \"" + subject + "\" and I know exactly how I can relate to it. Writing the song now!")

        genres = self.__get_existing_genres()

        chat_completion = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': self.__get_song_request_prompt(subject, memories, genres or [])}
                ],
                functions=[
                {
                    "name": "write_new_song",
                    "description": "Write all the information about a new song, including all the lyrics, the genre, etc. The subject must be about: " + subject,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "genre_and_style": {
                                "type": "string",
                                "description": "The genre of the song, as well as any stylistic choices, i.e. 'dark pop', 'upbeat electronic', 'aggressive heavy metal', etc. Remember that you can choose any genre, so be eclectic and creative! But only describe the genres as concisely as possible, with no extra words. For example, 'dark pop, electronic elements' or 'industrial metal, electropop' are both valid."
                            },
                            "lyrics": {
                                "type": "string",
                                "description": "All the lyrics of the song. Do NOT, under any circumstances, include tags like [Chorus] or [Verse], or 'Chorus:' or 'Verse:', or any such markers; only write the lyrics that will actually be sung. EXCLUDE structure markers! Every line should be on its own line! If the chorus is sung multiple times, write out its lyrics every time."
                            },
                            "chorus": {
                                "type": "string",
                                "description": "Which part of the lyrics is the chorus? Copy the entire chorus here. Careful not to make any typos; it should be exactly the same as it's written in the lyrics. EXACTLY the same with no differences at all. Every line should be on its own line!"
                            },
                            "title": {
                                "type": "string",
                                "description": "The title of the song."
                            }
                        },
                        "required": ["genre_and_style", "lyrics", "chorus", "title"]
                    }
                }
            ],
            function_call={"name": "write_new_song"}
        )

        response_message = chat_completion["choices"][0]["message"]

        if response_message.get("function_call"):
            function_name = response_message["function_call"]["name"]
            if function_name != 'write_new_song':
                print('ERROR: Chat GPT made up a different function than the songwriting one. Bad AI.')
                return None
            function_args = json.loads(response_message["function_call"]["arguments"])
            function_args['subject'] = subject
            songtitle = function_args.get('title')
            self.songs[songtitle] = function_args
            return songtitle
        else:
            print('ERROR: Chat GPT did not call the songwriting function at all. Bad AI.')
        return None

    def __format_as_quatrains(self, lyrics):
        lyrics = lyrics.strip()
        sectionTypes = re.findall('\[(.*?)\]', lyrics)
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
        chorus = song['chorus'].strip()
        lyrics = re.sub('([.!?](?!\.)\s*)', r'\1\n', lyrics).strip()
        chorus = re.sub('([.!?](?!\.)\s*)', r'\1\n', chorus).strip()
        parsed = lyrics.replace(chorus, '[Chorus]\n' + chorus + '\n\n[Verse]').strip()
        if not parsed.startswith('[Chorus]'):
            parsed = '[Verse]\n' + parsed
        parsed = re.sub('\n +', r'\n', parsed)
        parsed = re.sub('\n{3,}', r'\n\n', parsed)
        parsed = re.sub('\]\n\s*\n+', r']\n', parsed).strip()
        parsed = re.sub('\[Verse\]\s*$', '', parsed)
        parsed = re.sub('(?<!\n)\[', r'\n\n[', parsed)
        parsed = re.sub('\[Verse\]\n\[Chorus\]', '[Chorus]', parsed)
        parsed = self.__format_as_quatrains(parsed)
        return parsed.strip()

    def process_songs(self):
        for key, value in self.songs.items():
            cleaned = self.__process_song(value)
            self.songs[key]['formatted_lyrics'] = cleaned

    def save_songs(self):
        with open(self.songFilename, 'w') as f:
            json.dump(self.songs, f, indent=2)

    def __get_existing_song_topics(self):
        return [x['subject'] for x in self.songs.values()]
    
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