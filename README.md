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
   - Open the browser console and go to the newtwork tab if you want to see the requests
1. Browser will close when complete
1. File .used_keys will be generated for future runs of the tool (skips redemption call so we don't waste time on stuff we know is already used)

## Configuraation

At the top of the file there are two variables

defaults are `redeem_retry_rate_seconds = 30 | redeem_cooldown_minutes = 10`

```
Because I ran this on my own stuff I have not been able to test multiple settings
I used 30 seconds between redeems and a 30 minute cooldown (not recommended)
a 30 minute cooldown is not long enough of a wait so I ended up with an hour
gap between redemption sessions over the course of 700 game keys (very long)

It is possible that a 30 second gap between redemptions hurts more than it helps
I was able to redeem around 41 games at a time per hour which took 20 minutes minimum
If performed faster you might hit the rate limit and initiate the longer coolown sooner
but I'm really not sure as of now

Please report back how/what worked for you if you have the time!
```
