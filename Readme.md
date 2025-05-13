Lab 6 Report: Coherent Distributed Object Implementation in Python
Overview
This report describes the implementation of a coherent distributed object system using Python and MPI. The system maintains data consistency across multiple processes using a token-based coherence protocol that preserves the Single Writer, Multiple Reader (SWMR) invariant.

Implementation Details
Core Components
TokenManager (token_manager.py)
Manages token distribution between processes
Ensures coherence by controlling read and write access
Handles token requests and transfers
DistObj (dist_obj.py)
Implements the distributed object interface
Maintains local data and synchronizes with other processes
Handles message passing for data updates
Main Program (main.py)
Tests the implementation with different data types
Demonstrates read and write operations across multiple processes
Token Coherence Protocol
The implementation uses a token-based coherence protocol with the following rules:

The total number of tokens equals the number of processes
Initially, process 0 holds all tokens
To read an object, a process needs at least one token
To write an object, a process needs all tokens
After a write operation, tokens are redistributed to allow multiple readers
Algorithm Flow
Object Initialization Flow
mermaid
graph TD
    A[Process starts] --> B{Is this process 0?}
    B -->|Yes| C[Create object with initial value]
    B -->|No| D[Create empty object]
    C --> E[Hold all tokens initially]
    D --> F[Announce presence]
    F --> G[Request current value from process 0]
    G --> H[Update local object with received value]
    E --> I[Start message listener thread]
    H --> I
Read Operation Flow
mermaid
graph TD
    A[read() called] --> B{Has at least one token?}
    B -->|Yes| C[Return local copy]
    B -->|No| D[Request token from other processes]
    D --> E[Wait for token]
    E --> F{Received token?}
    F -->|Yes| C
    F -->|No| E
Write Operation Flow
mermaid
graph TD
    A[write() called] --> B{Has all tokens?}
    B -->|Yes| C[Update local copy]
    B -->|No| D[Request all tokens from other processes]
    D --> E[Wait for all tokens]
    E --> F{Have all tokens?}
    F -->|Yes| C
    F -->|No| E
    C --> G[Broadcast update to all processes]
    G --> H[Wait for acknowledgments]
    H --> I[Redistribute tokens]
Message Handling Flow
mermaid
graph TD
    A[Receive message] --> B{What type?}
    B -->|TOKEN_REQUEST| C[Process wants to read]
    B -->|WRITE_REQUEST| D[Process wants to write]
    B -->|DATA_UPDATE| E[Process updated value]
    B -->|NEW_PROCESS| F[New process joined]
    B -->|TOKEN_RELEASE| G[Receive tokens]
    
    C --> H{Can I spare tokens?}
    H -->|Yes| I[Send token]
    H -->|No| J[Ignore request]
    
    D --> K{Am I writing?}
    K -->|No| L[Send all my tokens]
    K -->|Yes| M[Ignore request]
    
    E --> N[Update local copy]
    N --> O[Send acknowledgment]
    
    F --> P{Have excess tokens?}
    P -->|Yes| Q[Send one token]
    P -->|No| R[Ignore]
    
    G --> S[Increase token count]
    S --> T[Notify waiting threads]
Code Structure
MessageType Enumeration
Defines the types of messages that can be exchanged between processes:

TOKEN_REQUEST: Request for reading tokens
TOKEN_RELEASE: Transferring tokens between processes
READ_REQUEST: Request to read the current value
WRITE_REQUEST: Request for all tokens to write
NEW_PROCESS: Announcing a new process joining
DATA_UPDATE: Broadcasting an updated value
ACKNOWLEDGE: Confirming receipt of updates
TokenManager Class
acquire_read_token(): Ensures the process has at least one token for reading
acquire_write_tokens(): Ensures the process has all tokens for writing
release_tokens(): Redistributes tokens after writing
handle_message(): Processes token-related messages
announce_presence(): Notifies other processes when joining
DistObj Class
init(): Initializes the object and synchronizes with existing processes
read(): Reads the object value (requires at least one token)
write(): Updates the object value (requires all tokens)
message_listener(): Background thread that handles incoming messages
Testing Results
The implementation was tested with both primitive types (integers) and complex types (dictionaries):

Integer Test: Each process reads and writes a simple integer value
Dictionary Test: Demonstrates that the system works with more complex data structures
The tests verify that:

All processes see consistent data
Read operations require at least one token
Write operations require all tokens
New processes correctly initialize with the current value
Updates are propagated to all processes
Conclusion
This implementation successfully demonstrates a coherent distributed object system using Python and MPI. The token coherence protocol ensures that the Single Writer, Multiple Reader invariant is maintained, preventing data races and ensuring consistency across all processes.

The modular design separates token management from the distributed object implementation, making it easy to extend or modify the system for different requirements.

mpiexec -n 4 python main.py