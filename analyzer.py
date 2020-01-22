#---------------------------
#SMS Text Analyzer Pet Project
#Ian Murray
#January 20th, 2020
#---------------------------
from sklearn.feature_extraction.text import TfidfVectorizer, TfidfTransformer, CountVectorizer
from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import RandomOverSampler
from sklearn.feature_selection import chi2
from sklearn.naive_bayes import MultinomialNB
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import pandas as pd 
import numpy as np

#---SMS Class, represents text and its metadata---
class SMS():
    #---Constructor---
    #Initialize the phone #, timestamp, sent/received flag, and body for an SMS
    def __init__(self, number, timestamp, category, content, contact):
        self.number = number
        self.timestamp = timestamp
        self.contact = contact
        if category == "1":
            self.category = "Received Text"
        else:
            self.category = "Sent Text"
        self.content = content
        
    #---Print function override---
    def __str__(self):
        return "From: " + self.number + \
        "\nTimestamp: " + self.timestamp + \
        "\nCategory: " + self.category + \
        "\nContact: " + self.contact + \
        "\nContent: " + self.content
    
#---Function buildSMSData---
#Builds the lits of text messages along with their metadata
#Param FILENAME: where the text input is located
#Param THRESHOLD: the min # of messages to be included in the dataframe
#Param MODE: a flag indicates to add either sent or received messages
#Returns the constructed dataframe 
def buildSMSData(FILENAME, THRESHOLD, MODE):
    print("------------------------------------------------------------------")
    print("Building SMS Database...", end = '')
    #List of texts
    SMS = []
    
    #Set up parser
    tree = ET.parse(FILENAME)
    root = tree.getroot()
    for child in root: #For each individual text
        #Grab attributes and build on list
        number = child.attrib.get("address")[-10:] #10 digit number to avoid country codes
        timestamp = child.attrib.get("readable_date")
        category = child.attrib.get("type")
        content = child.attrib.get("body") 
        contact = child.attrib.get("contact_name")
        #SMSDatabase.append(SMS(number, timestamp, category, content))  
        if MODE == "3":
            SMS.append({"number": number, "timestamp": timestamp, "category": category, "content": content, "contact": contact})  
        elif category == MODE: #Only consider messages sent to me
            SMS.append({"number": number, "timestamp": timestamp, "category": category, "content": content, "contact": contact})  

    #Convert to pandas dataframe
    SMSDatabase = pd.DataFrame(SMS, columns = ["number", "timestamp", "category", "content", "contact"])  
    #Filter out contacts with less than threshold contacts
    SMSDatabase = SMSDatabase[SMSDatabase.groupby('number').number.transform(len) >= THRESHOLD]
    
    print("Done! " + str(SMSDatabase['number'].nunique()) + " contacts and " + \
      str(SMSDatabase.size) + " messages saved.")
    return SMSDatabase

#---Function plotTopContacts---
#Plots the users top contacts in a bar graph
#Param SMSDatabase: the data structure to plot
def plotTopContacts(SMSDatabase):
    print("------------------------------------------------------------------")
    fig = plt.figure(figsize=(8,6))
    SMSDatabase.groupby('contact').content.count().plot.bar(ylim = 0)
    plt.show()
    
#---Function findDefiningWords---    
#For each contact, use vectorizers and Chi-square to find their most distinguising words & phrases
#Param SMSDatabase: the data structure with underlying data
#Param N, how many unigrams/bigrams to plot per user
def findDefiningWords(SMSDatabase, N):
    print("------------------------------------------------------------------")
    #Speeds up code by truncating duplicate output
    SMSDatabase['contact_id'] = SMSDatabase['contact'].factorize()[0]
    category_id_df = SMSDatabase[['contact', 'contact_id']].drop_duplicates().sort_values('contact_id')
    category_to_id = dict(category_id_df.values)
    #id_to_category = dict(category_id_df[['number_id', 'contact']].values)
    
    #Vectorize the data
    tfidf = TfidfVectorizer(sublinear_tf = True, min_df = 2, norm = 'l2', encoding = 'latin-1', ngram_range=(1, 2), stop_words = 'english')
    features = tfidf.fit_transform(SMSDatabase.content).toarray()
    labels = SMSDatabase.contact_id
    
    #Apply chi2, sort, and print results
    for contact, contact_id in sorted(category_to_id.items()):
        features_chi2 = chi2(features, labels == contact_id)
        indices = np.argsort(features_chi2[0])
        feature_names = np.array(tfidf.get_feature_names())[indices]
        unigrams = [v for v in feature_names if len(v.split(' ')) == 1]
        bigrams = [v for v in feature_names if len(v.split(' ')) == 2]
        print("\nContact: '{}':".format(contact))
        print("  ---Most distinguishing words---\n. {}".format('\n. '.join(unigrams[-N:])))
        print("  ---Most distiguishing 2-word phrases---\n. {}".format('\n. '.join(bigrams[-N:])))
    
#---Function guess---    
#A simple game where users can input any text and the model will determine who is most likely to say that
#Param SMSDatabase: the data structure with underlying data
#Param SAMPLING: should we undergo sampling to even out the text distribution?
def guess(SMSDatabase, SAMPLING):
    print("------------------------------------------------------------------")
    if SAMPLING == 1: #Remove texts from favorite contacts
        RUS = RandomUnderSampler(random_state=0)
        XData, YData = RUS.fit_resample(SMSDatabase.iloc[:, [3]], SMSDatabase.iloc[:, 4])
    elif SAMPLING == 2: #Add duplicate texts from lessser contacts
        RUS = RandomOverSampler(random_state=0)
        XData, YData = RUS.fit_resample(SMSDatabase.iloc[:, [3]], SMSDatabase.iloc[:, 4])
    else: #Use data as is
        XData = SMSDatabase.iloc[:, [3]]
        YData = SMSDatabase.iloc[:, 4]
    
    #Reformat and initialize mutlinomialNB model paramteres
    formattedData = pd.DataFrame({"Content": XData['content'], "Contact": YData})  
    countVectorizer = CountVectorizer()
    XCount = countVectorizer.fit_transform(formattedData['Content'])
    tfidfTransformer = TfidfTransformer()
    XTfidf = tfidfTransformer.fit_transform(XCount)
    model = MultinomialNB().fit(XTfidf, formattedData['Contact'])
    
    #Initiate game
    text = ""
    while text != "quit":
        text = input("Please enter some text for me to guess, or type quit: ")
        if text != "quit":
            print("This sounds most like: ", end = '')
            print(model.predict(countVectorizer.transform([text])))
    print("Thanks for playing!")
           
#---Function runModel---
#Reserve fun for parameter tuning only by putting other function calls here
#See main() for detailed param descriptions
def runModel(FILENAME, THRESHOLD, MODE, PLOT, UNIQUEWORDS, N, GUESSING, SAMPLING):
    SMSDatabase = buildSMSData(FILENAME, THRESHOLD, MODE) #Construct data structure    
    if PLOT:
        plotTopContacts(SMSDatabase) #Plot top contact figures
    if UNIQUEWORDS:
        findDefiningWords(SMSDatabase, N) #Output tops words & phrases for each contact
    if GUESSING:
        guess(SMSDatabase, SAMPLING) #Guessing game
    
#---Function Main---
#Master controller for entire program
def main():
    
    #------Program Parameters, Adjust as needed------
    
    #***Universal Parameters***
    #Filename: The name of the file where your texts are stored, works best if file is stored
    #in local directory. I used the program "SMS Backup & Restore" on the Google Play store
    #to generate this data.
    FILENAME = "texts.xml"
    #Threshold: The minimum number of messages required to not be culled out of the data.
    #This is useful for removing outlier contacts that you may have only a few messages with.
    #Generally the model works better when it considers a fewer amount of contacts with
    #more messages per contact. Recommended value: Something that limits the number of
    #remaining contacts to no more than 10-15. See PLOT constant below for help.
    THRESHOLD = 500
    #Mode: Determines what kind of texts messages you would like to analyze.
    #Set to "1" to consider only messages you have received from your contacts
    #Set to "2" to consider only messages you have sent to your contacts
    #Set to "3" to consider both sent and received messages (not recommended)
    MODE = "1"
    
    #***Graph-Related Parameters****
    #Plot: Set to True if you would like to see a bar graph showing the number of messages
    #between you and your contacts. The MODE constant affects the results of this graph
    #This function is useful for fine-tuning the THRESHOLD value above
    #Set to False to save computing time as this function can take 15 seconds or so.
    PLOT = True
    
    #***Distinguishing Words Parameters***
    #UniqueWords: Set to True if you would like to see the top words and phrases that are
    #associated with each contact. The MODE constant determines whether this function will
    #show the top phrases the contact likes to send to you, or which phrases you often send
    #to this contact.
    #Set to False to save computing time as this function can take 3-5 seconds per contacts
    UNIQUEWORDS = True
    #N: How many words and phrases would you like to be displayed for each contact?
    #Some of these words & phrases can be inaccurate if this value is set too high
    #Recommended value: Between 3 and 10.
    N = 8
    
    #***Guessing Game Parameters***
    #Guessing: Set to True if you would like to enable the bot that guesses who is most
    #likely to send a text message containing the given input. If MODE is set to "2" it
    #will instead show which contact you are most likely to send this message to.
    #Set to False to avoid playing this game
    GUESSING = True
    #Sampling: In cases where you interact with one contact way more than others, the guessing
    #algoritm's accuracy drops significantly due to overrepresentation. This can be fixed by
    #applying a resampling mechanism. Check the graph generated by PLOT to determine if your
    #data needs to be resampled.
    #Set to "1" to apply undersampling. The model will randomly remove some text messages
    #from your overrepresented contact. This will improve accuracy at the cost of a less
    #exhaustive data set.
    #Set to "2" to apply oversampling. This model will randomly duplicate text messages
    #from your underrepresented contacts. This will improve accuracy at the cost of
    #the model overfitting the data
    #Set to "3" to disable resampling entirely. Not recommended if your bar-graph is
    #not evenly distributed.
    #NOTE: Which resampling method produces better results depends on the nature of the dataset.
    #Try each method and select whatever appears to work better for you.
    SAMPLING = 2
    
    #-------------------------------------------------------------------------------------------
    
    runModel(FILENAME, THRESHOLD, MODE, PLOT, UNIQUEWORDS, N, GUESSING, SAMPLING)

#Call main
if __name__ == "__main__":
    main()