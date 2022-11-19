from selenium import webdriver
from selenium.webdriver.common.by import By
from json import loads, dumps
from os import path
from time import sleep

# User defined variables

# Because I ran this on my own stuff I have not been able to test multiple settings
# I used 30 seconds between redeems and a 30 minute cooldown (not recommended)
# a 30 minute cooldown is not long enough of a wait so I ended up with an hour
# gap between redemption sessions over the course of 700 game keys (very long)

# It is possible that a 30 second gap between redemptions hurts more than it helps
# I was able to redeem around 41 games at a time per hour which took 20 minutes minimum
# If performed faster you might hit the rate limit and initiate the longer coolown sooner
# but I'm really not sure as of now

# Please report back how/what worked for you if you have the time!

redeem_retry_rate_seconds = 30
redeem_cooldown_minutes = 10
# end User defined variables end

# try not to repeat redeem keys
if path.exists("./.used_keys") :
  used_keys = loads(open("./.used_keys", "r", encoding="utf8").read())
else :
  open("./.used_keys", "w", encoding="utf8")
  used_keys = {}

driver = webdriver.Firefox()

# log in to humble bundle
driver.get("https://www.humblebundle.com/login")
input("Once logged in, Press Enter:")

# get json of orders from humble bundle
driver.get("view-source:https://www.humblebundle.com/api/v1/user/order")
json = loads(driver.find_element(By.TAG_NAME,"pre").text)
try_redeem = []
needs_reveal = []
for gamekey in json :
  driver.get(f"view-source:https://www.humblebundle.com/api/v1/orders?all_tpkds=true&gamekeys={gamekey['gamekey']}")
  contents = loads(driver.find_element(By.TAG_NAME,"pre").text)
  items = contents[f"{gamekey['gamekey']}"]["tpkd_dict"]["all_tpks"]
  for item in items :
    if item["key_type"] == "steam":
      if item.get("redeemed_key_val") :
        try_redeem.append(item)
      else :
        needs_reveal.append(item)

# humble bundle has a wierd system where you have to "reveal" keys and in order 
# to get the keys from the api calls they need to be revealed
for item in needs_reveal :
  # This is a round about way to do a post request in selenium
  js = f'''var xhr = new XMLHttpRequest();
  xhr.open('POST', 'https://www.humblebundle.com/humbler/redeemkey', false);
  xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
  xhr.send('key={item['gamekey']}&keyindex={item['keyindex']}&keytype={item['machine_name']}');
  return xhr.response;'''
  # this executes above
  response = loads(driver.execute_script(js))
  if response["success"] == True or response["success"] == "true":
    driver.get(f"view-source:https://www.humblebundle.com/api/v1/orders?all_tpkds=true&gamekeys={item['gamekey']}")
    contents = loads(driver.find_element(By.TAG_NAME,"pre").text)
    item = contents[f"{item['gamekey']}"]["tpkd_dict"]["all_tpks"][item['keyindex']]
    try_redeem.append(item)

# log into steam
driver.get("https://steamcommunity.com/login/home/")
input("Once logged in, Press Enter:")

# getting session id for redemption
driver.get(f"https://store.steampowered.com/account/registerkey")
sessionid = driver.execute_script("return g_sessionID")

# To handle errors that are recoverable circumstances we pop(0) entries off the top of the list
# For loops would skip in a case like "too many requests from this ip"
while try_redeem :
  # set item
  item = try_redeem[0]
  # we do not want to repeat redemption attempts because of steam limits
  if used_keys.get(f"{item['redeemed_key_val']}") :
    try_redeem.pop(0)
    continue
  # no real reason this would come up for steam keys
  if item["is_expired"] == "True" or item["is_expired"] == True :
    try_redeem.pop(0)
    continue

  # This is a round about way to do a post request in selenium
  js = f'''var xhr = new XMLHttpRequest();
  xhr.open('POST', 'https://store.steampowered.com/account/ajaxregisterkey/', false);
  xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
  xhr.send('product_key={item['redeemed_key_val']}&sessionid={sessionid}');
  return xhr.response;'''
  # this executes above
  response = loads(driver.execute_script(js))

  # response 1 (or true) is success / 2 for some kind of failure 
  # I don't care enough to be ultra specific
  # In most cases we want to pop off the top of the list below
  if response["success"] == True or response["success"] == "true":
    used_keys[f"{item['redeemed_key_val']}"] = "sucessfully redeemed"
    try_redeem.pop(0)
    print(f"Sucessfully redeemed {item['human_name']}")
    sleep(redeem_retry_rate_seconds) # sleep for a number of seconds
  # purchase_result_details 9 or 15 seem to be things that are not redeemable
  elif response.get("purchase_result_details") == 9 or response.get("purchase_result_details") == 15:
    used_keys[f"{item['redeemed_key_val']}"] = "previously used"
    try_redeem.pop(0)
    sleep(redeem_retry_rate_seconds) # sleep for a number of seconds
  # purchase_result_details 53 indicates too many requests
  elif response.get("purchase_result_details") == 53:
    print(f"Steam is disallowing redeem due to too many requests, waiting for a while ({redeem_cooldown_minutes} min) and will continue...")
    # occasionally write to file
    open("./.used_keys", "w", encoding="utf8").write(dumps(used_keys))
    sleep(redeem_cooldown_minutes*60) # steam got angry, sleep for a number of minutes
  else :
    try_redeem.pop(0)
    print(f"The following response was not handled {response}")
    sleep(redeem_retry_rate_seconds) # sleep for a number of seconds

# cleanup
driver.close()
open("./.used_keys", "w", encoding="utf8").write(dumps(used_keys))