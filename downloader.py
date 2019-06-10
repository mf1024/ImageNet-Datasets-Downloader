import os
import numpy as np
import requests
import argparse
import json

from requests.exceptions import ConnectionError, ReadTimeout, TooManyRedirects, MissingSchema

parser = argparse.ArgumentParser(description='ImageNet image scraper')
parser.add_argument('-scrape_only_flickr', default=True, type=lambda x: (str(x).lower() == 'true'))
parser.add_argument('-number_of_classes', default = 10, type=int)
parser.add_argument('-images_per_class', default = 10, type=int)
parser.add_argument('-data_root', default='' , type=str)
parser.add_argument('-use_class_list', default=False,type=lambda x: (str(x).lower() == 'true'))
parser.add_argument('-class_list', default=[], nargs='*')

args, args_other = parser.parse_known_args()

if len(args.data_root) == 0:
    print("-data_root is required to run downloader!")
    exit()

if not os.path.isdir(args.data_root):
    print(f'folder {args.data_root} does not exist! please provide existing folder in -data_root arg!')
    exit()


IMAGENET_API_WNID_TO_URLS = lambda wnid: f'http://www.image-net.org/api/text/imagenet.synset.geturls?wnid={wnid}'

current_folder = os.path.dirname(os.path.realpath(__file__))

class_info_json_filename = 'imagenet_class_info.json'
class_info_json_filepath = os.path.join(current_folder, class_info_json_filename)

class_info_dict = dict()

with open(class_info_json_filepath) as class_info_json_f:
    class_info_dict = json.load(class_info_json_f)

classes_to_scrape = []

if args.use_class_list == True:

   for item in args.class_list:
       classes_to_scrape.append(item)
       if item not in class_info_dict:
           print(f'Class {item} not found in ImageNete')


elif args.use_class_list == False:

    potential_class_pool = []

    for key, val in class_info_dict.items():

        if args.scrape_only_flickr:
            if int(val['flickr_img_url_count'])*0.8 > args.images_per_class:
                potential_class_pool.append(key)
        else:
            if int(val['img_url_count'])*0.8 > args.images_per_class:
                potential_class_pool.append(key)

    picked_classes_idxes = np.random.choice(len(potential_class_pool), args.number_of_classes)

    for idx in picked_classes_idxes:
        classes_to_scrape.append(potential_class_pool[idx])

print("Picked following clases")
for class_wnid in classes_to_scrape:
    print(class_wnid)
    print(class_info_dict[class_wnid])
    print(class_info_dict[class_wnid]['class_name'])


imagenet_images_folder = os.path.join(args.data_root, 'imagenet_images')
if not os.path.isdir(imagenet_images_folder):
    os.mkdir(imagenet_images_folder)


img_url_counts = dict(
    all=dict(
        tried=0,
        success=0,
    ),
    is_flickr=dict(
        tried=0,
        success=0,
    ),
    not_flickr=dict(
        tried=0,
        success=0
    )
)

for class_wnid in classes_to_scrape:

    class_images = 0

    class_name = class_info_dict[class_wnid]["class_name"]
    print(f'Scraping images for class \"{class_name}\"')
    url_urls = IMAGENET_API_WNID_TO_URLS(class_wnid)

    resp = requests.get(url_urls)

    class_folder = os.path.join(imagenet_images_folder, class_name)
    if not os.path.exists(class_folder):
        os.mkdir(class_folder)

    for img_url in resp.content.splitlines():

        if len(img_url) < 5:
            continue

        cls=''
        if 'flickr' in img_url.decode('utf-8'):
            cls = 'is_flickr'
        else:
            cls = 'not_flickr'
            if args.scrape_only_flickr:
                continue

        print(img_url)
        img_url_counts[cls]['tried'] += 1
        img_url_counts['all']['tried'] += 1


        try:
            img_resp = requests.get(img_url.decode('utf-8'), timeout = 1)
        except ConnectionError:
            print("Connection Error")
            continue
        except ReadTimeout:
            print("Read Timeout")
            continue
        except TooManyRedirects:
            print("Too many redirects")
            continue
        except MissingSchema:
            continue

        if not 'content-type' in img_resp.headers:
            continue

        if not 'image' in img_resp.headers['content-type']:
            print("Not an image:")
            continue

        if (len(img_resp.content) < 1000):
            print("Img too small")
            continue


        print(img_resp.headers['content-type'])
        print(len(img_resp.content))

        img_name = img_url.decode('utf-8').split('/')[-1]
        img_file_path = os.path.join(class_folder, img_name)

        print(f'Saving image in {img_file_path}')

        with open(img_file_path, 'wb') as img_f:
            img_f.write(img_resp.content)

            class_images += 1
            img_url_counts[cls]['success'] += 1
            img_url_counts['all']['success'] += 1


        print(f'Tried counts {img_url_counts}')
        if img_url_counts["is_flickr"]["tried"] > 0:
            print(f'{100.0 * img_url_counts["is_flickr"]["success"]/img_url_counts["is_flickr"]["tried"]}% of success rate for flickr urls ')
        if img_url_counts["not_flickr"]["tried"] > 0:
            print(f'{100.0 * img_url_counts["not_flickr"]["success"]/img_url_counts["not_flickr"]["tried"]}% of success rate for other urls ')
        if img_url_counts["all"]["tried"] > 0:
            print(f'{100.0 * img_url_counts["all"]["success"]/img_url_counts["all"]["tried"]}% of success rate for all urls ')

        if class_images == args.images_per_class:
            break
