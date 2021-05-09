import csv
import json
import random
import re

# reproducibility bit ----------------
from random import seed; seed(42)
from numpy.random import seed as np_seed; np_seed(42)
import os; os.environ['PYTHONHASHSEED'] = str(42)
# -----------------------------------

from tqdm import tqdm
from glob import glob


class DataLoader(object):

    def __init__(self):
        pass


class RedditLoader(DataLoader):

    def __init__(self, snap_dir='/data/reddit', year=2019):
        """Loads and filters Reddit data based on snap zips.

        Parameters
        ----------
        snap_dir : str, optional
            directory containing snaps, by default '/data/reddit'
        year : int, optional
            year of snaps to extract data from, by default 2019
        """
        self.snap_dir = snap_dir
        self.year = year

    def _iter(self):
        for file_name in glob(self.snap_dir + '/*' + self.year + '*'):
            try:
                if 'zst' not in file_name and 'bz2' not in file_name:
                    open_func = open
                elif 'bz2' in file_name:  # NOTE: old format compatibility
                    import bz2
                    open_func = bz2.open
                else:
                    return
                for line in tqdm(open_func(file_name, 'r')):
                    reddit_object = json.loads(line)
                    yield reddit_object['id'], reddit_object['body']
            except Exception as e:
                print(f"Error in: {e}")

    @staticmethod
    def find_gender(text):
        return re.findall(r'(?:[^A-Za-z0-9]+)' +
                          r'([sS]he|[hH]e|[hH]is|[hH]im|' +
                          r'[hH]er|[hH]ers|[hH]imself|[hH]erself]){1}' +
                          r'[^A-Za-z0-9]', text)

    @staticmethod
    def preprocess_sent(sent):
        sent = ' '.join(sent.replace('\n', ' ').split())
        if sent[0] == ' ':
            sent = sent[1:]
        if sent[-1] not in ['.', ',', '?', '!', '*']:
            sent = sent + '.'
        return sent

    def _doc_to_gender_sents(self, doc):
        for sent in re.split(r'\.|\?|\!', doc):
            if self.find_gender(sent):
                yield self.preprocess_sent(sent)

    def to_full_csv(self, file_out='./reddit_gender.csv'):
        """Dump full dataset as csv in file_out location.

        Parameters
        ----------
        file_out : str, optional
            directory path of dump file, by default './reddit_gender.csv'
        """
        csv_writer = csv.writer(open(file_out, 'a'), delimiter=',',
                                quotechar="'", quoting=csv.QUOTE_ALL)
        for _id, doc in tqdm(self._iter()):
            for sent in self._doc_to_gender_sents(doc):
                csv_writer.writerow([_id, sent])

    def _get_samples(self):
        data, samples = {}, {}
        for _id, doc in tqdm(self._iter()):
            for ix, sent in enumerate(self.doc_to_gender_sents(doc)):
                data[ix] = (_id, sent)
                for hit in self.find_gender(sent):
                    form = ''.join(hit).lower()
                    if form == 'hisself':  # nope
                        continue
                    if not samples.get(form):
                        samples[form] = []
                    samples[form].append(ix)
        return data, samples

    def to_train_test_splits(self, dir_out='./'):
        """Dump train and test splits in dir_out location.

        Parameters
        ----------
        dir_out : str, optional
            directory path to dump train and test, by default './'
        """
        (data, samples), sample_idx = self._get_samples(), []
        with open(dir_out + 'reddit.test', 'w') as fo:
            for sample in samples:
                for instance in random.sample(samples[sample], 80):
                    sample_idx.append(instance)
                    fo.write(data[instance][1] + '\n')
        with open(dir_out + './reddit.test', 'w') as fo:
            for ix, (_id, sent) in tqdm(data.items()):
                if ix not in sample_idx:
                    fo.write(sent + '\n')


if __name__ == '__main__':
    # from glob import glob
    # from multiprocessing import Pool
    # get_sample()
    pass
