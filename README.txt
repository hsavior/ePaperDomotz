# ePaperDomotz
This is my Python Code to monitor some Stats via Domotz API and present at the ePaper

To install dependencies:

pip3 install -r requirements.txt

To execute the script during system boot edit the crontab with 'crontab -e' and add the following line:

@reboot cd /home/USERNAME/ePaperDomotz  && ./updateScreen.py >> /tmp/epaper.out
@reboot cd /home/USERNAME/ePaperDomotz  && ./configWebpage.py >> /tmp/webpageCofig.out


To edit the API_KEY, Agent_ID and API_URL edit the file updateScreen.conf or access the address http://<Pi_IP_Address>:5000
