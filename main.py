import discord
import asyncio

client = discord.Client()

def get_token():
    #j
    token = ''
    with open('token.txt', 'r') as file:
        token += file.read()
    return token

async def start_poll(message):
    #aggregate message into its components, then delete it
    content_split = message.content[5:].split(' !')[1:]
    question = content_split[0]
    options = content_split[1:]
    await message.delete()

    #create poll from message
    msg = f'@here\n-- POLL --\n{question}'
    for i, option in enumerate(options):
        msg += f'\nVotes for {option} [{i}]'
    await message.channel.send(msg)

@client.event
async def on_ready():
    print('Client is online')
    #add_verification_emoji_to_rules_post

# // @client.event: If a user connects to the music voice channel, the 'Music' role will be assigned to them \\
# // @client.event: If a user disconnects from the music voice channel, the 'Music' role will be removed from them \\

@client.event
async def on_message(message):
    if(message.content.startswith('+')):
        server  = message.channel.guild
        channel = message.channel
        barry = server.get_member(242844146555944961)

        # // user message: +poll [!Question] [!Option1] [!Option2] ... [!OptionN] \\
        # Bot will do
        """
        @here
        -- POLL --
        Question

        Votes for [Option1] [1]
        Votes for [Option2] [2]
        .
        .
        .
        Votes for [OptionN] [N]
        """
        if ( message.content[1:5].lower() == 'poll' ):
            start_poll(message)

client.run(get_token())
