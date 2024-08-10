from pydantic import BaseModel, Field
from enum import Enum

class SubjectBasedMemory(BaseModel):
    event_description: str = Field(description="Explain what happened, in a single paragraph, in detail, as specific as possible. It should be detailed and specific enough to inspire a song, but no more than 5 or 6 sentences maximum.")
    age: int = Field(description="How old were you when this event happened, in years? Pick an age between 10 and 29.")
    impact: str = Field(description="Describe, in one or two sentences maximum, how this event made you feel. Begin with the words \"I felt\".")

class FreeMemory(BaseModel):
    emotion: str = Field(description="What emotion is associated with this memory? Joy, sadness, anger, fear, love, etc.?")
    age: int = Field(description="How old were you when this event happened, in years? Pick an age between 10 and 29.")
    event_description: str = Field(description="Explain what happened, in a single paragraph, in detail, as specific as possible. It should be detailed and specific enough to inspire a song, but no more than 5 or 6 sentences maximum.")
    impact: str = Field(description="Describe, in one or two sentences maximum, how this event made you feel. Begin with the words \"I felt\".")
    # def __init__(self, *args, allowedEmotions: list[str] = None, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if allowedEmotions:
    #         self.emotion = Enum('EmotionEnum', {k:k for k in allowedEmotions}, type=str)
    #     else:
    #         self.emotion = Field(description="What emotion is associated with this memory? Joy, sadness, anger, fear, love, etc.?", type=str)

class VibeEnum(str, Enum):
    casual_and_fun = "casual_and_fun"
    deep_and_personal = "deep_and_personal"
    def _get_value(self, **kwargs):
        return self.value

class MemoryTopic(BaseModel):
    vibe: VibeEnum = Field(description="The overall feeling of the song. Are you writing a casual and fun song to dance to, or a deep and personal song to move the listener? About 50%% of your songs should be casual and 50%% should be personal.")
    subject: str = Field(description="The topic of the song, in one short sentence. It doesn't have to be serious, it can be light-hearted and fun, too, about things that make you happy, for instance. It should be clearly inspired by that memory.")
    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        value = super(MemoryTopic, cls).model_json_schema(*args, **kwargs)
        value['properties']['vibe']['anyOf'] = value['properties']['vibe']['allOf']
        value['properties']['vibe'].pop('allOf', None)
        return value

class SongInfo(BaseModel):
    genre_and_style: str = Field(description="The genre of the song, as well as any stylistic choices, i.e. 'dark pop', 'upbeat electronic', 'aggressive heavy metal', etc. Remember that you can choose any genre, so be eclectic and creative! But only describe the genres as concisely as possible, with no extra words. For example, 'dark pop, electronic' or 'industrial metal, electropop' are both valid, but do not say 'synthpop with indie rock elements'; that would be better written as 'synthpop, indie rock'.")
    lyrics: str = Field(description="All the lyrics of the song. Do NOT, under any circumstances, include tags like [Chorus], [Verse], etc.; nor 'Chorus:', 'Verse:', etc.; nor any such markers! ONLY write the lyrics that will actually be sung! EXCLUDE structure markers! Every line must be on its own line! If the chorus is sung multiple times, write out its lyrics every time. Include any backing vocals or gang vocals if you like, including 'heys' and 'oohs', (in parentheses) where they should be sung.")
    choruses: list[str] = Field(description="Which parts of the lyrics are the chorus? Copy the entire chorus here. Most songs will only have one chorus, but only if this has variations on a chorus, each distinct variation should be listed separately here. Multiple stanzas of the same chorus should be grouped together, not considered separate choruses here. Be careful not to make any typos; it should be exactly the same as it's written in the lyrics. EXACTLY the same with no differences at all, including any backing vocals or gang vocals! Every chorus variation should be included in this list verbatim, one full chorus per list entry. Only include choruses, not any verses or bridges. Include each variation of the chorus, which should be only one if the chorus doesn't change throughout the song. This MUST be exactly the chorus as written in the lyrics, and CANNOT have anything else in it. Only include gang vocals if they're actually part of the chorus.")
    title: str = Field(description="The title of the song.")
    has_bridge: bool = Field(description="If this song has a bridge, set this to True. If it does not, set this to False. At least 50%% of your songs should have a bridge, but not every one.")