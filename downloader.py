import os
import numpy as np
import requests
import argparse
import json
import time
import logging
import csv

from requests.exceptions import ConnectionError, ReadTimeout, TooManyRedirects, MissingSchema, InvalidURL

parser = argparse.ArgumentParser(description='ImageNet image scraper')
parser.add_argument('-scrape_only_flickr', default=True, type=lambda x: (str(x).lower() == 'true'))
parser.add_argument('-number_of_classes', default = 10, type=int)
parser.add_argument('-images_per_class', default = 10, type=int)
parser.add_argument('-data_root', default='' , type=str)
parser.add_argument('-use_class_list', default=False,type=lambda x: (str(x).lower() == 'true'))
parser.add_argument('-class_list', default=[], nargs='*')
parser.add_argument('-debug', default=False,type=lambda x: (str(x).lower() == 'true'))

args, args_other = parser.parse_known_args()

if args.debug:
    logging.basicConfig(filename='resnet_scarper.log', level=logging.DEBUG)

if len(args.data_root) == 0:
    logging.error("-data_root is required to run downloader!")
    exit()

if not os.path.isdir(args.data_root):
    logging.error(f'folder {args.data_root} does not exist! please provide existing folder in -data_root arg!')
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
           logging.error(f'Class {item} not found in ImageNete')
           exit()

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


print("Picked the following clases:")
print([ class_info_dict[class_wnid]['class_name'] for class_wnid in classes_to_scrape ])

imagenet_images_folder = os.path.join(args.data_root, 'imagenet_images')
if not os.path.isdir(imagenet_images_folder):
    os.mkdir(imagenet_images_folder)


scraping_stats = dict(
    all=dict(
        tried=0,
        success=0,
        time_spent=0,
    ),
    is_flickr=dict(
        tried=0,
        success=0,
        time_spent=0,
    ),
    not_flickr=dict(
        tried=0,
        success=0,
        time_spent=0,
    )
)

def add_debug_csv_row(row):
    with open('stats.csv', "a") as csv_f:
        csv_writer = csv.writer(csv_f, delimiter=",")
        csv_writer.writerow(row)

if args.debug:
    row = [
        "all_tried",
        "all_success",
        "all_time_spent",
        "is_flickr_tried",
        "is_flickr_success",
        "is_flickr_time_spent",
        "not_flickr_tried",
        "not_flickr_success",
        "not_flickr_time_spent"
    ]
    add_debug_csv_row(row)

def add_stats_to_debug_csv():
    row = [
        scraping_stats['all']['tried'],
        scraping_stats['all']['success'],
        scraping_stats['all']['time_spent'],
        scraping_stats['is_flickr']['tried'],
        scraping_stats['is_flickr']['success'],
        scraping_stats['is_flickr']['time_spent'],
        scraping_stats['not_flickr']['tried'],
        scraping_stats['not_flickr']['success'],
        scraping_stats['not_flickr']['time_spent']
    ]
    add_debug_csv_row(row)

def print_stats(cls, print_func):
    if scraping_stats[cls]["tried"] > 0:
        print_func(f'{100.0 * scraping_stats[cls]["success"]/scraping_stats[cls]["tried"]}% success rate for {cls} urls ')
    if scraping_stats[cls]["success"] > 0:
        print_func(f'{scraping_stats[cls]["time_spent"] / scraping_stats[cls]["success"]} seconds spent per {cls} succesful image download')

url_tries = 0

for class_wnid in classes_to_scrape:

    class_images = 0

    class_name = class_info_dict[class_wnid]["class_name"]
    print(f'Scraping images for class \"{class_name}\"')
    url_urls = IMAGENET_API_WNID_TO_URLS(class_wnid)

    resp = requests.get(url_urls)

    class_folder = os.path.join(imagenet_images_folder, class_name)
    if not os.path.exists(class_folder):
        os.mkdir(class_folder)

    t_last = time.time()
    cls=''

    for img_url in resp.content.splitlines():

        if len(img_url) <= 1:
            continue

        url_tries += 1

        if url_tries % 500 == 0:
            print(f'\nScraping stats {scraping_stats}')
            print_stats('is_flickr', print)
            print_stats('not_flickr', print)
            print_stats('all', print)
            if args.debug:
                add_stats_to_debug_csv()

        if cls:
            t_cur = time.time()
            t_spent = t_cur - t_last

            scraping_stats[cls]['time_spent'] += t_spent
            scraping_stats['all']['time_spent'] += t_spent

            t_last = t_cur

        if 'flickr' in img_url.decode('utf-8'):
            cls = 'is_flickr'
        else:
            cls = 'not_flickr'
            if args.scrape_only_flickr:
                continue

        logging.debug(img_url)
        scraping_stats[cls]['tried'] += 1
        scraping_stats['all']['tried'] += 1


        try:
            img_resp = requests.get(img_url.decode('utf-8'), timeout = 1)
        except ConnectionError:
            logging.debug("Connection Error")
            continue
        except ReadTimeout:
            logging.debug("Read Timeout")
            continue
        except TooManyRedirects:
            print("Too many redirects")
            continue
        except MissingSchema:
            continue
        except InvalidURL:
            continue

        if not 'content-type' in img_resp.headers:
            continue

        if not 'image' in img_resp.headers['content-type']:
            logging.debug("Not an image")
            continue

        if (len(img_resp.content) < 1000):
            continue


        logging.debug(img_resp.headers['content-type'])
        logging.debug(f'image size {len(img_resp.content)}')

        img_name = img_url.decode('utf-8').split('/')[-1]

        if (len(img_name) <= 1):
            continue

        img_file_path = os.path.join(class_folder, img_name)

        logging.debug(f'Saving image in {img_file_path}')

        with open(img_file_path, 'wb') as img_f:
            img_f.write(img_resp.content)
            class_images += 1
            scraping_stats[cls]['success'] += 1
            scraping_stats['all']['success'] += 1


        logging.debug(f'Scraping stats {scraping_stats}')
        print_stats('is_flickr', logging.debug)
        print_stats('not_flickr', logging.debug)
        print_stats('all', logging.debug)

        if class_images == args.images_per_class:
            break
