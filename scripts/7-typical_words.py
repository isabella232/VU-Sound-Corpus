
# coding: utf-8

from lxml import etree
from collections import Counter
from math import log
import random
import tabulate
from functools import partial
from wordcloud import WordCloud

# Palettes availabe for the coloring of the word clouds.
palettes = {0: [(77, 137, 99), (105, 165, 131), (225, 179, 120),
                (224, 204, 151), (236, 121, 154), (159, 2, 81)],
                
            1: [(163, 30, 57), (72, 92, 90), (140, 156, 154),
                (157, 178, 177), (191, 207, 204), (214, 228, 225)],
                
            2: [(97, 148, 188), (165, 209, 243), (208, 234, 255),
                (228, 0, 27), (236, 236, 236), (96, 96, 96)],
                
            3: [(230, 84, 0), (116, 32, 104), (35, 68, 131), (12, 99, 124),
                (1, 137, 130), (71, 100, 117), (80, 84, 77)],
                
            4: [(2, 120, 120), (253, 182, 50), (43, 196, 68), (16, 197, 205),
                (158, 243, 235), (2, 120, 42), (242, 243, 158), (194, 35, 38)],
                
            5: [(33, 182, 168), (23, 127, 117), (182, 119, 33), (127, 23, 31), (182, 33, 45)],
            
            6: [(52, 152, 219), (68, 187, 255), (137, 127, 186), (113, 186, 81),
                (223, 85, 79), (252, 208, 54), (237, 87, 132), (255, 116, 22)],
            }

def random_color_func(word=None, font_size=None, position=None,
                      orientation=None, font_path=None, random_state=None,
                      palette=1):
    "Random color generation."
    if palette == None:
        # Default:
        colors = palettes[0]
    else:
        colors = palettes[palette]
    return random.choice(colors)

def wordcloud(text, filename):
    "Generate word cloud for a text."
    wc = WordCloud(width=2500,
                   height=2500,
                   font_path="/Users/Emiel/Library/Fonts/FiraMono-Regular.ttf",
                   background_color='white',
                   relative_scaling=0.5)
    generated = wc.generate(text)
    generated.recolor(color_func=partial(random_color_func, palette=1))
    generated.to_file(filename)
    return generated

def typical_cloud(words,c,group):
    "Save a word cloud for the typical words from a group."
    filename = group + '.png'
    text = ' '.join([word for word in words for i in range(c[word])])
    wordcloud(text, filename)

# Load the data
xml  = etree.parse('../steps/4-results/results.xml')
root = xml.getroot()

# Get counts for the tags
def label_counter(query):
    "Return a Counter with a label count for elements matching the query."
    return Counter(tag.attrib['label'] for tag in root.xpath(query))

# try to get as many matches as possible by replacing spaces in crowd tags by dashes.
# (original freesound tags do not have any spaces in them)
def spacetodash(tag_dict):
    for tag in list(filter(lambda x: ' ' in x, tag_dict.keys())):
        dash_tag = tag.replace(' ','-')
        if dash_tag in tag_dict:
            tag_dict[dash_tag] += tag_dict[tag]
            tag_dict.pop(tag)
    return tag_dict

# Define function to look only at shared tags, and how they are distributed.
def shared(d1,d2):
    "Takes two dictionaries and returns them with only the shared keys."
    shared_tags = set(d1.keys()) & set(d2.keys())
    d1 = dict((tag,count) for tag,count in d1.items() if tag in shared_tags)
    d2 = dict((tag,count) for tag,count in d2.items() if tag in shared_tags)
    return d1, d2




def log_likelihood(corpus_1_counts,corpus_2_counts):
    """Computes the log likelihood for words to appear more in one corpus than
    in the other."""
    # Rayson, P. and Garside, R. (2000)
    # http://dl.acm.org/citation.cfm?id=1117730
    total_c1    = float(sum(corpus_1_counts.values()))
    total_c2    = float(sum(corpus_2_counts.values()))
    total       = total_c1 + total_c2
    overlap     = set(corpus_1_counts.keys()) & set(corpus_2_counts.keys())
    l = []
    for k in overlap:
        a = float(corpus_1_counts[k])
        b = float(corpus_2_counts[k])
        E1 = total_c1 * (a+b) / total
        E2 = total_c2 * (a+b) / total
        LL = 2 * ((a * log(a/E1)) + (b * log(b/E2)))
        l.append((LL,k))
    return l

def typical_words(corpus_1_counts,corpus_2_counts,c1_name='c1',c2_name='c2'):
    """Uses the log likelihood function to determine words that are typical for
    the first corpus (c1) and the second corpus (c2)."""
    
    # Thanks to Paul Rayson's website (http://ucrel.lancs.ac.uk/llwizard.html)
    # we are able to say something about which words occur *significantly* more
    # in one corpus than in the other. See the other note below.
    
    log_scores = log_likelihood(corpus_1_counts,corpus_2_counts)
    
    total       = sum(corpus_1_counts.values())
    c1_rel_freq = dict((k,float(val)/total) for k,val in corpus_1_counts.items())
    
    total       = sum(corpus_2_counts.values())
    c2_rel_freq = dict((k,float(val)/total) for k,val in corpus_2_counts.items())
    
    c1_words = []
    c2_words = []
    for val,word in log_scores:
        if val > 3.84:
            # this corresponds to the 0.05 significance level according to:
            # http://ucrel.lancs.ac.uk/llwizard.html
            if c1_rel_freq[word] > c2_rel_freq[word]:
                c1_words.append(word)
            elif c1_rel_freq[word] < c2_rel_freq[word]:
                c2_words.append(word)
    return {c1_name:c1_words, c2_name:c2_words}




# Make comparison for the normalized tags:
author_tags    = label_counter('./sound/author-tags/tag')
crowd_tags     = label_counter('./sound/crowd-tags/tag')
crowd_tags     = spacetodash(crowd_tags)

# Determine shared tags:
author_tags, crowd_tags = shared(author_tags, crowd_tags)

# Get the typical words for the author:
result = typical_words(author_tags, crowd_tags, 'freesound', 'crowd')

# Write to file:
with open('../steps/4-results/typical_normalized/freesound.txt','w') as f:
    f.write('\n'.join(result['freesound']))

with open('../steps/4-results/typical_normalized/crowd.txt','w') as f:
    f.write('\n'.join(result['crowd']))

# Make comparison for the raw tags:
author_tags    = label_counter('./sound/author-tags/tag')
raw_crowd_tags = label_counter('./sound/crowd-tags/tag/raw')
raw_crowd_tags = spacetodash(raw_crowd_tags)

# Determine shared tags:
author_tags, raw_crowd_tags = shared(author_tags, raw_crowd_tags)

# Get the typical words for the author:
result = typical_words(author_tags, raw_crowd_tags, 'freesound', 'crowd')

typical_cloud(result['freesound'], author_tags, '../steps/4-results/figures/freesound')
typical_cloud(result['crowd'], raw_crowd_tags, '../steps/4-results/figures/crowd')

# Write to file:
with open('../steps/4-results/typical_raw/freesound.txt','w') as f:
    f.write('\n'.join(result['freesound']))

with open('../steps/4-results/typical_raw/crowd.txt','w') as f:
    f.write('\n'.join(result['crowd']))

table = [['Crowd', ', '.join(random.sample(result['crowd'], 50))],
['Freesound', ', '.join(random.sample(result['freesound'], 50))]]

print(tabulate.tabulate(table, tablefmt='latex_booktabs'))
