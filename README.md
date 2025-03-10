# Redis Database Migration Script

This Python script allows for the migration of Redis keys from one Redis server to another, while preserving TTLs (time-to-live) and supporting parallel processing for improved performance. It can be used to transfer data between Redis databases on different servers or clusters.

## Features

- **Batch Processing**: Migrates Redis keys in batches using `SCAN` to avoid blocking the Redis server.
- **Preserves TTLs**: Retains TTLs of keys during migration.
- **Parallel Execution**: Uses threading to parallelize the migration of keys, speeding up the transfer process.
- **Error Handling**: Includes error handling for various Redis operations.
- **Supports Multiple Databases**: Allows migrating multiple Redis databases in parallel.

## Prerequisites

- Python 3.x
- Redis Python Client (`redis-py`) - Install via `pip install redis`.

## Usage

### Command-line Arguments
```bash
python3 redis_migrate_parallel.py --export-host <export_redis_host> --import-host <import_redis_host> --db <db_list> --scan-batch-size <scan_batch_size> --chunk-size <chunk_size>

```
### Arguments

- `--export-host`: The hostname or IP address of the Redis server you are exporting keys from (Required).
- `--import-host`: The hostname or IP address of the Redis server you are importing keys to (Required).
- `--db`: A comma-separated list of Redis database numbers to migrate (Required).
- `--scan-batch-size`: The batch size for the `SCAN` operation (default: 1000).
- `--chunk-size`: The size of the key chunks to be processed in parallel (default: 100).
- `--key-pattern`: Pattern to filter keys (default '*').

### Example

To migrate Redis keys from a database on a server at `export_redis_host` to another server at `import_redis_host`, transferring data from databases 0 and 1, you can run:
```bash
python3 redis_migrate_parallel.py --export-host keydb-s0-2 --import-host keydb-s0-0 --db 0,1,4,5,6,9,11,12,13 --scan-batch-size 2000 --chunk-size 500
```
This command will:

1. Export keys from databases 0 and 1 on the Redis server at `keydb-s0-2`.
2. Import those keys into the Redis server at `keydb-s0-0`.
3. Use a scan batch size of 2000 and process the keys in chunks of 500.

### How It Works

- The script connects to the source and target Redis servers and uses the `SCAN` command to iterate over keys in the source database.
- The keys are processed in chunks and migrated using Redis pipelining to ensure efficient transfer.
- It ensures that TTL values are preserved and applies the correct TTL to each key on the target Redis server.
- The process is parallelized using Python's `ThreadPoolExecutor` for improved performance, with each chunk being processed by a separate thread.
- If a key already exists on the target Redis server, it will be deleted and restored with the same TTL and value.

### Parallel Migration

The migration can be run in parallel for multiple databases. The `migrate_db_in_process` function runs each database migration in a separate process, allowing for efficient concurrent migrations.

## Requirements

- **Python 3.x**: Ensure you have Python 3.x installed.
- **Redis**: The Redis server(s) being used must be running and accessible from the machine running this script.

## Installation

1. Clone or download this repository.
2. Install the required dependencies:

    ```
    pip install redis
    ```
   or
   ```
   pip install -r requirements.txt
   ```

3. Run the script as shown in the examples above.

## License

This script is licensed under the MIT License. See the LICENSE file for details.
