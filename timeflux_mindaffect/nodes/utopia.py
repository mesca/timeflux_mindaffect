"""Send data to MindAffect decoder"""

from mindaffectBCI.utopiaclient import UtopiaClient, DataHeader, DataPacket, getTimeStamp
from timeflux.core.exceptions import WorkerInterrupt
from timeflux.core.node import Node
from timeflux.core.sync import Server
from timeflux.helpers.background import Task


class Client(Node):

    """Connect to the Utopia Hub and send data to the decoder.

    This plugin makes the MindAffect decoder compatible with any device supported by
    Timeflux.

    Attributes:
        i (Port): Default input, expects DataFrame.

    Example:
        .. literalinclude:: /../../timeflux_mindaffect/examples/openbci.yaml
           :language: yaml
    """

    def __init__(self, host=None, port=8400, timeout=5000):
        """
        Args:
            host (str): The Utopia Hub hostname. Leave to `None` for autodiscovery.
            port (int): The Utopia Hub port.
            timeout (int): Delay (in ms) after which we stop trying to connect.
        """

        # Connect to the Utopia Hub
        self._client = UtopiaClient()
        try :
            self._client.autoconnect(host, port, timeout_ms=timeout)
        except:
            pass
        if not self._client.isConnected:
            raise WorkerInterrupt('Could not connect to Utopia hub')

        # Keep track of the header so it is sent only once
        self._header = None

        # Start the sync server
        self._task = Task(Server(), 'start').start()


    def update(self):
        if self.i.ready():
            now = getTimeStamp()
            data = self.i.data.values.tolist()
            if not self._header:
                rate = self.i.meta['rate']
                channels = self.i.data.shape[1]
                labels = list(self.i.data.columns)
                self._header = DataHeader(now, rate, channels, labels)
                self._client.sendMessage(self._header)
            self._client.sendMessage(DataPacket(now, data))

    def terminate(self):
        self._client.disconnect()
        self._task.stop()
