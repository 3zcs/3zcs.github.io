---
title: Obtaining my driving data
description: >-
  How can I obtain my driving data from my insurance company and analyze it for insights.
author: 3zcs
date: 2024-08-09 20:55:00 +0800
categories: [Blogging]
tags: [data analysis]
pin: true
---

## Obtaining my driving data

I was a bit curious about how many hours I spent on my car, my insurance company gave me a telematics device connected to their app that tracks my driving behavior and they have sort of incentives program based on that.
this app shows my trips along with the time spent on each trip, this is exactly the data that I want. 
obviously there isn't an easy wat to export this data xD, so in this blog I'll go through the steps that I made to obtain the data, I'll try to make it concise but informative as much as I can.

I have a rooted android device and I installed the target app, they don't have any root detection mitigation.

I start with the basics, I reverse the apk and found that it's obfuscated, I noticed that they use react native for building the app, going through the code will be a bit of hustle, I avoid it when I start and see if I'll need it later.

I went to the app package I found many folders I went laterally over each and every one, then I found `/databases` folder, inside this folder many databases I use `adb` tool, I pulled all DBs and started exploring, and I found that one file had all trips recorded, so started working on it, I connected to the DB and queried the data, after some analysis I found out the stored data is less than the data presented on the app, there is a huge difference, and some data is broken, filled with zeros, so, I have to find another way.

As the data on the app obliviously it came through the network, I went down to intercept the traffic using [Burp Suite](https://portswigger.net/burp) with this [configuring](https://portswigger.net/burp/documentation/desktop/mobile/config-android-device), and as expected they have SSL, so I used Frida with a famous script [frida-multiple-unpinning](https://codeshare.frida.re/@akabe1/frida-multiple-unpinning/) and hit this command 


```console
$ frida -U -f com.my.target -l frida-multiple-unpinning.js 
```

it works perfectly, it only asks you to put burp's certificate  on this folder `/data/local/tmp/cert-der.crt`

after that I start see each of my trips as a clear response, the downside is that there is a lot of traffic that I don't need, I found out that the api used for all trips is `/api/v1/drives/`, I use this endpoint to filter all the responses, and there is a cool feature in burp suite save all items (requests and responses) as XML document. I had literally a file with 16 mb, it was really hard to open it in any editor and to explore or edit. 
so I used a great python lib `xmltodict` and with this snippet, I convert the whole xml to json 
 
```python
import xmltodict
import json

with open("data.xml", "r") as f:
  xml_data = f.read()

# Parse the XML into a dictionary
data_dict = xmltodict.parse(xml_data)

# Convert the dictionary to a JSON string
json_data = json.dumps(data_dict)
```
I have data as a json I remove some responses that use the same endpoint but not trips data, and there are some issues during the conversions from XML to JSON.
I narrowed the filtration as I went, and I found out all the responses that include `includeSubDomains` I'm interested in them, but I have to do some data cleaning. 
also, I need only responses that has `distance_mapmatched_km` as a json element
then I built my csv file 

```python
def print_json_elements(filename):

  try:
    with open(filename, "r") as f:
      data = f.read()
      parsed_data = json.loads(data)
      count = 0

      items = parsed_data['items']
      for element in items['item']:
        element['response']= json.loads(json.dumps(element['response']).replace("includeSubDomains\\n\\n", "'includeSubDomains': "))
        eleist = list(element['response'].values())

        # find index and remove it with what before
        end = eleist[1].find('\'includeSubDomains')
        if end == -1:
        # response not wanted if includeSubDomains no included
          continue

        # check if there is distance_mapmatched_km in the json or skip this response
        inclufe_distance = eleist[1].find('distance_mapmatched_km')
        if inclufe_distance == -1:
          # print(eleist[1])
          continue

        # if all good give me id, start_time, end_time, distance
        eobj = json.loads(eleist[1][end+21:])
        csv_list.append([str(eobj['id']),str(eobj['start']['ts']), str(eobj['end']['ts']), str(eobj['distance_mapmatched_km'])])
        # count number of recored
        count += 1

  except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error processing JSON file: {e}")

  write_csv(csv_list)
  print(count)
```
it's not the code that you want to share but as a line work I don't fix it I move on to the next.
my csv file looks like this

```python
csv_list = [["id", "start_time", "end_time", "distance"]]
```
filled with 4418 record

then I move on to [jupyter notebook](https://jupyter.org/) with python's `pandas` I start exploring the data, in the following snippet, I created several columns and I found out there was a huge duplication so I dropped duplicated rows 

```python
  df = pd.read_csv('thecsvdata.csv')
  # convert date to datetime object 
  df['start_time'] = pd.to_datetime(df['start_time'])
  df['end_time'] = pd.to_datetime(df['end_time'])
  # find the total time for each trip in secound 
  df['duration_in_seconds'] = (df['end_time'] - df['start_time']).dt.total_seconds()
  # in min
  df['duration_in_min'] = df['duration_in_seconds'] / 60
  # in hour 
  df['duration_in_hour'] = df['duration_in_min'] / 60
  # week number for each trip 
  df['week_no'] = df['start_time'].dt.isocalendar().week
  # month number for each trip 
  df['month_no'] = df['start_time'].dt.month
  # day of the week for each trip 
  df['dayofweek'] = df['start_time'].dt.dayofweek
  # drop duplication
  df = df.drop_duplicates(keep='first')
  # print
  df
```
now the data is ready to be consumed, so I print a weekly hour spent on the car 
```python 
per_week = df.groupby('week_no')['duration_in_min'].sum()
per_week = per_week.drop([6,18])
per_week.plot(kind="bar", title='number of min per week ')
weekly_in_hour = (per_week / 60 )
weekly_in_hour 

#### reslut 
week_no
 7     19.465833
 8     13.173611
 9     15.554167
 10    21.767778
 11    18.558333
 12    12.918056
 13    17.767778
 14    13.659444
 15    10.629444
 16    16.558889
 17    10.382500
```
it was OOOPPS moment, on avarge `weekly_in_hour.mean() ` I spent 15.49, which is 2.21 daily.
then I try to find out in which day of the week I spent more time on the car, it was obviously during work days 

```python
per_day = df_weeks.groupby('dayofweek')['duration_in_min'].sum()
per_day.plot(kind="bar", title='number of min in days ')
per_day
####### result 
# starts on Monday, which is denoted by 0 and ends on Sunday which is denoted by 6
# 5 and 4 is weekend in here
day
0    2210.050000
1    2209.166667
2    1954.916667
3    1476.700000
4    1183.266667
5     960.150000
6    1887.466667

```
mostly I don't drive a lot on the weekend xD.

it was fun to go over this, I didn't expect obtaining the data to be that hustle, but as I went I thought "This is the last step everything after this gonna be smooth xD", the ultimate goal was to be aware of how I much time is spent there and how I make it useful with work above I have the awareness and I need to find ideas to reduce the time or make it so so useful as it is a big part of my daily life xD 

[back](./)
