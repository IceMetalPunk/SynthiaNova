# TODO: Generate performance of lyrics and upload to YouTube:

'''
1. When Suno releases their API, pass lyrics in one chunk at a time, then download the resulting Whole Song.
    1b. If there's a way to grade music quality, use that to choose clips; otherwise, just take the first result.
    1c. Maybe run a Whisper pass and calculate edit distance from intended lyrics to help detect cutoffs, repeats, and mispronunciations?

2. Spoof traffic to vocalremover.org to split vocal and music tracks.

3. (Optional -- for consistent voice) Use kits.ai API to convert the vocals to a trained voice, passing the music as a backing track to get the full compiled output.

4. Use standard YouTube API to upload result to Synthia Nova's own channel.
'''