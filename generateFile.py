#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import random

from collections import defaultdict

instances = []
label_set = []


# mark the location of entities in a sentence and get the corresponding relations

def get_relations(dataset):

    for i in range(len(dataset)):
        list_sentences = [0]
        len_list_sentences = 0

        # get length of each list of sentences from 'sents' field

        for x in dataset[i]['sents']:
            len_list_sentences += len(x)
            list_sentences.append(len_list_sentences)

        # get vertexSet details

        vertexSet = dataset[i]['vertexSet']

        # point position added with sent start position

        for j in range(len(vertexSet)):
            for k in range(len(vertexSet[j])):
                vertexSet[j][k]['sent_id'] = \
                    int(vertexSet[j][k]['sent_id'])
                sent_id = vertexSet[j][k]['sent_id']
                dict_len = list_sentences[sent_id]
                pos1 = vertexSet[j][k]['pos'][0]
                pos2 = vertexSet[j][k]['pos'][1]
                vertexSet[j][k]['pos'] = (pos1 + dict_len, pos2 + dict_len)

        sentences = dataset[i]['sents']
        labels = dataset[i].get('labels', [])
        sent_length = {}
        j = 0

        while j < len(sentences):
            sent_length[j] = len(sentences[j])
            j = j + 1

        modVertexSet = []

        # modify the position to mark the location of entities in the sentence

        for vertexset in vertexSet:
            tmp = []
            for vertex in vertexset:
                pos = vertex['pos']
                sent_id = vertex['sent_id']
                prev_sents = []
                for i in range(0, sent_id):
                    prev_sents.append(i)

                prev_sent_length = 0
                for term in prev_sents:
                    prev_sent_length += sent_length.get(term)

                if sent_id != 0:
                    mod_pos = (pos[0] - prev_sent_length, pos[1] - prev_sent_length)
                else:
                    mod_pos = pos

                vertex['mod_pos'] = mod_pos
                tmp.append(vertex)

            modVertexSet.append(tmp)

        # locate the head, tail, evidence and relation for each label

        for label in labels:
            inst_tmp = []

            if label['r'] not in label_set:
                label_set.append(label['r'])

            inst_tmp.append(label['r'])

            head = label['h']
            tail = label['t']
            evidence = label['evidence']

            head_vertex = vertexSet[head]
            tail_vertex = vertexSet[tail]

            # get random entity from head_vertex

            rand_num_head = random.randint(0, len(head_vertex) - 1)
            req_ent_head = head_vertex[rand_num_head]
            sent_id_head = req_ent_head['sent_id']
            pos_head = req_ent_head['mod_pos']

            # get random entity from tail_vertex

            rand_num_tail = random.randint(0, len(tail_vertex) - 1)
            req_ent_tail = tail_vertex[rand_num_tail]
            sent_id_tail = req_ent_tail['sent_id']
            pos_tail = req_ent_tail['mod_pos']

            # if both entities are in same sentence

            if sent_id_head == sent_id_tail:

                sentence = sentences[sent_id_tail]
                mod_sent = []
                j = 0
                while j < len(sentence):

                    # if entity1, then add <e1> tag

                    if j == pos_head[0]:
                        toks = []
                        for i in range(pos_head[0], pos_head[1]):
                            toks.append(sentence[i])
                        mod_sent.append('<e1> ' + ' '.join(toks) + ' </e1>')
                        j = j + len(toks) - 1

                    # if entity2, then add <e2> tag

                    if j == pos_tail[0]:
                        toks = []
                        for i in range(pos_tail[0], pos_tail[1]):
                            toks.append(sentence[i])
                        mod_sent.append('<e2> ' + ' '.join(toks) + ' </e2>')
                        j = j + len(toks) - 1
                    else:

                        mod_sent.append(sentence[j])
                    j = j + 1

                inst_tmp.append(' '.join(mod_sent))
                instances.append(inst_tmp)

            # if both entities are in different sentences

            if sent_id_head != sent_id_tail:

                sent_toks = []
                sentence = sentences[sent_id_head]
                mod_sent_head = []
                j = 0
                while j < len(sentence):

                    # if entity1, then add <e1> tag

                    if j == pos_head[0]:
                        toks = []
                        for i in range(pos_head[0], pos_head[1]):
                            toks.append(sentence[i])
                        mod_sent_head.append('<e1> ' + ' '.join(toks) + ' </e1>')
                        j = j + len(toks) - 1
                    else:
                        mod_sent_head.append(sentence[j])
                    j = j + 1

                for term in mod_sent_head:
                    sent_toks.append(term)

                sentence = sentences[sent_id_tail]
                mod_sent_tail = []
                j = 0
                while j < len(sentence):

                    # if entity2, then add <e2> tag

                    if j == pos_tail[0]:
                        toks = []
                        for i in range(pos_tail[0], pos_tail[1]):
                            toks.append(sentence[i])
                        mod_sent_tail.append('<e2> ' + ' '.join(toks) + ' </e2>')
                        j = j + len(toks) - 1
                    else:
                        mod_sent_tail.append(sentence[j])
                    j = j + 1

                for term in mod_sent_tail:
                    sent_toks.append(term)

                inst_tmp.append(' '.join(sent_toks))
                instances.append(inst_tmp)

                temp_sent = []

                # collect evidence sentences for each relation

                for e in evidence:

                    # get evidence sentences which are not identified by the relation's 'sent_id'

                    if e != sent_id_head or e != sent_id_tail:
                        sentence = sentences[e]
                        head_name = req_ent_head['name']
                        tail_name = req_ent_tail['name']

                        line = ' '.join(sentence)
                        if head_name in line:
                            new_head = '<e1> ' + head_name + ' </e1>'
                            line = line.replace(head_name, new_head)
                        if tail_name in line:
                            new_tail = '<e2> ' + tail_name + ' </e2>'
                            line = line.replace(tail_name, new_tail)
                        temp_sent.append(line)
                if temp_sent:
                    instances.append(temp_sent)


data_file_name = 'train_annotated.json'

ori_data = json.load(open(data_file_name))

get_relations(ori_data)

labels_count = defaultdict(int)
for inst in instances:
    labels_count[inst[0]] += 1

# write the relations and sentences pair to tsv file

with open('train.tsv', 'w', encoding='utf-8') as f:
    for term in instances:
        f.write('\t'.join(term) + '\n')
f.close()

label_set.sort()

# get all the unique relations in the json

with open('labels.txt', 'w', encoding='utf-8') as f:
    for term in label_set:
        f.write(term + '\n')
f.close()