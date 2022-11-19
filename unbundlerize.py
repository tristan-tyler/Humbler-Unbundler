from selenium import webdriver
from selenium.webdriver.common.by import By
from json import loads, dumps
from os import path
from time import sleep

# User defined variables
# Please report back what worked for you (how many games in a row/how long it took) if you have the time!
# Make an issue! https://github.com/gr8engineer2b/Humbler-Unbundler/issues
redeem_retry_rate_seconds = 60
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
  # In most cases we want to pop off the top of the list below
  if response["success"] == True or response["success"] == "true":
    used_keys[f"{item['redeemed_key_val']}"] = "sucessfully redeemed"
    try_redeem.pop(0)
    print(f"Sucessfully redeemed {item['human_name']}")
    sleep(redeem_retry_rate_seconds) # sleep for a number of seconds
  elif response.get("purchase_result_details") == 15:
    used_keys[f"{item['redeemed_key_val']}"] = "owned by a different account"
    try_redeem.pop(0)
    sleep(redeem_retry_rate_seconds) # sleep for a number of seconds
  elif response.get("purchase_result_details") == 9:
    used_keys[f"{item['redeemed_key_val']}"] = "already redeemed to this account"
    try_redeem.pop(0)
    sleep(redeem_retry_rate_seconds) # sleep for a number of seconds
  elif response.get("purchase_result_details") == 24:
    print(f"You need another product before it is possible to redeem : {item['human_name']}")
    used_keys[f"{item['redeemed_key_val']}"] = f"other software required for: {item['human_name']}"
    try_redeem.pop(0)
    sleep(redeem_retry_rate_seconds) # sleep for a number of seconds
  elif response.get("purchase_result_details") == 53:
    print(f"Steam is disallowing redeem due to too many requests, waiting for a while ({redeem_cooldown_minutes} min) and will continue...")
    # occasionally write to file so as not to lose progress
    open("./.used_keys", "w", encoding="utf8").write(dumps(used_keys))
    sleep(redeem_cooldown_minutes*60) # steam got angry, sleep for a number of minutes
  else :
    try_redeem.pop(0)
    print(f"The following response was not handled {response}")
    sleep(redeem_retry_rate_seconds) # sleep for a number of seconds

# cleanup
open("./.used_keys", "w", encoding="utf8").write(dumps(used_keys))
driver.close()
print("FINISHED!")