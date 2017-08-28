""" Metadata
Recreated on Sunday, October 16, 2016
@author: Colin Wilder
Other intellectual property allegations: Incorporates some code from the Programming Historian. DHC 2.0 was designed by CFW and Travis Mullen and implemented by Travis Mullen. The present version is not implemented or designed by Travis at all, but doubtless has some conceptual/design elements that carry over from DHC 2.0. So some credit to Travis probably percolates in there.
Notes: This is a partial reboot of the main crawler.
The change is as follows: This version makes the URLs in a different way. Instead of making one for each search string up front, I put the search string(s) into a list, and loop through the list. In the loop, I use my utility function makeURLforNextPageOfResults each time. Seems to work.

TODO:
 - make a counter so that when the console/output is printing the record it says "record 1 of x"; important for long batches to come
 - put retrieved book records into instances of your edition class
 - put retrieved author names into instances of your person class
 - record links between them as pairs or something (or in Neo4J)
 - compare author names via edit distance, after stripNonAlphaNumeric, lowerCasing, etc.
 - write the log to an html file and open it up in a new browser tab so you can see it immediately (for dev. purposes)

NOTES:
 - Doesn't make sense to sort items because first letters could be aberrations. Searching i.e. edit distance measuring will depend on all letters taken together.
 - Actually sorting first might help. I remember we did that late in 350. Also, pre-sorting is mentioned several times in http://cs.stackexchange.com/questions/27539/how-fast-can-we-identifiy-almost-duplicates-in-a-list-of-strings.
 - So pre-sort the list of terms.
    + Check item 0 against all the ones after it in sorted list of n terms.
    + Then check item 1 against all the terms after it.
    + Then check item 2 against all the terms after it.
    + Then check item i against all the terms after it, up to the n-1th and final item.
"""

#arcana imperii
import os, datetime, string, urllib2, utilities, webbrowser

#commencement
print "DHC 2.1"

################################
### Stage 1: Input and setup ###
################################

##    Initialize new log file.
##    Take keyword inputs.
##    Put in string.
##    Construct query URL(s) from string.
##    Put URL(s) in list.

currentIndex = utilities.findCurrentOutputIndex() # find the index of the most recent output (which is now frozen in carbonite)
currentIndex += 1
basePath = './output'
indexPath = basePath + '/index.txt'
with open(indexPath, "w") as f:
    f.write(str(currentIndex))

newFolder = "output" + str(currentIndex) # make the folder if need be
folderPath = basePath + '/' + newFolder
if not os.path.exists(folderPath):
    os.makedirs(folderPath)

# open log file for writing; this will stay open until end of session a while from now
logFilePath = folderPath + '/logFile.txt'
f = open(logFilePath,"w")
now = datetime.datetime.today().strftime("Log file created on %m/%d/%Y, %H:%M:%S"+"\n")
f.write(now)
f.write("Here is the message text." + "\n")

# take input
modal_1 = input("Enter 1 for string input or 2 for text file input: ")
if modal_1 == 1:
    modal_2 = raw_input("Enter string of keywords: ")
    print("keywords to send to WorldCat: " + modal_2)
elif modal_1 == 2:
    modal_2 = input("Enter full path + name of text file including suffix: ")
else:
    print("error man" + "\n")

# put search term(s) into Python list
listOfQueryStrings = []
if modal_1 == 1: #if user is just entering a string of search terms...
    #just put it as only item in list
    listOfQueryStrings.append(modal_2)
    f.write(modal_2 + "\n") # write the string of search terms to the log file # print to output ###################################
elif modal_1 == 2:
    g = open(modal_2, 'r') # g is the file object for the text input file from the user; not to be confused with f, the log file
    for line in g: # for each line in the file
        listOfQueryStrings.append(line) # read it and do listOfQueryURLs.append(makeQueryURL(#line)) to it
        f.write(line+"\n") # write each line in list of search terms to log file # print to output ###################################
    g.close # close the text input file
else:
    print "error - you didn't type 1 or 2 apparently\n"
    exit

# output to console and to log file confirming receipt of input
confirmatoryOutput ="query list contents: " + str(listOfQueryStrings) + "\n"
f.write(confirmatoryOutput)
print(confirmatoryOutput)
# the list of search strings is now ready to be sent to WorldCat

###############################
### Stage 2: Query WorldCat ###
###############################

#
##    Send each query URL you've made to WorldCat.
##    Extract all OCLC numbers from each.
##    When applicable, visit multiple results pages.

# global variables for this section
OCLCNumbers = [] #receptacle to put OCLC numbers in
pageNumberToTry = 1 # for iterating results pages

# big loop
for searchString in listOfQueryStrings:
    while True:
        # make URL, visit page, capture its HTML
        print "trying page " + str(pageNumberToTry)
        nextPageOfResultsURL=utilities.makeURLforNextPageOfResults(searchString, pageNumberToTry)
        response = urllib2.urlopen(nextPageOfResultsURL)
        retrieved_HTML = response.read() # here is the first stage - the original capture
        print "tried page and captured result to string"

        # write results to a local .html file etc.
        outputHTMLfileName = folderPath + '/' + 'retrieved_HTML_page_' + str(pageNumberToTry) + '.html'
        h = open(outputHTMLfileName, 'w') # making .html file
        h.write(retrieved_HTML)
        h.close

        # if no error, capture OCLC numbers and iterate
        errorMessage = "Search Error" # this is the only marker in the HTML search results pages I could find that works
        print "testing whether resulting page is error or has results"
        if string.find(retrieved_HTML, errorMessage) > -1: # error message is a substring of page
            # error # page does not work
            print "error; breaking loop" # stub
            break
        else: # look at the successful page and extract OCLC numbers
            print "extracting OCLC numbers from page"
            utilities.getOCLCNumbers(OCLCNumbers, retrieved_HTML)
            print "after page(s) of results from this search string, OCLCNumbers list is " + str(OCLCNumbers)
            print "page OK - so now we look for successive pages to this one"
            pageNumberToTry += 1 # increment page number
            utilities.waitRandomTime()

# finished
print "search and retrieval of all sought-after terms is complete"

#test that receptacle contains the OCLC numbers you want
confirmatoryOutput = ""
listOfAuthorNames = []
for oclcNumberCollected in OCLCNumbers: # get the actual data associated with each OCLC number
    record=utilities.OCLCNumberToRecord(oclcNumberCollected)
    # output to console and to log file confirming receipt of input
    confirmatoryOutput="record: \n"+record
    f.write(confirmatoryOutput)
    print(confirmatoryOutput)
    latestAuthorNamesExtracted = utilities.extractAuthorNames(record)
    confirmatoryOutput="author names extracted from this record: " + str(latestAuthorNamesExtracted)+"\n\n"
    f.write(confirmatoryOutput)
    print(confirmatoryOutput)
    listOfAuthorNames = listOfAuthorNames + latestAuthorNamesExtracted
    utilities.waitRandomTime()
    confirmatoryOutput = str(listOfAuthorNames)
    f.write(confirmatoryOutput)
    print(confirmatoryOutput + "\n")

# the end
print "exit stage right"
f.write("end")

# don't forget to close the log file at the end'
f.close()
