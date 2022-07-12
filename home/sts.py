from sentence_transformers import SentenceTransformer, util
import numpy as np

class Sts():

    def __init__(self) :
        self.emb = SentenceTransformer('jhgan/ko-sbert-sts')

    def set_corpus(self, corpus) :
        self.corpus = corpus
        self.embcor = self.emb.encode(corpus, convert_to_tensor = True)

    def set_line(self, line) :
        self.line = line

    def similarity(self, query) :
        
        self.line = len(self.corpus) if self.line > len(self.corpus) else self.line
        query_emb = self.emb.encode(query, convert_to_tensor = True)
        cos_score = util.pytorch_cos_sim(query_emb, self.embcor)[0]
        cos_score = cos_score.cpu() 
        self.idx  = np.argpartition(-cos_score, range(self.line))[0 : self.line]   

        return list(self.idx.tolist())
