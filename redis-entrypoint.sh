#!/bin/sh

# Create the log files
mkdir -p /logs/redis
touch /logs/redis/redis.log
chmod -R 644 /logs

# Start Redis with the provided configuration file
exec redis-server /usr/local/etc/redis/redis.conf
