import requests
import threading
import queue
from utils import retry_handler
from bs4 import BeautifulSoup

def checkSitemap(url):
    return len(url) > 3 and url[-3:] == 'xml' 

# TODO:
# 
#
@retry_handler(max_retry=6,sleep_time=1)
def scrapper(url : str):
    print(url)
    data = requests.get(url)
    soup = BeautifulSoup(data.content,'xml')
    locElementList = soup.findAll("loc")
    textList = [it.get_text() for it in locElementList ] 
    sitemapURLsList = list(filter(checkSitemap,textList))
    data = list(filter(lambda x: not x in sitemapURLsList, textList))
    return sitemapURLsList, data


class crawler(threading.Thread):
    def __init__(self,workerQueue : queue.Queue ,outputQueue : queue.Queue ):
        threading.Thread.__init__(self)
        self.workerQueue = workerQueue
        self.outputQueue = outputQueue
    def run(self):
        while True:
            url = self.workerQueue.get()
            try:
                sitemapURLsList, data = scrapper(url=url)
            except: 
                sitemapURLsList , data = [] , []
            self.outputQueue.put((sitemapURLsList, data))
            self.workerQueue.task_done()

def saveData(path: str, data: list):
    with open(path,'w') as writer:
        for it in data:
            writer.writelines(it+'\n')
        writer.close()

def handler(url : str, numberWorker : int, path : str):
    unduplicateDataList = set()
    unduplicateSitemapUrlList = set()
    sitemapURLsList, data = scrapper(url=url)
    unduplicateDataList.update(data)
    unduplicateSitemapUrlList.update(sitemapURLsList)
    print(sitemapURLsList)

    while True:
        workerQueue = queue.Queue()
        outputQueue = queue.Queue()
        listenQueue =  queue.Queue()
        currentTask =  0
        endTask =  len(sitemapURLsList)
        if endTask == 0:
            break
        for _ in range(numberWorker):
            tempCrawler = crawler(workerQueue=workerQueue,outputQueue=outputQueue)
            tempCrawler.setDaemon(True)
            tempCrawler.start()
        
        for url in sitemapURLsList:
            workerQueue.put(url)
        workerQueue.join()
        sitemapURLsList =  list()

        def trackingQueue(q : queue.Queue):
            while True:
                listenQueue.put((q,q.get()))
        
        _ = threading.Thread(target=trackingQueue,args=(outputQueue,),daemon=True).start()

        while True:
            whichQueue, message = listenQueue.get()
            if whichQueue is outputQueue:
                tempsitemapURLsList , data = message
                tempsitemapURLsList = list(filter(lambda x: not x in unduplicateSitemapUrlList,tempsitemapURLsList))
                sitemapURLsList.extend(tempsitemapURLsList)
                print(sitemapURLsList)
                unduplicateSitemapUrlList.update(tempsitemapURLsList)
                currentTask += 1
                unduplicateDataList.update(data)
            if endTask == currentTask :
                break


    saveData(path=path,data=list(unduplicateDataList))

handler(url= "https://www.vecteezy.com/sitemap.xml",numberWorker=10,path="./test.txt")