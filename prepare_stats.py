import os
import requests
import csv
import codecs
import matplotlib.pyplot as plt
import json

DATA_ROOT = '/Users/martinsf/ai/deep_learning_projects/data'
URL_WORDNET = 'http://image-net.org/archive/words.txt'
IMAGENET_API_WNID_TO_URLS = lambda wnid: f'http://www.image-net.org/api/text/imagenet.synset.geturls?wnid={wnid}'

current_folder = os.path.dirname(os.path.realpath(__file__))

wordnet_filename = URL_WORDNET.split('/')[-1]
wordnet_file_path = os.path.join(current_folder, wordnet_filename)
print(wordnet_file_path)
if not os.path.exists(wordnet_file_path):

    print(f'Downloading {URL_WORDNET}')
    resp = requests.get(URL_WORDNET)

    with open(wordnet_file_path, "wb") as file:
        file.write(resp.content)
        file.close()

# Downloaded from http://image-net.org/imagenet_data/urls/imagenet_fall11_urls.tgz
url_list_filepath = '/Users/martinsf/ai/datasets/imagenet/fall11_urls.txt'
img_url_dict = dict()

total_urls = 0
flickr_urls = 0

#Go trough the urls list and count urls per class and flickr_urls per class, store the info in csv
with codecs.open(url_list_filepath, 'r', encoding='utf-8', errors='ignore') as f:
    it = 0
    for line  in f:
        it += 1
        if it % 10000 == 0:
            print(it)
        row = line.split('\t')

        if (len(row) != 2):
            continue
        id = row[0].split('_')[0]
        url = row[1]

        if not id in img_url_dict:
            img_url_dict[id] = dict(urls = 0, flickr_urls = 0)

        img_url_dict[id]['urls'] += 1
        total_urls += 1
        if 'flickr' in url:
            flickr_urls += 1
            img_url_dict[id]['flickr_urls'] += 1


    wnid_to_class_dict = dict()
    with open(wordnet_file_path, "r") as word_list_file:
            csv_reader_word_list = csv.reader(word_list_file, delimiter='\t')
            for row in csv_reader_word_list:
                wnid = row[0]
                keywords = row[1]
                wnid_to_class_dict[wnid] = keywords

    class_info_json_filename = 'imagenet_class_info.json'
    class_info_json_filepath = os.path.join(current_folder, class_info_json_filename)

    img_counts = []
    total_url_counts = []
    flickr_url_counts = []

    class_info_dict = dict()

    with open("classes_in_imagenet.csv", "w") as csv_f:
        csv_writer  = csv.writer(csv_f, delimiter=",")
        csv_writer.writerow(["synid", "class_name", "urls", "flickr_urls"])

        for key, val in img_url_dict.items():
            class_info_dict[key] = dict(
                img_url_count = val['urls'],
                flickr_img_url_count = val['flickr_urls'],
                class_name = wnid_to_class_dict[key].split(',')[0]
            )
            print(f'{wnid_to_class_dict[key]} {len(val)}')
            total_url_counts.append(val['urls'])
            csv_writer.writerow([key, wnid_to_class_dict[key].split(',')[0], val['urls'], val["flickr_urls"]])

            flickr_url_counts.append(val['flickr_urls'])


    with open(class_info_json_filepath,"w") as class_info_json_f:
        json.dump(class_info_dict, class_info_json_f)
        csv_writer = csv.writer(class_info_json_f, delimiter=';')

    print(f'In total there are {total_urls} img urls and {flickr_urls} flickr urls')

    fig, axs = plt.subplots(3,1)
    plt.style.use('seaborn')

    plt.subplots_adjust(hspace = 0.5)

    axs[0].hist(total_url_counts, range=(500,2000), bins=50, rwidth=0.8)
    axs[0].set_title('All ImageNet urls')
    axs[0].set_xticks([x for x in range(500,2000,150)])
    axs[0].set_xlabel("Images per class")
    axs[0].set_ylabel("Number of classes")

    axs[1].set_title('Flickr ImageNet urls')
    axs[1].hist(flickr_url_counts, range=(500,2000), bins=50, rwidth=0.8)
    axs[1].set_xticks([x for x in range(500,2000,150)])
    axs[1].set_xlabel("Images per class")
    axs[1].set_ylabel("Number of classes")

    axs[2].set_title('Flickr ImageNet urls')
    axs[2].hist(flickr_url_counts, range=(500,2000), bins=50, rwidth=0.8, cumulative=-1)
    axs[2].set_xticks([x for x in range(500,2000,150)])
    axs[2].set_xlabel("Images per class")
    axs[2].set_ylabel("Number of classes")

    plt.show()