import os
import time
import re
from slackclient import SlackClient
from collections import *
import json
import random
import requests


# load environment variables
from os.path import join, dirname
from dotenv import load_dotenv, find_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path, override=True)

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
bot_id = None

# CONSTANTS
RTM_READY_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "help"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
ADD_USER_REGEX = "<@(|[WU].+?)>"
CHOICES = {}
SORTS = {}
FAKE_FUNCTIONS = ['umarfc']
FAKE_SORTS = ['umar']

# PR Label names
LABEL_COOP_REVIEW = "Coop Review"
LABEL_FT_REVIEW = "Review"
LABEL_WIP = "Work in Progress"
member_list = open("coops.txt", "r") # coop review
BOX_1 = deque(filter(None, member_list.read().split('\n')))
member_list.close()
member_list = open("fulltimes.txt", "r") # full timer review
BOX_2 = deque(filter(None, member_list.read().split('\n')))
member_list.close()
member_list = open("standup.txt", "r") # standup list
BOX_3 = deque(filter(None, member_list.read().split('\n')))
member_list.close()
member_list = open("backup.txt", "r") # backup list
BOX_4 = deque(filter(None, member_list.read().split('\n')))
member_list.close()

def show_table(command, sender, table=BOX_1):
    print
    'in show_table func'
    if len(table) < 1:
        return 'The table is empty!'
    else:
        tableString = 'The table contains:\n'
        for member in table:
            reviewer = slack_client.api_call("users.info", user=member)
            tableString += (reviewer['user']['name'] + '\n')
        return tableString

def show_high_table(command, sender):
    print
    'in show_high_table func'
    return show_table(command, sender, BOX_2)

def show_standup_table(command, sender):
    print
    'in show_standup_table func'
    return show_table(command, sender, BOX_3)

def show_umarfc(command, sender):
    print
    'in show_umarfc func'
    dm_channel = slack_client.api_call("conversations.open", users=sender)['channel']['id']
    if (sender in BOX_4): 
        return {
            'text': show_table(command, sender, BOX_4),
            'channel': dm_channel
        }
    else:
        return {
            'text': "YOUR NOT PART OF THE UAMR FOTBALL CLUB",
            'channel': dm_channel
        }

def drop_table(command, sender, table=BOX_1):
    print
    'in drop_table func'
    if len(table) < 1:
        return 'The table is already empty'
    else:
        table.clear()
        save_table_to_file(table)
        return 'The table has been cleared'

def drop_high_table(command, sender):
    print
    'in drop_high_table func'
    return drop_table(command, sender, BOX_2)

def drop_standup_table(command, sender):
    print
    'in drop_standup_table func'
    return drop_table(command, sender, BOX_3)

def drop_umarfc(command, sender):
    print
    'in drop_umarfc func'
    return drop_table(command, sender, BOX_4)

def list_commands(command, sender):
    print
    'in list_commands func'
    commandList = 'Here are a list of commands:\n'
    for key, value in CHOICES.items():
        if (key not in FAKE_FUNCTIONS):
            commandList += (key + '\n')
    commandList += "For a full explanation of all commands, view the README here:\n"
    commandList += "https://github.com/hubdoc/codereview-slackbot/blob/master/README.md"
    return commandList

def add_to_table(command, sender, table=BOX_1):
    print
    'in add_to_BOX_1 func'
    message = command.split(' ')
    users_added = 0
    print
    message
    if len(message) > 1:
        for token in range(1, len(message)):
            match = re.search(ADD_USER_REGEX, message[token])
            if match:
                if match.group(1) == 'U936HFKUJ':
                    return "You cannot add me to do reviews >:("
                elif match.group(1) not in table:
                    table.append(match.group(1))
                    save_table_to_file(table)
                    users_added += 1
                else:
                    print
                    'User already exists at the table'
            else:
                return 'Users to add must be in the form of "@USER"'

        return '{} users added to the table!'.format(users_added)
    return 'No user to add'

def add_to_high_table(command, sender):
    print
    'in add_to_high_table func'
    return add_to_table(command, sender, BOX_2)

def add_to_standup_table(command, sender):
    print
    'in add_to_standup_table func'
    return add_to_table(command, sender, BOX_3)

def add_to_umarfanclub(command, sender, table = BOX_4):
    print
    'in add_to_umarfanclub func'
    if sender not in table:
        table.append(sender)
        save_table_to_file(table)
    else:
        print
        'User already exists at the table'

def remove_from_table(command, sender, table=BOX_1):
    print
    'in remove_from_table func'
    message = command.split(' ')
    if len(message) > 1:
        match = re.search(ADD_USER_REGEX, message[1])
        if match:
            if table.count(match.group(1)) < 1:
                return 'No user found to remove'
            else:
                # top_of_list = table[0]
                table.remove(match.group(1))
                save_table_to_file(table)
                return '<@{}> removed from the table!'.format(match.group(1))
    return '"remove @<user>" to remove a member of the table.'

def remove_from_high_table(command, sender):
    print
    'in remove_from_high_table func'
    return remove_from_table(command, sender, BOX_2)

def remove_from_standup_table(command, sender):
    print
    'in remove_from_standup_table func'
    return remove_from_table(command, sender, BOX_3)

def remove_from_umarfc(command, sender, table=BOX_4):
    print
    'in remove_from_umarfc func'
    if sender in table:
        table.remove(sender)
        save_table_to_file(table)
    else:
        print
        'User is not currently in the fanclub'

def assign_reviewer(command, sender, table=BOX_1):
    message = {'text': 'The pull request does not exist!'}
    if (len(table) == 1):
        return "You're the only one in the table!"
    nextReviewer = table[0]
    try:
        pr_ID = command.split(' ')[1]
    except:
        return "Your command should be formatted as 'review <number>'"
    reviewee = slack_client.api_call("users.info", user=sender)
    try:
        pr = robot_repo.get_pull(int(pr_ID))
    except:
        return message['text']
    pr_url = 'https://github.com/hubdoc/{}/pull/{}'.format(repo_name, pr_ID)
    pr_state = "Lines added: {}, Lines removed: {}, Files changed: {}".format(pr.additions, pr.deletions,
                                                                              pr.changed_files)
    message['attachment'] = json.dumps([
        {
            "title": pr.title,
            "title_link": pr_url,
            "text": pr_url + "\n" + pr_state,
            "fallback": "error",
            "color": "#FFFABA",
            "attachment_type": "default",
            "thumb_url": "https://assets-cdn.github.com/images/modules/logos_page/GitHub-Mark.png"
        }])

    if (sender == nextReviewer):
        tempFront = table.popleft()
        message['text'] = '<@{}> has been assigned by {} to review'.format(table[0], reviewee['user']['name'])
        table.rotate(-1)
        table.appendleft(tempFront)
        save_table_to_file(table)
    else:
        message['text'] = '<@{}> has been assigned by {} to review'.format(table[0], reviewee['user']['name'])
        table.rotate(-1)
        save_table_to_file(table)
    pr.set_labels(LABEL_COOP_REVIEW)
    return message

def finish_review(command, sender, table=BOX_2):
    print
    'in finish_review func'
    if (len(table) == 1):
        return "You're the only one in the table!"
    message = {'text': 'The pull request does not exist!'}
    nextReviewer = table[0]
    try:
        pr_ID = command.split(' ')[1]
    except:
        return "Your command should be formatted as 'finish <number>'"

    try:
        pr = robot_repo.get_pull(int(pr_ID))
    except:
        return message["text"]

    pr_url = 'https://github.com/hubdoc/{}/pull/{}'.format(repo_name, pr_ID)
    pr_state = "Lines added: {}, Lines removed: {}, Files changed: {}".format(pr.additions, pr.deletions,
                                                                              pr.changed_files)
    message['attachment'] = json.dumps([
        {
            "title": pr.title,
            "title_link": pr_url,
            "text": pr_url + "\n" + pr_state,
            "fallback": "error",
            "color": "#FFA500",
            "attachment_type": "default",
            "thumb_url": "https://assets-cdn.github.com/images/modules/logos_page/GitHub-Mark.png"
        }])
    if (sender == nextReviewer):
        tempFront = table.popleft()
        message['text'] = '<@{}> has been requested to finish the code review'.format(table[0])
        table.rotate(-1)
        table.appendleft(tempFront)
        save_table_to_file(table)
    else:
        message['text'] = '<@{}> has been requested to finish the code review'.format(table[0])
        table.rotate(-1)
        save_table_to_file(table)
    pr.set_labels(LABEL_FT_REVIEW)
    return message

def volunteer(command, sender, table=BOX_1):
    message = '<@{}> has volunteered!'.format(sender)
    if (sender in table):
        table.remove(sender)
        table.appendleft(sender)
        save_table_to_file(table)
    else:
        message = '<@{}> is not in the table!'.format(sender)
    return message

def high_volunteer(command, sender):
    print
    'in high_volunteer func'
    return volunteer(command, sender, BOX_2)

def move_to_wip(command, sender):
    print
    "in move_to_wip"
    pr_ID = command.split(' ')[1]
    if (not pr_ID.isdigit()):
        return "Please provide the pull request ID as a number"
    pr = robot_repo.get_pull(int(pr_ID))
    pr.set_labels(LABEL_WIP)
    return "Set pull request back to work in progress"

def sort_help():
    print
    "in sort_help"
    sortList = "Here is the list of sorts:\n"
    for key in SORTS.keys():
        if (key not in FAKE_SORTS):
            sortList += (key + '\n')
    sortList += "You can probably figure out what each one is ;)"
    return sortList

def choose_standup_order(command, sender, table=BOX_3):
    print
    "in choose_standup_order"

    command_string = command.split(' ')
    if len(command_string) == 1 or command_string[1] not in SORTS:
        return sort_help()

    if len(table) < 1:
        return 'The table is empty!'
    else: 
        tableString = 'This week\'s standup order:\n'
        temp = SORTS[command_string[1]](command, sender)
        if (len(command_string) > 2 and command_string[2] == "pickme"):
            sender_name = get_name(sender)
            temp.insert(0, temp.pop(temp.index(sender_name))) if sender_name in temp else temp
        if (len(command_string) > 2 and command_string[2] == "last"):
            sender_name = get_name(sender) 
            temp.append(temp.pop(temp.index(sender_name))) if sender_name in temp else temp
        elif (len(command_string) > 2):
            coolguy = [i for i in temp if command_string[2] in i]
            temp.insert(0, temp.pop(temp.index(coolguy[0]))) if len(coolguy) else temp
        for member in temp: 
            tableString += member
        
        return {
            'text': tableString,
            'channel': slack_client.api_call("conversations.open", users=sender)['channel']['id'] if command_string[1] == 'umar' else None
        }

def alpha_order(command, sender, table=BOX_3):
    return sorted(map(get_name, table))

def reverse_alpha_order(command, sender, table=BOX_3):
    return sorted(map(get_name, table), reverse=True)
  
def name_length_order(command, sender, table=BOX_3):
    return sorted(map(get_name, table), key = len)

def randomize_standup(command, sender, table=BOX_3):
    users = [mem for mem in table]
    random.shuffle(users)
    return map(get_name, users)

def umar(command, sender, random = False, table = BOX_3):
    slack_client.api_call("conversations.open", users=sender)['channel']['id']
    command_string = command.split(' ')
    num_umars = 10 if (len(command_string) < 3 or not is_valid_number(command_string[2])) else int(command_string[2])
    if (num_umars > 15):
        add_to_umarfanclub(command, sender)
        return ["You're obsessed with Umar. Welcome to the Umar fanclub :eyes:"] 
    elif (num_umars < 1):
        remove_from_umarfc(command, sender)
        return ["This is a true :umar-beatdown:"]
    return [umar for umar in filter(lambda name: "umar" in name.lower(), map(get_name, table))] * num_umars

def is_valid_number(string):
    if string[0] == "-":
        string = string[1:]
    for i in string: 
        if (ord(i) < ord('0') or ord(i) > ord('9')):
            return False
    return True

def get_name(member):
    temp = slack_client.api_call("users.info", user=member)
    return temp['user']['name'] + '\n'

# === ALL POSSIBLE BOT COMMANDS END ===

# === BOT COMMAND MAPPING ===

CHOICES['showtable'] = show_table
CHOICES['ftshowtable'] = show_high_table
CHOICES['sushowtable'] = show_standup_table
CHOICES['droptable'] = drop_table
CHOICES['ftdroptable'] = drop_high_table
CHOICES['sudroptable'] = drop_standup_table
CHOICES['help'] = list_commands
CHOICES['add'] = add_to_table
CHOICES['ftadd'] = add_to_high_table
CHOICES['suadd'] = add_to_standup_table
CHOICES['remove'] = remove_from_table
CHOICES['ftremove'] = remove_from_high_table
CHOICES['suremove'] = remove_from_standup_table
CHOICES['review'] = assign_reviewer
CHOICES['finish'] = finish_review
CHOICES['volunteer'] = volunteer
CHOICES['ftvolunteer'] = high_volunteer
CHOICES['wip'] = move_to_wip
CHOICES['sort'] = choose_standup_order
CHOICES['umarfc'] = show_umarfc

# sorts
SORTS['alpha'] = alpha_order
SORTS['ralpha'] = reverse_alpha_order
SORTS['length'] = name_length_order
SORTS['random'] = randomize_standup
SORTS['umar'] = umar

# === BOT COMMAND MAPPING END ===

def command_list(index, command, sender):
    result = CHOICES.get(index, None)
    if result != None:
        result = result(command, sender)
    return result

def save_table_to_file(table=BOX_1):
    if (table == BOX_1):
        member_list = open("coops.txt", "w")
    elif (table == BOX_2):  # unnecessary but just to double check
        member_list = open("fulltimes.txt", "w")
    elif(table == BOX_3):
        member_list = open("standup.txt", "w")
    elif(table == BOX_4):
        member_list = open("backup.txt", "w")
    else:
        print("something went wrong!")
    file_buffer = ''
    for member in table:
        file_buffer += member + '\n'
    member_list.write(file_buffer)
    member_list.close()

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == codereviewbot_id:
                return message, event["channel"], event["user"]
    return None, None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel, sender):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Type *{}* for a list of commands.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    
    # This is where you start to implement more commands!
    command_switch = command.split(' ')[0]

    response = command_list(command_switch, command, sender)

    # Sends the response back to the channel
    if isinstance(response, str) or response is None:
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response
        )
    elif (response['text']):
        slack_client.api_call(
            "chat.postMessage",
            channel=response['channel'] if response['channel'] else channel,
            text=response['text']
        )
    else:
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response['text'] or default_response,
            attachments=response['attachment']
        )

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False, auto_reconnect=True):
        print("Code Review Robin connected and running!")
        # Read bot's user ID by calling web API method `auth.test`
        codereviewbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel, sender = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel, sender)
            time.sleep(RTM_READY_DELAY)
    else:
        print("Connection failed.")
