import collections

class Broadcaster:

    def __init__(self, size):

        self.channels = []
        self.channel_size = size

    def add_channel(self):

        channel = collections.deque(maxlen=self.channel_size)
        self.channels.append(channel)
        return channel

    def remove_channel(self, channel):

        try:
            self.channels.remove(channel)
        except:
            pass

    def broadcast(self, value):

        for channel in self.channels:
            channel.append(value)