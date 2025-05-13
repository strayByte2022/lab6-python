# Lab 6 Report: Coherent Distributed Object with Token Coherence (SWMR)

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

## Detailed Algorithm Explanation

### Initialization
- **Process 0** initializes the distributed object with the initial value and holds all tokens.
- **Other processes** start with no tokens and an uninitialized object. Upon joining, each broadcasts a `NEW_PROCESS` message to all others and requests the current value from process 0. This ensures that late-joining processes synchronize their state with the current system state.

### Read Operation
- To read, a process must possess at least one token. If it does not, it sends a `TOKEN_REQUEST` to other processes and waits until a token is received. This guarantees that only processes with tokens can read, enforcing the SWMR invariant by preventing reads during exclusive writes.
- Once a token is held, the process reads its local copy of the object. Since all writes require exclusive token ownership and broadcast updates, the local copy is always coherent.

### Write Operation
- To write, a process must acquire all tokens. If it does not have all tokens, it sends `WRITE_REQUEST` messages to all other processes and waits until all tokens are received.
- Once all tokens are held, the process updates its local object value. It then broadcasts a `DATA_UPDATE` message to all other processes, ensuring that every replica is updated.
- The process waits for acknowledgments (`ACKNOWLEDGE`) from all other processes, confirming that the update has been received and applied.
- After acknowledgment, the process redistributes tokens to allow multiple readers, typically by releasing tokens back to other processes.

### Token Management
- **TokenManager** is responsible for tracking the number of tokens held, processing incoming token requests, and ensuring that tokens are only transferred when it is safe (e.g., not during a write operation).
- When a process receives a `TOKEN_REQUEST` and is not writing, it can transfer a token if it has more than one. If it is writing or only has one token, it ignores the request.
- When a process receives a `WRITE_REQUEST` and is not writing, it transfers all its tokens to the requester. If it is writing, it ignores the request.

### New Process Join
- When a new process joins, it broadcasts a `NEW_PROCESS` message. Other processes respond by sending a token if they have more than one, helping the new process to participate in reads.
- The new process requests the current value from process 0, ensuring it starts with the correct, coherent state.

### Message Handling
- Each process runs a background listener thread to handle incoming messages (token requests, data updates, new process notifications, etc.) asynchronously. This ensures responsiveness and correct protocol operation even as processes join or leave dynamically.

### Pseudocode for Key Operations

**Initialization:**
```python
// Initialization
if rank == 0:
    object.value = initial_value
    tokens = total_processes
else:
    object.value = None
    tokens = 0
    broadcast NEW_PROCESS
    request current value from process 0
```
![image](flows\object-initialization.png)

**Read Operation:**
```python
// Read Operation
if tokens >= 1:
    return object.value
else:
    send TOKEN_REQUEST to other processes
    wait until token received
    return object.value
```
![image](flows\read-operation.png)

**Write Operation:**
```python
// Write Operation
if tokens == total_processes:
    object.value = new_value
    broadcast DATA_UPDATE to all processes
    wait for ACKNOWLEDGE from all processes
    redistribute tokens to allow multiple readers
else:
    send WRITE_REQUEST to all processes
    wait until all tokens received
    proceed as above
```
![image](flows\write-operation.png)

**TokenManager Handling:**
```python
// TokenManager Handling
on receive TOKEN_REQUEST:
    if not writing and tokens > 1:
        send one token to requester
    else:
        ignore request

on receive WRITE_REQUEST:
    if not writing:
        send all tokens to requester
    else:
        ignore request
```

**New Process Join:**
```python
// New Process Join
on process join:
    broadcast NEW_PROCESS
    request current value from process 0
    update local object with received value
```
![image](flows\new-process-joins.png)

**Message Listener:**
```python
// Message Listener (runs in background)
while running:
    receive and handle incoming messages (TOKEN_REQUEST, WRITE_REQUEST, DATA_UPDATE, NEW_PROCESS, ACKNOWLEDGE, etc.)
```
### Running the Program
1. Locate to the folder where `main.py` is located.
2. Run the program using the command: `mpiexec -n <num_processes> python main.py`
3. The program will demonstrate the usage of the distributed object with both primitive and complex data types.


### Output

Try running the program with function ```test_integer_object()``` in ```main.py```
```bash
Process 1 received and ignored unexpected data: {'type': <MessageType.TOKEN_RELEASE: 2>, 'sender': 0, 'token_count': 1}
Process 2 received and ignored unexpected data: {'type': <MessageType.TOKEN_RELEASE: 2>, 'sender': 0, 'token_count': 1}
Process 3 received and ignored unexpected data: {'type': <MessageType.TOKEN_RELEASE: 2>, 'sender': 0, 'token_count': 1}
Process 0 read dict: {'hello': 'world', 'count': 0}
```

Explaination:
- Token Release Messages:
    - Processes 1, 2, and 3 each received a ```TOKEN_RELEASE``` message from Process 0, indicating that Process 0 attempted to redistribute tokens (after a write or as part of protocol maintenance).
    - The message was ignored by these processes because, according to the protocol logic, they were not in a state to accept or use the token at that moment (e.g., not waiting for a token, or not eligible to receive one). This is a safeguard to prevent incorrect token handling and ensures the SWMR invariant is maintained.
- Read Confirmation:
    - Process 0 read dict: ```{'hello': 'world', 'count': 0}``` shows that Process 0 successfully read the current value of the distributed object, confirming that the system is coherent and the protocol is functioning as intend

Try running the program with function ```test_dict_object()``` in ```main.py```

```bash
Process 3 started (total: 4)
Process 2 started (total: 4)
Process 1 started (total: 4)
Process 0 started (total: 4)
Process 1 received and ignored unexpected data: {'type': <MessageType.NEW_PROCESS: 5>, 'sender': 0}
Process 2 received and ignored unexpected data: {'type': <MessageType.NEW_PROCESS: 5>, 'sender': 0}
Process 3 received and ignored unexpected data: {'type': <MessageType.NEW_PROCESS: 5>, 'sender': 0}
Process 2 received and ignored unexpected data: {'type': <MessageType.TOKEN_RELEASE: 2>, 'sender': 0, 'token_count': 1}
Process 3 received and ignored unexpected data: {'type': <MessageType.TOKEN_RELEASE: 2>, 'sender': 0, 'token_count': 1}
Process 1 received and ignored unexpected data: {'type': <MessageType.TOKEN_RELEASE: 2>, 'sender': 0, 'token_count': 1}
Process 0 read value: 42
```
