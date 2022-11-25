import datetime
import requests as r
import os
import re
import subprocess
import ffmpeg

# subprocess.call(['pip', 'install', 'ffmpeg-python', 'requests'])
# os.system('cls')
print('======================================================================\n')
print("Pexels Video Downloader v1\n")
print('======================================================================\n')
print()
# -------------------------- CONFIG START --------------------------
# Input Paths
PATHS_SELECTED = [
    "./VideoLinks.txt",
    "./DownloadedVideoLinks.txt",
    "./BlockedVideoLinksLog.txt",
    "./InvalidVideoLinks.txt",

]

# Output Paths
OUTPUT_PATH1 = "./Temporary" # Downloaded Videos
OUTPUT_PATH2 = "./Completed Videos" # Downloaded videos + added comment or title

# getting inputs from user
res = input("** Video Resolution to download (SD / HD / UHD / MAX)? ")
orientation = input("** Specific Video Orientations (V / H / S / X)? ") # (Vertical / Horizontal / Square / All)
title = input("** Write Title in the Title section of the video (Y/N)? ")
comment = input("** Write Link in the Comments section of the video (Y/N)? ")
# -------------------------- CONFIG END --------------------------

DownloadedVideoLinks = []
BlockedVideoLinksLog = []

# create folder if not already exists
if not os.path.exists(OUTPUT_PATH1):
    os.mkdir(OUTPUT_PATH1)
if not os.path.exists(OUTPUT_PATH2):
    os.mkdir(OUTPUT_PATH2)


# read input file
with open(PATHS_SELECTED[0], 'r') as f:
    urls = f.read().split('\n')
    urls = [ii for ii in urls if ii]

print()
print(f"Links Found: {len(urls)}")
print('----------------------------------------------------------------------\n')


# read blocked url file
blocked_url = []
with open(PATHS_SELECTED[1], 'r') as f:
    blocked_url = f.read().split('\n')
    blocked_url = [ii for ii in blocked_url if ii]


def extract_id(urls):
    lis_ = []
    for k in urls:
        m = re.search(r'\d{7,8}', k)
        if m:
            lis_.append(m.group())
    return lis_


urls = extract_id(urls)
blocked_url = extract_id(blocked_url)

urls = list(set(urls) - set(blocked_url))  # remove blocked urls from urls
BlockedVideoLinksLog = list(set(urls) & set(blocked_url))
# Save Blocked Links url id
with open(PATHS_SELECTED[3], 'w') as f:
    BlockedVideoLinksLog = [
        "https://www.pexels.com/video/%s/" % x for x in BlockedVideoLinksLog]
    f.write('\n'.join(BlockedVideoLinksLog))

mk_req = []

invalid = []


def get_video_info(id_):
    headers = {
        'Authorization': '563492ad6f9170000100000115f75ed96f2944c2ad48fb5ea96cb025'} # api key
    res = r.get(f'https://api.pexels.com/videos/videos/{id_}', headers=headers)
    if res.status_code == 200:
        mk_req.append(res)
    else:
        invalid.append(id_)
        print('Failed to get video info', res.status_code)


print('\nGetting info using Pexel API')
# print(urls)
for id_ in urls:
    print("https://www.pexels.com/video/%s/" % id_)
    get_video_info(id_)

# save invalid url id
with open(PATHS_SELECTED[4], 'w') as f:
    invalid = ["https://www.pexels.com/video/%s/" % x for x in invalid]
    f.write('\n'.join(invalid))



print(f"\n\nLinks to Download: {len(mk_req)}")
print('----------------------------------------------------------------------\n\n')
print('STARTED DOWNLOADING...\n\n')


def download(v_res, index):
    d = v_res.json()

    vid_url = d.get('url')  # video url
    name = vid_url.split('/')[-2].replace('-', ' ')  # video filename
    videos = sorted(d['video_files'], key=lambda x: x['width'])
    vv = videos[-1]

    # Determine Video Orientation
    if not orientation.upper() == 'X':  # All
        v_orient = ''
        if vv['width'] == vv['height']: # Square
            v_orient = 'S'
        elif vv['width']/vv['height'] < 1: # Vertical
            v_orient = 'V'
        else: # Horizontal
            v_orient = 'H'
        # print(v_orient)
        if orientation.upper() != v_orient:
            return

    # select resolution

    d_link = vv['link']  # max res by default

    dl = dict()
    if not res.lower() == 'max':
        for vid in videos:
            if vid['quality'] == res.lower():
                dl[vid['width']] = vid['link']
                #file_type = vid['file_type'].split('/')[-1]
        d_link = dl[max(dl)]
        if not dl:
            print(
                f'{res.upper()} resolution not found for this video, automatically choosing the max res.')

    file_type = vv['file_type'].split('/')[-1] # video extension

    # Download video
    print(f"\n#{index}. {vid_url}")
    x = r.get(d_link)

    if x.status_code == 200:

        filename = '{0}.{1}'.format(name, file_type)
        print(filename)
        filepath1 = os.path.join(OUTPUT_PATH1, filename)
        filepath2 = os.path.join(OUTPUT_PATH2, filename)
        # save video
        with open(filepath1, 'wb') as f:
            f.write(x.content)
        print("Downloaded\n")
        DownloadedVideoLinks.append(vid_url)
    else:
        print("Unable to Download.\n")
        return

    # adding title and comment using ffmpeg python 
    stream = ffmpeg.input(filepath1)

    meta1 = name # filename in Title 
    meta2 = vid_url # video link in Comment
    if title.lower() == 'y':

        if comment.lower() == 'y':
            stream = ffmpeg.output(
                stream, filepath2, loglevel="quiet", **{'metadata': 'title=%s' % (meta1), 'metadata:': 'comment=%s' % (meta2)})
        else:
            stream = ffmpeg.output(stream, filepath2, loglevel="quiet",
                                   metadata='title=' + meta1)
    elif comment.lower() == 'y':
        stream = ffmpeg.output(stream, filepath2, loglevel="quiet",
                               metadata='comment='+meta2)
    else:
        stream = ffmpeg.output(stream, filepath1, loglevel="quiet")

    ffmpeg.run(stream, overwrite_output=True)


for i, _ in enumerate(mk_req):
    download(_, i+1)


today = datetime.datetime.today()
date_t = datetime.datetime.strftime(today, "%Y-%m-%d %H:%M")

print('\n======================================================================')
print(
    f'\n Successfully Downloaded {len(DownloadedVideoLinks)} Videos {date_t}')
print('\n======================================================================')
# Save Downlaod Links url
with open(PATHS_SELECTED[2], 'w') as f:
    f.write('\n'.join(DownloadedVideoLinks))
