from sentence_transformers import SentenceTransformer, CrossEncoder, util
import faiss
import re
import json
import os
model = SentenceTransformer('all-mpnet-base-v2')
cross_ranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
contradiction_checker = CrossEncoder('cross-encoder/nli-deberta-v3-base')

class Memories:
    memory_list = list()
    database = None
    name = None
    memory_embeddings = None
    def __init__(self, name: str = 'Synthia Nova'):
        self.name = name
    def add(self, memory: str):
        ''' Note: ALWAYS remember to save after adding all your memories, or they won't be searchable! '''
        self.memory_list.append(memory)
    def getCleanName(self):
        return re.sub('[^a-zA-Z0-9_]', '_', self.name.lower())

    def load(self, filename: str = None):
        if filename is None:
            filename = self.getCleanName() + '_memories.json'
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write('[]')
        with open(filename, 'r') as f:
            self.memory_list = json.load(f)
        self.save(filename)

    def save(self, filename: str = None):
        if filename is None:
            filename = self.getCleanName() + '_memories.json'
        with open(filename, 'w') as f:
            json.dump(self.memory_list, f, indent = 2)
        if len(self.memory_list) <= 0:
            return
        self.memory_embeddings = model.encode(self.memory_list)
        index = faiss.IndexFlatL2(self.memory_embeddings.shape[1])
        index.add(self.memory_embeddings)
        
        faiss.write_index(index, 'index_' + self.getCleanName() + '_memories')
        self.database = faiss.read_index('index_'+self.getCleanName()+'_memories')

    def does_contradict(self, query: str):
        cross_inp = [(memory, query) for memory in self.memory_list]
        cross_scores = contradiction_checker.predict(cross_inp)

        args = cross_scores.argmax(axis=1)
        for i, score_max in enumerate(args):
            if score_max == 0:
                return True
        return False

    def recall(self, query: str, count: int = 5):
        ''' Note: Will only search through the last saved memories, so save before searching! '''
        if len(self.memory_list) <= 0 or self.database is None:
            return []

        question_embedding = model.encode(query, convert_to_tensor=True)
        count = min(count, len(self.memory_list))
        to_retrieve = min(count * 7, len(self.memory_list))
        hits = util.semantic_search(question_embedding, self.memory_embeddings, top_k=to_retrieve)
        hits = hits[0]  # Get the hits for the first query

        cross_inp = [[query, self.memory_list[hit['corpus_id']]] for hit in hits]
        cross_scores = cross_ranker.predict(cross_inp)

        # Sort results by the cross-encoder scores
        for idx in range(len(cross_scores)):
            hits[idx]['cross-score'] = cross_scores[idx]
            hits[idx]['text'] = self.memory_list[hits[idx]['corpus_id']]

        hits = sorted(hits, key=lambda x: x['cross-score'], reverse=True)
        return [hit['text'] for hit in hits[0:count] if hit['cross-score'] > -6]