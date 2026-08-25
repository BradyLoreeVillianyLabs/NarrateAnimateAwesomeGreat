from storyforge.planner import sentence_split,group_sentences

def test_sentence_split(): assert sentence_split('Hello there. How are you? Fine!')==['Hello there.','How are you?','Fine!']
def test_group(): assert len(group_sentences(['One two.','Three four.','Five six.'],target_words=4))==2
