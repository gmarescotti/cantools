# A CAN bus node (or Board unit)

class Node(object):
    """An NODE on the CAN bus.

    """

    def __init__(self,
                 name,
                 comment,
                 dbc_specifics=None):
        self._name = name
        self._comment = comment
        self._dbc = dbc_specifics
        self._senders = set()
        self._receivers = set()

    @property
    def name(self):
        """The node name as a string.

        """

        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def comment(self):
        """The node comment, or ``None`` if unavailable.

        """

        return self._comment

    @comment.setter
    def comment(self, value):
        self._comment = value

    @property
    def dbc(self):
        """An object containing dbc specific properties like e.g. attributes.

        """

        return self._dbc

    @dbc.setter
    def dbc(self, value):
        self._dbc = value

    @staticmethod
    def fill_senders_receivers(database):
        # GGG push "messages" in any node
        allnodes = dict()   
        for node in database.nodes:
            allnodes[node.name] = node

        for message in database.messages:
            for sender in message.senders:
                allnodes[sender]._senders.add(message)
                
            for signal in message.signals:
                for receiver in signal.receivers:
                    allnodes[receiver]._receivers.add(message)

    @property
    def senders(self):
        """The node senders as a list.

        """

        return self._senders

    @property
    def receivers(self):
        """The node senders as a list.

        """

        return self._receivers
    
    def __repr__(self):
        return "node('{}', {}, {}, {})".format(
            self._name,
            "'" + self._comment + "'" if self._comment is not None else None,
            self._senders,
            self._receivers)
