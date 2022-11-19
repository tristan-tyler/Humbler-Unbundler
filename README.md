## Preface

This tool doesn't really leverage anything too weird and is very simple in execution (it's all front end api calls that the websites make)

To my knowledge there are no inherent dangers of using this tool, I presonally redeemed over 500 games (which took 12 or so hours)

HOWEVER,

```
Please use this tool at your own risk
I make no garuntees involving the of the safety of using this tool.
```

## Prerequisites

- Firefox (or change script, explained below)
- Python 3
- pip (usually comes with python)
- selenium (`pip install selenium`)

## Usage

This script is currently set up to use Firefox change line 32 if you would like to try using a different browser

`driver = webdriver.Firefox() --> driver = webdriver.Chrome()`

https://www.selenium.dev/documentation/webdriver/browsers/

It should work on whatever you want, let me know if it does!

### Purpose

This is a tool for automatically redeeming humble bundle steam keys to steam. With the script as-is you can expect about 41 games per hour redeemed automatically

`python unbundlerize.py`

## Flow

1. Web browser will open
   - Address bar will be red with a little robot symbol at the start
   - Browser should not grab credentials already used in the browser of choice
   - Browser extentions should be disabled
1. Hublebundle login page will open
   - Log In
   - Press enter in `terminal`
1. Pages will flash rapidly grabbing json info for processing
1. Steam login page will open
   - Log In
   - Press enter in `terminal`
1. Console will output messages about redemption, the process may take quite a while (it did for me)
   - Open the browser console and go to the network tab (usually F12) if you want to see the requests being made
1. Browser will close when complete
1. File .used_keys will be generated for future runs of the tool (skips redemption call so we don't waste time on stuff we know is already used)

## Configuraation

At the top of the file there are two variables

defaults are `redeem_retry_rate_seconds = 60 | redeem_cooldown_minutes = 10`

```
With settings 30 sec, 30 min it took me quite a while because it wouldn't have stopped being angry after 30 minutes and then it would take an hour
with settings 30 sec, 10 min I had way more success and it would take 20 - 50 minutes between request sessions, idk why tbh

Please report back how/what other stuff worked for you if you have the time!
```
