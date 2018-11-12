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
    return [translation.text for translation in translations if len(translation.text.split())==1] #REMOVE CONDITION WHEN WORKING WITH PHRASES

def label_point(x, y, val, ax):
    a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
    for i, point in a.iterrows():
        ax.text(point['x']+.02, point['y'], str(point['val']))

def visualise_model(model,output_file_path, label_points=True,additional_data=None):
    vocab = list(model.wv.vocab)
    word_context_class = None
    if additional_data is not None:
        relevant_row=additional_data.iloc[0]
        positive=list(relevant_row['positive adjectives'])
        negative=list(relevant_row['negative adjectives'])
        neutral=list(relevant_row['neutral adjectives'])
        keywords=relevant_row['keyword combo'][1:-1].replace(',',' ').replace('\'','').split()
        #word_context_class = ['POSITIVE' if x in positive else 'NEGATIVE' if x in negative else 'NEUTRAL' if x in neutral else 'KEYWORD' if x in keywords else 'DISTANT' for x in vocab]
        word_context_class = ['POSITIVE' if x in positive else 'NEGATIVE' if x in negative else 'KEYWORD' if x in keywords else 'other' for x in vocab]

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

words_of_interest_slovene=['azilant','migrant','prebežnik']
words_of_interest_english=['migrant','refugee'] #'asylum seeker' #Handle phrases
regions_slovene=['Slovenia']

sentiWordNet=load_sentiWordNet()
#sentiWordNet['objectiveScore']=sentiWordNet['PosScore']+sentiWordNet['NegScore']
#sentiWordNet['objectiveScore']=1-(sentiWordNet['PosScore']+sentiWordNet['NegScore'])
sentiWordNet['objectiveScore']=sentiWordNet['PosScore'] - sentiWordNet['NegScore']
#remove neutral words
#sentiWordNet = sentiWordNet[(sentiWordNet['PosScore'] != 0.0) & (sentiWordNet['NegScore'] != 0.0)]
model_dir='../../data_modeling/models/'
model_words_sentiment_by_region = {'REGION': [], 'WORD': [], 'SENTIMENT': []}
regionNews_sentiment_scores={'region':[],'sentiment score':[], 'keyword combo':[], 'positive adjectives':[], 'negative adjectives':[], 'neutral adjectives':[]}
tmp={'REGION':[],'WORD':[],'SENTIMENT':[]}
for filename in os.listdir(model_dir):
    if filename.endswith(".model"):
        region_name = filename[:filename.index('_word2vec.model')]

        if region_name in ['Slovenia']:
            continue

        words2pos = words_to_pos(region_name)
        model_file_path = os.path.join(model_dir, filename)
        print('***Article analysis for region:', region_name)
        print('\tRestoring model from file:', model_file_path)
        model=gensim.models.Word2Vec.load(model_file_path)
        print('\t...done.')

        vocab = list(model.wv.vocab)
        for w in vocab:
            sentiWordNet_score = sentiWordNet[sentiWordNet['SynsetTerms'] == w]
            pos_score = sum(sentiWordNet_score['PosScore'])
            neg_score = sum(sentiWordNet_score['NegScore'])
            model_words_sentiment_by_region['WORD'].append(w)
            model_words_sentiment_by_region['REGION'].append(region_name)
            if pos_score > neg_score:
                model_words_sentiment_by_region['SENTIMENT'].append('POSITIVE')
            elif pos_score < neg_score:
                model_words_sentiment_by_region['SENTIMENT'].append('NEGATIVE')
            else:
                model_words_sentiment_by_region['SENTIMENT'].append('NEUTRAL')

        words_of_interest=words_of_interest_slovene if region_name in regions_slovene else words_of_interest_english
        combinations_of_words_of_interest=list(chain.from_iterable([combinations(words_of_interest,i) for i in range(1,len(words_of_interest))]))#.append(tuple(words_of_interest))
        combinations_of_words_of_interest.append(tuple(words_of_interest))
        print('combos:',combinations_of_words_of_interest)

        file=open('../word_neighborhood/'+region_name+'.txt','w')
        for words_of_interest_combo in combinations_of_words_of_interest:
            print('\tWords closest to:',words_of_interest_combo,'are:')
            similar_words = model.wv.most_similar(words_of_interest_combo, topn=250)
            similar_words_in_english=slo_to_eng([x[0] for x in similar_words]) if region_name in regions_slovene else [x[0] for x in similar_words]
            similar_words_with_sentiWord_score = [similar_words[x] for x in range(len(similar_words_in_english)) if similar_words_in_english[x] in list(sentiWordNet['SynsetTerms'])]
            #similar_adjectives_with_sentiWord_score = [similar_words_with_sentiWord_score[x] for x in range(len(similar_words_with_sentiWord_score)) if (region_name in regions_slovene and 'P' in words2pos[similar_words_with_sentiWord_score[x][0]]) or (region_name not in regions_slovene and 'J' in words2pos[similar_words_with_sentiWord_score[x][0]])]
            similar_adjectives_with_sentiWord_score = []
            similar_adjectives_positive = []
            similar_adjectives_negative = []
            similar_adjectives_neutral = []
            for w in similar_words_with_sentiWord_score:
                if (region_name in regions_slovene and 'P' in words2pos[w[0]]) or (region_name not in regions_slovene and 'J' in words2pos[w[0]]):
                   #ADJECTIVE
                    similar_adjectives_with_sentiWord_score.append(w)
                    tmp['WORD'].append(w)
                    tmp['REGION'].append(region_name)
                    sentiWordNet_score=sentiWordNet[sentiWordNet['SynsetTerms']==w[0]]
                    pos_score=sum(sentiWordNet_score['PosScore'])
                    neg_score = sum(sentiWordNet_score['NegScore'])
                    if pos_score>neg_score:
                        similar_adjectives_positive.append(w[0])
                        tmp['SENTIMENT'].append('POSITIVE')
                    elif pos_score<neg_score:
                        similar_adjectives_negative.append(w[0])
                        tmp['SENTIMENT'].append('NEGATIVE')
                    else:
                        similar_adjectives_neutral.append(w[0])
                        tmp['SENTIMENT'].append('NEUTRAL')

            regionNews_sentiment_scores['positive adjectives'].append(similar_adjectives_positive)
            regionNews_sentiment_scores['negative adjectives'].append(similar_adjectives_negative)
            regionNews_sentiment_scores['neutral adjectives'].append(similar_adjectives_neutral)

            similar_adjectives_with_sentiWord_score_str='\t\t'+'\n\t\t'.join([str(x) for x in similar_adjectives_with_sentiWord_score])
            sentiWordNet_relevant_rows=sentiWordNet[(sentiWordNet['SynsetTerms'].isin([x[0] for x in similar_adjectives_with_sentiWord_score])) & (sentiWordNet['POS']=='a')]
            objective_score_mean=np.nanmean(sentiWordNet_relevant_rows['objectiveScore'])
            regionNews_sentiment_scores['region'].append(region_name)
            regionNews_sentiment_scores['sentiment score'].append(objective_score_mean)
            regionNews_sentiment_scores['keyword combo'].append(str(words_of_interest_combo))
            print(similar_adjectives_with_sentiWord_score_str)
            print('\t\t\tMEAN OBJECTIVE SCORE:',objective_score_mean)
            file.write('\nWords closest to: '+str(words_of_interest_combo)+' are:\n'+similar_adjectives_with_sentiWord_score_str+'\n\t\tMEAN OBJECTIVE SCORE:'+str(objective_score_mean))
            print('\t...done.')
        file.close()
        regionNews_sentiment_scores_df = pd.DataFrame.from_dict(regionNews_sentiment_scores)
        if words_of_interest_combo == tuple(words_of_interest):
            if not os.path.exists('../models_scatter_plots'):
                os.makedirs('../models_scatter_plots')
            data=regionNews_sentiment_scores_df.loc[(regionNews_sentiment_scores_df['keyword combo']==str(tuple(words_of_interest))) & (regionNews_sentiment_scores_df['region']==region_name)]
            visualise_model(model, '../models_scatter_plots/' + region_name + '.png',additional_data=data)
    else:
        continue
#
df=pd.DataFrame(model_words_sentiment_by_region)
sns.countplot(y="REGION", hue="SENTIMENT", data=df)
plt.savefig('../region_wordCount_sentiment.png')

df=pd.DataFrame(tmp)
sns.countplot(y="REGION", hue="SENTIMENT", data=df)
plt.savefig('../region_wordCount_sentiment_similarAdjectives_250.png')


#Visualize final sentiment by region
data=pd.DataFrame(regionNews_sentiment_scores)
data=data.sort_values(by=['sentiment score'])
sns.catplot(x="region", y="sentiment score", hue='keyword combo', kind="point", data=data)
#plt.show()
plt.savefig('../plot_region_sentimentScore.png')