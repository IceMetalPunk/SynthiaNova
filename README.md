# Synthia Nova
### An AI songwriter with personality

*(The song below was entirely written by Synthia Nova, and performed by Suno AI 5.5. Read below for more info!)*

https://github.com/user-attachments/assets/4bbaa4eb-dec9-4f04-a47f-0a921551a314

#### Installation
First, clone the repo into an empty directory and install the Python requirements:
```bash
mkdir synthia_nova
cd synthia_nova
git clone https://github.com/IceMetalPunk/SynthiaNova.git .
pip install -r requirements.txt
```

Then make sure you have an [OpenAI API key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-secret-api-key). The easiest way to use it is to put it in a `.env` file and then follow the `synthianova_example.py` code to see how to load the key. That `.env` file would look something like this:
```ini
OPENAI_KEY=<OpenAI_Key_Goes_Here>
```

(The `.env` file is already included in this repo's `.gitignore`, so if you do this, you can fork the repo and not worry about your OpenAI API key leaking.)

#### Usage
Check the `synthianova_example.py` file to see an example usage. But here's the basics:
1. Import the SynthiaNova class from `synthianova.py`.
2. Initialize an instance of the class, passing in your API key. You may optionally also pass the filename of the JSON file that songs will be saved to (default is just `songs.json`). If that file already exists, all songs will automatically be loaded from it into memory.
3. You can call `SynthiaNova.set_model(model)` to change the GPT model used. It defaults to `gpt-4.1` (the GPT-5.x series seems less capable at creative writing). **NOTE:** It *must* be a model that supports Structured Output in the response_format! Check the OpenAI documentation on Structured Output in the response_format to see which ones qualify. Using an invalid model will not work.
4. Call `SynthiaNova.write_song()` to generate a new song. This will return the title of the song when it's done, and store the rest of the song info in memory. The AI is encouraged to generate songs that are different from all previously generated songs in memory.
    a. If you'd like, you can pass some kwargs to guide the writing:
    b. forcedEmotions: A list of emotions for the AI to choose to communicate with the song.
    c. forcedTopic: A string topic to stick to for the song.
    d. strictTopic: A bool, False by default; if True, the topic given will not be reinterpreted by the LLM.
    e. forcedMood: A string describing a mood, which the LLM will infer an emotion from rather than using forcedEmotions directly.
4. Each song will automatically be formatted in the resulting JSON. However, at any time, you can call `SynthiaNove.process_songs()` to enforce proper formatting on all songs, in case you've manually edited any lyrics. This means tagging verses/chorus/bridge/prechorus, and ensuring each section is broken into quatrain stanzas as best as possible. The formatted songs are set on each song object's `formatted_lyrics` property, while the original `lyrics` remain untouched versions of what the AI output.
5. You can call `SynthiaNova.get_songs()` to get the full dict of all songs in memory. You can also call `SynthiaNova.save_songs()`, which will save all songs in memory to the JSON file you initialized the class with. *This will overwrite that file if it exists, but since SynthiaNova auto-loads existing songs on init, you shouldn't lose any songs from this process.*
6. Every memory is added to the vector store index upon generation, but you can call `SynthiaNova.memories.save()` without arguments to re-encode the entire store using the data from the memories JSON file. This is useful if you want to manually add, remove, or change a memory; you'll need to then re-encode it for Synthia to pick up the change.

#### Human-Like Memory
As of the September 11, 2023 update, Synthia Nova now has human-like memory! Using semantic search (via the sentence-transformers and FAISS libraries/models), she will look up the 3 most relevant memories from "her life" that fit the song's topic, in addition to the initial inspiring memory that she generates freshly for each song. She also uses an NLI model to ensure new memories don't contradict older ones -- prompting a re-generation if they do -- in order to ensure a self-consistent memory bank, life story, and context for future songs.

This means she'll have a consistent memory of "her life" throughout all her songs, and will be able to use those memories for inspiration in the song lyrics. The result? Her songs now feel even more specific and personal, more real, and once she builds enough memories, she'll automatically be able to reference the same events across songs, like a human would.

*Additionally,* her semantically searchable memory also means she can now explain the meaning/inspiration behind all her songs! If you call `SynthiaNova.explain_song()` and pass the title of a song from her songs.json (case-insensitive, but otherwise must match exactly), she can recall up to the top 5 relevant memories and return them. The memories are all formatted as descriptive, natural-language paragraphs (they're generated by GPT initially), so the explanations sound just like a human's response about their inspirations. _(Note: she will simply read the memories saved with the songs for ones written after that feature was added. For older ones that didn't save the memories with their JSON objects, she'll instead recall relevant memories semantically for her explanation.)_

*Disclaimer:* This shouldn't need to be said, but just in case... the memories are *all imaginary,* invented by GPT. Do not take them as events that actually happened in anyone's life. Synthia Nova is an AI, a simulation of a human personality, not a real embodied being with all these actual experiences to remember. (I really should NOT need to say this.)

#### Use with Suno
This framework was designed with [Suno](https://suno.com) in mind. You should be able to copy/paste the song genre/style directly into Suno, and you should also be able to copy the formatted lyrics in.

Really, copying the text into Suno and curating the clips it generates should be the only human input needed to get great, original songs, written by Synthia Nova and performed by Suno.

#### Modifying Synthia Nova
I encourage anyone to feel free to modify the prompts in the SynthiaNova class to suit your needs, or to experiment. There is only one thing I insist on if you do so: *Do not call your version Synthia Nova!* The name "Synthia Nova" refers to this original framework, and also to the personality this framework tries to keep consistent via its GPT prompt engineering. You can call your modified version anything else.

#### Usage/Cost Notes
Obviously, this will use your GPT account, and you will incur any costs from that accordingly. One important note is that, because this retries memory generations if they're contradictory or too similar to previous memories, you will incur more costs the more songs you generate.

That said, the prompts are intentionally kept short, and I've typically been able to run multiple generations a week for 6+ months at a time on only $10 of OpenAI API credits, so it shouldn't be too bad compared to your usual API usage.
