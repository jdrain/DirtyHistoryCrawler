''' Metadata
Created on Oct 7, 2016
@author: Colin Wilder
Notes: These are utility functions for DHC 2.1.
'''

# arcana imperii
import datetime, os, pickle, random, re, string, time, urllib2, webbrowser

########################
###### Miscellany ######
########################
def waitRandomTime(): # function to wait a random though short period of time
    minWait=3; maxWait=12
    timeToWait=random.randint(minWait,maxWait)
    print "waiting " + str(timeToWait) + " seconds"
    time.sleep(timeToWait)

#####################
###### Logging ######
#####################
def findCurrentOutputIndex(): # returns the index of the current output folder based on the index file
    basePath = "./output"
    #read and increment the index file
    indexPath = basePath + "/index.txt"
    f = open(indexPath, "r")
    currentIndex = int(f.readline())
    f.close()
    return currentIndex

def initializeNewOutput(): # increments output index by 1, creates log file for new output, returns folder path of new/next output
    currentIndex = findCurrentOutputIndex()
    currentIndex += 1
    basePath = "./output"
    indexPath = basePath + "/index.txt"
    f = open(indexPath, "w")
    f.write(str(currentIndex))
    f.close
    # prep for complementary function to write to this new output
    newFolder = "output" + str(currentIndex)
    folderPath = basePath + "/" + newFolder
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
    logFilePath = folderPath + "/" + "logFile.txt"
    f = open(logFilePath,"w")
    now = datetime.datetime.today().strftime("Log file created on %m/%d/%Y, %H:%M:%S")
    f.write(now)
    f.write("\nThis is the message log. Could be used for pickling, lists, etc.")
    f.close()
    return folderPath

def addStringToLog(aString):
    currentIndex = findCurrentOutputIndex()
    path = "./output" + "/output" + currentIndex + "/logFile.txt"
    f = open(path, "a")
    f.write(aString)
    f.close()

def addOCLCNumbersToCurrentOutputFolder(list):
    #look to see if there is an OCLC number list in the current folder
    #write or bzw. append OCLC numbers in input list to OCLC number list in current output
    currentIndex = findCurrentOutputIndex()
    thePath = "./output" + "/output" + currentIndex + "/OCLC_numbers.txt"
    if not os.path.exists(thePath): # path does not exist, no OCLC numbers have yet been stored in this output
        os.makedirs(thePath)
        f = open(thePath, "w") # write
        f.write(str(list))
        f.close()
    else: # path already exists, OCLC numbers are already here so append rather than overwrite
        f = open(thePath,"a") # append
        f.write(str(list))
        f.close()

#######################################
###### Web pages, scraping, URLs ######
#######################################
def makeQueryURL(string): # function to produce query url
    #here is a sample url: https://www.worldcat.org/search?q=johann+nicolaus+hertius&qt=results_page
    # alt sample: https://www.worldcat.org/search?q=johann+nicolaus+hertius&fq=&dblist=638&start=21&qt=next_page
    urlPrefix = "https://www.worldcat.org/search?q="
    urlSuffix = "&qt=results_page"
    QueryURL = ""
    QueryURL += urlPrefix
    # the following part makes a string out of the search terms
    for term in string.split():
        QueryURL += term
        QueryURL += "+"
    QueryURL = QueryURL[:-1]
    QueryURL += urlSuffix
    return QueryURL

def makeURLforNextPageOfResults(string, pageNumber): # produce query URL
    URL_part_1 = "http://www.worldcat.org/search?q="
    URL_part_2 = ""
    # the following part makes a string out of the search terms
    for term in string.split():
        URL_part_2 += term
        URL_part_2 += "+"
    URL_part_2 = URL_part_2[:-1]
    URL_part_3 = "&fq=&dblist=638&start="
    URL_part_4 = str(10*pageNumber-9) # e.g. for page 2, this produces 11
    URL_part_5 = "&qt=next_page"
    return URL_part_1 + URL_part_2 + URL_part_3 + URL_part_4 + URL_part_5

def captureWebPageToString(aURL): # takes URL and brings back all HTML as a string
    # based on code from The Programming Historian.
    response = urllib2.urlopen(aURL)
    html = response.read()
    text = stripTags(html).lower()
    return text # note that this function does NOT strip non-alphanumerics

#################################
###### Text transformation ######
#################################
def stripNonAlphaNum(text): # strip out non-alphanumeric characters
    # useful for OCLC numbers of varying length
    # this is a slight alteration of the function in the Progr. Hist.
    import re
    list = re.split(r'\W+', text)
    return ' '.join(list)

def stripTags(aString): # strip tags out of a text string and replace with \n.
    #based on code from The Programming Historian.
    #startLoc = aString.find('''<p align="left" class="H_body_text">''') # these three lines are useful if you have good beginning or ending tags you can work with
    #endLoc = aString.rfind('''<p class="H_body_text">Source:</p>''')
    #aString = aString[startLoc:endLoc]
    inside = 0
    text = ""
    for char in aString:
        if char == "<":
            inside = 1
        elif (inside == 1 and char == ">"):
            inside = 0
            text += "\n"
        elif inside == 1:
            continue
        else:
            text += char
    return text

##########################
###### Extract data ######
##########################
def getOCLCNumbers(ls, SearchResultsPageAsHTMLString): # extract OCLC number(s) from big page of HTML string
    startLoc=0
    while True:
        startLoc=SearchResultsPageAsHTMLString.find('<div class="oclc_number">', startLoc) # look for substring <div class="oclc_number">
        if startLoc == -1:
            break
        startLoc +=  25
        oclcNumber = SearchResultsPageAsHTMLString[startLoc:startLoc+9]
        oclcNumber = stripNonAlphaNum(oclcNumber)
        ls.append(oclcNumber)
        startLoc += 9
    return ls

def OCLCNumberToRecord(OCLCNumber): # make target URL, open it on web, and read it into a new string
    urlPrefix = "http://www.worldcat.org/oclc/"
    urlSuffix = "?page=endnote&client=worldcat.org-detailed_record"
    targetUrl = urlPrefix + str(OCLCNumber) + urlSuffix # concatenate prefix, OCLC no., and suffix
    response = urllib2.urlopen(targetUrl)
    record = response.read()
    return record # returns string of record

def OCLCNumberToCitation(oclcNo): # pretty-print bibliogr. citation (given an OCLC number)
    recordString = OCLCNumberToRecord(oclcNo)
    author = ""; title = ""; date = ""
    # extract author info
    if "AU  -" not in recordString:
        print "no author"
    else:
        startLoc = recordString.find("AU  - ")
        endLoc = recordString.find("PB  -")
        author = recordString[startLoc+6:endLoc-1]
    # extract title info
    if "T1  -" not in recordString:
        print "no title"
    else:
        startLoc = recordString.find("T1  - ")
        endLoc = recordString.find("AU  -")
        title = recordString[startLoc+6:endLoc-1]
    if "Y1  -" not in recordString:
        print "no date"
    else:
        startLoc = recordString.find("Y1  - ")
        endLoc = recordString.find("ER  -")
        date = recordString[startLoc+6:endLoc-4] # 1 space to get to right place, 3 for backslashes
    return str(oclcNo) + ": " + author + " / " + title + " / " + date

def extractAuthorNames(oclcRecordString): # extract author name(s) from an OCLC record string and return them as list
    authorNames = []
    currentIndex = 0
    endOfLine = 0
    while True:
        currentIndex = oclcRecordString.find("AU  - ",currentIndex)
        if currentIndex == -1:
            break
        if oclcRecordString.find("\n",currentIndex) == -1:
            endOfLine = len(oclcRecordString)
        else:
            endOfLine = oclcRecordString.find("\n",currentIndex)
        authorNameYouFound = oclcRecordString[currentIndex+6:endOfLine]
        authorNameYouFound2 = re.split(r'\W+', authorNameYouFound)
        authorNameYouFound3 = ' '.join(authorNameYouFound2)
        authorNames.append(authorNameYouFound3)
        currentIndex = endOfLine + 1
        if currentIndex >= len(oclcRecordString):
            break
    return authorNames

# pickling operations
#pickle.dump(fD,newFileObject)
