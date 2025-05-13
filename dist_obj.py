from mpi4py import MPI
import threading
import pickle
import time
from token_manager import TokenManager, MessageType


class DistObj:
    def __init__(self, initial_value=None):
        """
        Initialize a distributed object

        Parameters:
            initial_value: Initial value for the object (only used by process 0)
        """
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()

        # Initialize token manager
        self.token_manager = TokenManager()

        # Initialize object value
        if self.rank == 0 and initial_value is not None:
            self.obj = initial_value
        else:
            self.obj = None

        # Set up message listener
        self.running = True
        self.listener_thread = threading.Thread(target=self.message_listener)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        time.sleep(0.1)  # Give the listener thread time to start

        # Announce presence to other processes
        self.token_manager.announce_presence()

        # If not the first process, get current value
        if self.rank != 0:
            self.comm.send({
                'type': MessageType.READ_REQUEST,
                'sender': self.rank
            }, dest=0, tag=0)

            # Wait for data update message
            while True:
                data = self.comm.recv(source=0, tag=0)
                if data.get('type') == MessageType.DATA_UPDATE:
                    self.obj = data['value']
                    break
                else:
                    print(f"Process {self.rank} received and ignored unexpected data: {data}")

    def read(self):
        """
        Read the value of the distributed object

        Returns:
            The current value of the object
        """
        # Acquire at least one token for reading
        self.token_manager.acquire_read_token()

        # We can now read the local copy
        result = self.obj

        # No need to release tokens after reading
        return result

    def write(self, value):
        """
        Write a new value to the distributed object

        Parameters:
            value: The new value to write
        """
        # Acquire all tokens for writing
        self.token_manager.acquire_write_tokens()

        # Update local copy
        self.obj = value

        # Broadcast the update to all processes
        for i in range(self.size):
            if i != self.rank:
                self.comm.send({
                    'type': MessageType.DATA_UPDATE,
                    'sender': self.rank,
                    'value': value
                }, dest=i, tag=0)

                # Wait for acknowledgment
                ack = self.comm.recv(source=i, tag=0)

        # Release tokens after writing
        self.token_manager.release_tokens(True)

    def message_listener(self):
        """Listen for incoming messages related to this object"""
        while self.running:
            # Check for incoming messages with non-blocking probe
            if self.comm.Iprobe(source=MPI.ANY_SOURCE, tag=0):
                # Receive the message
                msg = self.comm.recv(source=MPI.ANY_SOURCE, tag=0)

                # Handle the message based on type
                if msg['type'] in [MessageType.TOKEN_REQUEST, MessageType.TOKEN_RELEASE,
                                   MessageType.WRITE_REQUEST, MessageType.NEW_PROCESS]:
                    self.token_manager.handle_message(msg)

                elif msg['type'] == MessageType.READ_REQUEST:
                    # Someone wants to read our current value
                    if self.token_manager.has_read_access():
                        self.comm.send({
                            'type': MessageType.DATA_UPDATE,
                            'sender': self.rank,
                            'value': self.obj
                        }, dest=msg['sender'], tag=0)

                elif msg['type'] == MessageType.DATA_UPDATE:
                    # Someone is updating the object value
                    self.obj = msg['value']

                    # Send acknowledgment
                    self.comm.send({
                        'type': MessageType.ACKNOWLEDGE,
                        'sender': self.rank
                    }, dest=msg['sender'], tag=0)

            # Sleep a bit to avoid busy waiting
            time.sleep(0.01)

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.running = False
        if self.listener_thread.is_alive():
            self.listener_thread.join(timeout=1.0)