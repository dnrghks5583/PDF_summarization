from transformers import PreTrainedTokenizerFast
from transformers import BartForConditionalGeneration

import torch

class Kobart :
    
    def __init__(self) :
        self.tokenizer = PreTrainedTokenizerFast.from_pretrained('digit82/kobart-summarization')
        self.model     = BartForConditionalGeneration.from_pretrained('home/model')
        # 'home/model'
        # 'digit82/kobart-summarization'
    def summary(self, text) :
        ex            = text.replace('\n', ' ')
        raw_input_ids = self.tokenizer.encode(ex)
        input_ids     = [self.tokenizer.bos_token_id] + raw_input_ids + [self.tokenizer.eos_token_id]
        summary_ids   = self.model.generate(torch.tensor([input_ids]),
                                            num_beams    = 4,
                                            max_length   = 512,
                                            eos_token_id = 1)
        return self.tokenizer.decode(summary_ids.squeeze().tolist(), skip_special_tokens = True)
    
    def para_summary(self, pp, para_list) :
        para_sum   = []       # 문단별 요약
        for p in pp :
            summ = []
            if p[0] not in para_list : continue
            for text in p[1] :
                summ.append(self.summary(text))
            para_sum.append((p[0], summ))        
        return para_sum
    
    def __str__(self) :
        return 'KoBART'