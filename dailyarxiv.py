# -*- coding: utf-8 -*-
"""
Created on Sat Jul 14 14:24:58 2018

@author: ZZH
"""


#!/home/zzh/.conda/envs/spider/bin/python


import requests
import re
import time
import pandas as pd
from bs4 import BeautifulSoup
import pymysql
from collections import Counter
import os
import random

import smtplib
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


def get_one_page(url):
    response = requests.get(url)
    print(response.status_code) 
    while response.status_code == 403:
        time.sleep(500 + random.uniform(0, 500))
        response = requests.get(url)
        print(response.status_code)
    print(response.status_code)
    if response.status_code == 200:
        return response.text

    return None


def send_email(title, content):

    #发送者邮箱
    sender = 'dailyarxiv@163.com'
    #发送者的登陆用户名和密码
    user = 'dailyarxiv@163.com'
    password = 'aaaaaaaa'#dailyarxiv123
    #发送者邮箱的SMTP服务器地址
    smtpserver = 'smtp.163.com'
    #接收者的邮箱地址
    receiver = 'youremail@qq.com' #receiver 可以是一个list


    msg = MIMEMultipart('alternative')  

    part1 = MIMEText(content, 'plain', 'utf-8')  
    #html = open('subject_file.html','r')
    #part2 = MIMEText(html.read(), 'html')

    msg.attach(part1)  
    #msg.attach(part2)

    #发送邮箱地址
    msg['From'] = sender
    #收件箱地址
    msg['To'] = receiver
    #主题
    msg['Subject'] = title

    smtp = smtplib.SMTP() #实例化SMTP对象
    smtp.connect(smtpserver, 25) #（缺省）默认端口是25 也可以根据服务器进行设定
    smtp.login(user, password) #登陆smtp服务器
    smtp.sendmail(sender, receiver, msg.as_string()) #发送邮件 ，这里有三个参数
    '''
    login()方法用来登录SMTP服务器，sendmail()方法就是发邮件，由于可以一次发给多个人，所以传入一个list，邮件正文
    是一个str，as_string()把MIMEText对象变成str。
    '''
    smtp.quit()


def main():

    url = 'https://arxiv.org/list/cs/pastweek?show=1000'
    html = get_one_page(url)
    soup = BeautifulSoup(html, features='html.parser')
    content = soup.dl
    date = soup.find('h3')
    list_ids = content.find_all('a', title = 'Abstract')
    list_title = content.find_all('div', class_ = 'list-title mathjax')
    list_authors = content.find_all('div', class_ = 'list-authors')
    list_subjects = content.find_all('div', class_ = 'list-subjects')
    list_subject_split = []
    for subjects in list_subjects:
        subjects = subjects.text.split(': ', maxsplit=1)[1]
        subjects = subjects.replace('\n\n', '')
        subjects = subjects.replace('\n', '')
        subject_split = subjects.split('; ')
        list_subject_split.append(subject_split)

    items = []
    for i, paper in enumerate(zip(list_ids, list_title, list_authors, list_subjects, list_subject_split)):
        items.append([paper[0].text, paper[1].text, paper[2].text, paper[3].text, paper[4]])
    name = ['id', 'title', 'authors', 'subjects', 'subject_split']
    paper = pd.DataFrame(columns=name,data=items)
    paper.to_csv('/home/zzh/Code/Spider/paperspider/arxiv/daily/'+time.strftime("%Y-%m-%d")+'_'+str(len(items))+'.csv')


    '''subject split'''
    subject_all = []
    for subject_split in list_subject_split:
        for subject in subject_split:
            subject_all.append(subject)
    subject_cnt = Counter(subject_all)
    #print(subject_cnt)
    subject_items = []
    for subject_name, times in subject_cnt.items():
        subject_items.append([subject_name, times])
    subject_items = sorted(subject_items, key=lambda subject_items: subject_items[1], reverse=True)
    name = ['name', 'times']
    subject_file = pd.DataFrame(columns=name,data=subject_items)
    #subject_file = pd.DataFrame.from_dict(subject_cnt, orient='index')
    subject_file.to_csv('/home/zzh/Code/Spider/paperspider/arxiv/sub_cnt/'+time.strftime("%Y-%m-%d")+'_'+str(len(items))+'.csv')
    #subject_file.to_html('subject_file.html')    


    '''key_word1 selection'''
    key_words = ['track', 'occlu', 'multiple object', 'multiple target', 'multi-object', 'multi-target', 'people', 'person', 'pedestrian', 'human', 'siam'] 
    Key_words = ['MOT', 'SOT']
    key_words2 = ['quantization', 'compress', 'prun']
    Key_words2 = ['MOT']    
    selected_papers = paper[paper['title'].str.contains(key_words[0], case=False)]
    for key_word in key_words[1:]:
        selected_paper1 = paper[paper['title'].str.contains(key_word, case=False)]
        selected_papers = pd.concat([selected_papers, selected_paper1], axis=0)
    for Key_word in Key_words[1:]:
        selected_paper1 = paper[paper['title'].str.contains(Key_word, case=True)]
        selected_papers = pd.concat([selected_papers, selected_paper1], axis=0)
    selected_papers.to_csv('/home/zzh/Code/Spider/paperspider/arxiv/selected/'+time.strftime("%Y-%m-%d")+'_'+str(len(selected_papers))+'.csv')
    '''key_word2 selection'''
    selected_papers2 = paper[paper['title'].str.contains(key_words2[0], case=False)]
    for key_word in key_words2[1:]:
        selected_paper1 = paper[paper['title'].str.contains(key_word, case=False)]
        selected_papers2 = pd.concat([selected_papers2, selected_paper1], axis=0)
    for Key_word in Key_words2[1:]:
        selected_paper1 = paper[paper['title'].str.contains(Key_word, case=True)]
        selected_papers2 = pd.concat([selected_papers2, selected_paper1], axis=0)
    selected_papers2.to_csv('/home/zzh/Code/Spider/paperspider/arxiv/selected2/'+time.strftime("%Y-%m-%d")+'_'+str(len(selected_papers2))+'.csv')



    '''send email'''
    #selected_papers.to_html('email.html')
    content = 'Today arxiv has {} new papers in CS area, and {} of them is about CV, {}/{} of them contain your keywords.\n\n'.format(len(list_title), subject_cnt['Computer Vision and Pattern Recognition (cs.CV)'], len(selected_papers), len(selected_papers2))
    content += 'Ensure your keywords is ' + str(key_words) + ' and ' + str(Key_words) + '(case=True). \n\n'
    content += 'This is your paperlist.Enjoy! \n\n'
    for i, selected_paper in enumerate(zip(selected_papers['id'], selected_papers['title'], selected_papers['authors'], selected_papers['subject_split'])):
        #print(content1)
        content1, content2, content3, content4 = selected_paper
        content += '------------' + str(i+1) + '------------\n' + content1 + content2 + str(content4) + '\n'
        content1 = content1.split(':', maxsplit=1)[1]
        content += 'https://arxiv.org/abs/' + content1 + '\n\n'

    content += 'Ensure your keywords2 is ' + str(key_words2) + ' and ' + str(Key_words2) + '(case=True). \n\n'
    content += 'This is your paperlist.Enjoy! \n\n'
    for i, selected_paper2 in enumerate(zip(selected_papers2['id'], selected_papers2['title'], selected_papers2['authors'], selected_papers2['subject_split'])):

        #print(content1)
        content1, content2, content3, content4 = selected_paper2
        content += '------------' + str(i+1) + '------------\n' + content1 + content2 + str(content4) + '\n'
        content1 = content1.split(':', maxsplit=1)[1]
        content += 'https://arxiv.org/abs/' + content1 + '\n\n'


    content += 'Here is the Research Direction Distribution Report. \n\n'
    for subject_name, times in subject_items:
        content += subject_name + '   ' + str(times) +'\n'
    title = time.strftime("%Y-%m-%d") + ' you have {}+{} papers'.format(len(selected_papers), len(selected_papers2))
    send_email(title, content)
    freport = open('/home/zzh/Code/Spider/paperspider/arxiv/report/'+title+'.txt', 'w')
    freport.write(content)
    freport.close()


    '''dowdload key_word selected papers'''
    list_subject_split = []
    if not os.path.exists('/home/zzh/Code/Spider/paperspider/arxiv/selected/'+time.strftime("%Y-%m-%d")):
        os.makedirs('/home/zzh/Code/Spider/paperspider/arxiv/selected/'+time.strftime("%Y-%m-%d"))
    for selected_paper_id, selected_paper_title in zip(selected_papers['id'], selected_papers['title']):
        selected_paper_id = selected_paper_id.split(':', maxsplit=1)[1]
        selected_paper_title = selected_paper_title.split(':', maxsplit=1)[1]
        r = requests.get('https://arxiv.org/pdf/' + selected_paper_id) 
        while r.status_code == 403:
            time.sleep(500 + random.uniform(0, 500))
            r = requests.get('https://arxiv.org/pdf/' + selected_paper_id)
        selected_paper_id = selected_paper_id.replace(".", "_")
        pdfname = selected_paper_title.replace("/", "_")   #pdf名中不能出现/和：
        pdfname = pdfname.replace("?", "_")
        pdfname = pdfname.replace("\"", "_")
        pdfname = pdfname.replace("*","_")
        pdfname = pdfname.replace(":","_")
        pdfname = pdfname.replace("\n","")
        pdfname = pdfname.replace("\r","")
        print('/home/zzh/Code/Spider/paperspider/arxiv/selected/'+time.strftime("%Y-%m-%d")+'/%s %s.pdf'%(selected_paper_id, selected_paper_title))
        with open('/home/zzh/Code/Spider/paperspider/arxiv/selected/'+time.strftime("%Y-%m-%d")+'/%s %s.pdf'%(selected_paper_id,pdfname), "wb") as code:    
           code.write(r.content)



if __name__ == '__main__':
    main()
    time.sleep(1)




