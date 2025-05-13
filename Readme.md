# Lab 6 Report: Coherent Distributed Object with Token Coherence (SWMR)

## Requirement
Implement a program that realizes a distributed object offering coherently replicated data. Devise and implement a mechanism that maintains the Single Writer, Multiple Reader (SWMR) invariant for each object using token coherence.

- When a new process joins, it should broadcast a message to notify all other processes and initialize a new distributed object with the current coherence value.
- Any inter-process communication method (MPI, RPC, etc.) may be used.
- The report must describe the algorithm flow (flow chart, pseudocode, step-by-step demo, etc.) with detailed explanation.

## Overview
This project implements a distributed object system in Python using MPI for inter-process communication. The system ensures data consistency across all processes by enforcing the SWMR invariant through a token-based coherence protocol.

## Core Components
- **TokenManager (`token_manager.py`)**: Manages token distribution, enforces SWMR, handles token requests and transfers.
- **DistObj (`dist_obj.py`)**: Implements the distributed object interface, maintains local data, synchronizes updates, and manages message passing.
- **Main Program (`main.py`)**: Demonstrates and tests the system with both primitive and complex data types.

## Token Coherence Protocol
- The total number of tokens equals the number of processes.
- Initially, process 0 holds all tokens.
- **Read**: A process must hold at least one token to read.
- **Write**: A process must hold all tokens to write.
- After a write, tokens are redistributed to allow multiple readers.
- When a new process joins, it broadcasts its presence and requests the current value to synchronize.

## Algorithm Flow

### 1. Object Initialization Flow
```mermaid
graph TD
    A[Process starts] --> B{Is this process 0?}
    B -- Yes --> C[Create object with initial value]
    B -- No --> D[Create empty object]
    C --> E[Hold all tokens initially]
    D --> F[Broadcast NEW_PROCESS message]
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

## Run Instructions

To run the program, use the following command:
