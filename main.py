from mpi4py import MPI
import time
from dist_obj import DistObj


def test_integer_object():
    """Test with an integer object"""
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Create a distributed integer
    initial_value = 42 if rank == 0 else None
    dist_int = DistObj(initial_value)
    comm.barrier()  # <-- Add this line to synchronize
    # Each process reads the value
    value = dist_int.read()
    print(f"Process {rank} read value: {value}")

    # Let processes take turns updating the value
    comm.barrier()

    for i in range(size):
        if i == rank:
            # This process's turn to update
            new_value = 100 + rank
            print(f"Process {rank} writing value: {new_value}")
            dist_int.write(new_value)

            # Let everyone read the updated value
            comm.barrier()

            updated_value = dist_int.read()
            print(f"Process {rank} read updated value: {updated_value}")

        comm.barrier()


def test_dict_object():
    """Test with a dictionary object"""
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Create a distributed dictionary
    initial_value = {"hello": "world", "count": 0} if rank == 0 else None
    dist_dict = DistObj(initial_value)
    comm.barrier()  # <-- Add this line to synchronize
    # Each process reads the value
    value = dist_dict.read()
    print(f"Process {rank} read dict: {value}")

    # Let processes take turns updating the value
    comm.barrier()

    for i in range(size):
        if i == rank:
            # This process's turn to update
            value = dist_dict.read()
            value["count"] = rank
            value["last_modified_by"] = f"Process {rank}"

            print(f"Process {rank} writing dict: {value}")
            dist_dict.write(value)

            # Let everyone read the updated value
            comm.barrier()

            updated_value = dist_dict.read()
            print(f"Process {rank} read updated dict: {updated_value}")

        comm.barrier()


def main():
    """Main function to run the distributed object tests"""
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    print(f"Process {rank} started (total: {size})")

    # Test with different data types
    test_integer_object()
    print("-" * 30)
    #test_dict_object()


if __name__ == "__main__":
    main()