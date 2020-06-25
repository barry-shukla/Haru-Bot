import discord
import asyncio
import configparser
import queue
import os

# Warning: default log message limit is unlimited
_DEFAULT_MSG_LIMIT = 0

class MsgLog:

    '''Defines an asyncio-compatible in-memory Discord message log.
    '''

    def __init__(self, *args, **kwargs):
        if 'msg_limit' not in kwargs:
            self.msg_limit = _DEFAULT_MSG_LIMIT
        else:
            self.msg_limit = kwargs['msg_limit']
        self.filename = kwargs['filename']
        # enqueues will block once the queue is full - this queue is thread safe
        self.log = queue.Queue(maxsize=self.msg_limit)


    async def log(self, message: discord.Message) -> None:
        '''Writes a message to the log.
        
        Args:
            message (discord.Message): An instance of a discord message to log.
        
        Since: 24/05/2020
    
        Author: Christen Ford
        '''
        # this *could* potentially block the client if users spam it fast enough
        self.log.put(message)
        if self.log.full():
            await self.dump()


    async def dump(self) -> None:
        '''Dumps the log to file. This method can be called manually, but it is called
        automatically by the log() method once the log message limit is reached.
        
        Since: 24/05/2020
    
        Author: Christen Ford
        '''
        def _dump():
            with open(filename, 'a') as f:
                while not self.log.empty():
                    msg = self.log.get()
                    f.write('{}:{}:{}:{}'.format(msg.id, msg.author, msg.content, msg.created_at)))
        
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,  _dump()
        )
        
        if not result:
            # TODO: error occurred dumping message log to file
            pass
    

class HaruClient(discord.Client):

    def __init__(*args, loop=None, **options):
        super(discord.Client, self).__init__(*args, loop, **options)
        # do not catch the potential KeyErrors here, let it be the users fault
        self.__config = options['config']
        self.__log = MsgLog(log_msg_limit = config['log_msg_limit'])

        
    async def start_poll(self, message: discord.Message):
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
    async def on_ready(self):
        print('Client is online')
        #add_verification_emoji_to_rules_post

    # // @client.event: If a user connects to the music voice channel, the 'Music' role will be assigned to them \\
    # // @client.event: If a user disconnects from the music voice channel, the 'Music' role will be removed from them \\

    @client.event
    async def on_message(self, message: discord.Message):
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

                
    @client.event
    async def on_member_join(self, member: discord.Member) -> None:
        '''Overrides the on_member_join event to let Haru welcome users to the server.
        
        Arguments:
            member (discord.Member): A reference to the guild member that just joined.
            
        Since: 20/06/2020
        
        Author(s): Christen Ford 
        '''
        # Haru should greet new users in as cute a fashion possible. She should also react
        #   to this message using the :coffee: and :bagel: emojis.
        msg = 'Hey there {mn}! Welcome to {gn}. Have this :bagel: and enjoy some :coffee:. It\'s on me :wink:.'.format(
            gn=member.guild.name, 
            mn=member.name
        )
        await member.guild.get_channel(693695218460917761).send(msg)

#
# utility methods
#

def get_config(config_file='config.txt' -> str):
    '''Returns an instance of a ConfigParser from Lib/configparser.

    Args:
        config_file (str): The path to the configuration file.
        
    Since: 24/05/2020
    
    Author: Christen Ford
    '''
    config = configparser.ConfigParser()
    try:
        f = open(config_file)
        config.read_file(f)
        close(f)
    except IOError:
        print('Error: Configuration file not found, using default Python configuration!')
    return config


def get_token(token_file='token.txt' -> str):
    #j
    token = ''
    with open(token_file) as file: # 'r' is default open mode
        token += file.read()
    return token

#
# main method
#

def main():
    # get an instance of the bot and start it
    client = HaruClient(config=get_config())
    client.run(get_token())


if __name__ == '__main__':
    main()
