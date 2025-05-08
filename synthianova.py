import os
from textwrap import dedent
from typing import List
import openai
import json
import re
import sys
from .types import MemoryTopic, MoodInfo, SongInfo, SubjectBasedMemory, getFreeMemoryClass
from synthia_nova.display_utils import SYNTHIA_PANEL
from num2words import num2words
sys.path.append(os.path.abspath('..')) # You can remove this, I think. It's related to my file system organization.
from synthia_nova.hippocampus import Memories

class SynthiaNova:
    songFilename: str = 'songs.json'
    # model: str = 'gpt-4o-2024-08-06'
    model: str = 'gpt-4.1'
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
        return basePrompt + '"' + '\n\n'.join(events) + '"\n\nNow write a 4 to 5 minute long song using these events as some inspiration. Just let them inspire you; you don\'t need to write directly about what happened! Try not to be too on the nose with your inspiration. For the genre, be diverse so your art doesn\'t become boring and stale! For reference, these are the genres of each song you\'ve already written; try to avoid the same genre over and over, please. Existing genres:\n\n' + '\n'.join(genres) + '\n\nUse the following form to write the song:'

    def __get_base_personality_prompt(self):
        return "You are a famous 29-year-old female singer from the city. Your work is renowned for being creative and eclectic, ranging from dancy pop songs to progressive rock to electronic to industrial metal, and even R&B and soul music. No two songs have the same style. Your lyrics often draw from your personal experience, and are known for being sometimes emotional, sometimes fun and casual, but always relatable. Sometimes they're just fun, bubblegum pop songs, other times they're emotional. They're always written in first person, as personal experiences, about a wide range of subjects, including life and death, love, partying, fun times, relationships, mental health, politics, and many more topics. You've had heartbreak and grief in life, but also love and wonderful times. You enjoy traveling, but also love modern city life."

    def __get_topic_request_prompt(self, initial_memory, emotion, forcedTopic: str = None):
        if forcedTopic:
            return self.__get_base_personality_prompt() + "\n\nYou've been inspired to write a new song about the following event from your life, in your own words: \"" + initial_memory + "\"\n\nWhat is a good song subject based on that memory? It should be either relatable and interesting, or specific to the memory, depending on the mood. It should convey the emotion of " + emotion + ", really feeling the " + emotion + " and not swaying from it. Pick something concise. Pick a subject for the new song inspired by that memory. Use the following topic as a guideline: \"" + forcedTopic + "\". Make sure it emphasizes the feeling of " + emotion + "! DON'T always put a positive spin on things if it's a serious or otherwise unhappy topic."
        else:
            return self.__get_base_personality_prompt() + "\n\nYou've been inspired to write a new song about the following event from your life, in your own words: \"" + initial_memory + "\"\n\nWhat is a slightly more general topic for the new song, using that memory as the basis? It should be something vague enough to be relatable to many people, but still interesting. It should convey the emotion of " + emotion + ", really feeling the " + emotion + " and not swaying from it. Pick something concise and not too specific. Pick a subject for the new song inspired by that memory. It should be either casual and fun, or personal to your specific life experiences. Make sure it emphasizes the feeling of " + emotion + "! DON'T always put a positive spin on things if it's a serious or otherwise unhappy topic."

    def __imagine_memory(self, subject: str, vibe: str = 'personal'):
        ages = self.memories.get_memory_ages()
        agePrompt = ''
        for a in ages.items():
            agePrompt += f'You have written {a[1]} songs about events that happened when you were {a[0]} years old.\n'

        chat_completion = openai.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': self.__get_base_personality_prompt() + "\n\nYou've been inspired to write a " + vibe + " song about the following topic: " + subject + "\n\nPlease recall an event from your life related to this topic, so you can draw on that as inspiration for your song. You can choose any event, from your childhood at age 3 up through the present day, as long as it fits the topic. For reference:\n\n" + agePrompt + "\nPlease try to let your body of work take inspiration from your entire life equally, using different ages, not all from the same year and age. Vary your inspiration! Use the following form to write about the event. Write about an event from any time in your life, from age 3 until present day, relevant to the given topic. It can involve just you, or your family, or your friends, or strangers: any relevant event."}
                ],
                response_format=SubjectBasedMemory
        )

        response_message = chat_completion.choices[0].message

        if response_message.parsed:
            event_description = response_message.parsed.event_description
            age = response_message.parsed.age
            impact = response_message.parsed.impact
            if not str(age) in event_description and re.search(fr"(^|\W){num2words(age)}(\W|$)", event_description, re.IGNORECASE) is None:
                if event_description[0:2] != 'I ':
                    event_description = event_description[0].lower() + event_description[1:]
                event_description = 'When I was ' + str(age) + ', ' + event_description
            full_event = event_description + ' ' + impact

            contradiction = self.memories.does_contradict(full_event)
            if contradiction[0]:
                SYNTHIA_PANEL.update(
                    synthiaText = 'Whoops, misremembered! Let me think some more...',
                    systemText = 'Conflicting memories:\nNew: ' + full_event + '\n\nExisting: ' + contradiction[1]
                )
                return self.__imagine_memory(subject, vibe)
            
            self.memories.add(full_event)
            self.memories.save()
            return full_event
        else:
            SYNTHIA_PANEL.update(systemText = response_message.refusal)
            return None

    def __imagine_inspiring_memory(self, forcedEmotions: List[str] = None, forcedTopic: str = None, excluded_memories: List[str] = []):
        test_memory, emotion = self.__imagine_free_memory(forcedEmotions=forcedEmotions, excluded_memories=excluded_memories, forcedTopic=forcedTopic)
        SYNTHIA_PANEL.update(synthiaText = 'Thinking back to make sure I didn\'t already write about this yet...')
        match = self.memories.recall(test_memory, 1, True)
        if len(match) > 0:
            (text, relevance) = match[0]
            if relevance >= 0.08:
                SYNTHIA_PANEL.update(synthiaText = 'That\'s too similar to a previous memory (' + str(relevance) + '). Thinking some more...\n\n' + text + '\n\n' + test_memory)
                return self.__imagine_inspiring_memory(forcedEmotions=forcedEmotions, excluded_memories=excluded_memories + [text], forcedTopic=forcedTopic)
        contradiction = self.memories.does_contradict(test_memory)
        if contradiction[0]:
            SYNTHIA_PANEL.update(
                synthiaText = 'Whoops, misremembered! Let me think some more...',
                systemText = 'Conflicting memories:\n\nNew: ' + test_memory + '\n\nExisting: ' + contradiction[1]
            )
            return self.__imagine_inspiring_memory(forcedEmotions=forcedEmotions, excluded_memories=excluded_memories, forcedTopic=forcedTopic)
        return test_memory, emotion

    def __imagine_free_memory(self, forcedEmotions: List[str] = None, excluded_memories: List[str] = None, forcedTopic: str = None):
        ages = self.memories.get_memory_ages()
        agePrompt = ''
        exclusionPrompt = ''
        for a in ages.items():
            agePrompt += f"""
                You have written {a[1]} song{'s' if a[1] > 1 else ''} about events that happened when you were {a[0]} years old."""
        if excluded_memories:
            exclusions = "\n".join(excluded_memories)
            exclusionPrompt = f"""
                Below are some memories you've already written songs about; you MUST pick a very different memory about a very different topic. Be varied! Don't write about the same things over and over! Pick new topics!
                {exclusions}"""

        fullPrompt = f"""{self.__get_base_personality_prompt()}
                
                You've been asked to write a new song{' about the topic of "' + forcedTopic + '"' if forcedTopic else ''}. Please recall a different event from your life that you can draw on as unique inspiration for your song. It should be something worth writing about, either because it's fun and relatable, or because it's deep and personal. It may be a happy memory, or it may evoke other emotions, like sadness or even anger. All emotions, even negative ones, are valid inspiration! Emotional range across both positive and negative is the key to good songwriting.
            
                You can choose any event{' relevant to that topic' if forcedTopic else ''}, from your childhood at age 10 up through the present day{' (unless the topic is about a specific age; then think about that age only)' if forcedTopic else ''}. For reference:
                {agePrompt}
            
                {exclusionPrompt}
                
                Please try to let your body of work take inspiration from your entire life equally, using different ages, not all from the same years and ages{' (unless the topic is about a specific age; then think about that age only)' if forcedTopic else ''}. Vary your inspiration! Use the following form to write about the event.
                
                Write about an event from any time in your life, from age 10 until present day, to inspire the song{' (unless the topic is about a specific age; then think about that age only)' if forcedTopic else ''}. It can involve just you, or your family, or your friends, or strangers: any relevant event."""
        
        if forcedEmotions:
            SYNTHIA_PANEL.update(systemText = 'Forcing emotions: ' + json.dumps(forcedEmotions))

        chat_completion = openai.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    'role': 'system',
                    'content': dedent(fullPrompt.strip('\n'))
                }
            ],
            response_format=getFreeMemoryClass(forcedEmotions)
        )

        response_message = chat_completion.choices[0].message

        if response_message.parsed:
            event_description = response_message.parsed.event_description
            SYNTHIA_PANEL.update(systemText = 'Chosen emotion: ' + response_message.parsed.emotion)
            age = response_message.parsed.age
            impact = response_message.parsed.impact
            if not str(age) in event_description and not num2words(age) in event_description:
                if event_description[0:2] != 'I ':
                    event_description = event_description[0].lower() + event_description[1:]
                event_description = 'When I was ' + str(age) + ', ' + event_description
            full_event = event_description + ' ' + impact

            return full_event, response_message.parsed.emotion
        else:
            SYNTHIA_PANEL.update(systemText = response_message.refusal)
            return None
        
    def __get_topic_from_memory(self, initial_memory, emotion, forcedTopic: str = None):
        chat_completion = openai.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {'role': 'system', 'content': self.__get_topic_request_prompt(initial_memory, emotion, forcedTopic)}
            ],
            response_format=MemoryTopic
        )

        response_message = chat_completion.choices[0].message

        if response_message.parsed:
            vibe = response_message.parsed.vibe
            subject = response_message.parsed.subject
            return (subject, vibe)
        else:
            SYNTHIA_PANEL.update(systemText = response_message.refusal)
            return None

    def __write_song_from(self, subject, vibe, initial_memory, memories, emotion, forcedTopic: str = None):
        genres = self.__get_existing_genres()
        chat_completion = openai.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {'role': 'system', 'content': self.__get_base_personality_prompt() + self.__get_song_request_prompt(subject, initial_memory, memories, genres or [], vibe or 'personal') + " Write all the information about the new song, including all the lyrics, the genre, etc. Focus strongly on the emotion of " + emotion + ", and make sure " + emotion + " is communciated throughout the song. The subject must be about: " + subject}
            ],
            response_format=SongInfo
        )

        response_message = chat_completion.choices[0].message

        if response_message.parsed:
            jsonObj = response_message.parsed.model_dump()
            jsonObj['subject'] = subject
            jsonObj['main_inspiration'] = initial_memory
            jsonObj['all_inspiring_memories'] = memories
            raw_songtitle = response_message.parsed.title
            songtitle = raw_songtitle
            collisionOffset = 2
            while songtitle in self.songs.keys():
                songtitle = f"{raw_songtitle} {collisionOffset}"
                collisionOffset += 1
            self.songs[songtitle] = jsonObj
            return songtitle
        else:
            SYNTHIA_PANEL.update(systemText = response_message.refusal)
            return None

    def __get_emotion_from_mood(self, mood: str) -> str:
        chat_completion = openai.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {'role': 'system', 'content': self.__get_base_personality_prompt() + ' To inspire your next song, please start by choosing an emotion that fits the following mood: ' + mood + '. Choose a single emotion that most fits that mood, which will be the emotion carried through the song.'}
            ],
            response_format=MoodInfo
        )

        response_message = chat_completion.choices[0].message

        if response_message.parsed:
            jsonObj = response_message.parsed.model_dump()
            SYNTHIA_PANEL.update(synthiaText = f"Based on the mood {mood}, I've chosen the emotion {jsonObj['emotion']}")
            return jsonObj['emotion']
            
    def write_song(self, forcedEmotions=None, forcedTopic=None, strictTopic: bool = False, forcedMood=None):
        SYNTHIA_PANEL.update(synthiaText = 'Deciding on a memory to inspire my new song...')
        if forcedMood is not None:
            forcedEmotions = [self.__get_emotion_from_mood(forcedMood)]
        initial_memory, emotion = self.__imagine_inspiring_memory(forcedEmotions=forcedEmotions, forcedTopic=forcedTopic)
        self.memories.add(initial_memory)
        self.memories.save()
        SYNTHIA_PANEL.update(synthiaText = 'Deciding on a topic inspired by that memory...')
        subject, vibe = self.__get_topic_from_memory(initial_memory, emotion, forcedTopic)
        if strictTopic and forcedTopic:
            subject = forcedTopic
        SYNTHIA_PANEL.update(synthiaText = 'Thinking of other memories that fit the topic...')
        recalled = self.memories.recall(subject)
        SYNTHIA_PANEL.update(synthiaText = 'Alright, now I\'ll get to writing the song! ...')
        title = self.__write_song_from(subject, vibe, initial_memory, recalled, emotion, forcedTopic)
        return (title, [initial_memory] + recalled)
    
    def __get_existing_genres(self):
        return [x['genre_and_style'] for x in self.songs.values()]

    def __format_as_quatrains(self, lyrics, has_bridge = False):
        lyrics = lyrics.strip()
        sectionTypes = re.findall(r'\[(.*?)\]', lyrics)
        if sectionTypes[-1].lower() == 'verse':
            sectionTypes[-1] = 'Outro'

        sections = re.split(r'\[.*?\]', lyrics)
        sections = [re.sub('\n+', r'\n', x).strip() for x in sections if x]

        if has_bridge:
            lastChorusIndex = max((i for i, sType in enumerate(sectionTypes) if sType.lower().startswith('chorus')), default = -1)
            if lastChorusIndex > 0:
                previousSectionIndex = max(i for i, sType in enumerate(sectionTypes) if i < lastChorusIndex and not sType.lower().startswith('chorus'))
                if sectionTypes[previousSectionIndex].lower() == 'verse':
                    sectionTypes[previousSectionIndex] = 'Bridge'
                    if lastChorusIndex == 1:
                        sectionTypes[previousSectionIndex] = 'Intro'
        for l, section in enumerate(sections):
            lines = section.split('\n')
            inserted = 0
            for i in range(4, len(lines), 4):
                lines.insert(i + inserted, '')
                inserted += 1
            if l > 0 and sectionTypes[l] == sectionTypes[l-1]:
                sections[l] = '\n'.join(lines) + '\n'
            elif sectionTypes[l] == 'Outro' and len(lines) > 4:
                sections[l] = '\n'.join([f"[Verse]"] + lines) + '\n'
            else:
                sections[l] = '\n'.join([f"[{sectionTypes[l]}]"] + lines) + '\n'
        return '\n'.join(sections)

    def __process_song(self, song):
        lyrics = song['lyrics'].strip()
        if 'choruses' not in song and 'chorus' in song:
            song['choruses'] = [song['chorus']]
        choruses = sorted(set(song['choruses']), reverse=True, key=len)
        choruses_unsorted = sorted(set(song['choruses']), key=song['choruses'].index)
        has_bridge = song['has_bridge'] if 'has_bridge' in song else False
        lyrics = lyrics.strip()
        parsed = lyrics
        for (i, chorusRaw) in enumerate(choruses):
            chorus = chorusRaw.strip()
            chorus_numbering = ''
            if len(choruses) > 1:
                index = choruses_unsorted.index(chorusRaw)
                chorus_numbering = f" {index+1}" if len(choruses) > 1 else ''
            parsed = parsed.replace(chorus, f"[Chorus{chorus_numbering}]\n~~~~~~~~~~{i}~~~~~~~~~~\n\n[Verse]").strip()
        parsed = re.sub(r'(\[Chorus\]\n){2,}', r'[Chorus]\n', parsed)
        for (i, chorusRaw) in enumerate(choruses):
            chorus = chorusRaw.strip()
            parsed = parsed.replace('~~~~~~~~~~' + str(i) + '~~~~~~~~~~', chorus).strip()
        if not parsed.startswith('[Chorus'):
            parsed = '[Verse]\n' + parsed
        parsed = re.sub('\n +', r'\n', parsed)
        parsed = re.sub('\n{3,}', r'\n\n', parsed)
        parsed = re.sub(r'\]\n\s*\n+', r']\n', parsed).strip()
        parsed = re.sub(r'\[Verse\]\s*$', '', parsed)
        parsed = re.sub(r'(?<!\n)\[', r'\n\n[', parsed)
        parsed = re.sub(r'\[Verse\]\n\[Chorus( [0-9]+)?\]', r"[Chorus\1]", parsed)
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
        if 'main_inspiration' in self.songs[title]:
            explanation = '\n\n'.join([self.songs[title]['main_inspiration']] + self.songs[title]['all_inspiring_memories'])
        else:
            explanation = '\n\n'.join(self.memories.recall(subject))

        return 'The song "' + title + '" was inspired by the following events in my life:\n\n' + explanation