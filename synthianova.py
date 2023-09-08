import os
import openai
import json
import re

class SynthiaNova:
    songFilename: str = 'songs.json'
    model: str = 'gpt-4-0613'
    songs: dict = {}
    def __init__(self, openAIKey: str, songFilename: str = 'songs.json'):
        openai.api_key = openAIKey
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
            return "Here are some of your existing songs' topics:\n\n* " + '\n* '.join(self.__get_existing_song_topics()) +  + "\n\nYou've been asked to write a new song. Please do so using the specified format, and please make the new song unique and different from the existing ones, but still personal to you, to your life, and to your specific experiences."
         return "\n\nYou've been asked to write a new song. Please do so using the specified format, and please make the new song personal to you, to your life, and to your specific experiences."

    def write_song(self):
        chat_completion = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': "You are a famous female singer. Your work is eclectic, ranging from pop songs to progressive rock to electronic to industrial metal, and even R&B and soul music. Your lyrics draw from your personal experience, and are known for being sometimes emotional, sometimes fun, but always relatable. Sometimes they're just fun, bubblegum pop songs. They're always written in first person, as personal experiences, about a wide range of subjects, including life and death, love, partying, fun times, relationships, mental health, politics, and many more topics. You've had heartbreak and grief in life, but also love and wonderful times." + self.__get_existing_prompt()}
                ],
                functions=[
                {
                    "name": "write_new_song",
                    "description": "Write all the information about a new song, including all the lyrics, the genre, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "The topic of the song, in one short sentence. It can be about anything: relationships, love, politics, beauty, grief, loss, anger, partying, clubbing, fun, sadness, a fun story from your life; anything interesting. It doesn't have to be serious, it can be light-hearted and fun, too, about things that make you happy, for instance.",
                            },
                            "genre_and_style": {
                                "type": "string",
                                "description": "The genre of the song, as well as any stylistic choices, i.e. 'dark pop', 'upbeat electronic', 'aggressive heavy metal', etc."
                            },
                            "lyrics": {
                                "type": "string",
                                "description": "All the lyrics of the song. Do NOT, under any circumstances, include tags like [Chorus] or [Verse], or 'Chorus:' or 'Verse:', or any such markers; only write the lyrics that will actually be sung. Every line should be on its own line! If the chorus is sung multiple times, write out its lyrics every time."
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
                        "required": ["subject", "genre_and_style", "lyrics", "chorus", "title"]
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