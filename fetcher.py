from requests_html import HTMLSession
import json
session = HTMLSession()


def fetch_chengdu_iptv():
    url = 'http://epg.51zmt.top:8000/sctvmulticast.html'
    r = session.get(url)
    trs = r.html.find('table > tr')
    channels = []
    for tr in trs:
        if 'header' in tr.attrs['class']:
            continue
        tds = tr.find('td')
        channel = {
            'name': tds[1].text,
            'multicast_addr': tds[2].text,
            'res': get_text(tds[5].find('em.res', first=True)),
            'fps': get_text(tds[5].find('em.fps', first=True)),
            'rate': get_text(tds[5].find('em.rate', first=True))
        }
        channels.append(channel)
    return channels


def get_text(element):
    if element is None:
        return None
    return element.text


def get_channel_info():
    url = 'http://epg.51zmt.top:8000/'
    r = session.get(url)
    trs = r.html.find('tr')
    channel_info = {}
    group_set = set()
    for tr in trs:
        tds = tr.find('td')
        if len(tds) == 0:
            continue
        tvg_logo = tds[0].find('a', first=True).attrs['href']
        tvg_name = tds[2].text
        tvg_id = tds[3].text
        group_title = tds[4].text
        channel_info[tvg_name] = {
            'tvg_logo': tvg_logo,
            'tvg_id': tvg_id,
            'group_title': group_title
        }
        group_set.add(group_title)
    print(group_set)
    return channel_info


def gen_m3u_file(channels, channel_info):
    resList = {item['res'] for item in channels}
    print(resList)
    exist_name_FHD = {item['name'].replace('高清', '') for item in channels if '高清' in item['name']}
    # EXTM3U
    # EXTINF:-1 tvg-id="1" tvg-name="CCTV1" tvg-logo="http://epg.51zmt.top:8000/tb1/CCTV/CCTV1.png" group-title="央视",﻿CCTV-1高清
    # http://192.168.100.1:4022/udp/239.93.0.184:5140
    f = open('chengdu_iptv.m3u', 'w')
    f.write('# EXTM3U\n')
    for channel in channels:
        if '画中画' in channel['name']:
            continue
        if '单音轨' in channel['name']:
            continue
        if '体验' in channel['name']:
            continue
        if channel['name'].isdigit():
            continue
        if channel['name'].replace('直播室', '').isdigit():
            continue
        if channel['res'] is None:
            continue
        # 存在高清版，跳过
        if channel['name'] in exist_name_FHD:
            continue
        tvg_name = get_tvg_name(channel['name'])
        tvg_logo = get_tvg_logo(tvg_name, channel_info)
        tvg_id = get_tvg_id(tvg_name, channel_info)
        group_title = get_group_title(tvg_name, channel_info)
        f.write(f"# EXTINF:-1 tvg-id=\"{tvg_id}\" tvg-name=\"{tvg_name}\" tvg-logo=\"{tvg_logo}\" group-title=\"{group_title}\",{channel['name']}\n")
        f.write(f"http://192.168.100.1:4022/udp/{channel['multicast_addr']}\n")
    f.close()


def get_group_title(name, channel_info):
    if name in channel_info:
        return channel_info[name]['group_title']
    if '卫视' in name:
        return '卫视'
    if '四川' in name or 'SCTV' in name:
        return '四川'
    return '未分类'


def get_tvg_logo(name, channel_info):
    if name in channel_info:
        return channel_info[name]['tvg_logo']


def get_tvg_id(name, channel_info):
    if name in channel_info:
        return channel_info[name]['tvg_id']


def get_tvg_name(name):
    if name == 'CCTV-少儿高清':
        name = 'CCTV14'
    if name == 'CCTV-5＋高清':
        name = 'CCTV5+'
    return name.replace('杜比高清', '').replace('高清', '').replace('-', '')


def write_channels(channels):
    with open('channels.json', 'w') as f:
        f.write(json.dumps(channels))


def read_channels():
    with open('channels.json', 'r') as f:
        return json.loads(f.read())


if __name__ == '__main__':
    channels = fetch_chengdu_iptv()
    # write_channels(channels)
    # channels = read_channels()
    channel_info = get_channel_info()
    gen_m3u_file(channels, channel_info)
