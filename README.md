# Pi-Fi
An occupancy estimator using Wi-Fi and big data methods

With this program running in its own terminal window, along with Kismet running on the same RPi in Kali Linux, 
you can estimate the occupancy/count devices close to the Raspberry Pi.

The following Linux packages must be installed on the RPi:

Kismet:
```
wget -O - https://www.kismetwireless.net/repos/kismet-release.gpg.key | sudo apt-key add -
echo 'deb https://www.kismetwireless.net/repos/apt/release/kali kali main' | sudo tee /etc/apt/sources.list.d/kismet.list
sudo apt update
sudo apt install kismet
```

MQTT Broker mosquito:
```
sudo apt-get install mosquitto mosquito-clients 
```
Python Packages:
```
pip3 install pandas  
pip3 install sqlite3 
pip3 install numpy 
pip3 install ouilookup
pip3 install -U scikit-learn
```

Now we create a monitoring interface via the airmon-ng application and the kismet application:
```
sudo airmon-ng check kill
sudo airmon-ng start wlan0
sudo kismet -c wlan0mon
```
In a new terminal window we run the python script with the following command by opening a terminal in the folder which contains 
the “pi-fi.py” and “train.csv” files downloaded from GitHub this repository.
```
python3 pi-fi.py
```
