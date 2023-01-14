import requests
import multiprocessing
import queue
from utils import retry_handler
from bs4 import BeautifulSoup


def checkSitemap(url):
    return len(url) > 3 and url[-3:] == "xml"


# default max_retry of a task is 6 , and sleep time is 1 second
@retry_handler(max_retry=6, sleep_time=1)
def scrapper(url: str):
    print(url)
    data = requests.get(url)
    soup = BeautifulSoup(data.content, "xml")
    locElementList = soup.findAll("loc")
    textList = [it.get_text() for it in locElementList]
    sitemapURLsList = list(filter(checkSitemap, textList))
    data = list(filter(lambda x: not x in sitemapURLsList, textList))
    return sitemapURLsList, data


class crawler(multiprocessing.Process):
    def __init__(
        self,
        workerQueue: multiprocessing.JoinableQueue(),
        outputQueue: multiprocessing.Queue(),
    ):
        multiprocessing.Process.__init__(self)
        self.workerQueue = workerQueue
        self.outputQueue = outputQueue

    def run(self):
        while True:
            url = self.workerQueue.get()
            try:
                sitemapURLsList, data = scrapper(url=url)
            except Exception as e:
                print(f"The task is still running but please check the error: {e}")
                sitemapURLsList, data = [], []
            self.outputQueue.put((sitemapURLsList, data))
            self.workerQueue.task_done()
        return


### Save data
def saveData(path: str, data: list):
    with open(path, "w") as writer:
        for it in data:
            writer.writelines(it + "\n")
        writer.close()


def handler(url: str, path: str):
    # use set to avoid duplicate element
    unduplicateDataList = set()
    unduplicateSitemapUrlList = set()
    sitemapURLsList, data = scrapper(url=url)
    unduplicateDataList.update(data)
    unduplicateSitemapUrlList.update(sitemapURLsList)
    numberOfWorker = multiprocessing.cpu_count() * 2

    while True:
        workerQueue = multiprocessing.JoinableQueue()
        outputQueue = multiprocessing.Queue()
        currentTask = 0
        endTask = len(sitemapURLsList)

        if endTask == 0:
            break
        for _ in range(numberOfWorker):
            tempCrawler = crawler(workerQueue=workerQueue, outputQueue=outputQueue)
            tempCrawler.daemon = True
            tempCrawler.start()

        for it, url in enumerate(sitemapURLsList):
            workerQueue.put(url)
        sitemapURLsList = list()

        while True:
            tempsitemapURLsList, data = outputQueue.get()
            # filter to avoid duplicate path
            tempsitemapURLsList = list(
                filter(
                    lambda x: not x in unduplicateSitemapUrlList, tempsitemapURLsList
                )
            )
            sitemapURLsList.extend(tempsitemapURLsList)
            unduplicateSitemapUrlList.update(tempsitemapURLsList)
            currentTask += 1  # Although the task can be failed or out of the number of max_retry, still calculate the task is completed
            unduplicateDataList.update(data)
            if currentTask == endTask:
                break
        workerQueue.join()

    saveData(path=path, data=list(unduplicateDataList))
    print("COMPLETED")
