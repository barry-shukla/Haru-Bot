import discord
import asyncio
import configparser
import queue
import os

class MsgLog:

    '''Defines an asyncio-compatible in-memory Discord message log.'''

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
                    f.write('{}:{}:{}:{}'.format(msg.id, msg.created_at, msg.author, msg.content)))
        
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,  _dump()
        )
        
        if not result:
            # TODO: error occurred dumping message log to file
            pass
    

class HaruClient(discord.Client):

    def __init__(*args, loop=None, **options):
        '''Returns a new instance of a HaruClient discord bot. It is required 'options'
        contain a 'config' key that maps to a ConfigParser object. The parser can be empty
        but it can not be None.

        Args:
            args (collections.abc.Sequence): A sequence containing arguments passed to the 
            client during initialization.
            loop (asyncio event loop): The loop to run the client on.
            options (collections.abc.Mapping): A dict-like object containing key-value pairs
            passed to the client during initialization.

        Raises:
            (KeyError): If 'config' is not found in 'options'.
            (TypeError):  If 'config' is None or is not a ConfigParser object.
        '''
        super(discord.Client, self).__init__(*args, loop, **options)
        if 'config' not in options:
            raise KeyError
        if not options['config'] or type(options['config']) is not configparser.ConfigParser:
            raise TypeError
        self.config = options['config']
        self.log = MsgLog(log_msg_limit = config['DEFAULT']['log_msg_limit'])


    def get_config_value(self, key: str, section='DEFAULT': str):
        '''Attempts to return a value from the the clients configuration.

        Args:
            key (str): The key corresponding to the value to retrieve.
            section (str): The section the key falls under (default: 'DEFAULT').

        Raises:
            (KeyError): If section or key do not exist in the configuration.

        Since: 26/06/2020

        Author: Christen Ford
        '''
        if section not in self.config:
            raise KeyError
        if key not in self.config[section]:
            raise KeyError
        return self.__config[section][key]


    def stash_config_value(self, section: str, key: str, value) -> None:
        '''Stores a key/value pair in the configuration under the specified section.
        Do not store non-primitive types (i.e. object types) in the configuration file.
        If you need to store a dictionary, store it as a separate section. Iterable types
        like lists, dicts and sets should be ok though as long as they do not contain 
        custom object types.

        Args:
            section (str): The section to store the value in.
            key (str): The key used to uniquely identify the value.
            value (Any): The value to store in the configuration.

        Since: 26/06/2020

        Author: Christen Ford
        '''
        if section not in self.config:
            self.config[section] = dict()
        self.config[section][key] = value

    
    def quote_inspirobot(url='http://inspirobot.me/api?generate=true'):
        '''Attempts to connect to the inspirobot quote AI. Returns an error message
        on error, or the response body on success.

        Args:
            url (str): The inspirobot url (default: \'http://inspirobot.me/api?generate=true\')

        Since: 26/06/2020

        Author: Christen Ford
        '''
        import http.client as http

        conn = http.HTTPConnection(url)
        resp = conn.getresponse()
        conn.close()
        if resp.status != 200:
            return 'Sorry, I couldn\'t reach inspirobot."
        else:
            return resp.read()


    @staticmethod
    async def start_poll(message: discord.Message):
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
                HaruClient.start_poll(message)
        elif message.content.lower() == '!haru-inspire':
            await message.channel.send(quote_inspirobot())
        elif message.content.lower() == '!haru-help':
            # TODO: Currently thinking of the best place to store the help string
            await message.channel.send('Nani?')
        elif message.content.lower() == '!haru-move':
            await HaruClient.move_members_to(message)


    @staticmethod
    async def move_members_to(message):
        '''Moves mentioned members to the first voice channel mentioned.

        Args:
            (discord.Message): A discord message object containing at least one mentioned member and 
            at least one mentioned voice channel.
        
        Since: 06/07/2020

        Author(s): Christen Ford
        '''
        if not message.channel_mentions:
            await message.channel.send(
                'I cannot move guild members \'{}\', no voice channel mentioned!', 
                ', '.join(m.nick for m in message.mentions)
            )
        if not message.mentions:
            await message.channel.send(
                'I cannot move guild members to \'{}\', no members mentioned!',
                message.channel_mentions[0]
            )
        # get the channel id
        channel = message.channel_mentions[0]
        # TODO: Not entirely sure this check works since mentioned channels are discord.GuildChannel 
        #   types - The abc class for TextChannel, VoiceChannel and CategoryChannel
        if not isinstance(channel, discord.VoiceChannel):
            await message.channel.send(
                'I cannot move guild members \'{}\' to \'{}\', invalid channel specified!',
                ', '.join(m.nick for m in message.mentions),
                message.channel_mentions[0]
            )
        # move all mentioned users to it
        for member in message.mentions:
            await member.move_to(channel)

                
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

def get_config(config_file='config.txt': str):
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


def get_token(token_file='token.txt': str):
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
