from wikibaseintegrator import WikibaseIntegrator
import json
import pytumblr
import datetime
import sys
from schedule import every, repeat, run_pending
import schedule
import time
from wikibaseintegrator.wbi_config import config as wbi_config
import requests



class Colors:
    """ ANSI color codes """
    COLOR = lambda R,G,B: f'\033[38;2;{R};{G};{B}m'
    TIMECOLOR = '\033[38;2;255;86;127m'

    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"

    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"

    END = "\033[0m"
    
ANSI = Colors

def noConnection() -> bool:
    try:
        requests.get('http://api.tumblr.com')
        requests.get('http://www.wikidata.org')
        return False
    except:
        return True



def isDead(person:str)->bool:
    
    deathDate = 'P570'
    wbi = WikibaseIntegrator()
    my_first_wikidata_item = wbi.item.get(entity_id=person)


    d = my_first_wikidata_item.get_json()
    if deathDate in d['claims'].keys():
        return True
    else:
        return False
    
    
def post(post: dict,client:pytumblr.TumblrRestClient,deceased:bool) -> dict:
    today = datetime.date.today()
    date = today.strftime(post['date'])
    if deceased:
        option = 'dead'
        RUN = False
    else:
        option = 'alive'
        post['alive']['body'] = post['alive']['body'] % date
    
    #Creating a text post
    post = client.create_text(
        blogname = post['blogName'], 
        state="published", 
        slug="tumblr-death-bot by @allie-anarchist",
        title=post[option]['title'], 
        body=post[option]['body'],
        tags=post['tags']
    )

    return post


def job(configPath: str, client: pytumblr.TumblrRestClient,forcePost: bool) -> None:
    global RUN
    
    f = open(configPath,'r')
    f = f.read()
    config = json.loads(f)


    today = datetime.datetime.now()
    date = today.strftime("%Y-%m-%d %H:%M:%S")
    try:
        if noConnection():
            raise('fuck')
    except:
        print(f'{ANSI.TIMECOLOR}[{date}]{ANSI.END} {ANSI.YELLOW}[ERROR]{ANSI.END} - {ANSI.BROWN+ANSI.ITALIC}SOMETHING FUCKED UP: NO CONNECTION... TRYING AGAIN LATER{ANSI.END}')
        return
    
    try:
        dead = isDead(config['wiki']['personID'])
        was_posted = f'{ANSI.BOLD+ANSI.PURPLE}[STATUS]{ANSI.END}'

        #-ONLY POST AT DEFAULT_POST_TIME OR IF HE KICKS IT-#
        if forcePost or dead:
            result = post(config['tumblr']['post'],client,dead)
            was_posted = f'{ANSI.BOLD+ANSI.CYAN}[POSTED]{ANSI.END}'
        #

        #-system messages-#
        if dead:
            print(f'{ANSI.TIMECOLOR}[{date}]{ANSI.END} {was_posted} - {ANSI.RED}HENRY KISSINGER IS DEAD{ANSI.END}')
            RUN = False #- STOP RUNNING WHEN HE FINALLY KICKS IT -#
        else:
            print(f'{ANSI.TIMECOLOR}[{date}]{ANSI.END} {was_posted} - {ANSI.GREEN}HENRY KISSINGER IS ALIVE{ANSI.END}')

        #
    except:
        print(f'{ANSI.TIMECOLOR}[{date}]{ANSI.END} {ANSI.YELLOW}[ERROR]{ANSI.END} - {ANSI.BROWN+ANSI.ITALIC}SOMETHING FUCKED UP SOMEWHERE... TRYING AGAIN LATER{ANSI.END}')
        


RUN = True
def main() -> None:
    
    #-get configs-#
    configPath = sys.argv[1]
    if len(sys.argv) >= 3:
        postOnStart = sys.argv[2]
    else: 
        postOnStart = False
    if postOnStart == "True":
        postOnStart = True
    else:
        postOnStart = False

    f = open(configPath,'r')
    f = f.read()
    config = json.loads(f)
    #
    #-KEYS-#
    f = open(config['tumblr']['keys'],'r')
    f = f.read()
    keys = json.loads(f)
    client = pytumblr.TumblrRestClient(
        keys['consumer_key'],
        keys['consumer_secret'],
        keys['oauth_token'],
        keys['oauth_secret']
    )
    #
    #--#
    wbi_config['USER_AGENT'] = config['wiki']['user']
    #

    #-default post time and interval-#
    DEFAULT_POST_TIME = config['scheduling']['default_post_time']
    interval = config['scheduling']['interval']
    if type(interval) != int:
        raise Exception('scheduling[interval] must be int')
    if interval >= 60:
        raise Exception('scheduling[interval] must be less than 60')
    #

    job(configPath,client,postOnStart)

    #-run every minute with forcePost=False except AT DEFAULT_POST_TIME-#
    hrs = [n for n in range(0,24) if n != DEFAULT_POST_TIME]
    for i in hrs:
        for n in [i*interval for i in range(0,60) if i*interval < 60]:
            schedule.every().day.at(f'{i:02}:{n:02}').do(job,configPath,client,False)
    #

    schedule.every().day.at(f'{DEFAULT_POST_TIME:02}:00').do(job,configPath,client,True)#- run with forcePost at DEFAULT_POST_TIME -#

    while RUN:
        run_pending()
        time.sleep(1)
    
if __name__ == '__main__':
    main()
