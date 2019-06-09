# ImageNet-datasets-downloader

This is ImageNet dataset downloader. **You can create new datasets from subsets of ImageNet by specifying how many 
classes you need and how many images per class you need.** 
This is achieved by using image urls provided by ImageNet API.


More details [in this blog post.](mf1024.github.io)

## Usage


The following command will randomly select 100 of ImageNet classes with at least 200 images in it and start downloading:
```
./downloader.py \
    -data_root /Users/mf1024/ai/imagenet \
    -number_of_classes 100 \
    -images_per_class 200
```


The following command will download 500 images from each of select class:
```
./downloader.py 
    -data_root /Users/mf1024/ai/imagenet \
    -use_class_list True \
    -class_list n09858165 n01539573 n03405111 \
    -images_per_class 500 
```
