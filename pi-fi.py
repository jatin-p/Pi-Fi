import os
import subprocess
import time
import glob
import sqlite3
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt
import threading


from OuiLookup import OuiLookup
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from matplotlib import pyplot as plt
from pathlib import Path

home = str(Path.home())


# Name of device manufacterers we want to mark as valid
MAKERS = ["SAMSUNG","APPLE","GOOGLE","LG","MOTOROLA","HUAWEI","ONEPLUS","SONY","BLACKBERRY","INTEL","BROADCOM","KILLER"]


broker_address="localhost" # Enter broker IP here if not localhost

client = mqtt.Client("mqtt-pifiscanner") # create new instance
client.connect(broker_address) # connect to broker




# Returns string of latest kismet log file
def get_kismet():
    # cwd = os.getcwd()
    files_path = os.path.join(home, '*.kismet')
    files = sorted(glob.iglob(files_path), key=os.path.getctime, reverse=True) 
    return files[0]

# Copy file into two directories 0 and 1
def split_dir():
    os.system("mkdir 0 1")
    os.system("sudo cp "+get_kismet()+" 0/")
    os.system("sudo cp "+get_kismet()+" 1/")

# Extract Wi-Fi Clients and other categories from database, create time, vendor, and valid_ columns
# Returns a pandas df and saves non-identifiable info to csv file for training
def extract_clients():
    con = sqlite3.connect(get_kismet())

    # Extract Wi-Fi Clients from devices database along with all relevent columns
    clients= pd.read_sql_query("SELECT bytes_data,strongest_signal,devmac,first_time,last_time FROM devices WHERE type='Wi-Fi Client'",con)

    # Calculate total time of client
    clients["time"]=clients["last_time"]-clients["first_time"]


    # Create empty list to append the vendors
    vendors =[]
    for index in range(len(clients["devmac"])):
        # lookup OUI and save to temp variable
        temp=OuiLookup().query(clients.loc[index,"devmac"])
        # extract vendor string and append to list
        vendors.append(temp[0].values())
    
    # Convert vendor list to df
    df = pd.DataFrame.from_dict(vendors)
    # Create vendor column in clients df
    clients["vendor"]=df
    clients.dropna()

     
    #regstr = '|'.join(makers)

    # Check if vendor is valid by checking if a manufacters name appears in vendor column
    vendor_results=[]
    for index,row in clients.iterrows():
        # lookup vendor name and store in temp
        temp = row["vendor"]
        temp=str.upper(str(temp))
        res = any(x in temp for x in MAKERS)

        if bool(res):
            vendor_results.append(1)
        else:
            vendor_results.append(0)

    # Mark vendor as valid if from reputable smartphone maker
    clients["valid_vendor"]=vendor_results



    # Mark clients < 90s as 0 via new column, 1 for 
    clients["valid_time"]=np.where(clients["time"]<90,0,1)
    # Mark strongest_signal of 0 is invalid
    clients["valid_rssi"]=np.where(clients["strongest_signal"]==0,0,1)
    # Mark strongest_signal of 0 is invalid
    clients["valid_bytes"]=np.where(clients["bytes_data"]==0,0,1)
   
    # Mark outcome as 1 if anycolumns are valid 
    clients["outcome"]=np.where((clients["valid_vendor"]&((clients["valid_time"]+clients["valid_rssi"]+clients["valid_bytes"])>=2)),1,0)
    print("Valid devices: %d" % clients["outcome"].sum())
    
    con.close()
    return clients

def create_train_csv(clients):
    # Create a training file with the 1st 
    clients=clients.drop(columns=["devmac"])
    clients.to_csv("train.csv",index=False)

def scan_devices():
    test=extract_clients()
    
    create_train_csv(test) # comment if you don't need to create your own csv for training
    
    
    train = pd.read_csv("train.csv")
    X_train = train[['bytes_data','strongest_signal','time']]
    y_train = train[['outcome']]
    X_test = test[['bytes_data','strongest_signal','time']]
    y_test = test[['outcome']]
    
    
    classifier = KNeighborsClassifier(n_neighbors=5)
    classifier.fit(X_train, y_train.values.ravel())
    
    y_pred = classifier.predict(X_test)
    
    test["prediction"]=y_pred
    
    
    print(confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred))
    
    
    for index,row in test.iterrows():
        if row["valid_vendor"]:
            print('{}/{}'.format(row["vendor"],row["devmac"]))
    estimate = test["prediction"].sum()
    
    print("\n***** ESTIMATE: %d *****\n" % estimate)
    
    client.publish("home/occupancy",int(estimate))


if __name__ == "__main__":
    # Create wifi monitoring interface
    # os.system("sudo airmon-ng check kill")
    # os.system("sudo airmon-ng start wlan0")
    # os.system("sudo run_scanner.sh")
    # Run kismet on wifi monitoring interface in subprocess
    # p=subprocess.run(["sudo kismet -c wlan0mon"],capture_output=True,text=True,shell=True)
    
    while(1):
        # print(p.stdout)
        scan_devices()
        time.sleep(10)

    

    
