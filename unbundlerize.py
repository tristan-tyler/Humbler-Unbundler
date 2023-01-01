from selenium.webdriver import Firefox as Browser
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from json import loads, dumps
from os import path
from time import sleep
from datetime import datetime
from sys import argv, exit, stdout
import logging, getopt

# Please report back what worked for you (how many games in a row/how long it took) if you have the time!
# Make an issue! https://github.com/gr8engineer2b/Humbler-Unbundler/issues

# Defaults
retry_rate_seconds = 60
redeem_cooldown_minutes = 10
loglevel = "INFO"

#initialize log
try:
  opts, args = getopt.getopt(argv[1:],"hr:c:",["log="])
except getopt.GetoptError:
      print('unbundlerize.py -r <retry_rate_seconds> -c <redeem_cooldown_minutes> --log=(DEBUG|INFO|etc...)')
for opt, arg in opts :
  if opt == '-h':
    print('unbundlerize.py -r <retry_rate_seconds> -c <redeem_cooldown_minutes> --log=(DEBUG|INFO|etc...)')
    exit()
  elif opt in ("--log="):
    loglevel = arg
  elif opt in ("-r"):
    retry_rate_seconds = arg
    if not retry_rate_seconds.isdigit() :
      raise ValueError("Invalid retry rate (seconds)")
    retry_rate_seconds = int(retry_rate_seconds)
  elif opt in ("-c"):
    redeem_cooldown_minutes = arg
    if not redeem_cooldown_minutes.isdigit() :
      raise ValueError("Invalid redeem cooldown (minutes)")
    redeem_cooldown_minutes = int(redeem_cooldown_minutes)

numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)

logname = f'Unbundler {datetime.now().strftime("%H%M %m%d%y")}.log'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=numeric_level)
logging.getLogger().addHandler(logging.StreamHandler(stdout))

logging.info("BEGIN!")

logging.info("Checking for used keys file")
if path.exists("./.used_keys") :
  logging.info("Used keys file exists")
  used_keys = loads(open("./.used_keys", "r", encoding="utf8").read())
else :
  logging.info("Used keys file does not exist, creating")
  open("./.used_keys", "w", encoding="utf8")
  logging.info("Successfully created used keys file")
  used_keys = {}

logging.info("Initializing Browser")
driver = Browser()

logging.info("Opening login page for humble bundle")
driver.get("https://www.humblebundle.com/login")
logging.info("Waiting for user input")
input("Once logged in, Press Enter:")

logging.info("Received input, getting owned bundles json")
try :
  driver.get("view-source:https://www.humblebundle.com/api/v1/user/order")
  json = loads(driver.find_element(By.TAG_NAME,"pre").text)
except NoSuchElementException as err :
  driver.get("https://www.humblebundle.com/api/v1/user/order")
  json = loads(driver.find_element(By.TAG_NAME,"pre").text)

logging.debug(json)
try_redeem = []
needs_reveal = []
logging.info("Getting individual keys from bundles")
for gamekey in json :
  try :
    driver.get(f"view-source:https://www.humblebundle.com/api/v1/orders?all_tpkds=true&gamekeys={gamekey['gamekey']}")
    contents = loads(driver.find_element(By.TAG_NAME,"pre").text)
  except NoSuchElementException as err :
    driver.get(f"https://www.humblebundle.com/api/v1/orders?all_tpkds=true&gamekeys={gamekey['gamekey']}")
    contents = loads(driver.find_element(By.TAG_NAME,"pre").text)

  items = contents[f"{gamekey['gamekey']}"]["tpkd_dict"]["all_tpks"]
  logging.debug(items)
  logging.info("Sorting keys")
  for item in items :
    logging.debug(item)
    if item["key_type"] != "steam":
      logging.info("Key is not a steam key")
      continue
    if item.get("redeemed_key_val") :
      logging.info("Key already revealed")
      try_redeem.append(item)
    else :
      logging.info("Key not yet revealed")
      needs_reveal.append(item)

# humble bundle has a weird system where you have to "reveal" keys and in order 
# to get the keys from the api calls they need to be revealed
for item in needs_reveal :
  # This is a round about way to do a post request in selenium
  js = f'''var xhr = new XMLHttpRequest();
  xhr.open('POST', 'https://www.humblebundle.com/humbler/redeemkey', false);
  xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
  xhr.send('key={item['gamekey']}&keyindex={item['keyindex']}&keytype={item['machine_name']}');
  return xhr.response;'''
  # this executes above
  logging.info("Attempting to reveal key")
  logging.debug(item)
  response = loads(driver.execute_script(js))
  if response["success"] == True or response["success"] == "true":
    logging.info("Key revealed")
    try :
      driver.get(f"view-source:https://www.humblebundle.com/api/v1/orders?all_tpkds=true&gamekeys={item['gamekey']}")
      contents = loads(driver.find_element(By.TAG_NAME,"pre").text)
    except NoSuchElementException as err :
      driver.get(f"https://www.humblebundle.com/api/v1/orders?all_tpkds=true&gamekeys={item['gamekey']}")
      contents = loads(driver.find_element(By.TAG_NAME,"pre").text)

    contents = loads(driver.find_element(By.TAG_NAME,"pre").text)
    item = contents[f"{item['gamekey']}"]["tpkd_dict"]["all_tpks"][item['keyindex']]
    logging.debug(item)
    try_redeem.append(item)

logging.info("Opening login page for Steam")
driver.get("https://steamcommunity.com/login/home/")
logging.info("Waiting for user input")
input("Once logged in, Press Enter:")

logging.info("Received input, getting session id for redemption")
driver.get(f"https://store.steampowered.com/account/registerkey")
sessionid = driver.execute_script("return g_sessionID")
logging.debug(sessionid)

# To handle errors that are recoverable circumstances we pop(0) entries off the top of the list
# For loops would skip in a case like "too many requests from this ip"
logging.info("Entering redeem loop")
while try_redeem :
  # set item
  item = try_redeem[0]
  # we do not want to repeat redemption attempts because of steam limits
  logging.debug(item)
  logging.info("Checking for key in .used_keys")
  if used_keys.get(f"{item['redeemed_key_val']}") :
    try_redeem.pop(0)
    logging.info("Key existed, skipped")
    continue

  # This is a round about way to do a post request in selenium
  js = f'''var xhr = new XMLHttpRequest();
  xhr.open('POST', 'https://store.steampowered.com/account/ajaxregisterkey/', false);
  xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
  xhr.send('product_key={item['redeemed_key_val']}&sessionid={sessionid}');
  return xhr.response;'''
  # this executes above
  logging.info("Attempting to redeem key")
  logging.debug(item)
  response = loads(driver.execute_script(js))
  logging.debug(response)

  # response 1 (or true) is success / 2 for some kind of failure 
  # In most cases we want to pop off the top of the list below
  if response["success"] == True or response["success"] == "true":
    used_keys[f"{item['redeemed_key_val']}"] = "successfully redeemed"
    try_redeem.pop(0)
    logging.info(f"Successfully redeemed {item['human_name']}")
    sleep(retry_rate_seconds) # sleep for a number of seconds
  elif response.get("purchase_result_details") == 15:
    used_keys[f"{item['redeemed_key_val']}"] = "owned by a different account"
    try_redeem.pop(0)
    logging.info(f"{item['human_name']} is owned by a different account")
    sleep(retry_rate_seconds) # sleep for a number of seconds
  elif response.get("purchase_result_details") == 9:
    used_keys[f"{item['redeemed_key_val']}"] = "already redeemed to this account"
    try_redeem.pop(0)
    logging.info(f"{item['human_name']} is already redeemed to this account")
    sleep(retry_rate_seconds) # sleep for a number of seconds
  elif response.get("purchase_result_details") == 24:
    try_redeem.pop(0)
    logging.info(f"You need another product before it is possible to redeem : {item['human_name']}")
    sleep(retry_rate_seconds) # sleep for a number of seconds
  elif response.get("purchase_result_details") == 53:
    logging.info(f"Steam is disallowing redeem due to too many requests, waiting for a while ({redeem_cooldown_minutes} min) and will continue...")
    # occasionally write to file so as not to lose progress
    logging.info("Writing keys to file")
    open("./.used_keys", "w", encoding="utf8").write(dumps(used_keys))
    logging.info("Finished writing keys to file")
    sleep(redeem_cooldown_minutes*60) # steam got angry, sleep for a number of minutes
  else :
    try_redeem.pop(0)
    logging.warning(f"The following response was not handled {response}")
    sleep(retry_rate_seconds) # sleep for a number of seconds

# cleanup
open("./.used_keys", "w", encoding="utf8").write(dumps(used_keys))
driver.close()
logging.info("ALL DONE!")