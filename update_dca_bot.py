from py3cw.request import Py3CW
import json
import sys

# 3Commas DCA Bot Base Order and Safety Order calculator
# uses python3 and py3cw (https://github.com/bogdanteodoru/py3cw)
# pip install py3cw

# Put your API Key and Secret here
# API needs read bot, write bot and read account
API_KEY = ''
API_SECRET = ''


# add your bot names and percentage of the portfolio you want to use
# e.g. we use 50% for the bot "Bitmex USDT Long Bot" and 25% for "Bitmex USDT Short Bot"
BOTS = {"Bitmex USDT Long Bot": 50, "Bitmex USDT Short Bot": 25}

def getAccounts():
    error, data = p3cw.request(
        entity='accounts',
        action=''
    )

    # print error and exit
    if error:
        print("ERROR: " + str(error))
        sys.exit()

    account_amount = {}

    for account in data:  # we only need the id and usd amount
        account_id = account['id']
        value = account['usd_amount']
        account_amount[account_id] = value

    return account_amount


def getBots():
    error, data = p3cw.request(
        entity='bots',
        action=''
    )

    # print("Bot: " +  str(data))
    # print error and exit
    if error:
        print("ERROR: " + str(error))
        sys.exit()

    return data


def writeBot(bot: json):
    error, data = p3cw.request(
        entity='bots',
        action='update',
        action_id=str(bot["id"]),
        payload=bot
    )

    # print error and exit
    if error:
        print("ERROR: " + str(error))
        sys.exit()


def updateBots():
    bots = getBots()
    accounts = getAccounts()

    for bot in bots:
        name = bot['name']

        print("---------------------------------------------")

        if name not in BOTS:
            print("Bot: " + name + " will be ignored")
            continue

        bot_related_account_id = bot['account_id']
        account_usd_value = float(accounts[bot_related_account_id])

        print("Bot: " + name + " for account ID: " +
              str(bot_related_account_id))

        # calculate base order
        # 1. calculate factor
        # -> base order + all safety orders = factor
        martingale_volume_coefficient = float(
            bot['martingale_volume_coefficient'])
        base_order = 100 # base order size
        safety_order_1 = base_order * 2 # first safety = 2 * base order
        safety_order_x = 0
        i = 1
        while i < bot['max_safety_orders']:
            safety_order_x += safety_order_1 * pow(martingale_volume_coefficient, i)
            i += 1

        factor = (base_order + safety_order_1 + safety_order_x) / 100
        print("Calculated factor: " + str(factor))

        # 2. calculate base order and first safety
        # -> usd_for_bot / max_deals = max amount for one deal
        # -> max amount for one deal divided by factor = base order
        max_deals = bot['max_active_deals']
        usd_for_bot = account_usd_value * BOTS[name] / 100
        base_order = usd_for_bot / max_deals / factor
        safety_order = base_order * 2

        print("Bot uses: " + str(BOTS[name]) + "% of $" + str(account_usd_value)+ " =>> $" + str(usd_for_bot))
        print("Old BO: " + bot['base_order_volume'] + " Old SO: " + bot['safety_order_volume'] + " New BO: " +
              str(base_order) + " New SO: " + str(safety_order))

        # set new base order and safety and write bot
        bot['base_order_volume'] = str(base_order)
        bot['safety_order_volume'] = str(safety_order)

        write_input = input("Do you want to write the new Base and Safety Orders? Y/N ")
        if write_input.lower() == "y" or write_input.lower() == "yes":
            writeBot(bot)
            print("Bot Settings updated")
        else:
            print("read only no update")


# main

p3cw = Py3CW(
    key=API_KEY,
    secret=API_SECRET
)

updateBots()
