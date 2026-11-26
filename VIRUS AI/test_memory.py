
import memory

# Create the database
memory.create_database()

# Save information
print(memory.save_memory("My name is Offline Helper."))

print(memory.save_memory("I work completely offline when using local features."))

# Retrieve saved information
print("\n--- Offline Helper MEMORIES ---")

for memory_id, information in memory.get_memories():
    print(f"{memory_id}: {information}")
    