from mpi4py import MPI
import threading
import time
import enum


class MessageType(enum.Enum):
    TOKEN_REQUEST = 1
    TOKEN_RELEASE = 2
    READ_REQUEST = 3
    WRITE_REQUEST = 4
    NEW_PROCESS = 5
    DATA_UPDATE = 6
    ACKNOWLEDGE = 7


class TokenManager:
    def __init__(self):
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()

        # Initialize token count
        self.total_tokens = self.size
        self.local_tokens = self.size if self.rank == 0 else 0

        # Protection for shared resources
        self.lock = threading.Lock()
        self.cv = threading.Condition(self.lock)
        self.write_mode = False

    def acquire_read_token(self):
        """Acquire at least one token for reading"""
        with self.lock:
            # If we already have tokens, we can read
            if self.local_tokens > 0:
                return True

            # Request a token from other processes
            for i in range(self.size):
                if i != self.rank:
                    self.comm.send({
                        'type': MessageType.TOKEN_REQUEST,
                        'sender': self.rank,
                        'token_count': 1
                    }, dest=i, tag=0)

            # Wait until we get a token
            while self.local_tokens == 0:
                self.cv.wait()

            return True

    def acquire_write_tokens(self):
        """Acquire all tokens for writing"""
        with self.lock:
            # If we already have all tokens, we can write
            if self.local_tokens == self.total_tokens:
                self.write_mode = True
                return True

            # Request all tokens from other processes
            for i in range(self.size):
                if i != self.rank:
                    self.comm.send({
                        'type': MessageType.WRITE_REQUEST,
                        'sender': self.rank,
                        'token_count': self.total_tokens
                    }, dest=i, tag=0)

            # Wait until we get all tokens
            while self.local_tokens < self.total_tokens:
                self.cv.wait()

            self.write_mode = True
            return True

    def release_tokens(self, was_writing):
        """Release tokens after operation"""
        with self.lock:
            if was_writing:
                # After writing, keep one token and distribute the rest
                tokens_to_distribute = self.total_tokens - 1
                tokens_per_process = tokens_to_distribute // (self.size - 1)
                remainder = tokens_to_distribute % (self.size - 1)

                for i in range(self.size):
                    if i != self.rank:
                        tokens_to_send = tokens_per_process + (1 if remainder > 0 else 0)
                        if remainder > 0:
                            remainder -= 1

                        if tokens_to_send > 0:
                            self.comm.send({
                                'type': MessageType.TOKEN_RELEASE,
                                'sender': self.rank,
                                'token_count': tokens_to_send
                            }, dest=i, tag=0)
                            self.local_tokens -= tokens_to_send

                self.write_mode = False
            # For read operations, we keep our tokens

    def handle_message(self, msg):
        """Process incoming token-related messages"""
        with self.lock:
            msg_type = msg['type']

            if msg_type == MessageType.TOKEN_REQUEST:
                # Someone is requesting tokens for reading
                if self.local_tokens > 1 and not self.write_mode:
                    # We can spare a token
                    self.comm.send({
                        'type': MessageType.TOKEN_RELEASE,
                        'sender': self.rank,
                        'token_count': 1
                    }, dest=msg['sender'], tag=0)
                    self.local_tokens -= 1

            elif msg_type == MessageType.WRITE_REQUEST:
                # Someone needs all tokens for writing
                if self.local_tokens > 0 and not self.write_mode:
                    # Send all our tokens
                    self.comm.send({
                        'type': MessageType.TOKEN_RELEASE,
                        'sender': self.rank,
                        'token_count': self.local_tokens
                    }, dest=msg['sender'], tag=0)
                    self.local_tokens = 0

            elif msg_type == MessageType.TOKEN_RELEASE:
                # We're receiving tokens
                self.local_tokens += msg['token_count']
                self.cv.notify_all()  # Wake up any waiting threads

            elif msg_type == MessageType.NEW_PROCESS:
                # A new process has joined
                # Redistribute tokens if we have more than one
                if self.local_tokens > 1 and not self.write_mode:
                    self.comm.send({
                        'type': MessageType.TOKEN_RELEASE,
                        'sender': self.rank,
                        'token_count': 1
                    }, dest=msg['sender'], tag=0)
                    self.local_tokens -= 1

    def announce_presence(self):
        """Broadcast presence to all existing processes"""
        for i in range(self.size):
            if i != self.rank:
                self.comm.send({
                    'type': MessageType.NEW_PROCESS,
                    'sender': self.rank
                }, dest=i, tag=0)

    def get_local_tokens(self):
        """Get number of tokens currently held"""
        return self.local_tokens

    def has_read_access(self):
        """Check if process has enough tokens for reading"""
        return self.local_tokens > 0

    def has_write_access(self):
        """Check if process has enough tokens for writing"""
        return self.local_tokens == self.total_tokens