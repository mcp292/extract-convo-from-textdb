# AUTHOR: Michael Partridge <mcp292@nau.edu>
#
# Sources:
# https://github.com/mcp292/sql-to-df

# TODO: loc vs at, iat: https://stackoverflow.com/questions/28757389/pandas-loc-vs-iloc-vs-at-vs-iat

import argparse
import os
import re
import sqlite3 as sql
import pandas as pd
from time import tzname, localtime, strftime


# usually to, from but following C and pandas convention to put stream last
def get_table(table, con):
    return pd.read_sql(f"SELECT * FROM {table}", con) # df


def format_tel(tel):
    AREA_BOUNDARY = 3           # 800.6288737
    SUBSCRIBER_SPLIT = 6        # 800628.8737

    tel = tel.removeprefix("+")
    tel = tel.removeprefix("1")     # remove leading +1, or 1
    tel = re.sub("[ ()-]", '', tel) # remove space, (), -

    assert(len(tel) == 10)
    tel = (f"{tel[:AREA_BOUNDARY]}-"
           f"{tel[AREA_BOUNDARY:SUBSCRIBER_SPLIT]}-{tel[SUBSCRIBER_SPLIT:]}")

    return tel


def get_transcript_filename(conversation_name):
    conversation_name = conversation_name.lower()
    conversation_name = conversation_name.replace(' ', '_')
    conversation_name = conversation_name.replace(',', "_and")

    return f"transcript_{conversation_name}.txt"


def get_header(conversation_name):
    participants = conversation_name.replace(",", " and") # TODO: can use actual participants

    return f"Text transcript with {participants}"


def main():
    parser = argparse.ArgumentParser(description="This program extracts a "
                                     "specific conversation from an android "
                                     "text messages database.")
    parser.add_argument("db",
                        help="The SQL database to extract the conversation "
                        "from.")
    parser.add_argument("conversation",
                        help="The exact name of the conversation as it appears "
                        "in your messaging app (case sensitive). Format: "
                        "\"Conversation Name\". If exact name unknown, use "
                        "option [TODO].")
    # TODO: search flag that returns messages names that contain string that makes positional optional
    args = parser.parse_args()

    # open db
    con = sql.connect(args.db)

    # extract tables into dfs
    conversations = get_table("conversations", con)
    messages = get_table("messages", con)
    parts = get_table("parts", con)
    participants = get_table("participants", con)

    # keys start at conversations, conversation_id maps to messages, message_ids
    # map to actual messages in parts, sender_id maps to participants
    # find conversation_id by conversation name
    conversation = conversations[conversations["name"] == args.conversation]
    conversation_id = conversation["_id"].iat[0] # should be single convo

    # find list of message_ids for that conversation
    matching_messages = messages[messages["conversation_id"] == conversation_id]
    message_data = matching_messages[["_id", "sender_id", "received_timestamp"]]

    # open file and write header
    filename = get_transcript_filename(args.conversation)
    f = open(filename, "w")
    f.write(get_header(args.conversation) + "\n\n")

    # iterate through each message and extract message_id, sender_id, timestamp
    for index in message_data.index:
        message_id = message_data.at[index, "_id"]
        sender_id = message_data.at[index, "sender_id"]
        unix_time = message_data.at[index, "received_timestamp"]
        unix_time /= 1000 # android stores in milliseconds -> convert to seconds

        # find message text by message_id
        parts_data = parts[parts["message_id"] == message_id]
        message = parts_data.at[parts_data.index[0], "text"]

        # find sender by sender_id (name, number)
        sender_data = participants[participants["_id"] == sender_id]
        sender_name = sender_data.at[sender_data.index[0], "full_name"]
        sender_tel = sender_data.at[sender_data.index[0], "contact_destination"]
        sender_tel = format_tel(sender_tel)

        # convert timestamp to [date; time]
        timezone = tzname[0]
        fmt = f"[%m.%d.%Y; %H:%M {timezone}]"
        timestamp = strftime(fmt, localtime(unix_time))

        # format sender_stamp
        sender_stamp = f"{sender_name} ({sender_tel}) {timestamp}:"

        # write to file
        f.write(sender_stamp + '\n')
        f.write(message + "\n")
        f.write("-\n\n")

    f.close()


if __name__ == "__main__":
    main()
