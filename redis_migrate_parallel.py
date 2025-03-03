import redis
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Process

def process_chunk(source_redis, target_redis, keys, db):
    """
    Processes keys chunks using pipelining.
    """
    try:
        pipeline = target_redis.pipeline()
        for key in keys:
            if not source_redis.exists(key):
                continue
            serialized_value = source_redis.dump(key)
            if serialized_value is None:
                continue
            ttl = source_redis.pttl(key)
            ttl = 0 if ttl < 0 else ttl  # Set a permanent TTL if the key does not have one
            if target_redis.exists(key):
                target_redis.delete(key)  # Delete the existing key
            pipeline.restore(key, ttl, serialized_value)
        pipeline.execute()
    except redis.exceptions.ResponseError as e:
        print(f"[DB {db}] Error processing chunk: {e}")
    except Exception as e:
        print(f"[DB {db}] Unknown error: {e}")

def migrate_db(export_host, import_host, db, scan_batch_size=1000, chunk_size=100, key_pattern="*"):
    """
    Migrate keys from one Redis database to another using SCAN, chunks, and pipelining.
    """
    try:
        print(f"[DB {db}] Connecting to the servers...")
        source_redis = redis.Redis(host=export_host, port=6379, db=db)
        target_redis = redis.Redis(host=import_host, port=6379, db=db)

        print(f"[DB {db}] Starting the transfer...")
        cursor = 0
        migrated_keys = 0

        with ThreadPoolExecutor() as executor:
            futures = []
            while True:
                cursor, keys = source_redis.scan(cursor=cursor, match=key_pattern, count=scan_batch_size)
                # Breaking keys into chunks
                for i in range(0, len(keys), chunk_size):
                    chunk = keys[i:i + chunk_size]
                    futures.append(executor.submit(process_chunk, source_redis, target_redis, chunk, db))

                if cursor == 0:  # SCAN completed
                    break

            for future in as_completed(futures):
                try:
                    future.result()
                    migrated_keys += chunk_size
                except Exception as e:
                    print(f"[DB {db}] Error during processing: {e}")

        print(f"[DB {db}] Migration complete. Approximately {migrated_keys} keys migrated.")
    except Exception as e:
        print(f"[DB {db}] Error: {e}")

def migrate_db_in_process(export_host, import_host, db, scan_batch_size, chunk_size, key_pattern):
    """
    Wrapper for running database migration in a separate process.
    """
    process = Process(target=migrate_db, args=(export_host, import_host, db, scan_batch_size, chunk_size, key_pattern))
    process.start()
    return process

def main():
    parser = argparse.ArgumentParser(description="Script for transferring keys between servers while preserving TTL.")
    parser.add_argument('--export-host', required=True, help="Export Redis Host")
    parser.add_argument('--import-host', required=True, help="Import Redis Host")
    parser.add_argument('--db', required=True, help="List of databases to migrate (comma separated)")
    parser.add_argument('--scan-batch-size', type=int, default=1000, help="Batch size for SCAN (default 1000)")
    parser.add_argument('--chunk-size', type=int, default=100, help="Chunk size for parallel processing (default 100)")
    parser.add_argument('--key-pattern', type=str, default="*", help="Pattern to filter keys (default '*')")

    args = parser.parse_args()

    try:
        db_list = [int(db.strip()) for db in args.db.split(',')]
    except ValueError:
        print("Error: The database list must contain only integers.")
        sys.exit(1)

    processes = []
    for db in db_list:
        processes.append(migrate_db_in_process(args.export_host, args.import_host, db, args.scan_batch_size, args.chunk_size, args.key_pattern))

    for process in processes:
        process.join()

if __name__ == "__main__":
    main()
