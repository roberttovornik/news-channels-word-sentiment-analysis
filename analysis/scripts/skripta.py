import os
import gensim
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from itertools import combinations,chain
from sklearn.manifold import TSNE
from googletrans import Translator #pip3 install git+https://github.com/BoseCorp/py-googletrans.git --upgrade




def list_word_pos(df):
    word_pos_tags={}
    for idx,row in df.iterrows():
        if isinstance(row['article_text_processed_lemmatized'], float):
            continue
        lemmatized_text=row['article_text_processed_lemmatized'].split()
        pos_taggs=row['article_text_processed_POS'].split()
        for i in range(len(lemmatized_text)):
            lemma = lemmatized_text[i]
            if lemma=='_':
                continue
            tag=pos_taggs[i]
            if lemma not in word_pos_tags:
                word_pos_tags[lemma]=[tag[0]]
            elif tag[0] not in word_pos_tags[lemma]:
                word_pos_tags[lemma].append(tag[0])
    return word_pos_tags

def words_to_pos(region_name):
    df_file_path='../../pre-processing/data/'+region_name+'.pkl'
    df=pd.read_pickle(df_file_path)
    return list_word_pos(df)

def load_sentiWordNet(file_path='../external_data_sources/SentiWordNet_3.0.0_20130122.txt'):
    return pd.read_csv(file_path,delimiter='\t',comment='#')

def slo_to_eng(slo_word_list):
    #Reaching API request limit
    translator = Translator()
    print(slo_word_list)
    translations = translator.translate(slo_word_list,src='sl',dest='en')

    '''
    #Reaching API request limit
    #https://stackoverflow.com/questions/49497391/googletrans-api-error-expecting-value-line-1-column-1-char-0?fbclid=IwAR1Av8FtpIiBaTfJaesyR7-Jk63aNp0_JHPU-a6VdvcxZcXkDCZQn3neW0s
    translations=[]
    for w in slo_word_list:
        translator = Translator()
        translations.append(translator.translate(w,src='sl',dest='en'))
    '''
    return [translation.text if len(translation.text.split())==1 else translations.text.split[-1] for translation in translations if len(translation.text.split())==1] #REMOVE CONDITION WHEN WORKING WITH PHRASES

def label_point(x, y, val, ax):
    a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
    for i, point in a.iterrows():
        ax.text(point['x']+.02, point['y'], str(point['val']))

'''
def visualise_model(model,output_file_path, label_points=True,additional_data=None):
    vocab = list(model.wv.vocab)

    X = model[vocab]
    tsne = TSNE(n_components=2)
    X_tsne = tsne.fit_transform(X)
    df = pd.DataFrame({'x':X_tsne[:,0],'y':X_tsne[:,1],'vocab':vocab,'word class':word_context_class}, index=vocab)

    ax = sns.lmplot('x',
                    'y',
                    hue='word class',
                    #hue_order=['DISTANT','NEUTRAL','POSITIVE','NEGATIVE','KEYWORD'],
                    #palette={'DISTANT':'grey','NEUTRAL':'blue','POSITIVE':'green','NEGATIVE':'red','KEYWORD':'yellow'},
                    hue_order=['other','POSITIVE','NEGATIVE','KEYWORD'],
                    palette={'other':'grey','KEYWORD':'blue','POSITIVE':'green','NEGATIVE':'red'},
                    data=df,  # Data source
                    fit_reg=False,  # Don't fix a regression line
                    size=10,
                    aspect=2)  # size and dimension
    if label_points:
        df=df[df['word class']!='other']
        label_point(df['x'], df['y'], df['vocab'], plt.gca())
    #plt.show()
    plt.savefig(output_file_path)
'''

words_of_interest_slovene=['migrant','prebežnik','begunec']
words_of_interest_english=['migrant','immigrant','refugee'] #'asylum seeker' #Handle phrases
regions_slovene=['Slovenia']

sentiWordNet=load_sentiWordNet()
#sentiWordNet['objectiveScore']=sentiWordNet['PosScore']+sentiWordNet['NegScore']
#sentiWordNet['objectiveScore']=1-(sentiWordNet['PosScore']+sentiWordNet['NegScore'])
sentiWordNet['objectiveScore']=sentiWordNet['PosScore'] - sentiWordNet['NegScore']
#remove neutral words
#sentiWordNet = sentiWordNet[(sentiWordNet['PosScore'] != 0.0) & (sentiWordNet['NegScore'] != 0.0)]
model_dir='../../data_modeling/models/'
word_info=pd.DataFrame({'WORD':[],'IS_ADJECTIVE':[],'IS_NOUN':[],'IS_VERB':[],'SENTI_SCORE':[],'SENTI_CLASS':[]})
similar_words_byRegion_byKeywords=pd.DataFrame({'REGION':[],'KEYWORDS':[],'SIMILAR_WORD':[],'SIMILARITY_DISTANCE':[]})
sentiScore_byRegion_byKeywords={'REGION':[],'KEYWORDS':[],'SENTI_SCORE':[]}
for filename in os.listdir(model_dir):
    if filename.endswith(".model"):
        region_name = filename[:filename.index('_word2vec.model')]

        '''
        if region_name not in ['Austria','Norway']:
            continue
        '''
        if region_name not in regions_slovene:
            continue

        #List POS tags, that each lemma's origin word in corpus is tagged with
        words2pos = words_to_pos(region_name)
        model_file_path = os.path.join(model_dir, filename)
        print('***Article analysis for region:', region_name)
        print('\tRestoring model from file:', model_file_path)
        model=gensim.models.Word2Vec.load(model_file_path)
        print('\t...done.')

        #Add description for new words
        print('\tClassifying words in model vocabulary based on their sentiment score.')
        vocab = list(model.wv.vocab)
        vocab.remove('_') #Quick&dirty fix
        if not region_name in regions_slovene: #googletrans API limit reached:P
            vocab_eng=slo_to_eng(vocab) if region_name in regions_slovene else vocab
        for i in range(len(vocab)):
            if not region_name in regions_slovene:  # googletrans API limit reached:P
                w=vocab_eng[i]
            w_true=vocab[i]
            if w_true in word_info['WORD']:
                continue
            row={'WORD':[],'IS_ADJECTIVE':[],'IS_NOUN':[],'IS_VERB':[],'SENTI_SCORE':[],'SENTI_CLASS':[]}
            row['WORD'].append(w_true)
            row['IS_ADJECTIVE'].append(True if (region_name in regions_slovene and 'P' in words2pos[w_true]) or (region_name not in regions_slovene and 'J' in words2pos[w_true]) else False)
            row['IS_NOUN'].append(True if (region_name in regions_slovene and 'S' in words2pos[w_true]) or (region_name not in regions_slovene and 'N' in words2pos[w_true]) else False)
            row['IS_VERB'].append(True if (region_name in regions_slovene and 'G' in words2pos[w_true]) or (region_name not in regions_slovene and 'V' in words2pos[w_true]) else False)
            if not region_name in regions_slovene:  # googletrans API limit reached:P
                sentiWordNet_score_word = sentiWordNet[(sentiWordNet['SynsetTerms'] == w)]
                if sentiWordNet_score_word.shape[0] <= 1:
                    sentiWordNet_score=sentiWordNet_score_word
                else:
                    pos_tag_filter = []  # append all-false vector
                    if row['IS_ADJECTIVE']:
                        pos_tag_filter.append((sentiWordNet_score_word['POS'] == 'a'))
                    if row['IS_NOUN']:
                        pos_tag_filter.append((sentiWordNet_score_word['POS'] == 'n'))
                    if row['IS_VERB']:
                        pos_tag_filter.append((sentiWordNet_score_word['POS'] == 'v'))
                    pos_tag_filter = np.array(sum(pos_tag_filter)).astype(bool)
                    sentiWordNet_score=sentiWordNet_score_word[pos_tag_filter]
                pos_score = sum(sentiWordNet_score['PosScore'])
                neg_score = sum(sentiWordNet_score['NegScore'])
                row['SENTI_SCORE'].append(pos_score-neg_score)
                row['SENTI_CLASS'].append('POSITIVE' if pos_score > neg_score else 'NEGATIVE' if pos_score < neg_score else 'NEUTRAL' if pos_score==neg_score else 'N/A')
            else:
                row['SENTI_SCORE'].append(np.nan)
                row['SENTI_CLASS'].append(np.nan)
            word_info=word_info.append(pd.DataFrame(row))
        print('\t...done.')

        print('\tCreating all combinations of keywords for analysis...')
        words_of_interest=words_of_interest_slovene if region_name in regions_slovene else words_of_interest_english
        combinations_of_words_of_interest=list(chain.from_iterable([combinations(words_of_interest,i) for i in range(1,len(words_of_interest))]))#.append(tuple(words_of_interest))
        combinations_of_words_of_interest.append(tuple(words_of_interest))

        if region_name in regions_slovene:  # googletrans API limit reached:P
            combinations_of_words_of_interest=combinations_of_words_of_interest[-2:]
        print('\tcombos:',combinations_of_words_of_interest)
        print('\t...done.')

        file=open('../word_neighborhood/'+region_name+'.txt','w')
        similar_words_rows={'REGION':[],'KEYWORDS':[],'SIMILAR_WORD':[],'SIMILARITY_DISTANCE':[]}
        for words_of_interest_combo in combinations_of_words_of_interest:
            print('\tAdjectives closest to:',words_of_interest_combo,'are:')
            #Finding closes/most similar words to those of interest
            similar_words = model.wv.most_similar(words_of_interest_combo, topn=250)

            if region_name in regions_slovene: # googletrans API limit reached:P
                for w_true,distance in similar_words:
                    if w_true in word_info['WORD'].values and not any((word_info['WORD']==w_true) & word_info['SENTI_CLASS'].notnull()):
                        print('WORD ALREADY IN WORD INFO:',w_true in word_info['WORD'].values)
                        print('W_TRUE\'s SENTI CLASS IS NOT NULL',any((word_info['WORD']==w_true) & word_info['SENTI_CLASS'].notnull()))
                        w=slo_to_eng([w_true])
                        if len(w)==0:
                            #neuspesen prevod --> nepravilna beseda?, ali pa vecbeseden prevod?
                            #fallback: random word with neutral score:P
                            fallback_translation='macedonian'
                            print('Failed translation!!',w)
                            print('Substitution with fallback neutral word',fallback_translation)
                            w=fallback_translation

                        else:
                            w=w[0]
                        print('***TRANSLATION:',w)
                        row=word_info.loc[word_info['WORD']==w_true].iloc[0]
                        #print('ROW',row)

                        sentiWordNet_score_word = sentiWordNet.loc[sentiWordNet['SynsetTerms'] == w]
                        if sentiWordNet_score_word.shape[0] <= 1:
                            sentiWordNet_score = sentiWordNet_score_word
                        else:
                            pos_tag_filter = []  # append all-false vector
                            if row['IS_ADJECTIVE']:
                                pos_tag_filter.append((sentiWordNet_score_word['POS'] == 'a'))
                            if row['IS_NOUN']:
                                pos_tag_filter.append((sentiWordNet_score_word['POS'] == 'n'))
                            if row['IS_VERB']:
                                pos_tag_filter.append((sentiWordNet_score_word['POS'] == 'v'))
                            if len(pos_tag_filter)==0:
                                #word is not ADJECTIVE,NOUN or VERB
                                #Quick&dirty: word sentiment is NEUTRAL
                                word_info.loc[word_info['WORD'] == w_true, 'SENTI_SCORE'] = 0
                                word_info.loc[word_info['WORD'] == w_true, 'SENTI_CLASS'] = 'NEUTRAL'
                                continue
                            else:
                                #print('POS TAG FILTER BEFORE SUMMATION',pos_tag_filter)
                                pos_tag_filter = np.array(sum(pos_tag_filter)).astype(bool)
                                #print('POS TAG FILTER',pos_tag_filter)
                                #print('SENTI WORD NET CORE WORD', sentiWordNet_score_word)
                                #print('LEN POS TAG FILTER',len(pos_tag_filter))
                                sentiWordNet_score = sentiWordNet_score_word[pos_tag_filter]
                        pos_score = sum(sentiWordNet_score['PosScore'])
                        neg_score = sum(sentiWordNet_score['NegScore'])
                        word_info.loc[word_info['WORD'] == w_true, 'SENTI_SCORE']=pos_score - neg_score
                        word_info.loc[word_info['WORD'] == w_true, 'SENTI_CLASS']='POSITIVE' if pos_score > neg_score else 'NEGATIVE' if pos_score < neg_score else 'NEUTRAL' if pos_score == neg_score else 'N/A'


            for word in similar_words:
                similar_words_rows['REGION'].append(region_name)
                similar_words_rows['KEYWORDS'].append(str(words_of_interest_combo))
                similar_words_rows['SIMILAR_WORD'].append(word[0])
                similar_words_rows['SIMILARITY_DISTANCE'].append(word[1])

            similar_adjectives_with_sentiWord_score = list(word_info.loc[word_info['WORD'].isin([x[0] for x in similar_words]) & (word_info['IS_ADJECTIVE']),'WORD'])
            similar_adjectives_positive = list(word_info.loc[word_info['WORD'].isin([x[0] for x in similar_words]) & (word_info['IS_ADJECTIVE']) & (word_info['SENTI_CLASS']=='POSITIVE'),'WORD'])
            similar_adjectives_negative = list(word_info.loc[word_info['WORD'].isin([x[0] for x in similar_words]) & word_info['IS_ADJECTIVE'] & (word_info['SENTI_CLASS']=='NEGATIVE'),'WORD'])
            similar_adjectives_neutral = list(word_info.loc[word_info['WORD'].isin([x[0] for x in similar_words]) & (word_info['IS_ADJECTIVE']) & (word_info['SENTI_CLASS']=='NEUTRAL'),'WORD'])
            similar_adjectives_with_sentiWord_score_str='\t\t'+'\n\t\t'.join([str(x) for x in similar_adjectives_with_sentiWord_score])
            #Calculate sentiment score
            objective_score_mean = np.nanmean(word_info.loc[word_info['WORD'].isin(similar_adjectives_with_sentiWord_score),'SENTI_SCORE'].values)
            sentiScore_byRegion_byKeywords['REGION'].append(region_name)
            sentiScore_byRegion_byKeywords['KEYWORDS'].append(str(words_of_interest_combo))
            sentiScore_byRegion_byKeywords['SENTI_SCORE'].append(objective_score_mean)
            print(similar_adjectives_with_sentiWord_score_str)
            print('\t\t\tMEAN OBJECTIVE SCORE:',objective_score_mean)
            file.write('\nWords closest to: '+str(words_of_interest_combo)+' are:\n'+similar_adjectives_with_sentiWord_score_str+'\n\t\tMEAN OBJECTIVE SCORE:'+str(objective_score_mean))
            print('\t...done.')
        file.close()
        similar_words_byRegion_byKeywords=similar_words_byRegion_byKeywords.append(pd.DataFrame(similar_words_rows))
    else:
        continue
sentiScore_byRegion_byKeywords=pd.DataFrame(sentiScore_byRegion_byKeywords)

df=similar_words_byRegion_byKeywords.copy(deep=True)
#df['SENTI_CLASS']=df.apply(lambda row: word_info.loc[word_info['WORD']==row['SIMILAR_WORD'],'SENTI_CLASS'],axis=1)
df['SENTI_CLASS']=df.apply(lambda row: word_info.loc[word_info['WORD']==row['SIMILAR_WORD'],'SENTI_CLASS'].values[0],axis=1)
df=df[df['SENTI_CLASS']!='N/A']
for keywords,group in df.groupby('KEYWORDS'):
    sns.countplot(y="REGION", hue="SENTI_CLASS", data=group)
    plt.savefig('../region_wordCount_sentiment_similarAdjectives_250_'+keywords+'.png')
    plt.close()

'''
#DOPOLNI!!!!
if not os.path.exists('../models_scatter_plots'):
    os.makedirs('../models_scatter_plots')
df['SENTI_CLASS']=df.apply(lambda row: 'KEYWORD' if row['SIMILAR_WORD'] in row['KEYWORDS'].replace('\'','')[1:-1].split(',') else row['SENTI_CLASS'],axis=1)

for region_keywords,group in df.groupby(['REGION','KEYWORDS']):
    visualise_model(group)
'''
#Visualize final sentiment by region
sentiScore_byRegion_byKeywords=sentiScore_byRegion_byKeywords.sort_values(by=['SENTI_SCORE'])
sns.catplot(x="REGION", y="SENTI_SCORE", hue='KEYWORDS', kind="point", data=sentiScore_byRegion_byKeywords)
#plt.show()
plt.savefig('../plot_region_sentimentScore.png')
plt.close()


